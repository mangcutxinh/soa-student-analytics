from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class StudentCreate(BaseModel):
    student_id:   int
    name:         str
    age:          Optional[int]   = None
    gender:       Optional[str]   = None
    email:        Optional[str]   = None
    password:     Optional[str]   = None
    previous_gpa: Optional[float] = None
    role:         str = "student"


class StudentUpdate(BaseModel):
    name:         Optional[str]   = None
    age:          Optional[int]   = None
    gender:       Optional[str]   = None
    email:        Optional[str]   = None
    previous_gpa: Optional[float] = None
    status:       Optional[str]   = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    student_id:   int
    name:         str
    age:          Optional[int]
    gender:       Optional[str]
    email:        Optional[str]
    previous_gpa: Optional[float]
    role:         str
    status:       str
    created_at:   Optional[datetime]
    updated_at:   Optional[datetime]


class StudentListResponse(BaseModel):
    total:     int
    page:      int
    page_size: int
    items:     list[StudentResponse]


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int
