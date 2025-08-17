from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubscriptionType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class SubscriptionCreate(BaseModel):
    user_id: int
    subscription_type: SubscriptionType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    payment_method: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    subscription_type: Optional[SubscriptionType] = None
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    payment_method: Optional[str] = None

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    subscription_type: SubscriptionType
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime

class SubscriptionPlan(BaseModel):
    id: int
    name: str
    type: SubscriptionType
    price: float
    currency: str = "USD"
    duration_days: int
    features: List[str]
    is_active: bool = True
