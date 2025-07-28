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
                SELECT id, email, is_admin, is_doctor
                FROM users WHERE email = $1
                """,
                email
            )
            logger.debug(f"DB fetch result: {user}")

            user = dict(user)

            patient = await conn.fetchrow(
                """
                SELECT 
                    u.id AS id,
                    u.email,
                    u.is_admin,
                    u.is_doctor,
                    p.id AS patient_id,
                    p.first_name,
                    p.last_name,
                    p.date_of_birth,
                    p.address,
                    p.profile_image_url,
                    p.phone_number,
                    p.occupation,
                    t.therapy_type,
                    p.therapy_criticality,
                    p.emergency_contact_name,
                    p.emergency_contact_phone,
                    p.marital_status,
                    p.created_at
                FROM 
                    users u
                    INNER JOIN patients p ON u.id = p.user_id
                    LEFT JOIN therapy t ON p.therapy_type = t.id
                WHERE 
                    u.id = $1;
                """,
                user['id']
            )

            doctor = await conn.fetchrow(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.user_id AS id,
                    d.first_name,
                    d.last_name,
                    d.title,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    u.is_doctor,
                    u.is_admin,
                    u.email,
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
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'slot_id', das.id,
                                'available_at', das.available_at,
                                'status', das.status,
                                'created_at', das.created_at
                            )
                        )
                        FROM doctor_availability_slots das 
                        WHERE das.doctor_id = d.id
                    ) AS availability_slots,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = CURRENT_DATE
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
                            'status', a.status,
                            'created_at', a.created_at
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                JOIN users u ON d.user_id = u.id
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = CURRENT_DATE
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                WHERE d.user_id = $1
                GROUP BY d.id, d.user_id, d.first_name, d.last_name, u.email, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at, u.is_doctor, u.is_admin;
                """,
                user["id"]

            )

            if user is None:
                logger.warning(f"User not found for email: {email}")
                raise HTTPException(status_code=404, detail="User not found")
            if user["is_doctor"]:
                return dict(doctor)
            if patient is None and not user["is_doctor"]:
                logger.warning(f"Patient not found for user_id: {user['id']}")
                return dict(user)
            
            logger.info(f"User found: {dict(user)}")
            logger.debug("Exiting get_current_user successfully")
            return dict(patient)
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

async def get_current_doctor(current_user: dict = Depends(get_current_user)) -> dict:
    logger.info(f"Entered get_current_admin with user: {current_user}")
    if not current_user["is_doctor"]:
        logger.warning(f"User {current_user['email']} is not doctor")
        raise HTTPException(status_code=403, detail="Doctor access required")
    logger.info(f"User {current_user['email']} is doctor")
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