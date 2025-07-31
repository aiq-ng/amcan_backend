from shared.db import db
import logging
from modules.auth.utils import get_current_user, hash_password
from .models import PatientCreate, PatientUpdate, PatientResponse
from modules.appointments.models import AppointmentResponse
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_all_patients(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    therapy_name: str = None,
    created_at_from: datetime = None,
    created_at_to: datetime = None,
) -> dict:
    """
    Fetch all patients with optional search, filters, and pagination.
    - search: matches first_name, last_name, address, occupation, phone_number, emergency_contact_name, emergency_contact_phone
    - therapy_name: filter by therapy name (string)
    - created_at_from, created_at_to: filter by created_at datetime range
    Returns dict with 'data', 'total', 'page', 'page_size'
    """
    filters = []
    params = []
    param_idx = 1

    if search:
        filters.append(
            f"(p.first_name ILIKE ${param_idx} OR p.last_name ILIKE ${param_idx} OR p.address ILIKE ${param_idx} OR p.occupation ILIKE ${param_idx} OR p.phone_number ILIKE ${param_idx} OR p.emergency_contact_name ILIKE ${param_idx} OR p.emergency_contact_phone ILIKE ${param_idx})"
        )
        params.append(f"%{search}%")
        param_idx += 1

    if therapy_name is not None:
        filters.append(f"t.therapy_type ILIKE ${param_idx}")
        params.append(f"%{therapy_name}%")
        param_idx += 1

    if created_at_from is not None:
        filters.append(f"p.created_at >= ${param_idx}")
        params.append(created_at_from)
        param_idx += 1

    if created_at_to is not None:
        filters.append(f"p.created_at <= ${param_idx}")
        params.append(created_at_to)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    offset = (page - 1) * page_size
    limit = page_size

    count_query = f"""
        SELECT COUNT(*) FROM patients p
        LEFT JOIN therapy t ON p.therapy_type = t.id
        {where_clause}
    """

    data_query = f"""
        SELECT 
            p.id AS patient_id,
            p.user_id,
            p.first_name,
            p.last_name,
            p.date_of_birth,
            p.address,
            p.phone_number,
            p.occupation,
            p.therapy_type,
            p.therapy_criticality,
            p.emergency_contact_name,
            p.emergency_contact_phone,
            p.marital_status,
            p.profile_image_url,
            p.created_at,
            asumm.id AS summary_id,
            asumm.diagnosis,
            asumm.notes,
            asumm.prescription,
            asumm.follow_up_date,
            asumm.created_at AS summary_created_at,
            asumm.updated_at AS summary_updated_at,
            t.therapy_type AS therapy_name
        FROM patients p
        LEFT JOIN appointments_summary asumm ON p.user_id = asumm.patient_id
        LEFT JOIN therapy t ON p.therapy_type = t.id
        {where_clause}
        ORDER BY p.id
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """

    params_for_data = params.copy()
    params_for_data.append(limit)
    params_for_data.append(offset)

    async with db.get_connection() as conn:
        total = await conn.fetchval(count_query, *params)
        rows = await conn.fetch(data_query, *params_for_data)
        result = [dict(row) for row in rows]
        for row in result:
            if 'created_at' in row and isinstance(row['created_at'], datetime):
                row['created_at'] = row['created_at'].isoformat()
            if 'updated_at' in row and isinstance(row['updated_at'], datetime):
                row['updated_at'] = row['updated_at'].isoformat()
            if 'date_of_birth' in row and isinstance(row['date_of_birth'], datetime):
                row['date_of_birth'] = row['date_of_birth'].isoformat()
            if 'summary_created_at' in row and isinstance(row['summary_created_at'], datetime):
                row['summary_created_at'] = row['summary_created_at'].isoformat()
            if 'summary_updated_at' in row and isinstance(row['summary_updated_at'], datetime):
                row['summary_updated_at'] = row['summary_updated_at'].isoformat()
            if 'follow_up_date' in row and isinstance(row['follow_up_date'], datetime):
                row['follow_up_date'] = row['follow_up_date'].isoformat()
        meta_data = {
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        return {
            "patients": result,
            "meta_data": meta_data,
        }

async def get_patient_by_user_id(user_id: int) -> dict:
    async with db.get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                p.id AS patient_id,
                p.user_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.address,
                p.phone_number,
                p.occupation,
                p.therapy_type,
                p.therapy_criticality,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.marital_status,
                p.profile_image_url,
                p.created_at,
                t.therapy_type AS therapy_name
            FROM patients p
            LEFT JOIN therapy t ON p.therapy_type = t.id
            WHERE p.user_id = $1
            """,
            user_id
        )
        if row:
            result = dict(row)
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if 'updated_at' in result and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
            if 'date_of_birth' in result and isinstance(result['date_of_birth'], datetime):
                result['date_of_birth'] = result['date_of_birth'].isoformat()
            return result
        return None
    
async def get_patient_using_id(patient_id: int) -> dict:
    async with db.get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                p.id AS patient_id,
                p.user_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.address,
                p.phone_number,
                p.occupation,
                p.therapy_type,
                p.therapy_criticality,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.marital_status,
                p.profile_image_url,
                p.created_at,
                asumm.id AS summary_id,
                asumm.diagnosis,
                asumm.notes,
                asumm.prescription,
                asumm.follow_up_date,
                asumm.created_at AS summary_created_at,
                asumm.updated_at AS summary_updated_at,
                t.therapy_type AS therapy_name
            FROM patients p
            LEFT JOIN appointments_summary asumm ON p.user_id = asumm.patient_id
            LEFT JOIN therapy t ON p.therapy_type = t.id
            WHERE p.id = $1
            """,
            patient_id
        )
        if row:
            result = dict(row)
            # if 'created_at' in result and isinstance(result['created_at'], datetime):
            #     result['created_at'] = result['created_at'].isoformat()
            # if 'updated_at' in result and isinstance(result['updated_at'], datetime):
            #     result['updated_at'] = result['updated_at'].isoformat()
            # if 'date_of_birth' in result and isinstance(result['date_of_birth'], datetime):
            #     result['date_of_birth'] = result['date_of_birth'].isoformat()
            # if 'summary_created_at' in result and isinstance(result['summary_created_at'], datetime):
            #     result['summary_created_at'] = result['summary_created_at'].isoformat()
            # if 'summary_updated_at' in result and isinstance(result['summary_updated_at'], datetime):
            #     result['summary_updated_at'] = result['summary_updated_at'].isoformat()
            # if 'follow_up_date' in result and isinstance(result['follow_up_date'], datetime):
            #     result['follow_up_date'] = result['follow_up_date'].isoformat()
            return result
        return None

