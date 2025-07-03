# modules/video_call/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CallInitiate(BaseModel):
    appointment_id: int

class CallResponse(BaseModel):
    id: int
    appointment_id: int
    initiator_id: int
    receiver_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    created_at: datetime