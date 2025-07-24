from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Any

class PatientCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    address: str
    phone_number: str
    occupation: str
    emergency_contact_name: str
    emergency_contact_phone: str
    marital_status: str
    user_id: Any

    class Config:
        schema_extra = {
            "example": {
                "email": "newpatient@example.com",
                "password": "Patient123!",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-05-15",
                "address": "123 Main St, Kaduna",
                "phone_number": "+2348012345678",
                "occupation": "Teacher",
                "emergency_contact_name": "Jane Doe",
                "emergency_contact_phone": "+2348098765432",
                "marital_status": "Single"
            }
        }

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    occupation: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    marital_status: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    date_of_birth: datetime
    address: str
    phone_number: str
    occupation: str
    emergency_contact_name: str
    emergency_contact_phone: str
    marital_status: str
    profile_image_url: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    slot_time: datetime
    complain: Optional[str] = None
    status: str
    created_at: datetime
    doctor_first_name: str
    doctor_last_name: str
    doctor_title: str

    class Config:
        orm_mode = True