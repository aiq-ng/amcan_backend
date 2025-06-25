from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict

class Availability(BaseModel):
    day: str
    slots: List[str]

class DoctorCreate(BaseModel):
    user_id: int
    title: str
    bio: str
    experience_years: int
    patients_count: int
    location: str
    availability: List[Availability]

class DoctorResponse(BaseModel):
    id: int
    user_id: int
    title: str
    bio: str
    experience_years: int
    patients_count: int
    location: str
    rating: float
    availability: Dict[str, List[str]]
    created_at: str

class ReviewCreate(BaseModel):
    rating: int
    comment: str
    user_id: Optional[int] = None  # If needed based on your auth system
