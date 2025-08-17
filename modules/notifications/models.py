from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    APPOINTMENT = "appointment"
    SUBSCRIPTION = "subscription"
    SYSTEM = "system"
    REMINDER = "reminder"
    ALERT = "alert"
    MESSAGE = "message"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    data: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    status: NotificationStatus
    priority: NotificationPriority
    data: Optional[Dict[str, Any]]
    created_at: datetime
    read_at: Optional[datetime]
    scheduled_at: Optional[datetime]

class NotificationPreferences(BaseModel):
    user_id: int
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    appointment_reminders: bool = True
    subscription_alerts: bool = True
    system_notifications: bool = True
