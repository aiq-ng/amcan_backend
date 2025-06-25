# modules/chat/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    appointment_id: int
    message: str

class MessageResponse(BaseModel):
    id: int
    appointment_id: int
    sender_id: int
    receiver_id: int
    message: str
    sent_at: datetime