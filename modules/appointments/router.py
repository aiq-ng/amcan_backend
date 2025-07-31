from fastapi import APIRouter, Depends, HTTPException
from .models import AppointmentCreate, AppointmentResponse
from .manager import AppointmentManager
from modules.auth.utils import get_current_user, get_current_admin, get_current_doctor
from shared.response import success_response, error_response
from typing import List

router = APIRouter()

@router.post("/")
async def book_appointment(appointment: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    try:
        appointment_data = await AppointmentManager.book_appointment(appointment)
        return success_response(data=appointment_data, message="Appointment booked successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/")
async def get_appointments(current_user: dict = Depends(get_current_user)):
    try:
        appointments = await AppointmentManager.get_all_appointments()
        return success_response(data=appointments, message="Appointments retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)


@router.post("/{appointment_id}/confirm")
async def confirm_appointment(appointment_id: int, doctor_id: int, current_user: dict = Depends(get_current_doctor)):
    try:
        result = await AppointmentManager.confirm_appointment(appointment_id, doctor_id)
        return success_response(data=result, message="Appointment confirmed successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: int, doctor_id:int, current_user: dict = Depends(get_current_user)):
    try:
        result = await AppointmentManager.cancel_appointment(appointment_id, doctor_id)
        return success_response(data=result, message="Appointment cancelled successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/patients/{patient_id}")
async def get_patient_appointments(patient_id, current_user: dict = Depends(get_current_user)):
    try:
        appointments = await AppointmentManager.get_patient_appointments(patient_id)
        return {"success": True, "data": appointments, "message": "Patient appointments retrieved successfully"}
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Failed to retrieve appointments"}

@router.get("/all")
async def get_all_appointments(
    doctor_id: int = None,
    patient_id: int = None,
    status: str = None,
    slot_time_from: str = None,
    slot_time_to: str = None,
    created_at_from: str = None,
    created_at_to: str = None,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Admin endpoint to get all appointments with optional filters and pagination.
    """
    from datetime import datetime

    # Parse datetime strings if provided
    slot_time_from_dt = datetime.fromisoformat(slot_time_from) if slot_time_from else None
    slot_time_to_dt = datetime.fromisoformat(slot_time_to) if slot_time_to else None
    created_at_from_dt = datetime.fromisoformat(created_at_from) if created_at_from else None
    created_at_to_dt = datetime.fromisoformat(created_at_to) if created_at_to else None

    try:
        appointments = await AppointmentManager.get_all_appointments(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status=status,
            slot_time_from=slot_time_from_dt,
            slot_time_to=slot_time_to_dt,
            page=page,
            page_size=page_size,
            search=search,
            created_at_from=created_at_from_dt,
            created_at_to=created_at_to_dt,
        )
        return success_response(data=appointments, message="All appointments retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/{appointment_id}")
async def get_appointment_by_id(appointment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        appointment = await AppointmentManager.get_appointment_by_id(appointment_id, current_user)
        return success_response(data=appointment, message="Appointment retrieved successfully")
    except ValueError as e:
        return error_response(str(e), status_code=403)
    except Exception as e:
        return error_response(str(e), status_code=500)
    

@router.get("/doctor/{doctor_id}")
async def get_doctor_appointments(doctor_id: int, current_user: dict = Depends(get_current_user)):
    try:
        appointments = await AppointmentManager.get_appointments_for_doctor(doctor_id)
        print("print doctors appointment", appointments)
        return success_response(data=appointments, message="Doctor's appointments retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)