async def create_patient(patient_data: PatientCreate) -> dict:
    async with db.get_connection() as conn:
        password_hash = hash_password(patient_data.password)
       
        if not patient_data.user_id:
            try:
                user_id = await conn.fetchval(
                    """
                    INSERT INTO users (email, password_hash)
                    VALUES ($1, $2)
                    RETURNING id
                    """,
                    patient_data.email,
                    password_hash
                )
            except Exception as e:
                logger.error(f"[PATIENT MANAGER] Error creating user: {e}")
                raise ValueError(f"Error creating user: {str(e)}")
        else:
            user_id = patient_data.user_id

        patient_check = await conn.fetchrow(
            """
            SELECT id FROM patients WHERE user_id = $1  
            """,
            user_id
        )
        if patient_check:
            logger.warning(f"[PATIENT MANAGER] Patient already exists for user_id={user_id}")
            raise ValueError("Patient already exists for this user_id")

        patient_id = await conn.fetchval(
            """
            INSERT INTO patients (user_id, first_name, last_name, date_of_birth, address, phone_number,
                                 occupation, therapy_type, therapy_criticality, emergency_contact_name,
                                 emergency_contact_phone, marital_status, profile_image_url)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
            """,
            user_id, patient_data.first_name, patient_data.last_name, patient_data.date_of_birth,
            patient_data.address, patient_data.phone_number, patient_data.occupation,
            patient_data.therapy_type, patient_data.therapy_criticality, patient_data.emergency_contact_name,
            patient_data.emergency_contact_phone, patient_data.marital_status, patient_data.profile_image_url
        )
        row = await conn.fetchrow(
            """
            SELECT 
                p.id AS patient_id,
                p.user_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.address,
                p.phone_number,
                p.occupation,
                p.therapy_type,
                p.therapy_criticality,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.marital_status,
                p.profile_image_url,
                p.created_at,
                t.therapy_type AS therapy_name
            FROM patients p
            LEFT JOIN therapy t ON p.therapy_type = t.id
            WHERE p.id = $1
            """,
            patient_id
        )
        result = dict(row)
        if 'created_at' in result and isinstance(result['created_at'], datetime):
            result['created_at'] = result['created_at'].isoformat()
        if 'updated_at' in result and isinstance(result['updated_at'], datetime):
            result['updated_at'] = result['updated_at'].isoformat()
        if 'date_of_birth' in result and isinstance(result['date_of_birth'], datetime):
            result['date_of_birth'] = result['date_of_birth'].isoformat()
        return result

