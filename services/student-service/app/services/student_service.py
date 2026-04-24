from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from typing import Optional

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings


class StudentService:

    async def create(self, db: AsyncSession, data: StudentCreate) -> Student:
        exists = await db.execute(
            select(Student).where(Student.student_id == data.student_id)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(409, f"student_id {data.student_id} already exists")

        pw_hash = hash_password(data.password) if data.password else None
        student = Student(
            student_id   = data.student_id,
            name         = data.name,
            age          = data.age,
            gender       = data.gender,
            email        = data.email,
            password_hash= pw_hash,
            previous_gpa = data.previous_gpa,
            role         = data.role,
        )
        db.add(student)
        await db.flush()
        await db.refresh(student)
        return student

    async def get_by_student_id(self, db: AsyncSession, student_id: int) -> Student:
        result = await db.execute(
            select(Student).where(Student.student_id == student_id, Student.is_deleted == False)
        )
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(404, f"Student {student_id} not found")
        return s

    async def list_students(
        self, db: AsyncSession,
        page: int = 1, page_size: int = 20,
        gender: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        q = select(Student).where(Student.is_deleted == False)
        if gender: q = q.where(Student.gender.ilike(f"%{gender}%"))
        if search: q = q.where(Student.name.ilike(f"%{search}%"))

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    async def update(self, db: AsyncSession, student_id: int, data: StudentUpdate) -> Student:
        student = await self.get_by_student_id(db, student_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(student, k, v)
        await db.flush()
        await db.refresh(student)
        return student

    async def delete(self, db: AsyncSession, student_id: int) -> dict:
        student = await self.get_by_student_id(db, student_id)
        student.is_deleted = True
        return {"message": f"Student {student_id} deleted"}

    async def login(self, db: AsyncSession, email: str, password: str) -> dict:
        result = await db.execute(
            select(Student).where(Student.email == email, Student.is_deleted == False)
        )
        student = result.scalar_one_or_none()
        if not student or not student.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(password, student.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token  = create_access_token(
            subject=str(student.student_id),
            extra={"role": student.role, "name": student.name}
        )
        refresh_token = create_refresh_token(subject=str(student.student_id))
        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "expires_in":    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }


student_service = StudentService()
