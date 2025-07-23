
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class BlogPostCreateModel(BaseModel):
    title: str
    description: str
    content_type: str = Field(..., pattern='^(video|audio|article)$')
    content_url: str  # Cloudinary URL for video/audio; HTML for articles
    duration: Optional[int] = None  # Seconds for video/audio; NULL for articles
    thumbnail: Any
    mood_relevance: Dict[str, float] = Field(
        ...,
        example={"Happy": 0.8, "Calm": 0.5, "Manic": 0.2, "Sad": 0.1, "Angry": 0.0}
    )

    @validator('mood_relevance')
    def validate_mood_relevance(cls, v):
        valid_moods = {'Happy', 'Calm', 'Manic', 'Sad', 'Angry'}
        if not all(mood in valid_moods for mood in v.keys()):
            raise ValueError('Invalid mood keys; must be Happy, Calm, Manic, Sad, or Angry')
        if not all(0 <= score <= 1 for score in v.values()):
            raise ValueError('Relevance scores must be between 0 and 1')
        return v

    @validator('duration')
    def validate_duration(cls, v, values):
        if v is not None and values.get('content_type') == 'article':
            raise ValueError('Duration should not be set for articles')
        return v

class BlogPostResponseModel(BaseModel):
    id: str
    title: str
    content_type: str
    content_url: str  # HTML for articles; URL for video/audio
    duration: Optional[int]
    mood_relevance: Dict[str, float]
    created_at: datetime
    user_id: str

    class Config:
        schema_extra = {
            "example": {
                "id": "blog_003",
                "title": "Mindfulness Guide",
                "content_type": "article",
                "content_url": "<h1>Mindfulness Guide</h1><p>Learn to relax with these steps...</p>",
                "duration": 0,
                "mood_relevance": {"Happy": 0.3, "Calm": 0.9, "Manic": 0.1, "Sad": 0.4, "Angry": 0.0},
                "created_at": "2025-07-21T10:50:00-07:00",
                "user_id": "user_001"
            }
        }

class MoodRecommendationModel(BaseModel):
    current_mood: str = Field(..., pattern='^(Happy|Calm|Manic|Sad|Angry)$')
