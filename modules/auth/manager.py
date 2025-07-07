import logging
from .models import UserCreate
from .utils import hash_password, verify_password, create_access_token
from shared.db import db

logger = logging.getLogger(__name__)

class AuthManager:
    @staticmethod
    async def register(user: UserCreate) -> dict:
        logger.info(f"[AUTH MANAGER] register called for email: {user.email}")
        async with db.get_connection() as conn:
            # Check if email already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user.email
            )
            if existing_user:
                logger.warning(f"[AUTH MANAGER] Registration failed: Email already registered: {user.email}")
                raise ValueError("Email already registered")
            logger.info(f"[AUTH MANAGER] Registering new user: {user.email}")
            password_hash = hash_password(user.password)
            result = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, email, first_name, last_name, is_admin, is_doctor
                """,
                user.email,
                password_hash,
                user.first_name,
                user.last_name,
                user.is_admin
            )
            logger.info(f"[AUTH MANAGER] User registered successfully: {user.email}")
            return dict(result)

    @staticmethod
    async def login(email: str, password: str) -> str:
        logger.info(f"[AUTH MANAGER] login called for email and password: {email} and {password}")
        async with db.get_connection() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1",
                email
            )
            if not user:
                logger.warning(f"[AUTH MANAGER] Login failed: No user found for email: {email}")
                raise ValueError("Invalid email or password")
            if not verify_password(password, user["password_hash"]):
                logger.info(f"[AUTH MANAGER] Password verification result: {verify_password(password, user['password_hash'])}")
                logger.info(f"[AUTH MANAGER] Password: {password}")
                logger.info(f"[AUTH MANAGER] Password hash: {user['password_hash']}")
                logger.warning(f"[AUTH MANAGER] Login failed: Incorrect password for email and password: {email} and {password}")
                raise ValueError("Invalid email or password")
            logger.info(f"[AUTH MANAGER] Login successful for email: {email}")
            access_token = create_access_token(data={"sub": email})
            return access_token

            # INSERT_YOUR_CODE
    @staticmethod
    async def get_all_users() -> list:
        logger.info("[AUTH MANAGER] get_all_users called")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, email, first_name, last_name, is_admin, is_doctor
                FROM users
                """
            )
            users = [dict(row) for row in rows]
            logger.info(f"[AUTH MANAGER] Retrieved {len(users)} users")
            return users
