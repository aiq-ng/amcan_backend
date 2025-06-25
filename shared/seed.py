# shared/seed.py
from shared.db import db
from modules.auth.utils import hash_password
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    async with db.get_connection() as conn:
        logger.info("Checking if users table is empty...")
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if count == 0:
            logger.info("No users found. Seeding admin user...")
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
            logger.info(f"Admin user created with id: {admin_id}")

            logger.info("Seeding regular user...")
            user_password_hash = hash_password("User123!")
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                "user1@therapyapp.com",
                user_password_hash,
                "Jane",
                "Doe"
            )
            logger.info(f"Regular user created with id: {user_id}")

            logger.info("Seeding doctor user...")
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
            logger.info(f"Doctor user created with id: {doctor_id}")

            logger.info("Seeding doctor profile...")
            doctor_row = await conn.fetchrow(
                """
                INSERT INTO doctors (user_id, title, bio, experience_years, patients_count, location, availability)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                doctor_id,
                "Psychologist",
                "A compassionate therapist with a PhD in Clinical Psychology.",
                6,
                120,
                "Kaduna",
                '{"Mon": ["8:00AM", "6:00PM"], "Tue": ["8:00AM", "6:00PM"], "Wed": ["8:00AM", "6:00PM"], "Thu": ["8:00AM", "6:00PM"], "Fri": ["8:00AM", "6:00PM"]}'
            )
            doctor_id = doctor_row["id"]
            logger.info(f"Doctor profile created with id: {doctor_id}")

            logger.info("Seeding sample appointment...")
            appointment_row = await conn.fetchrow(
                """
                INSERT INTO appointments (doctor_id, user_id, slot_time, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                doctor_id,
                admin_id,
                datetime(2025, 6, 24, 10, 0, 0),
                'confirmed'
            )
            appointment_id = appointment_row["id"]
            logger.info(f"Appointment created with id: {appointment_id}")

        #     logger.info("Seeding sample chat message...")
        #     await conn.execute(
        #         """
        #         INSERT INTO chat_messages (appointment_id, sender_id, receiver_id, message)
        #         VALUES ($1, $2, $3, $4)
        #         """,
        #         appointment_id,
        #         admin_id,
        #         doctor_id,
        #         'Hello looking forward to our session!'
        #     )
        #     logger.info("Sample chat message created.")
        # else:
        #     logger.info("Users already exist. Skipping seeding.")
