from fastapi import APIRouter, Depends, HTTPException
from .models import DoctorCreate, DoctorResponse, ReviewCreate, CreateAvailability
from .manager import DoctorManager
from modules.auth.utils import get_current_admin, get_current_user
from shared.response import success_response, error_response
from decimal import Decimal
from datetime import datetime
import json

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

    def serialize_data(doctor_data: dict) -> dict:
        if isinstance(doctor_data.get('created_at'), datetime):
            doctor_data['created_at'] = doctor_data['created_at'].isoformat()
        return doctor_data

router = APIRouter()


@router.post("/")
async def create_doctor(doctor: DoctorCreate, current_admin: dict = Depends(get_current_admin)):
    try:
        doctor_data = await DoctorManager.create_doctor(doctor, current_admin["id"])
        print('Doctor created:', doctor_data)
        return success_response(data=json.loads(json.dumps(doctor_data, cls=DecimalEncoder)), message="Doctor created successfully")
    except Exception as e:
        return error_response(str(e), status_code=400)

@router.get("/{doctor_id}")
async def get_doctor(doctor_id: int):
    try:
        doctor = await DoctorManager.get_doctor(doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return {"status": "success", "data": doctor}
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/user/{user_id}")
async def get_doctor_user_id(user_id: int):
    try:
        doctor = await DoctorManager.get_doctor_by_user_id(user_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return {"status": "success", "data": doctor}
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/")
async def get_all_doctors(
    page: int = 1,
    page_size: int = 10,
    search: str = None,
    specialty: str = None,
    city: str = None,
    is_active: bool = None
):
    try:
        filters = {}
        if specialty is not None:
            filters['specialty'] = specialty
        if city is not None:
            filters['city'] = city
        if is_active is not None:
            filters['is_active'] = is_active

        result = await DoctorManager.get_doctors(
            page=page,
            page_size=page_size,
            search=search,
            specialty=specialty
        )
        
       

        return success_response(
            data=result,
            message="Doctors retrieved successfully"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/{doctor_id}/reviews")
async def add_review(doctor_id: int, review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    try:
        if review.rating < 1 or review.rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        review_data = await DoctorManager.add_review(doctor_id, current_user["id"], review.rating, review.comment)
        return success_response(data=review_data, message="Review added successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/{doctor_id}/availability")
async def create_availability_slot(doctor_id: int, available_at: datetime, current_admin: dict = Depends(get_current_user)):
    try:
        slot_data = await DoctorManager.create_availability_slot(doctor_id, available_at)
        return success_response(data=slot_data, message="Availability slot created successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)
