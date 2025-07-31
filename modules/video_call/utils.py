import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db

logger = logging.getLogger("video_call.utils")

# In-memory storage for active video call WebSocket connections
active_calls: Dict[int, Dict[int, WebSocket]] = {}  # appointment_id -> {user_id: websocket}

async def connect_websocket(websocket: WebSocket, appointment_id: int, user_id: int):
    logger.info(f"WebSocket connect requested: appointment_id={appointment_id}, user_id={user_id}")
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
    appointment_data = dict(appointment)
    logger.info(f"Fetched appointment data json for appointment_id={appointment_id}: {appointment_data}")
    logger.info(f"patient_id={appointment['patient_id']}, doctor_id={appointment['doctor_id']}")
    if not appointment:
        logger.warning(f"Unauthorized WebSocket connection attempt: appointment_id={appointment_id}, user_id={user_id}")
        await websocket.close(code=1008, reason="Unauthorized or invalid appointment")
        raise ValueError("Unauthorized")

    if appointment_id not in active_calls:
        logger.info(f"current active call data: {active_calls}")
        logger.debug(f"Creating new active_calls entry for appointment_id={appointment_id} with user_id={user_id}")
        active_calls[appointment_id] = {user_id: websocket}
        logger.info(f"after adding appointment id active call data: {active_calls}")

    active_calls[appointment_id][user_id] = websocket
    logger.info(f"WebSocket connected: appointment_id={appointment_id}, user_id={user_id}")
    logger.debug(f"Current active_calls: {active_calls}")
    patient_id = appointment['patient_id']
    doctor_id = appointment['doctor_id']
    return doctor_id, patient_id

async def disconnect_websocket(appointment_id: int, user_id: int):
    """Handle WebSocket disconnection and update call status."""
    logger.info(f"Disconnecting WebSocket: appointment_id={appointment_id}, user_id={user_id}")
    if appointment_id in active_calls and user_id in active_calls[appointment_id]:
        del active_calls[appointment_id][user_id]
        logger.debug(f"Removed user_id={user_id} from active_calls[{appointment_id}]")
        if not active_calls[appointment_id]:
            logger.info(f"No more active users for appointment_id={appointment_id}, ending call in DB")
            del active_calls[appointment_id]
            # Update call status to ended
            async with db.get_connection() as conn:
                result = await conn.execute(
                    """
                    UPDATE video_calls SET end_time = CURRENT_TIMESTAMP, status = 'ended'
                    WHERE appointment_id = $1 AND status = 'active'
                    """,
                    appointment_id
                )
                logger.debug(f"Updated video_calls status to 'ended' for appointment_id={appointment_id}, DB result: {result}")