from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse,
    StudentListResponse, LoginRequest, TokenResponse,
)
from app.services.student_service import student_service

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email + password → JWT tokens."""
    return await student_service.login(db, body.email, body.password)


@router.post("/students", response_model=StudentResponse, status_code=201, tags=["Students"])
async def create_student(body: StudentCreate, db: AsyncSession = Depends(get_db)):
    """Register a new student."""
    return await student_service.create(db, body)


@router.get("/students", response_model=StudentListResponse, tags=["Students"])
async def list_students(
    page:      int           = Query(1, ge=1),
    page_size: int           = Query(20, ge=1, le=100),
    gender:    Optional[str] = Query(None),
    search:    Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession         = Depends(get_db),
):
    """List all students with optional filters."""
    return await student_service.list_students(db, page, page_size, gender, search)


@router.get("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    """Get student profile by student_id (integer)."""
    return await student_service.get_by_student_id(db, student_id)


@router.patch("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
async def update_student(
    student_id: int, body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update student profile."""
    return await student_service.update(db, student_id, body)


@router.delete("/students/{student_id}", status_code=200, tags=["Students"])
async def delete_student(student_id: int, db: AsyncSession = Depends(get_db)):
    """Soft-delete a student."""
    return await student_service.delete(db, student_id)


@router.get("/health", tags=["System"])
async def health():
    return {"service": "student-service", "status": "ok"}
