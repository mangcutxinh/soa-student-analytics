from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.score import ScoreCreate, ScoreUpdate, ScoreResponse, ScoreListResponse, BulkScoreCreate
from app.services.score_service import score_service

router = APIRouter()

# ── Create ────────────────────────────────────────────────────────────────────
@router.post("/scores", response_model=ScoreResponse, status_code=201, tags=["Scores"])
async def create_score(body: ScoreCreate, db: AsyncSession = Depends(get_db)):
    """Submit student marks → auto-compute total_score, grade, PASS/FAIL."""
    return await score_service.create(db, body)

@router.post("/scores/bulk", tags=["Scores"])
async def bulk_create(body: BulkScoreCreate, db: AsyncSession = Depends(get_db)):
    """Upload multiple student scores at once."""
    return await score_service.bulk_create(db, body.scores)

# ── Read ──────────────────────────────────────────────────────────────────────
@router.get("/scores", response_model=ScoreListResponse, tags=["Scores"])
async def list_scores(
    pass_fail:  Optional[str] = Query(None, description="PASS or FAIL"),
    grade:      Optional[str] = Query(None, description="A, B, C, D, or F"),
    gender:     Optional[str] = Query(None),
    page:       int           = Query(1, ge=1),
    page_size:  int           = Query(20, ge=1, le=100),
    db: AsyncSession          = Depends(get_db),
):
    """List all scores. Filter by pass_fail=PASS|FAIL, grade=A|B|C|D|F."""
    return await score_service.list_all(db, pass_fail, grade, gender, page, page_size)

@router.get("/scores/summary", tags=["Analytics"])
async def class_summary(db: AsyncSession = Depends(get_db)):
    """Class-wide pass/fail summary with grade breakdown."""
    return await score_service.class_summary(db)

@router.get("/scores/student/{student_id}", response_model=ScoreResponse, tags=["Scores"])
async def get_score(student_id: int, db: AsyncSession = Depends(get_db)):
    """Get full score record for a student."""
    return await score_service.get_by_student(db, student_id)

@router.get("/scores/student/{student_id}/pass-fail", tags=["Scores"])
async def check_pass_fail(student_id: int, db: AsyncSession = Depends(get_db)):
    """Quick check: did this student pass or fail?
    Returns total_score, grade, PASS/FAIL, and score breakdown."""
    return await score_service.check_pass_fail(db, student_id)

# ── Update / Delete ───────────────────────────────────────────────────────────
@router.patch("/scores/student/{student_id}", response_model=ScoreResponse, tags=["Scores"])
async def update_score(student_id: int, body: ScoreUpdate, db: AsyncSession = Depends(get_db)):
    """Update marks → automatically recomputes total, grade, pass/fail."""
    return await score_service.update(db, student_id, body)

@router.delete("/scores/student/{student_id}", tags=["Scores"])
async def delete_score(student_id: int, db: AsyncSession = Depends(get_db)):
    return await score_service.delete(db, student_id)

# ── Health ────────────────────────────────────────────────────────────────────
@router.get("/health", tags=["System"])
async def health():
    return {"service": "score-service", "status": "ok"}
