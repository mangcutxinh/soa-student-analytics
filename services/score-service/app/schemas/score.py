from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class ScoreCreate(BaseModel):
    student_id:        int
    name:              Optional[str] = None
    age:               Optional[int] = None
    gender:            Optional[str] = None
    quiz1_marks:       float          # /10
    quiz2_marks:       float          # /10
    quiz3_marks:       float          # /10
    midterm_marks:     float          # /30
    final_marks:       float          # /50
    previous_gpa:      Optional[float] = None
    lectures_attended: Optional[int]  = 0
    labs_attended:     Optional[int]  = 0

    @field_validator("quiz1_marks","quiz2_marks","quiz3_marks")
    @classmethod
    def validate_quiz(cls, v):
        if not 0 <= v <= 10:
            raise ValueError("Quiz marks must be 0–10")
        return round(v, 1)

    @field_validator("midterm_marks")
    @classmethod
    def validate_midterm(cls, v):
        if not 0 <= v <= 30:
            raise ValueError("Midterm marks must be 0–30")
        return round(v, 1)

    @field_validator("final_marks")
    @classmethod
    def validate_final(cls, v):
        if not 0 <= v <= 50:
            raise ValueError("Final marks must be 0–50")
        return round(v, 1)


class ScoreUpdate(BaseModel):
    quiz1_marks:       Optional[float] = None
    quiz2_marks:       Optional[float] = None
    quiz3_marks:       Optional[float] = None
    midterm_marks:     Optional[float] = None
    final_marks:       Optional[float] = None
    lectures_attended: Optional[int]   = None
    labs_attended:     Optional[int]   = None


class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    student_id:       int
    name:             Optional[str]
    age:              Optional[int]
    gender:           Optional[str]
    # Raw marks
    quiz1_marks:      float
    quiz2_marks:      float
    quiz3_marks:      float
    midterm_marks:    float
    final_marks:      float
    previous_gpa:     Optional[float]
    lectures_attended: Optional[int]
    labs_attended:    Optional[int]
    # Computed
    quiz_score:       Optional[float]
    midterm_score:    Optional[float]
    final_score:      Optional[float]
    total_score:      Optional[float]
    grade:            Optional[str]
    grade_point:      Optional[float]
    pass_fail:        Optional[str]
    is_pass:          Optional[bool]
    performance_tier: Optional[str]
    attendance_rate:  Optional[float]
    created_at:       Optional[datetime]


class ScoreListResponse(BaseModel):
    total: int
    items: list[ScoreResponse]


class BulkScoreCreate(BaseModel):
    scores: list[ScoreCreate]


class PassFailSummary(BaseModel):
    total_students: int
    pass_count:     int
    fail_count:     int
    pass_rate_pct:  float
    fail_rate_pct:  float
    avg_total_score: float
    grade_breakdown: dict
