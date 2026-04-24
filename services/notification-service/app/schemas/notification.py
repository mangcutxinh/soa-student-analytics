from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class ChannelEnum(str, Enum):
    email  = "email"
    push   = "push"
    in_app = "in_app"


class NotificationCreate(BaseModel):
    recipient_id:    str
    recipient_email: Optional[str] = None   # plain str, no EmailStr to avoid email-validator
    channel:         ChannelEnum = ChannelEnum.in_app
    event_type:      str
    title:           str
    body:            str


class BulkNotificationCreate(BaseModel):
    recipient_ids:   list[str]
    channel:         ChannelEnum = ChannelEnum.in_app
    event_type:      str
    title:           str
    body:            str


class ScorePostedEvent(BaseModel):
    student_id:    str
    student_email: Optional[str] = None
    subject:       Optional[str] = None
    total_score:   float
    grade:         str
    pass_fail:     str   # PASS | FAIL


class AtRiskAlertEvent(BaseModel):
    students: list[dict]   # [{student_id, total_score, risk_level}]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    recipient_id: str
    channel:      str
    event_type:   str
    title:        str
    body:         str
    status:       str
    is_read:      bool
    sent_at:      Optional[datetime]
    created_at:   datetime


class NotificationListResponse(BaseModel):
    total: int
    items: list[NotificationResponse]
