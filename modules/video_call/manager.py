import logging
from .models import CallInitiate, CallResponse
from shared.db import db
from datetime import datetime

from .utils import active_calls

logger = logging.getLogger(__name__)

class VideoCallManager:
    @staticmethod
    async def initiate_call(appointment_id: int, initiator_id: int, receiver_id: int) -> dict:
        logger.info(f"Initiating call: appointment_id={appointment_id}, initiator_id={initiator_id}, receiver_id={receiver_id}")
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO video_calls (appointment_id, initiator_id, receiver_id, start_time, status)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4)
                RETURNING id, appointment_id, initiator_id, receiver_id, start_time, end_time, status, created_at
                """,
                appointment_id,
                initiator_id,
                receiver_id,
                'initiated'
            )
            logger.debug(f"Call initiated, DB row: {row}")
            return dict(row)

    @staticmethod
    async def update_call_status(appointment_id: int, status: str):
        logger.info(f"Updating call status: appointment_id={appointment_id}, new_status={status}")
        async with db.get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE video_calls SET status = $1, start_time = CURRENT_TIMESTAMP
                WHERE appointment_id = $2 AND status = 'initiated'
                """,
                status,
                appointment_id
            )
            logger.debug(f"Update result: {result}")

    @staticmethod
    async def broadcast_signal(appointment_id: int, signal_data: dict):
        logger.info(f"Broadcasting signal for appointment_id={appointment_id}, signal_data={signal_data}")
        logger.info(f"checking active calls: {active_calls}")
        if appointment_id in active_calls:
            for user_id, websocket in active_calls[appointment_id].items():
                logger.debug(f"Sending signal to user_id={user_id}")
                await websocket.send_json(signal_data)
        else:
            logger.warning(f"No active calls found for appointment_id={appointment_id}")