
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime

class ProductListingModel(BaseModel):
    id: str
    name: str
    price: int
    image_url: str
    average_rating: float
    total_reviews: int
    category: str

    class Config:
        schema_extra = {
            "example": {
                "id": "prod_001",
                "name": "Therapy Kit",
                "price": 50000,
                "image_url": "https://example.com/image.jpg",
                "average_rating": 4.5,
                "total_reviews": 10,
                "category": "Wellness"
            }
        }

class ProductDetailModel(BaseModel):
    id: str
    name: str
    description: str
    price: int
    image_urls: List[str]
    average_rating: float
    total_reviews: int
    key_benefits: List[str]
    specifications: List[Dict[str, str]]
    category: str

    class Config:
        schema_extra = {
            "example": {
                "id": "prod_001",
                "name": "Therapy Kit",
                "description": "A comprehensive therapy kit.",
                "price": 50000,
                "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "average_rating": 4.5,
                "total_reviews": 10,
                "key_benefits": ["Relieves stress", "Improves focus"],
                "specifications": [{"name": "Weight", "value": "12 lbs"}, {"name": "Color", "value": "Blue"}],
                "category": "Wellness"
            }
        }

class ReviewCreateModel(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str

    @validator('rating')
    def rating_must_be_valid(cls, v):
        if not isinstance(v, int):
            raise ValueError('Rating must be an integer')
        return v

class ReviewResponseModel(BaseModel):
    id: str
    rating: int
    comment: str
    user_name: str
    created_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "rev_001",
                "rating": 4,
                "comment": "Great product!",
                "user_name": "John Doe",
                "created_at": "2025-07-11T06:14:00Z"
            }
        }
