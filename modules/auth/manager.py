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
                INSERT INTO users (email, password_hash)
                VALUES ($1, $2)
                RETURNING id, email
                """,
                user.email,
                password_hash
               
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

    @staticmethod
    async def get_all_users() -> list:
        logger.info("[AUTH MANAGER] get_all_users called")
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, email, is_admin, is_doctor
                FROM users
                """
            )
            users = [dict(row) for row in rows]
            logger.info(f"[AUTH MANAGER] Retrieved {len(users)} users")
            return users

    @staticmethod
    async def update_user(user_id: int, update_data: dict, current_user: dict) -> dict:
        logger.info(f"[AUTH MANAGER] update_user called for user_id: {user_id} by {current_user['email']}")
        # Only allow if current user is admin or updating their own account
        if not (current_user["is_admin"] or current_user["id"] == user_id):
            logger.warning(f"[AUTH MANAGER] update_user forbidden for user_id: {user_id} by {current_user['email']}")
            raise ValueError("Not authorized to update this user")
        async with db.get_connection() as conn:
            # Build update query dynamically
            fields = []
            values = []
            if "email" in update_data and update_data["email"] is not None:
                fields.append("email = $%d" % (len(values)+1))
                values.append(update_data["email"])
            if "first_name" in update_data and update_data["first_name"] is not None:
                fields.append("first_name = $%d" % (len(values)+1))
                values.append(update_data["first_name"])
            if "last_name" in update_data and update_data["last_name"] is not None:
                fields.append("last_name = $%d" % (len(values)+1))
                values.append(update_data["last_name"])
            
            if "is_admin" in update_data and update_data["is_admin"] is not None and current_user["is_admin"]:
                fields.append("is_admin = $%d" % (len(values)+1))
                values.append(update_data["is_admin"])
            if "is_doctor" in update_data and update_data["is_doctor"] is not None and current_user["is_admin"]:
                fields.append("is_doctor = $%d" % (len(values)+1))
                values.append(update_data["is_doctor"])
            if not fields:
                logger.warning(f"[AUTH MANAGER] No valid fields to update for user_id: {user_id}")
                raise ValueError("No valid fields to update")
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = $%d RETURNING id, email, first_name, last_name, is_admin, is_doctor" % (len(values))
            result = await conn.fetchrow(query, *values)
            if not result:
                logger.warning(f"[AUTH MANAGER] User not found for update: {user_id}")
                raise ValueError("User not found")
            logger.info(f"[AUTH MANAGER] User updated successfully: {user_id}")
            return dict(result)

    @staticmethod
    async def delete_user(user_id: int, current_user: dict) -> dict:
        logger.info(f"[AUTH MANAGER] delete_user called for user_id: {user_id} by {current_user['email']}")
        if not current_user["is_admin"]:
            logger.warning(f"[AUTH MANAGER] delete_user forbidden for user_id: {user_id} by {current_user['email']}")
            raise ValueError("Only admin can delete users")
        async with db.get_connection() as conn:
            result = await conn.fetchrow("DELETE FROM users WHERE id = $1 RETURNING id, email, first_name, last_name, is_admin, is_doctor", user_id)
            if not result:
                logger.warning(f"[AUTH MANAGER] User not found for delete: {user_id}")
                raise ValueError("User not found")
            logger.info(f"[AUTH MANAGER] User deleted successfully: {user_id}")
            return dict(result)
