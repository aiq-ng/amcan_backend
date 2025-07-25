import logging
from .models import AppointmentCreate, AppointmentResponse
from shared.db import db
from datetime import datetime

logger = logging.getLogger(__name__)

class AppointmentManager:
    @staticmethod
    async def book_appointment(appointment: AppointmentCreate) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] book_appointment called for patient_id={appointment.patient_id}, doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")
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

                # Check availability by date and time
                slot_date = appointment.slot_time.date().isoformat()  # e.g., "2025-07-25"
                slot_time = appointment.slot_time.time().strftime("%H:%M")  # e.g., "14:30"
                logger.debug(f"[APPOINTMENT MANAGER] Checking slot_date={slot_date}, slot_time={slot_time}")

                # Compare with availability date and time
                avail_date = availability.get("date")
                avail_time = availability.get("time")
                logger.debug(f"[APPOINTMENT MANAGER] Availability date={avail_date}, time={avail_time}")
                if not avail_date or not avail_time or slot_date != avail_date or slot_time != avail_time:
                    logger.warning(f"[APPOINTMENT MANAGER] No availability for {slot_date} at {slot_time} (doctor_id={appointment.doctor_id})")
                    raise ValueError(f"No availability for {slot_date} at {slot_time} for doctor_id={appointment.doctor_id}, available is {avail_date} at {avail_time}")

                # Check if slot is already booked
                try:
                    # Convert offset-aware datetime to offset-naive for comparison
                    slot_time_naive = appointment.slot_time.replace(tzinfo=None)
                    existing = await conn.fetchrow(
                        """
                        SELECT 1 FROM appointments
                        WHERE doctor_id = $1 AND slot_time = $2
                        """,
                        appointment.doctor_id,
                        slot_time_naive
                    )
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error checking existing appointment: {e}")
                    raise RuntimeError(f"Database error checking existing appointment: {e}")

                if existing:
                    logger.warning(f"[APPOINTMENT MANAGER] Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")
                    raise ValueError(f"Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")

                # Book the appointment
                try:
                    # Convert offset-aware datetime to offset-naive for insertion
                    slot_time_naive = appointment.slot_time.replace(tzinfo=None)
                    row = await conn.fetchrow(
                        """
                        INSERT INTO appointments (doctor_id, patient_id, slot_time, status)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id, doctor_id, patient_id, slot_time, status, created_at
                        """,
                        appointment.doctor_id,
                        appointment.patient_id,
                        slot_time_naive,
                        'pending'
                    )
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Error inserting appointment: {e}")
                    raise RuntimeError(f"Database error inserting appointment: {e}")

                if not row:
                    logger.error(f"[APPOINTMENT MANAGER] Failed to book appointment for unknown reasons.")
                    raise RuntimeError("Failed to book appointment for unknown reasons.")

                # Fetch doctor details for response
                doctor_row = await conn.fetchrow(
                    """
                    SELECT d.id AS doctor_id, d.title AS doctor_title, d.bio AS doctor_bio, d.rating AS doctor_rating, d.location AS doctor_location,
                        d.first_name AS doctor_first_name, d.last_name AS doctor_last_name
                    FROM doctors d
                    WHERE d.id = $1
                    """,
                    appointment.doctor_id
                )
                if not doctor_row:
                    logger.warning(f"[APPOINTMENT MANAGER] Doctor not found for response: doctor_id={appointment.doctor_id}")
                    raise ValueError(f"Doctor not found for response: doctor_id={appointment.doctor_id}")

                response = dict(row)
                response.update(dict(doctor_row))

                logger.info(f"[APPOINTMENT MANAGER] Appointment booked: {response}")
                return response
        except Exception as exc:
            logger.exception(f"[APPOINTMENT MANAGER] Exception in book_appointment: {exc}")
            raise
    @staticmethod
    async def get_patient_appointments(patient_id: int) -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_patient_appointments called for patient_id={patient_id}")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                '''
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.slot_time,
                    a.complain,
                    a.status,
                    a.created_at,
                    d.id AS doctor_id,
                    d.first_name AS doctor_first_name,
                    d.last_name AS doctor_last_name,
                    d.title AS doctor_title,
                    d.bio AS doctor_bio,
                    d.rating AS doctor_rating,
                    d.location AS doctor_location,
                    d.profile_picture_url AS doctor_profile_picture_url,
                    p.first_name AS patient_first_name,
                    p.last_name AS patient_last_name,
                    asumm.diagnosis,
                    asumm.notes,
                    asumm.prescription,
                    asumm.follow_up_date
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN users u ON d.user_id = u.id
                JOIN patients p ON a.patient_id = p.user_id
                LEFT JOIN appointments_summary asumm ON a.doctor_id = asumm.doctor_id AND a.patient_id = asumm.patient_id
                WHERE a.patient_id = $1
                ORDER BY a.slot_time DESC
                ''',
                int(patient_id)
            )
            logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments for patient_id={patient_id}")
            return [dict(row) for row in rows]
        
    @staticmethod
    async def get_appointments_for_doctor(doctor_id: int) -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_appointments_for_doctor called for doctor_id={doctor_id}")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                '''
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.patient_id,
                    a.slot_time,
                    a.complain,
                    a.status,
                    a.created_at,
                    d.first_name AS doctor_first_name,
                    d.last_name AS doctor_last_name,
                    d.title AS doctor_title,
                    d.location AS doctor_location,
                    p.first_name AS patient_first_name,
                    p.last_name AS patient_last_name,
                    asumm.diagnosis,
                    asumm.notes,
                    asumm.prescription,
                    asumm.follow_up_date
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN patients p ON a.patient_id = p.user_id
                LEFT JOIN appointments_summary asumm ON a.doctor_id = asumm.doctor_id AND a.patient_id = asumm.patient_id
                WHERE a.doctor_id = $1
                ORDER BY a.slot_time DESC;
                ''',
                doctor_id
            )
            logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments for doctor_id={doctor_id}")
            return [dict(row) for row in rows]

    @staticmethod
    async def confirm_appointment(appointment_id: int, doctor_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] confirm_appointment called for appointment_id={appointment_id}, doctor_id={doctor_id}")
        try:
            async with db.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE appointments
                    SET status = 'confirmed'
                    WHERE id = $1 AND doctor_id = $2 AND status IN ('pending', 'cancelled')
                    """,
                    appointment_id,
                    doctor_id
                )
                
        except Exception as e:
            logger.error(f"[APPOINTMENT MANAGER] Error confirming appointment: {e}")
        logger.info(f"[APPOINTMENT MANAGER] Appointment confirmed: {(row)}")
        return {"doctor_id": doctor_id, "appointment_id": appointment_id}
    
    @staticmethod
    async def cancel_appointment(appointment_id: int, doctor_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] cancel_appointment called for appointment_id={appointment_id}, doctor_id={doctor_id}")
        
        try:
            async with db.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE appointments
                    SET status = 'cancelled'
                    WHERE id = $1 AND doctor_id = $2 AND status IN ('pending', 'confirmed')
                    RETURNING id, doctor_id, patient_id, slot_time, status, created_at
                    """,
                    appointment_id,
                    doctor_id
                )
                if row:
                    return dict(row)  # return actual updated row
                else:
                    logger.warning(f"No appointment updated for id={appointment_id} and doctor_id={doctor_id}")
                    return {"error": "No matching appointment found or already cancelled"}
        except Exception as e:
            logger.error(f"[APPOINTMENT MANAGER] Error cancelling appointment: {e}")
            return {"error": str(e)}


    @staticmethod
    async def get_all_appointments() -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_all_appointments called (admin)")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                '''
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.patient_id,
                    a.slot_time,
                    a.complain,
                    a.status,
                    a.created_at,
                    d.first_name AS doctor_first_name,
                    d.last_name AS doctor_last_name,
                    d.title AS doctor_title,
                    d.bio AS doctor_bio,
                    d.rating AS doctor_rating,
                    d.location AS doctor_location,
                    d.profile_picture_url AS doctor_profile_picture_url,
                    p.first_name AS patient_first_name,
                    p.last_name AS patient_last_name,
                    asumm.diagnosis,
                    asumm.notes,
                    asumm.prescription,
                    asumm.follow_up_date
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN patients p ON a.patient_id = p.user_id
                LEFT JOIN appointments_summary asumm ON a.doctor_id = asumm.doctor_id AND a.patient_id = asumm.patient_id
                ORDER BY a.slot_time DESC
                '''
            )
            logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments (admin)")
            return [dict(row) for row in rows]

    @staticmethod
    async def get_appointment_by_id(appointment_id: int, current_user: dict) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] get_appointment_by_id called for appointment_id={appointment_id} by user_id={current_user['id']}")
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                '''
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.user_id,
                    a.slot_time,
                    a.status,
                    a.created_at,
                    d.id AS doctor_id,
                    d.title AS doctor_title,
                    d.bio AS doctor_bio,
                    d.rating AS doctor_rating,
                    d.location AS doctor_location
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.id = $1
                ''',
                appointment_id
            )
            if not row:
                logger.warning(f"[APPOINTMENT MANAGER] Appointment not found: {appointment_id}")
                raise ValueError("Appointment not found")
            appt = dict(row)
            # Only allow if current user is admin or the user who booked the appointment
            if not (current_user["is_admin"] or appt["user_id"] == current_user["id"]):
                logger.warning(f"[APPOINTMENT MANAGER] Unauthorized access to appointment_id={appointment_id} by user_id={current_user['id']}")
                raise ValueError("Not authorized to view this appointment")
            logger.info(f"[APPOINTMENT MANAGER] Appointment retrieved: {appointment_id}")
            return appt