async def update_patient(patient_id: int, patient_data: PatientUpdate) -> dict:
    async with db.get_connection() as conn:
        updates = []
        values = []
        param_count = 2

        if patient_data.first_name is not None:
            updates.append(f"first_name = ${param_count}")
            values.append(patient_data.first_name)
            param_count += 1
        if patient_data.last_name is not None:
            updates.append(f"last_name = ${param_count}")
            values.append(patient_data.last_name)
            param_count += 1
        if patient_data.date_of_birth is not None:
            updates.append(f"date_of_birth = ${param_count}")
            values.append(patient_data.date_of_birth)
            param_count += 1
        if patient_data.address is not None:
            updates.append(f"address = ${param_count}")
            values.append(patient_data.address)
            param_count += 1
        if patient_data.phone_number is not None:
            updates.append(f"phone_number = ${param_count}")
            values.append(patient_data.phone_number)
            param_count += 1
        if patient_data.occupation is not None:
            updates.append(f"occupation = ${param_count}")
            values.append(patient_data.occupation)
            param_count += 1
        if patient_data.therapy_type is not None:
            updates.append(f"therapy_type = ${param_count}")
            values.append(patient_data.therapy_type)
            param_count += 1
        if patient_data.therapy_criticality is not None:
            updates.append(f"therapy_criticality = ${param_count}")
            values.append(patient_data.therapy_criticality)
            param_count += 1
        if patient_data.emergency_contact_name is not None:
            updates.append(f"emergency_contact_name = ${param_count}")
            values.append(patient_data.emergency_contact_name)
            param_count += 1
        if patient_data.emergency_contact_phone is not None:
            updates.append(f"emergency_contact_phone = ${param_count}")
            values.append(patient_data.emergency_contact_phone)
            param_count += 1
        if patient_data.marital_status is not None:
            updates.append(f"marital_status = ${param_count}")
            values.append(patient_data.marital_status)
            param_count += 1
        if patient_data.profile_image_url is not None:
            updates.append(f"profile_image_url = ${param_count}")
            values.append(patient_data.profile_image_url)
            param_count += 1

        if not updates:
            return await get_patient_by_patient_id(patient_id)

        query = f"""
        UPDATE patients
        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING id, user_id, first_name, last_name, date_of_birth, address, phone_number,
                  occupation, therapy_type, therapy_criticality, emergency_contact_name,
                  emergency_contact_phone, marital_status, profile_image_url, created_at, updated_at
        """
        row = await conn.fetchrow(query, *([patient_id] + values))
        if row:
            result = dict(row)
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if 'updated_at' in result and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
            if 'date_of_birth' in result and isinstance(result['date_of_birth'], datetime):
                result['date_of_birth'] = result['date_of_birth'].isoformat()
            return result
        return None

async def delete_patient(user_id: int) -> bool:
    async with db.get_connection() as conn:
        async with conn.transaction():
            patient = await conn.fetchrow("SELECT id FROM patients WHERE user_id = $1", user_id)
            if not patient:
                logger.warning(f"[PATIENT MANAGER] Patient not found for user_id={user_id}")
                return False
            await conn.execute("DELETE FROM patients WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
            logger.info(f"[PATIENT MANAGER] Deleted patient and user for user_id={user_id}")
            return True

async def get_patient_appointments(patient_id: int):
    async with db.get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                a.id AS id,
                a.doctor_id,
                a.patient_id,
                a.slot_time,
                a.complain,
                a.status,
                a.created_at,
                d.first_name AS doctor_first_name,
                d.last_name AS doctor_last_name,
                d.title AS doctor_title
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = $1
            ORDER BY a.slot_time DESC
            """,
            patient_id
        )
        result = [dict(row) for row in rows]
        for row in result:
            if 'created_at' in row and isinstance(row['created_at'], datetime):
                row['created_at'] = row['created_at'].isoformat()
            if 'slot_time' in row and isinstance(row['slot_time'], datetime):
                row['slot_time'] = row['slot_time'].isoformat()
        return [AppointmentResponse(**row) for row in result]