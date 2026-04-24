from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from typing import Optional
from collections import defaultdict

from app.models.score import Score
from app.schemas.score import ScoreCreate, ScoreUpdate


class ScoreService:

    async def create(self, db: AsyncSession, data: ScoreCreate) -> Score:
        existing = await db.execute(
            select(Score).where(Score.student_id == data.student_id, Score.is_deleted == False)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"Score for student {data.student_id} already exists. Use PATCH to update.")

        score = Score(**data.model_dump())
        score.compute_scores()   # ← auto-compute total, pass/fail, grade
        db.add(score)
        await db.flush()
        await db.refresh(score)
        return score

    async def bulk_create(self, db: AsyncSession, items: list[ScoreCreate]) -> dict:
        created, skipped = 0, 0
        for item in items:
            try:
                await self.create(db, item)
                created += 1
            except HTTPException:
                skipped += 1
        return {"created": created, "skipped_duplicates": skipped}

    async def get(self, db: AsyncSession, score_id: int) -> Score:
        result = await db.execute(
            select(Score).where(Score.id == score_id, Score.is_deleted == False)
        )
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(404, f"Score id={score_id} not found")
        return s

    async def get_by_student(self, db: AsyncSession, student_id: int) -> Score:
        result = await db.execute(
            select(Score).where(Score.student_id == student_id, Score.is_deleted == False)
        )
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(404, f"No score for student_id={student_id}")
        return s

    async def list_all(
        self, db: AsyncSession,
        pass_fail: Optional[str] = None,
        grade: Optional[str] = None,
        gender: Optional[str] = None,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        q = select(Score).where(Score.is_deleted == False)
        if pass_fail: q = q.where(Score.pass_fail == pass_fail.upper())
        if grade:     q = q.where(Score.grade == grade.upper())
        if gender:    q = q.where(Score.gender.ilike(gender))

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
        return {"total": total, "items": items}

    async def update(self, db: AsyncSession, student_id: int, data: ScoreUpdate) -> Score:
        score = await self.get_by_student(db, student_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(score, k, v)
        score.compute_scores()   # ← recompute after update
        await db.flush()
        await db.refresh(score)
        return score

    async def delete(self, db: AsyncSession, student_id: int) -> dict:
        score = await self.get_by_student(db, student_id)
        score.is_deleted = True
        return {"message": f"Score for student {student_id} deleted"}

    async def class_summary(self, db: AsyncSession) -> dict:
        """Pass/fail summary for the whole class."""
        result = await db.execute(
            select(Score).where(Score.is_deleted == False)
        )
        scores = result.scalars().all()
        if not scores:
            raise HTTPException(404, "No scores found")

        total      = len(scores)
        pass_list  = [s for s in scores if s.is_pass]
        fail_list  = [s for s in scores if not s.is_pass]
        totals     = [s.total_score for s in scores if s.total_score]

        grade_breakdown = defaultdict(int)
        for s in scores:
            grade_breakdown[s.grade or "?"] += 1

        return {
            "total_students":  total,
            "pass_count":      len(pass_list),
            "fail_count":      len(fail_list),
            "pass_rate_pct":   round(len(pass_list)/total*100, 2),
            "fail_rate_pct":   round(len(fail_list)/total*100, 2),
            "avg_total_score": round(sum(totals)/len(totals), 2) if totals else 0,
            "grade_breakdown": dict(sorted(grade_breakdown.items())),
        }

    async def check_pass_fail(self, db: AsyncSession, student_id: int) -> dict:
        """Quick endpoint: is this student passing?"""
        score = await self.get_by_student(db, student_id)
        return {
            "student_id":    score.student_id,
            "name":          score.name,
            "total_score":   score.total_score,
            "pass_fail":     score.pass_fail,
            "is_pass":       score.is_pass,
            "grade":         score.grade,
            "grade_point":   score.grade_point,
            "performance_tier": score.performance_tier,
            "score_breakdown": {
                "quiz_score":    score.quiz_score,
                "midterm_score": score.midterm_score,
                "final_score":   score.final_score,
                "total":         score.total_score,
            },
            "message": f"{'✅ PASSED' if score.is_pass else '❌ FAILED'} with {score.total_score}/100"
        }


score_service = ScoreService()
