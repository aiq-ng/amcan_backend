# shared/seed.py
from shared.db import db
from modules.auth.utils import hash_password
from datetime import datetime

async def seed_data():
    async with db.get_connection() as conn:
        # Seed users if empty
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if count == 0:
            password_hash = hash_password("Admin123!")
            admin_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                "admin@therapyapp.com",
                password_hash,
                "Admin",
                "User",
                True
            )
            doctor_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                "doctor1@therapyapp.com",
                hash_password("Doctor123!"),
                "Abimbola",
                "Taofeek"
            )
            # Seed a doctor first
            doctor_row = await conn.fetchrow(
                """
                INSERT INTO doctors (user_id, full_name, title, bio, experience_years, patients_count, location, availability)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                doctor_id,
                "Dr. Abimbola Taofeek",
                "Psychologist",
                "A compassionate therapist with a PhD in Clinical Psychology.",
                6,
                120,
                "Kaduna",
                '{"Mon": ["8:00AM", "6:00PM"], "Tue": ["8:00AM", "6:00PM"], "Wed": ["8:00AM", "6:00PM"], "Thu": ["8:00AM", "6:00PM"], "Fri": ["8:00AM", "6:00PM"]}'
            )
            doctor_id = doctor_row["id"]  # Use the generated doctor_id

            await conn.execute(
                """
                INSERT INTO appointments (doctor_id, user_id, slot_time, status)
                VALUES ($1, $2, $3, $4)
                """,
                doctor_id,  # Use the newly created doctor_id
                admin_id,
                datetime(2025, 6, 20, 10, 0, 0),  # Example slot time
                'pending'
            )
