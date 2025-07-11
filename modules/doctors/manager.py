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
                SELECT d.id, d.user_id, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.availability, d.created_at,
                       COUNT(r.id) as review_count, AVG(r.rating) as avg_rating,
                       u.id as user_id, u.email as doctor_email, u.first_name as doctor_first_name, u.last_name as doctor_last_name
                FROM doctors d
                LEFT JOIN reviews r ON d.id = r.doctor_id
                LEFT JOIN users u ON d.user_id = u.id
                GROUP BY d.id, u.id
                ORDER BY d.created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset
            )
            if not rows:
                return []
            else:
                result = [dict(row) for row in rows]
                # for doctor in result:
                #     doctor["rating"] = float(doctor["avg_rating"]) if doctor["avg_rating"] else 0.0
                #     del doctor["avg_rating"]
                #     # Convert datetime objects to ISO format strings
                #     if 'created_at' in doctor and isinstance(doctor['created_at'], datetime):
                #         doctor['created_at'] = doctor['created_at'].isoformat()
                #     # If availability is stored as JSONB in DB, it might come back as a Python list/dict, no need to dump again
                #     if 'availability' in doctor and isinstance(doctor['availability'], str):
                #         doctor['availability'] = json.loads(doctor['availability'])
                return result

    @staticmethod
    async def get_doctor(doctor_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT d.id, d.user_id, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.availability, d.created_at,
                       COUNT(r.id) as review_count, AVG(r.rating) as avg_rating,
                       u.id as user_id, u.email as doctor_email, u.first_name as doctor_first_name, u.last_name as doctor_last_name
                FROM doctors d
                LEFT JOIN reviews r ON d.id = r.doctor_id
                LEFT JOIN users u ON d.user_id = u.id
                WHERE d.id = $1
                GROUP BY d.id, u.id
                """,
                doctor_id
            )
            if row:
                result = dict(row)
                result["rating"] = float(result["avg_rating"]) if result["avg_rating"] else 0.0
                del result["avg_rating"]
                return result
            return None

    @staticmethod
    async def add_review(doctor_id: int, user_id: int, rating: int, comment: str) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO reviews (doctor_id, user_id, rating, comment)
                VALUES ($1, $2, $3, $4)
                RETURNING id, doctor_id, user_id, rating, comment, created_at
                """,
                doctor_id,
                user_id,
                rating,
                comment
            )
            return dict(row)


