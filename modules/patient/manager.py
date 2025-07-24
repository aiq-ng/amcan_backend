from shared.db import db
import logging
from modules.auth.utils import get_current_user
from .models import PatientCreate, PatientUpdate, PatientResponse
from modules.appointments.models import AppointmentResponse
from modules.auth.utils import hash_password


async def get_all_patients() -> list:
    async with db.get_connection() as conn:
        rows = await conn.fetch(
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
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.marital_status,
                p.profile_image_url,
                asumm.id AS summary_id,
                asumm.diagnosis,
                asumm.notes,
                asumm.prescription,
                asumm.follow_up_date,
                asumm.created_at AS summary_created_at,
                asumm.updated_at AS summary_updated_at
            FROM patients p
            LEFT JOIN appointments_summary asumm ON p.user_id = asumm.patient_id
            ORDER BY p.id
            """
        )
        if not rows:
            return []
        return [dict(row) for row in rows]

async def get_patient_by_user_id(user_id: int) -> dict:
    async with db.get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT p.id, p.user_id, p.first_name, p.last_name, p.date_of_birth, p.address, p.phone_number,
                   p.occupation, p.emergency_contact_name, p.emergency_contact_phone, p.marital_status,
                   p.profile_image_url, p.created_at
            FROM patients p
            WHERE p.user_id = $1
            """,
            user_id
        )
        return dict(row) if row else None
    
async def get_patient_by_patient_id(patient_id: int) -> dict:
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
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.marital_status,
                p.profile_image_url,
                asumm.id AS summary_id,
                asumm.diagnosis,
                asumm.notes,
                asumm.prescription,
                asumm.follow_up_date,
                asumm.created_at AS summary_created_at,
                asumm.updated_at AS summary_updated_at
            FROM patients p
            LEFT JOIN appointments_summary asumm ON p.user_id = asumm.patient_id
            WHERE p.id = $1
            ORDER BY p.id
            """,
            patient_id
        )
        return dict(row) if row else None

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
                    raise ValueError(f"An error occoured: {str(e)}")

        patient_check = await conn.fetchrow(
            """
            SELECT id FROM patients WHERE user_id = $1  
            """,
            patient_data.user_id
        )

        if patient_check:
            raise ValueError("Patient already exists for this user_id")

        patient_id = await conn.fetchval(
            """
            INSERT INTO patients (user_id, first_name, last_name, date_of_birth, address, phone_number,
                                occupation, emergency_contact_name, emergency_contact_phone, marital_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            user_id, patient_data.first_name, patient_data.last_name, patient_data.date_of_birth,
            patient_data.address, patient_data.phone_number, patient_data.occupation,
            patient_data.emergency_contact_name, patient_data.emergency_contact_phone, patient_data.marital_status
        )
        row = await conn.fetchrow(
            """
            SELECT p.id, p.user_id, p.first_name, p.last_name, p.date_of_birth, p.address, p.phone_number,
                   p.occupation, p.emergency_contact_name, p.emergency_contact_phone, p.marital_status,
                   p.profile_image_url
            FROM patients p
            WHERE p.id = $1
            """,
            patient_id
        )
        return dict(row)

async def update_patient(patient_id: int, patient_data: PatientUpdate) -> dict:
    async with db.get_connection() as conn:
        updates = []
        values = []
        params = [patient_id]
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

        if not updates:
            return await get_patient_by_user_id(patient_id)

        query = f"""
        UPDATE patients
        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
        RETURNING id, user_id, first_name, last_name, date_of_birth, address, phone_number,
                  occupation, emergency_contact_name, emergency_contact_phone, marital_status,
                  profile_image_url, created_at, updated_at
        """
        row = await conn.fetchrow(query, *([patient_id] + values))
        return dict(row) if row else None

async def delete_patient(user_id: int) -> bool:
    async with db.get_connection() as conn:
        await conn.execute("DELETE FROM patients WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
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
        return [AppointmentResponse(**dict(row)) for row in rows]