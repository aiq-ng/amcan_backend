from .models import UserCreate
from .utils import hash_password, verify_password, create_access_token
from shared.db import db

class AuthManager:
    @staticmethod
    async def register(user: UserCreate) -> dict:
        async with db.get_connection() as conn:
            # Check if email already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user.email
            )
            if existing_user:
                raise ValueError("Email already registered")
            
            password_hash = hash_password("password")
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
            return dict(result)

    @staticmethod
    async def login(email: str, password: str) -> str:
        async with db.get_connection() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1",
                email
            )
            if not user or not verify_password(password, user["password_hash"]):
                raise ValueError("Invalid email or password")
            access_token = create_access_token(data={"sub": email})
            return access_token
