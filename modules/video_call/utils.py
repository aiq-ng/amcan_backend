# modules/video_call/utils.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db

# In-memory storage for active video call WebSocket connections
active_calls: Dict[int, Dict[int, WebSocket]] = {}  # appointment_id -> {user_id: websocket}

async def connect_websocket(websocket: WebSocket, appointment_id: int, user_id: int):
    """Manage WebSocket connection and authentication for video calls."""
    await websocket.accept()
    # Verify appointment and user
    async with db.get_connection() as conn:
        appointment = await conn.fetchrow(
            """
            SELECT user_id, doctor_id, status FROM appointments
            WHERE id = $1 AND status = 'confirmed'
            """,
            appointment_id
        )
        if not appointment or (user_id not in (appointment["user_id"], appointment["doctor_id"])):
            await websocket.close(code=1008, reason="Unauthorized or invalid appointment")
            raise ValueError("Unauthorized")

    if appointment_id not in active_calls:
        active_calls[appointment_id] = {}
    active_calls[appointment_id][user_id] = websocket
    return appointment["user_id"], appointment["doctor_id"]

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