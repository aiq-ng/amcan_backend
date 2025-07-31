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
    async def get_all_appointments(
        doctor_id: int = None,
        patient_id: int = None,
        status: str = None,
        slot_time_from: datetime = None,
        slot_time_to: datetime = None,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        created_at_from: datetime = None,
        created_at_to: datetime = None,
    ) -> dict:
        """
        Get all appointments with optional filters and pagination.
        Returns a dict with 'data', 'total', 'page', 'page_size'.
        """
        logger.info(
            f"[APPOINTMENT MANAGER] get_all_appointments called (admin) with filters: "
            f"doctor_id={doctor_id}, patient_id={patient_id}, status={status}, "
            f"slot_time_from={slot_time_from}, slot_time_to={slot_time_to}, "
            f"created_at_from={created_at_from}, created_at_to={created_at_to}, "
            f"page={page}, page_size={page_size}, search={search}"
        )
        filters = []
        params = []
        param_idx = 1

        if doctor_id is not None:
            filters.append(f"a.doctor_id = ${param_idx}")
            params.append(doctor_id)
            param_idx += 1
        if patient_id is not None:
            filters.append(f"a.patient_id = ${param_idx}")
            params.append(patient_id)
            param_idx += 1
        if status is not None:
            filters.append(f"a.status = ${param_idx}")
            params.append(status)
            param_idx += 1
        if slot_time_from is not None:
            filters.append(f"a.slot_time >= ${param_idx}")
            params.append(slot_time_from)
            param_idx += 1
        if slot_time_to is not None:
            filters.append(f"a.slot_time <= ${param_idx}")
            params.append(slot_time_to)
            param_idx += 1
        if created_at_from is not None:
            filters.append(f"a.created_at >= ${param_idx}")
            params.append(created_at_from)
            param_idx += 1
        if created_at_to is not None:
            filters.append(f"a.created_at <= ${param_idx}")
            params.append(created_at_to)
            param_idx += 1
        if search:
            # Search in doctor or patient name or complain
            filters.append(
                f"(d.first_name ILIKE ${param_idx} OR d.last_name ILIKE ${param_idx} "
                f"OR p.first_name ILIKE ${param_idx} OR p.last_name ILIKE ${param_idx} "
                f"OR a.complain ILIKE ${param_idx})"
            )
            params.append(f"%{search}%")
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        offset = (page - 1) * page_size

        # Count query for total
        count_query = f"""
            SELECT COUNT(*) FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            LEFT JOIN therapy t ON p.therapy_type = t.id
            LEFT JOIN appointments_summary asumm ON a.id = asumm.id
            {where_clause}
        """

        # Data query with pagination
        data_query = f"""
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
            {where_clause}
            ORDER BY a.slot_time DESC
            LIMIT {page_size} OFFSET {offset}
        """

        async with db.get_connection() as conn:
            total = await conn.fetchval(count_query, *params)
            rows = await conn.fetch(data_query, *params)
            result = [dict(row) for row in rows]
            meta_data = {"total": total,
                "page": page,
                "page_size": page_size,}
            return {
                "appointments": result,
                "meta": meta_data,
            }

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

    @staticmethod
    async def reschedule_appointment(appointment_id: int, new_slot_time: datetime, current_user: dict) -> dict:
        """
        Reschedule an appointment by updating its slot_time.
        Only the patient who booked the appointment, the doctor in the appointment, or an admin can reschedule.
        Also updates the doctor_availability_slots table accordingly.
        """
        logger.info(f"[APPOINTMENT MANAGER] reschedule_appointment called for appointment_id={appointment_id} by user_id={current_user['id']} to new_slot_time={new_slot_time!r}")
        async with db.get_connection() as conn:
            # Fetch the appointment
            appt = await conn.fetchrow(
                "SELECT * FROM appointments WHERE id = $1",
                appointment_id
            )
            if not appt:
                logger.warning(f"[APPOINTMENT MANAGER] Appointment not found: {appointment_id}")
                raise ValueError("Appointment not found")
            # # Only allow if current user is admin, the patient who booked the appointment, or the doctor in the appointment
            # is_admin = current_user.get("is_admin", False)
            # is_patient = appt["patient_id"] == current_user.get("id")
            # is_doctor = (
            #     (current_user.get("doctor_id") is not None and appt["doctor_id"] == current_user.get("doctor_id"))
            #     or (appt["doctor_id"] == current_user.get("id"))
            # )
            # if not (is_admin or is_patient or is_doctor):
            #     logger.warning(f"[APPOINTMENT MANAGER] Unauthorized reschedule attempt for appointment_id={appointment_id} by user_id={current_user['id']}")
            #     raise ValueError("Not authorized to reschedule this appointment")
            
            doctor_id = appt["doctor_id"]
            old_slot_time = appt["slot_time"]

            # --- Slot time parsing and error logging ---
            from datetime import datetime

            # The error "Invalid isoformat string: 'new_slot_time=datetime.datetime(2025, 8, 2, 15, 0)'" 
            # is likely caused by passing a string like "new_slot_time=datetime.datetime(2025, 8, 2, 15, 0)" 
            # to datetime.fromisoformat(), which expects a plain ISO string, not a repr of a keyword argument.
            # This can happen if the input is a stringified Pydantic model or dict, not just the datetime string.

            # Try to robustly extract the datetime
            slot_time_naive = None
            try:
                if isinstance(new_slot_time, datetime):
                    slot_time_naive = new_slot_time.replace(tzinfo=None)
                    logger.info(f"[APPOINTMENT MANAGER] new_slot_time is a datetime object: {slot_time_naive}")
                elif isinstance(new_slot_time, str):
                    logger.info(f"[APPOINTMENT MANAGER] new_slot_time is a string: {new_slot_time}")
                    # Try to extract the datetime string if it's in the form "new_slot_time=..."
                    if new_slot_time.startswith("new_slot_time="):
                        # Try to eval the right side if possible
                        import re
                        match = re.match(r"new_slot_time=(datetime\.datetime\([^)]+\))", new_slot_time)
                        if match:
                            # Try to eval the datetime constructor
                            try:
                                slot_time_naive = eval(match.group(1)).replace(tzinfo=None)
                                logger.info(f"[APPOINTMENT MANAGER] Parsed slot_time_naive from eval: {slot_time_naive}")
                            except Exception as e:
                                logger.error(f"[APPOINTMENT MANAGER] Failed to eval new_slot_time: {e}")
                                raise ValueError("Invalid new_slot_time format. Please provide an ISO datetime string.")
                        else:
                            # Try to extract the value after '='
                            dt_str = new_slot_time.split("=", 1)[1].strip()
                            try:
                                slot_time_naive = datetime.fromisoformat(dt_str).replace(tzinfo=None)
                                logger.info(f"[APPOINTMENT MANAGER] Parsed slot_time_naive from isoformat: {slot_time_naive}")
                            except Exception as e:
                                logger.error(f"[APPOINTMENT MANAGER] Failed to parse new_slot_time after '=': {e}")
                                raise ValueError("Invalid new_slot_time format. Please provide an ISO datetime string.")
                    else:
                        try:
                            slot_time_naive = datetime.fromisoformat(new_slot_time).replace(tzinfo=None)
                            logger.info(f"[APPOINTMENT MANAGER] Parsed slot_time_naive from isoformat: {slot_time_naive}")
                        except Exception as e:
                            logger.error(f"[APPOINTMENT MANAGER] Failed to parse new_slot_time as isoformat: {e}")
                            raise ValueError("Invalid new_slot_time format. Please provide an ISO datetime string.")
                else:
                    logger.error(f"[APPOINTMENT MANAGER] new_slot_time is of unexpected type: {type(new_slot_time)}")
                    raise ValueError("Invalid new_slot_time type. Please provide a datetime object or ISO string.")
            except Exception as e:
                logger.error(f"[APPOINTMENT MANAGER] Error parsing new_slot_time: {e}")
                raise ValueError("Invalid new_slot_time format. Please provide an ISO datetime string.")

            # --- End slot time parsing ---

            # Check if new slot is available
            availability = await conn.fetchrow(
                """
                SELECT id, status FROM doctor_availability_slots
                WHERE doctor_id = $1 AND available_at = $2
                """,
                doctor_id,
                slot_time_naive
            )
            if not availability or availability["status"] != "available":
                logger.warning(f"[APPOINTMENT MANAGER] New slot not available for doctor_id={doctor_id}, slot_time={slot_time_naive}")
                # raise ValueError("Selected new slot is not available")

                # check if new slot is already in doctor_availability_slots
                existing_slot = await conn.fetchrow(
                    """
                    SELECT id FROM doctor_availability_slots
                    WHERE available_at = $1
                    """,
                    slot_time_naive
                )

                if not existing_slot:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO doctor_availability_slots (doctor_id, available_at, status)
                        VALUES ($1, $2, 'available')
                        RETURNING id, doctor_id, available_at, status, created_at
                        """,
                        doctor_id,
                        slot_time_naive
                        )

            # Check if new slot is already booked in appointments
            existing = await conn.fetchrow(
                """
                SELECT 1 FROM appointments
                WHERE doctor_id = $1 AND slot_time = $2 AND id != $3
                """,
                doctor_id,
                slot_time_naive,
                appointment_id
            )
            if existing:
                logger.warning(f"[APPOINTMENT MANAGER] New slot already booked for doctor_id={doctor_id}, slot_time={slot_time_naive}")
                raise ValueError("Selected new slot is already booked")

            # Transaction: update appointment, update doctor_availability_slots
            async with conn.transaction():
                # 1. Mark old slot as available
                if old_slot_time:
                    try:
                        await conn.execute(
                            """
                            UPDATE doctor_availability_slots
                            SET status = 'available'
                            WHERE doctor_id = $1 AND available_at = $2
                            """,
                            doctor_id,
                            old_slot_time.replace(tzinfo=None)
                        )
                        logger.info(f"[APPOINTMENT MANAGER] Marked old slot as available for doctor_id={doctor_id}, old_slot_time={old_slot_time}")
                    except Exception as e:
                        logger.error(f"[APPOINTMENT MANAGER] Failed to mark old slot as available: {e}")
                # 2. Mark new slot as booked
                try:
                    await conn.execute(
                        """
                        UPDATE doctor_availability_slots
                        SET status = 'booked'
                        WHERE doctor_id = $1 AND available_at = $2
                        """,
                        doctor_id,
                        slot_time_naive
                    )
                    logger.info(f"[APPOINTMENT MANAGER] Marked new slot as booked for doctor_id={doctor_id}, slot_time={slot_time_naive}")
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Failed to mark new slot as booked: {e}")
                    raise
                # 3. Update the appointment's slot_time
                try:
                    await conn.execute(
                        """
                        UPDATE appointments
                        SET slot_time = $1
                        WHERE id = $2
                        """,
                        slot_time_naive,
                        appointment_id
                    )
                    logger.info(f"[APPOINTMENT MANAGER] Updated appointment {appointment_id} slot_time to {slot_time_naive}")
                except Exception as e:
                    logger.error(f"[APPOINTMENT MANAGER] Failed to update appointment slot_time: {e}")
                    raise
            logger.info(f"[APPOINTMENT MANAGER] Appointment {appointment_id} rescheduled to {slot_time_naive}")
            # Return the updated appointment
            updated_appt = await conn.fetchrow(
                """
                SELECT * FROM appointments WHERE id = $1
                """,
                appointment_id
            )
            result = dict(updated_appt)
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if 'slot_time' in result and isinstance(result['slot_time'], datetime):
                result['slot_time'] = result['slot_time'].isoformat()
            logger.info(f"[APPOINTMENT MANAGER] Returning updated appointment: {result}")
            return result

    @staticmethod
    async def update_appointment(
        appointment_id: int,
        doctor_id: int = None,
        patient_id: int = None,
        slot_time: datetime = None,
        complain: str = None,
        status: str = None,
    ) -> dict:
        """
        Update an appointment's details.
        Only provided fields will be updated.
        Returns the updated appointment as a dict.
        """
        logger.info(f"[APPOINTMENT MANAGER] update_appointment called for id={appointment_id} with doctor_id={doctor_id}, patient_id={patient_id}, slot_time={slot_time}, complain={complain}, status={status}")
        async with db.get_connection() as conn:
            # Fetch current appointment
            appt = await conn.fetchrow(
                "SELECT * FROM appointments WHERE id = $1",
                appointment_id
            )
            if not appt:
                logger.warning(f"[APPOINTMENT MANAGER] No appointment found for id={appointment_id}")
                return {"error": "Appointment not found"}

            updates = []
            params = []
            param_idx = 1

            # Only update provided fields
            if doctor_id is not None:
                updates.append(f"doctor_id = ${param_idx}")
                params.append(doctor_id)
                param_idx += 1
            if patient_id is not None:
                updates.append(f"patient_id = ${param_idx}")
                params.append(patient_id)
                param_idx += 1
            if slot_time is not None:
                # Optionally, update doctor_availability_slots if slot_time changes
                updates.append(f"slot_time = ${param_idx}")
                # Remove tzinfo for naive DB storage if needed
                if hasattr(slot_time, "replace"):
                    params.append(slot_time.replace(tzinfo=None))
                else:
                    params.append(slot_time)
                param_idx += 1
            if complain is not None:
                updates.append(f"complain = ${param_idx}")
                params.append(complain)
                param_idx += 1
            if status is not None:
                updates.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1

            if not updates:
                logger.info(f"[APPOINTMENT MANAGER] No fields to update for appointment id={appointment_id}")
                return {"error": "No fields to update"}

            params.append(appointment_id)
            set_clause = ", ".join(updates)
            query = f"""
                UPDATE appointments
                SET {set_clause}
                WHERE id = ${param_idx}
                RETURNING id, doctor_id, patient_id, slot_time, complain, status, created_at
            """
            row = await conn.fetchrow(query, *params)
            if row:
                result = dict(row)
                if 'created_at' in result and isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                if 'slot_time' in result and isinstance(result['slot_time'], datetime):
                    result['slot_time'] = result['slot_time'].isoformat()
                logger.info(f"[APPOINTMENT MANAGER] Appointment updated: {result}")
                return result
            logger.warning(f"[APPOINTMENT MANAGER] No appointment updated for id={appointment_id}")
            return {"error": "Appointment not updated"}



