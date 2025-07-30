from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db

# In-memory storage for active video call WebSocket connections
active_calls: Dict[int, Dict[int, WebSocket]] = {}  # appointment_id -> {user_id: websocket}

async def connect_websocket(websocket: WebSocket, appointment_id: int, user_id: int):
    print("WebSocket connected", appointment_id, user_id)
    """Manage WebSocket connection and authentication for video calls."""
    # REMOVED: await websocket.accept() - It's now called in the router endpoint before this function.
    # If the router endpoint *didn't* call accept(), you'd keep it here.
    # But given your router's flow (receiving initial_data immediately after connection),
    # the router endpoint is the correct place for the first (and only) accept().

    # Verify appointment and user
    async with db.get_connection() as conn:
        appointment = await conn.fetchrow(
            """
            SELECT patient_id, doctor_id, status FROM appointments
            WHERE id = $1 AND status = 'confirmed'
            """,
            appointment_id
        )
        print("****appointment data", appointment)
        if not appointment:
            await websocket.close(code=1008, reason="Appointment not found or not confirmed")
            return None, None
        if user_id not in (appointment["patient_id"], appointment["doctor_id"]):
            await websocket.close(code=1008, reason="Unauthorized: user not part of appointment")
            return None, None

    if appointment_id not in active_calls:
        active_calls[appointment_id] = {}
    active_calls[appointment_id][user_id] = websocket
    return appointment["patient_id"], appointment["doctor_id"]

async def disconnect_websocket(appointment_id: int, user_id: int):
    """Handle WebSocket disconnection and update call status."""
    if appointment_id in active_calls and user_id in active_calls[appointment_id]:
        del active_calls[appointment_id][user_id]
        if not active_calls[appointment_id]:
            del active_calls[appointment_id]
            # Update call status to ended
            async with db.get_connection() as conn:
                await conn.execute(
                    """
                    UPDATE video_calls SET end_time = CURRENT_TIMESTAMP, status = 'ended'
                    WHERE appointment_id = $1 AND status = 'active'
                    """,
                    appointment_id
                )