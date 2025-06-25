from fastapi import APIRouter, Depends, HTTPException
from .models import AppointmentCreate, AppointmentResponse
from .manager import AppointmentManager
from modules.auth.utils import get_current_user
from shared.response import success_response, error_response
from typing import List

router = APIRouter()

@router.post("/")
async def book_appointment(appointment: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    try:
        appointment_data = await AppointmentManager.book_appointment(appointment, current_user["id"])
        return success_response(data=appointment_data, message="Appointment booked successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/")
async def get_appointments(current_user: dict = Depends(get_current_user)):
    try:
        appointments = await AppointmentManager.get_appointments(current_user["id"])
        return success_response(data=appointments, message="Appointments retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)


@router.post("/{appointment_id}/confirm")
async def confirm_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        result = await AppointmentManager.confirm_appointment(appointment_id, current_user["id"])
        return success_response(data=result, message="Appointment confirmed successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        result = await AppointmentManager.cancel_appointment(appointment_id, current_user["id"])
        return success_response(data=result, message="Appointment cancelled successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)