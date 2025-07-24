from .models import DoctorCreate, DoctorResponse
from shared.db import db
import json
from datetime import datetime

class DoctorManager:
    
    @staticmethod
    async def create_doctor(doctor_item: DoctorCreate, user_id: int) -> dict:
        print('creating doctor hit')

        async with db.get_connection() as conn:
            # Assuming you have a doctors table and are inserting/fetching data
            row = await conn.fetchrow(
                """
                INSERT INTO doctors (title, bio, experience_years, patients_count, location, user_id, availability)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, title, bio, experience_years, patients_count, location, created_at, user_id, availability
                """,
                doctor_item.title,
                doctor_item.bio,
                doctor_item.experience_years,
                doctor_item.patients_count,
                doctor_item.location,
                doctor_item.user_id,
                json.dumps([{"day": slot.day, "slots": slot.slots} for slot in doctor_item.availability]) # Convert Availability to list of dicts
            )

            # Update the user to set is_doctor = TRUE for the given user_id
            await conn.execute(
                """
                UPDATE users
                SET is_doctor = TRUE
                WHERE id = $1
                """,
                doctor_item.user_id
            )

            result = dict(row)
            print('doctor created:', result)

            # Convert datetime objects to ISO format strings
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            # Add similar conversions for any other datetime fields like 'updated_at', 'dob', etc.
            # if 'dob' in result and isinstance(result['dob'], datetime):
            #     result['dob'] = result['dob'].isoformat()

            # If availability is stored as JSONB in DB, it might come back as a Python list/dict, no need to dump again
            # If it's text, you might need to json.loads it here if you didn't do it during fetch
            if 'availability' in result and isinstance(result['availability'], str):
                 result['availability'] = json.loads(result['availability'])


            return result

    async def get_doctors(limit: int = 10, offset: int = 0) -> list:
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.first_name,
                    d.last_name,
                    d.title,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.availability,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'review_id', dr.id,
                                'user_id', dr.user_id,
                                'rating', dr.rating,
                                'comment', dr.comment,
                                'created_at', dr.created_at
                            )
                        )
                        FROM doctors_reviews dr 
                        WHERE dr.doctor_id = d.id
                    ) AS reviews,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'experience_id', de.id,
                                'institution', de.institution,
                                'position', de.position,
                                'start_date', de.start_date,
                                'end_date', de.end_date,
                                'description', de.description,
                                'created_at', de.created_at
                            )
                        )
                        FROM doctors_experience de 
                        WHERE de.doctor_id = d.id
                    ) AS experiences,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = DATE('2025-07-24')
                    ) AS appointment_count_today,
                    (
                        SELECT COUNT(DISTINCT dp.patient_id) 
                        FROM doctors_patients dp 
                        WHERE dp.doctor_id = d.id
                    ) AS patient_count,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'appointment_id', a.id,
                            'patient_id', a.patient_id,
                            'slot_time', a.slot_time,
                            'complain', a.complain,
                            'status', a.status
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = DATE('2025-07-24')
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                GROUP BY d.id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
                LIMIT $1 OFFSET $2;
                """,
                limit,
                offset
            )
            if not rows:
                return []
            else:
                result = [dict(row) for row in rows]
                return result

    @staticmethod
    async def get_doctor(doctor_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.first_name,
                    d.last_name,
                    d.title,
                    d.availability,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'review_id', dr.id,
                                'user_id', dr.user_id,
                                'rating', dr.rating,
                                'comment', dr.comment,
                                'created_at', dr.created_at
                            )
                        )
                        FROM doctors_reviews dr 
                        WHERE dr.doctor_id = d.id
                    ) AS reviews,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'experience_id', de.id,
                                'institution', de.institution,
                                'position', de.position,
                                'start_date', de.start_date,
                                'end_date', de.end_date,
                                'description', de.description,
                                'created_at', de.created_at
                            )
                        )
                        FROM doctors_experience de 
                        WHERE de.doctor_id = d.id
                    ) AS experiences,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = DATE('2025-07-24')
                    ) AS appointment_count_today,
                    (
                        SELECT COUNT(DISTINCT dp.patient_id) 
                        FROM doctors_patients dp 
                        WHERE dp.doctor_id = d.id
                    ) AS patient_count,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'appointment_id', a.id,
                            'patient_id', a.patient_id,
                            'slot_time', a.slot_time,
                            'complain', a.complain,
                            'status', a.status
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = DATE('2025-07-24')
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                WHERE d.id = $1
                GROUP BY d.id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
                """,
                doctor_id
            )
            if row:
                result = dict(row)
                # Convert datetime objects to ISO format strings
                if 'created_at' in result and isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                # If availability is stored as JSONB in DB, it might come back as a Python list/dict, no need to dump again
                # If it's text, you might need to json.loads it here if you didn't do it during fetch
                if 'availability' in result and isinstance(result['availability'], str):
                    result['availability'] = json.loads(result['availability'])
                return result
            return None

    async def get_doctor_by_user_id(user_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.first_name,
                    d.last_name,
                    d.user_id,
                    d.availability,
                    d.title,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'review_id', dr.id,
                                'user_id', dr.user_id,
                                'rating', dr.rating,
                                'comment', dr.comment,
                                'created_at', dr.created_at
                            )
                        )
                        FROM doctors_reviews dr 
                        WHERE dr.doctor_id = d.id
                    ) AS reviews,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'experience_id', de.id,
                                'institution', de.institution,
                                'position', de.position,
                                'start_date', de.start_date,
                                'end_date', de.end_date,
                                'description', de.description,
                                'created_at', de.created_at
                            )
                        )
                        FROM doctors_experience de 
                        WHERE de.doctor_id = d.id
                    ) AS experiences,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = DATE('2025-07-24')
                    ) AS appointment_count_today,
                    (
                        SELECT COUNT(DISTINCT dp.patient_id) 
                        FROM doctors_patients dp 
                        WHERE dp.doctor_id = d.id
                    ) AS patient_count,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'appointment_id', a.id,
                            'patient_id', a.patient_id,
                            'slot_time', a.slot_time,
                            'complain', a.complain,
                            'status', a.status
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = DATE('2025-07-24')
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                WHERE d.user_id = $1
                GROUP BY d.id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
                """,
                user_id
            )
            if row:
                result = dict(row)
                # Convert datetime objects to ISO format strings
                if 'created_at' in result and isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                # If availability is stored as JSONB in DB, it might come back as a Python list/dict, no need to dump again
                # If it's text, you might need to json.loads it here if you didn't do it during fetch
                if 'availability' in result and isinstance(result['availability'], str):
                    result['availability'] = json.loads(result['availability'])
                return result
            return None

    
    @staticmethod
    async def add_review(doctor_id: int, user_id: int, rating: int, comment: str) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO doctors_reviews (doctor_id, user_id, rating, comment)
                VALUES ($1, $2, $3, $4)
                RETURNING id, doctor_id, user_id, rating, comment, created_at
                """,
                doctor_id,
                user_id,
                rating,
                comment
            )
            return dict(row)


