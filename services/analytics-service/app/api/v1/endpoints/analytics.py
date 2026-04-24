from fastapi import APIRouter, Query
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("/analytics/overview", tags=["Analytics"])
async def overview():
    """Class KPIs: total students, pass/fail counts, avg score, grade distribution."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.overview(scores)


@router.get("/analytics/score-bands", tags=["Analytics"])
async def score_bands():
    """Score distribution by band (0-29, 30-39, ... 90-100)."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.score_bands(scores)


@router.get("/analytics/gender", tags=["Analytics"])
async def gender_breakdown():
    """Performance breakdown by gender."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.gender_breakdown(scores)


@router.get("/analytics/attendance", tags=["Analytics"])
async def attendance_impact():
    """Attendance rate vs pass rate — shows correlation."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.attendance_impact(scores)


@router.get("/analytics/at-risk", tags=["Analytics"])
async def at_risk():
    """Students who failed or have dangerously low attendance."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.at_risk(scores)


@router.get("/analytics/top-students", tags=["Analytics"])
async def top_students(n: int = Query(10, ge=1, le=50)):
    """Top N students by total score."""
    scores = await analytics_service._fetch_all_scores()
    return await analytics_service.top_students(scores, n)


@router.get("/analytics/student/{student_id}", tags=["Analytics"])
async def student_report(student_id: int):
    """Full score report for a single student with pass/fail verdict."""
    return await analytics_service.student_report(student_id)


@router.get("/health", tags=["System"])
async def health():
    return {"service": "analytics-service", "status": "ok"}
