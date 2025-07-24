from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class AppointmentCreate(BaseModel):
    doctor_id: int
    slot_time: datetime
    patient_id: int

    @validator("slot_time", pre=True)
    def parse_slot_time(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            # Try parsing with zero-padded hour first
            return datetime.fromisoformat(value)
        except ValueError:
            # Try parsing with single-digit hour
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except Exception as e:
            raise ValueError("slot_time must be a valid datetime string") from e

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    user_id: int
    slot_time: datetime
    status: str
    created_at: datetime