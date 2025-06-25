from .models import AppointmentCreate, AppointmentResponse
from shared.db import db
from datetime import datetime

class AppointmentManager:
    @staticmethod
    async def book_appointment(appointment: AppointmentCreate, user_id: int) -> dict:
        async with db.get_connection() as conn:
            # Check availability (ensure slot_time is within doctor's availability)
            doctor = await conn.fetchrow(
                "SELECT availability FROM doctors WHERE id = $1",
                appointment.doctor_id
            )
            if not doctor:
                raise ValueError("Doctor not found")
            import json
            availability = json.loads(doctor["availability"])

            slot_day = appointment.slot_time.strftime("%a")  # e.g., 'Mon'
            slot_time = appointment.slot_time.strftime("%-I:%M%p").replace("AM", "AM").replace("PM", "PM")  # e.g., '9:00AM'

            # Find the matching day in availability
            day_avail = next((item for item in availability if item["day"] == slot_day), None)
            if not day_avail or slot_time not in day_avail["slots"]:
                raise ValueError("Slot not available")

            # Check if slot is already booked
            existing = await conn.fetchrow(
                """
                SELECT 1 FROM appointments
                WHERE doctor_id = $1 AND slot_time = $2
                """,
                appointment.doctor_id,
                appointment.slot_time
            )
            if existing:
                raise ValueError("Slot already booked")

            row = await conn.fetchrow(
                """
                INSERT INTO appointments (doctor_id, user_id, slot_time, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id, doctor_id, user_id, slot_time, status, created_at
                """,
                appointment.doctor_id,
                user_id,
                appointment.slot_time,
                'pending'
            )
            return dict(row)

    @staticmethod
    async def get_appointments(user_id: int) -> list:
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, doctor_id, user_id, slot_time, status, created_at
                FROM appointments WHERE user_id = $1
                ORDER BY slot_time DESC
                """,
                user_id
            )
            return [dict(row) for row in rows]
        

    @staticmethod
    async def confirm_appointment(appointment_id: int, user_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE appointments
                SET status = 'confirmed'
                WHERE id = $1 AND user_id = $2 AND status IN ('pending', 'cancelled')
                RETURNING id, doctor_id, user_id, slot_time, status, created_at
                """,
                appointment_id,
                user_id
            )
            if not row:
                raise ValueError("Appointment not found or cannot be confirmed")
            return dict(row)

    @staticmethod
    async def cancel_appointment(appointment_id: int, user_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE appointments
                SET status = 'cancelled'
                WHERE id = $1 AND user_id = $2 AND status IN ('pending', 'confirmed')
                RETURNING id, doctor_id, user_id, slot_time, status, created_at
                """,
                appointment_id,
                user_id
            )
            if not row:
                raise ValueError("Appointment not found or cannot be cancelled")
            return dict(row)