from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class FeedItemBase(BaseModel):
    title: str
    content_type: Literal["video", "audio", "article"]
    description: Optional[str] = None

class FeedItemCreate(FeedItemBase):
    title: str
    url: Optional[str] = None  # For video or audio
    content_type: str
    content: Optional[str] = None  # For articles

class FeedItemResponse(FeedItemBase):
    id: int
    url: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime
    created_by: int