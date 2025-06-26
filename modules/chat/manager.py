# modules/chat/manager.py
from .models import MessageCreate, MessageResponse
from .utils import active_connections
from shared.db import db

class ChatManager:
    @staticmethod
    async def send_message(message: MessageCreate, sender_id: int) -> dict:
        async with db.get_connection() as conn:
            # Verify appointment exists and is confirmed
            appointment = await conn.fetchrow(
                """
                SELECT id, status FROM appointments
                WHERE id = $1 AND (user_id = $2 OR doctor_id = $2) AND status = 'confirmed'
                """,
                message.appointment_id,
                sender_id
            )
            if not appointment:
                raise ValueError("No confirmed appointment found for this user and doctor")

            # Determine receiver based on appointment
            doctor_id = await conn.fetchval(
                "SELECT doctor_id FROM appointments WHERE id = $1",
                message.appointment_id
            )
            receiver_id = doctor_id if sender_id != doctor_id else await conn.fetchval(
                "SELECT user_id FROM appointments WHERE id = $1",
                message.appointment_id
            )
            print('first receiver_id:', receiver_id)

            if receiver_id==doctor_id:
                receiver_id = await conn.fetchval(
                    "SELECT user_id FROM doctors WHERE id = $1",
                    doctor_id
                )
                print(f"Receiver ID determined as: {receiver_id}")

            row = await conn.fetchrow(
                """
                INSERT INTO chat_messages (appointment_id, sender_id, receiver_id, message)
                VALUES ($1, $2, $3, $4)
                RETURNING id, appointment_id, sender_id, receiver_id, message, sent_at
                """,
                message.appointment_id,
                sender_id,
                receiver_id,
                message.message
            )
            return dict(row)

    @staticmethod
    async def get_chat_history(appointment_id: int, user_id: int) -> list:
        async with db.get_connection() as conn:
            # Verify user is part of the appointment
            appointment = await conn.fetchrow(
                """
                SELECT id, status FROM appointments
                WHERE id = $1 AND (user_id = $2 OR doctor_id = $2) AND status = 'confirmed'
                """,
                appointment_id,
                user_id
            )
            if not appointment:
                raise ValueError("No confirmed appointment found for this user")

            rows = await conn.fetch(
                """
                SELECT id, appointment_id, sender_id, receiver_id, message, sent_at
                FROM chat_messages
                WHERE appointment_id = $1
                ORDER BY sent_at ASC
                """,
                appointment_id
            )
            return [dict(row) for row in rows]


    @staticmethod
    async def save_message(appointment_id: int, sender_id: int, receiver_id: int, message: str) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO chat_messages (appointment_id, sender_id, receiver_id, message)
                VALUES ($1, $2, $3, $4)
                RETURNING id, appointment_id, sender_id, receiver_id, message, sent_at
                """,
                appointment_id,
                sender_id,
                receiver_id,
                message
            )
            return dict(row)

    # You should define active_connections at the module level or import it if managed elsewhere.
    # Here is a simple in-memory example:
    # active_connections = {}

    @staticmethod
    async def broadcast_message(appointment_id: int, message_data: dict):
        import datetime
        import copy

        # Convert datetime objects to ISO format strings
        def serialize(obj):
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return obj

        safe_message_data = serialize(copy.deepcopy(message_data))

        if appointment_id in active_connections:
            for _, websocket in active_connections[appointment_id].items():
                await websocket.send_json(safe_message_data)