import logging
from .models import AppointmentCreate, AppointmentResponse
from shared.db import db
from datetime import datetime

logger = logging.getLogger(__name__)

class AppointmentManager:
    @staticmethod
    async def book_appointment(appointment: AppointmentCreate, user_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] book_appointment called for user_id={user_id}, doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")
        try:
            async with db.get_connection() as conn:
                # Check availability (ensure slot_time is within doctor's availability)
                try:
                    doctor = await conn.fetchrow(
                        "SELECT availability FROM doctors WHERE id = $1",
                        appointment.doctor_id
                    )
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error fetching doctor: {e}")
                    raise RuntimeError(f"Database error fetching doctor: {e}")

                if not doctor:
                    logger.warning(f"[APPOINTMENT MANAGER] Doctor not found: doctor_id={appointment.doctor_id}")
                    raise ValueError(f"Doctor not found (doctor_id={appointment.doctor_id})")

                import json
                try:
                    availability = json.loads(doctor["availability"])
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error parsing doctor availability: {e}")
                    raise ValueError(f"Invalid doctor availability format: {e}")

                logger.debug(f"[APPOINTMENT MANAGER] Doctor availability for doctor_id={appointment.doctor_id}: {availability}")

                try:
                    slot_day = appointment.slot_time.strftime("%a")  # e.g., 'Mon'
                    slot_time = appointment.slot_time.strftime("%-I:%M%p").replace("AM", "AM").replace("PM", "PM")  # e.g., '9:00AM'
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error formatting slot_time: {e}")
                    raise ValueError(f"Invalid slot_time format: {e}")

                logger.debug(f"[APPOINTMENT MANAGER] Requested slot_day={slot_day}, slot_time={slot_time}")

                # Find the matching day in availability
                try:
                    day_avail = next((item for item in availability if item["day"] == slot_day), None)
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error searching for day in availability: {e}")
                    raise ValueError(f"Error searching for day in availability: {e}")

                if not day_avail:
                    logger.warning(f"[APPOINTMENT MANAGER] No availability for day: {slot_day} (doctor_id={appointment.doctor_id})")
                if not day_avail or slot_time not in day_avail.get("slots", []):
                    logger.warning(f"[APPOINTMENT MANAGER] Slot not available: {slot_time} on {slot_day} for doctor_id={appointment.doctor_id}")
                    raise ValueError(f"Slot not available: {slot_time} on {slot_day} for doctor_id={appointment.doctor_id}")

                # Check if slot is already booked
                try:
                    existing = await conn.fetchrow(
                        """
                        SELECT 1 FROM appointments
                        WHERE doctor_id = $1 AND slot_time = $2
                        """,
                        appointment.doctor_id,
                        appointment.slot_time
                    )
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error checking existing appointment: {e}")
                    raise RuntimeError(f"Database error checking existing appointment: {e}")

                if existing:
                    logger.warning(f"[APPOINTMENT MANAGER] Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")
                    raise ValueError(f"Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")

                try:
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
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error inserting appointment: {e}")
                    raise RuntimeError(f"Database error inserting appointment: {e}")

                if not row:
                    logger.error(f"[APPOINTMENT MANAGER] Failed to book appointment for unknown reasons.")
                    raise RuntimeError("Failed to book appointment for unknown reasons.")

                logger.info(f"[APPOINTMENT MANAGER] Appointment booked: {dict(row)}")
                return dict(row)
        except Exception as exc:
            logger.exception(f"[APPOINTMENT MANAGER] Exception in book_appointment: {exc}")
            raise

    @staticmethod
    async def get_appointments(user_id: int) -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_appointments called for user_id={user_id}")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, doctor_id, user_id, slot_time, status, created_at
                FROM appointments WHERE user_id = $1
                ORDER BY slot_time DESC
                """,
                user_id
            )
            logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments for user_id={user_id}")
            return [dict(row) for row in rows]
        

    @staticmethod
    async def confirm_appointment(appointment_id: int, user_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] confirm_appointment called for appointment_id={appointment_id}, user_id={user_id}")
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
                logger.warning(f"[APPOINTMENT MANAGER] Appointment not found or cannot be confirmed: appointment_id={appointment_id}, user_id={user_id}")
                raise ValueError("Appointment not found or cannot be confirmed")
            logger.info(f"[APPOINTMENT MANAGER] Appointment confirmed: {dict(row)}")
            return dict(row)

    @staticmethod
    async def cancel_appointment(appointment_id: int, user_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] cancel_appointment called for appointment_id={appointment_id}, user_id={user_id}")
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
                logger.warning(f"[APPOINTMENT MANAGER] Appointment not found or cannot be cancelled: appointment_id={appointment_id}, user_id={user_id}")
                raise ValueError("Appointment not found or cannot be cancelled")
            logger.info(f"[APPOINTMENT MANAGER] Appointment cancelled: {dict(row)}")
            return dict(row)