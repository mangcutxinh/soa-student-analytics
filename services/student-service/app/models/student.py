from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.db.session import Base


class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    student_id    = Column(Integer, unique=True, index=True, nullable=False)  # 1,2,3... from CSV
    name          = Column(String(100), nullable=False)
    age           = Column(Integer, nullable=True)
    gender        = Column(String(10), nullable=True)
    email         = Column(String(120), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    previous_gpa  = Column(Float, nullable=True)
    role          = Column(String(20), default="student")   # student | lecturer | admin
    status        = Column(String(20), default="active")    # active | inactive | graduated

    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted    = Column(Boolean, default=False)
