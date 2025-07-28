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
                # Check if doctor exists
                doctor = await conn.fetchrow(
                    "SELECT id FROM doctors WHERE id = $1",
                    appointment.doctor_id
                )
                if not doctor:
                    logger.warning(f"[APPOINTMENT MANAGER] Doctor not found: doctor_id={appointment.doctor_id}")
                    raise ValueError(f"Doctor not found (doctor_id={appointment.doctor_id})")

                # Check availability in doctor_availability_slots
                slot_time_naive = appointment.slot_time.replace(tzinfo=None)
                availability = await conn.fetchrow(
                    """
                    SELECT id, status FROM doctor_availability_slots
                    WHERE doctor_id = $1 AND available_at = $2
                    """,
                    appointment.doctor_id,
                    slot_time_naive
                )

                currently_available = await conn.fetchrow(
                    """
                    SELECT available_at FROM doctor_availability_slots 
                    WHERE doctor_id = $1 AND status = 'available'
                    """,
                    appointment.doctor_id
                )
                if not availability:
                    logger.warning(f"[APPOINTMENT MANAGER] No availability for slot_time={appointment.slot_time} (doctor_id={appointment.doctor_id})")
                    raise ValueError(f"No availability for {appointment.slot_time} for doctor_id={appointment.doctor_id}")
                if availability['status'] != 'available':
                    logger.warning(f"[APPOINTMENT MANAGER] Slot not available: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}, status={availability['status']}")
                    raise ValueError(f"Slot not available: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}, status={availability['status']}: available: {currently_available}")

                # Check if slot is already booked
                existing = await conn.fetchrow(
                    """
                    SELECT 1 FROM appointments
                    WHERE doctor_id = $1 AND slot_time = $2
                    """,
                    appointment.doctor_id,
                    slot_time_naive
                )
                if existing:
                    logger.warning(f"[APPOINTMENT MANAGER] Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time}")
                    raise ValueError(f"Slot already booked: doctor_id={appointment.doctor_id}, slot_time={appointment.slot_time} available: {availability}")

                # Update availability slot status to 'booked'
                await conn.execute(
                    """
                    UPDATE doctor_availability_slots
                    SET status = 'booked'
                    WHERE id = $1
                    """,
                    availability['id']
                )

                # Book the appointment
                row = await conn.fetchrow(
                    """
                    INSERT INTO appointments (doctor_id, patient_id, slot_time, complain, status)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, doctor_id, patient_id, slot_time, complain, status, created_at
                    """,
                    appointment.doctor_id,
                    appointment.patient_id,
                    slot_time_naive,
                    appointment.complain,
                    'pending'
                )
                if not row:
                    logger.error(f"[APPOINTMENT MANAGER] Failed to book appointment for unknown reasons.")
                    raise RuntimeError("Failed to book appointment for unknown reasons.")

                # Fetch doctor details for response
                doctor_row = await conn.fetchrow(
                    """
                    SELECT d.id AS doctor_id, d.title AS doctor_title, d.bio AS doctor_bio, d.rating AS doctor_rating, 
                           d.location AS doctor_location, d.first_name AS doctor_first_name, d.last_name AS doctor_last_name
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
                if 'created_at' in response and isinstance(response['created_at'], datetime):
                    response['created_at'] = response['created_at'].isoformat()
                if 'slot_time' in response and isinstance(response['slot_time'], datetime):
                    response['slot_time'] = response['slot_time'].isoformat()

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
                """
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.patient_id,
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
                JOIN patients p ON a.patient_id = p.user_id
                LEFT JOIN appointments_summary asumm ON a.id = asumm.id
                WHERE a.patient_id = $1
                ORDER BY a.slot_time DESC
                """,
                int(patient_id)
            )
            result = [dict(row) for row in rows]
            # for row in result:
            #     if 'created_at' in row and isinstance(row['created_at'], datetime):
            #         row['created_at'] = row['created_at'].isoformat()
            #     if 'slot_time' in row and isinstance(row['slot_time'], datetime):
            #         row['slot_time'] = row['slot_time'].isoformat()
            #     if 'follow_up_date' in row and isinstance(row['follow_up_date'], datetime):
            #         row['follow_up_date'] = row['follow_up_date'].isoformat()
            # logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments for patient_id={patient_id}")
            return result
        
    @staticmethod
    async def get_appointments_for_doctor(doctor_id: int) -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_appointments_for_doctor called for doctor_id={doctor_id}")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
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
                JOIN patients p ON a.patient_id = p.id
                LEFT JOIN appointments_summary asumm ON a.id = asumm.id
                WHERE a.doctor_id = $1
                ORDER BY a.slot_time DESC
                """,
                doctor_id
            )
            result = [dict(row) for row in rows]
            # for row in result:
            #     if 'created_at' in row and isinstance(row['created_at'], datetime):
            #         row['created_at'] = row['created_at'].isoformat()
            #     if 'slot_time' in row and isinstance(row['slot_time'], datetime):
            #         row['slot_time'] = row['slot_time'].isoformat()
            #     if 'follow_up_date' in row and isinstance(row['follow_up_date'], datetime):
            #         row['follow_up_date'] = row['follow_up_date'].isoformat()
            # logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments for doctor_id={doctor_id}")
            return result

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
                    RETURNING id, doctor_id, patient_id, slot_time, complain, status, created_at
                    """,
                    appointment_id,
                    doctor_id
                )
                if row:
                    result = dict(row)
                    if 'created_at' in result and isinstance(result['created_at'], datetime):
                        result['created_at'] = result['created_at'].isoformat()
                    if 'slot_time' in result and isinstance(result['slot_time'], datetime):
                        result['slot_time'] = result['slot_time'].isoformat()
                    logger.info(f"[APPOINTMENT MANAGER] Appointment confirmed: {result}")
                    return result
                logger.warning(f"[APPOINTMENT MANAGER] No appointment updated for id={appointment_id} and doctor_id={doctor_id}")
                return {"error": "No matching appointment found or status not updatable"}
        except Exception as e:
            logger.error(f"[APPOINTMENT MANAGER] Error confirming appointment: {e}")
            raise
    
    @staticmethod
    async def cancel_appointment(appointment_id: int, doctor_id: int) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] cancel_appointment called for appointment_id={appointment_id}, doctor_id={doctor_id}")
        try:
            async with db.get_connection() as conn:
                # Fetch the appointment to get slot_time for updating doctor_availability_slots
                appointment = await conn.fetchrow(
                    """
                    SELECT slot_time FROM appointments
                    WHERE id = $1 AND doctor_id = $2
                    """,
                    appointment_id,
                    doctor_id
                )
                if not appointment:
                    logger.warning(f"[APPOINTMENT MANAGER] No appointment found for id={appointment_id} and doctor_id={doctor_id}")
                    return {"error": "No matching appointment found"}

                # Update the corresponding availability slot back to 'available'
                await conn.execute(
                    """
                    UPDATE doctor_availability_slots
                    SET status = 'available'
                    WHERE doctor_id = $1 AND available_at = $2
                    """,
                    doctor_id,
                    appointment['slot_time']
                )

                # Cancel the appointment
                row = await conn.fetchrow(
                    """
                    UPDATE appointments
                    SET status = 'cancelled'
                    WHERE id = $1 AND doctor_id = $2 AND status IN ('pending', 'confirmed')
                    RETURNING id, doctor_id, patient_id, slot_time, complain, status, created_at
                    """,
                    appointment_id,
                    doctor_id
                )
                if row:
                    result = dict(row)
                    if 'created_at' in result and isinstance(result['created_at'], datetime):
                        result['created_at'] = result['created_at'].isoformat()
                    if 'slot_time' in result and isinstance(result['slot_time'], datetime):
                        result['slot_time'] = result['slot_time'].isoformat()
                    logger.info(f"[APPOINTMENT MANAGER] Appointment cancelled: {result}")
                    return result
                logger.warning(f"[APPOINTMENT MANAGER] No appointment updated for id={appointment_id} and doctor_id={doctor_id}")
                return {"error": "No matching appointment found or already cancelled"}
        except Exception as e:
            logger.error(f"[APPOINTMENT MANAGER] Error cancelling appointment: {e}")
            raise

    @staticmethod
    async def get_all_appointments() -> list:
        logger.info(f"[APPOINTMENT MANAGER] get_all_appointments called (admin)")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
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
                    t.therapy_type AS therapy_name,
                    u.email AS patient_email,
                    asumm.diagnosis,
                    asumm.notes,
                    asumm.prescription,
                    asumm.follow_up_date
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN patients p ON a.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                LEFT JOIN therapy t ON p.therapy_type = t.id
                LEFT JOIN appointments_summary asumm ON a.id = asumm.id
                ORDER BY a.slot_time DESC
                """
            )
            result = [dict(row) for row in rows]
            # for row in result:
            #     if 'created_at' in row and isinstance(row['created_at'], datetime):
            #         row['created_at'] = row['created_at'].isoformat()
            #     if 'slot_time' in row and isinstance(row['slot_time'], datetime):
            #         row['slot_time'] = row['slot_time'].isoformat()
            #     if 'follow_up_date' in row and isinstance(row['follow_up_date'], datetime):
            #         row['follow_up_date'] = row['follow_up_date'].isoformat()
            # logger.info(f"[APPOINTMENT MANAGER] Retrieved {len(rows)} appointments (admin)")
            return result

    @staticmethod
    async def get_appointment_by_id(appointment_id: int, current_user: dict) -> dict:
        logger.info(f"[APPOINTMENT MANAGER] get_appointment_by_id called for appointment_id={appointment_id} by user_id={current_user['id']}")
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.id AS appointment_id,
                    a.doctor_id,
                    a.patient_id,
                    a.slot_time,
                    a.complain,
                    a.status,
                    a.created_at,
                    d.id AS doctor_id,
                    d.title AS doctor_title,
                    d.bio AS doctor_bio,
                    d.rating AS doctor_rating,
                    d.location AS doctor_location,
                    d.first_name AS doctor_first_name,
                    d.last_name AS doctor_last_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.id = $1
                """,
                appointment_id
            )
            if not row:
                logger.warning(f"[APPOINTMENT MANAGER] Appointment not found: {appointment_id}")
                raise ValueError("Appointment not found")
            appt = dict(row)
            # Only allow if current user is admin or the patient who booked the appointment
            if not (current_user["is_admin"] or appt["patient_id"] == current_user["id"]):
                logger.warning(f"[APPOINTMENT MANAGER] Unauthorized access to appointment_id={appointment_id} by user_id={current_user['id']}")
                raise ValueError("Not authorized to view this appointment")
            if 'created_at' in appt and isinstance(appt['created_at'], datetime):
                appt['created_at'] = appt['created_at'].isoformat()
            if 'slot_time' in appt and isinstance(appt['slot_time'], datetime):
                appt['slot_time'] = appt['slot_time'].isoformat()
            logger.info(f"[APPOINTMENT MANAGER] Appointment retrieved: {appointment_id}")
            return appt