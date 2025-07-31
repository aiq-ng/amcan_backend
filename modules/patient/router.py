from fastapi import APIRouter, HTTPException, Depends
router = APIRouter(prefix="/patients", tags=["patients"])
from .models import PatientCreate, PatientUpdate, PatientResponse
from .manager import get_patient_by_user_id, create_patient, update_patient, delete_patient, get_all_patients, get_patient_using_id
from modules.auth.utils import get_current_user
from shared.response import success_response

router = APIRouter()


@router.post("/")
async def create_patient_endpoint(patient_data: PatientCreate, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    patient = await create_patient(patient_data)
   
    if not patient:
        raise HTTPException(status_code=500, detail="Failed to create patient")
    return patient

from datetime import datetime

@router.get('/')
async def get_patients(
    page: int = 1,
    page_size: int = 10,
    search: str = None,
    therapy_name: str = None,
    therapy_criticality: str = None,
    created_at_from: str = None,
    created_at_to: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all patients with optional filters, search, and pagination.
    """
    try:
        filters = {}
        created_at_from_dt = None
        created_at_to_dt = None


        if therapy_criticality is not None:
            filters['therapy_criticality'] = therapy_criticality
        if created_at_from is not None:
            try:
                created_at_from_dt = datetime.fromisoformat(created_at_from)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid created_at_from format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
            filters['created_at_from'] = created_at_from_dt
        if created_at_to is not None:
            try:
                created_at_to_dt = datetime.fromisoformat(created_at_to)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid created_at_to format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
            filters['created_at_to'] = created_at_to_dt

        patients = await get_all_patients(
            page=page,
            page_size=page_size,
            search=search,
            therapy_name=therapy_name,
            created_at_from=created_at_from_dt,
            created_at_to=created_at_to_dt,
        )
        if not patients or not patients.get("data"):
            raise HTTPException(status_code=404, detail="No patients found")
        return success_response(message="Patients fetched successfully", data=patients)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/me")
async def get_patient_by_user(current_user: dict = Depends(get_current_user)):
    print("**** current user", current_user)
    patient = await get_patient_by_user_id(current_user["id"])
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get('/{patient_id}')
async def get_patient_by_patient_id(patient_id: int, current_user: dict = Depends(get_current_user)):
    patient = await get_patient_using_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/me")
async def update_patient_endpoint(patient_data: PatientUpdate, current_user: dict = Depends(get_current_user)):
    patient = await update_patient(current_user["id"], patient_data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or no updates applied")
    return patient

@router.delete("/me")
async def delete_patient_endpoint(current_user: dict = Depends(get_current_user)):
    success = await delete_patient(current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete patient")
    return {"message": "Patient deleted successfully"}

# @router.get("/me/appointments")
# async def get_patient_appointments_endpoint(current_user: dict = Depends(get_current_user)):
#     appointments = await get_patient_appointments(current_user["id"])
#     return appointments