import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import OAuth2PasswordBearer
from shared.db import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1200

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    logger.debug(f"Entered hash_password with password: {password}")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    logger.debug(f"Hashed password: {hashed}")
    logger.debug("Exiting hash_password")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info(f"Entered verify_password with plain_password: {plain_password}, hashed_password: {hashed_password}")
    result = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    logger.debug(f"Password verification result: {result}")
    logger.debug("Exiting verify_password")
    return result

def create_access_token(data: dict) -> str:
    logger.info(f"Creating access token for data: {data}")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    logger.debug(f"Token payload to encode: {to_encode}")
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Token created: {token}")
    logger.debug("Exiting create_access_token")
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    logger.info(f"Entered get_current_user with token: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded JWT payload: {payload}")
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token does not contain 'sub' (email)")
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.debug(f"Extracted email from token: {email}")
        async with db.get_connection() as conn:
            logger.info(f"Fetching user from DB with email: {email}")
            user = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, is_admin
                FROM users WHERE email = $1
                """,
                email
            )
            logger.debug(f"DB fetch result: {user}")
            if user is None:
                logger.warning(f"User not found for email: {email}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.info(f"User found: {dict(user)}")
            logger.debug("Exiting get_current_user successfully")
            return dict(user)
    except jwt.PyJWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise

async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    logger.info(f"Entered get_current_admin with user: {current_user}")
    if not current_user["is_admin"]:
        logger.warning(f"User {current_user['email']} is not admin")
        raise HTTPException(status_code=403, detail="Admin access required")
    logger.info(f"User {current_user['email']} is admin")
    logger.debug("Exiting get_current_admin successfully")
    return current_user

async def get_current_user_ws(websocket: WebSocket) -> dict:
    print('websockets', websocket)
    token = websocket.query_params.get("token")
    if not token:
        raise Exception("Missing token")
    logger.info(f"Entered get_current_user_ws with token: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded JWT payload (ws): {payload}")
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Websocket token does not contain 'sub' (email)")
            raise Exception("Invalid token")
        logger.debug(f"Extracted email from websocket token: {email}")
        async with db.get_connection() as conn:
            logger.info(f"Fetching user from DB with email: {email}")
            user = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, is_admin
                FROM users WHERE email = $1
                """,
                email
            )
            logger.debug(f"DB fetch result (ws): {user}")
            if user is None:
                logger.warning(f"User not found for email: {email}")
                raise Exception("User not found")
            logger.info(f"User found: {dict(user)}")
            logger.debug("Exiting get_current_user_ws successfully")
            return dict(user)
    except jwt.PyJWTError as e:
        logger.error(f"JWT decode error (websocket): {e}")
        raise Exception("Invalid token")
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user_ws: {e}")
        raise