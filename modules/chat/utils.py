import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db

# Configure logger
logger = logging.getLogger("chat.utils")
logging.basicConfig(level=logging.INFO)

# In-memory storage for active WebSocket connections (for simplicity; use Redis in production)
active_connections: Dict[int, Dict[int, WebSocket]] = {}  # appointment_id -> {user_id: websocket}

async def get_user_role(user_id: int):
    """Determine if the user is a patient or doctor based on appointment."""
    logger.info(f"Getting user role for user_id={user_id}")
    async with db.get_connection() as conn:
        appointment = await conn.fetchrow(
            """
            SELECT user_id, doctor_id, status FROM appointments
            WHERE id = (
                SELECT appointment_id FROM chat_messages 
                WHERE sender_id = $1 OR receiver_id = $1
                ORDER BY id DESC
                LIMIT 1
            ) AND status = 'confirmed'
            """,
            user_id
        )
        logger.debug(f"Fetched appointment: {appointment}")
        if not appointment:
            logger.warning(f"No confirmed appointment found for user_id={user_id}")
            raise ValueError("No confirmed appointment found")
        if appointment["user_id"] == user_id:
            logger.info(f"user_id={user_id} is a patient")
            return "patient"
        elif appointment["doctor_id"] == user_id:
            logger.info(f"user_id={user_id} is a doctor")
            return "doctor"
        else:
            logger.warning(f"user_id={user_id} is neither patient nor doctor in appointment")
            return None

async def connect_websocket(websocket: WebSocket, appointment_id: int, user_id: int):
    """Manage WebSocket connection and authentication."""
    logger.info(f"Connecting websocket for appointment_id={appointment_id}, user_id={user_id}")
    await websocket.accept()
    try:
        user_role = await get_user_role(user_id)
    except Exception as e:
        logger.error(f"Error getting user role: {e}")
        await websocket.close(code=1008)
        raise

    if not user_role:
        logger.warning(f"Unauthorized user_id={user_id} for appointment_id={appointment_id}")
        await websocket.close(code=1008)
        raise ValueError("Unauthorized user for this appointment")

    if appointment_id not in active_connections:
        active_connections[appointment_id] = {}
        logger.debug(f"Created new active_connections entry for appointment_id={appointment_id}")
    active_connections[appointment_id][user_id] = websocket
    logger.info(f"WebSocket connected: appointment_id={appointment_id}, user_id={user_id}, role={user_role}")
    return user_role

async def disconnect_websocket(appointment_id: int, user_id: int):
    logger.info(f"Disconnecting websocket for appointment_id={appointment_id}, user_id={user_id}")
    logger.debug(f"Current active_connections before disconnect: {active_connections.keys()}")

    if appointment_id in active_connections:
        logger.debug(f"Appointment ID {appointment_id} found in active_connections.")
        if user_id in active_connections[appointment_id]:
            del active_connections[appointment_id][user_id]
            logger.debug(f"Removed user_id={user_id} from active_connections for appointment_id={appointment_id}")
            if not active_connections[appointment_id]:
                del active_connections[appointment_id]
                logger.debug(f"Removed empty active_connections entry for appointment_id={appointment_id}")
        else:
            logger.warning(f"User_id={user_id} not found for appointment_id={appointment_id} during disconnect.")
    else:
        logger.warning(f"Appointment_id={appointment_id} not found in active_connections during disconnect.")

    logger.debug(f"Active connections after disconnect: {active_connections.keys()}")