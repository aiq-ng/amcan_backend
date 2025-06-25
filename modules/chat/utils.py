# modules/chat/utils.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db

# In-memory storage for active WebSocket connections (for simplicity; use Redis in production)
active_connections: Dict[int, Dict[int, WebSocket]] = {}  # appointment_id -> {user_id: websocket}

async def get_user_role(websocket: WebSocket, user_id: int):
    """Determine if the user is a patient or doctor based on appointment."""
    async with db.get_connection() as conn:
        appointment = await conn.fetchrow(
            """
            SELECT user_id, doctor_id, status FROM appointments
            WHERE id = (SELECT appointment_id FROM chat_messages WHERE id = (
                SELECT MAX(id) FROM chat_messages WHERE appointment_id = (
                    SELECT appointment_id FROM chat_messages WHERE sender_id = $1 OR receiver_id = $1
                )
            )) AND status = 'confirmed'
            """,
            user_id
        )
        if not appointment:
            raise ValueError("No confirmed appointment found")
        return "patient" if appointment["user_id"] == user_id else "doctor" if appointment["doctor_id"] == user_id else None

async def connect_websocket(websocket: WebSocket, appointment_id: int, user_id: int):
    """Manage WebSocket connection and authentication."""
    await websocket.accept()
    user_role = await get_user_role(websocket, user_id)
    if not user_role:
        await websocket.close(code=1008)
        raise ValueError("Unauthorized user for this appointment")

    if appointment_id not in active_connections:
        active_connections[appointment_id] = {}
    active_connections[appointment_id][user_id] = websocket
    return user_role

async def disconnect_websocket(appointment_id: int, user_id: int):
    """Handle WebSocket disconnection."""
    if appointment_id in active_connections and user_id in active_connections[appointment_id]:
        del active_connections[appointment_id][user_id]
        if not active_connections[appointment_id]:
            del active_connections[appointment_id]