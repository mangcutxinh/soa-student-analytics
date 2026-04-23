"""
Analytics-service unit tests – at-risk logic and score integration.
Run: pytest tests/ -v
"""
import pytest
from app.services.analytics_service import analytics_service


# Test score dataset:
#   "1" – good student: high gpa, good attendance
#   "3" – failing:      gpa < 5.0, is_failing=True, grade "F"
#   "5" – low-attend:   gpa ok but attendance_rate < 0.6

SCORES_MIXED = [
    # good student
    {"student_id": "1", "gpa": 7.76, "grade": "B", "attendance_rate": 0.80,
     "midterm_score": 10.0, "final_score": 7.3, "subject": "General",
     "is_failing": False, "warning": None},
    # failing student (grade_10 < 5.0)
    {"student_id": "3", "gpa": 3.8, "grade": "F", "attendance_rate": 0.0,
     "midterm_score": 3.0, "final_score": 3.5, "subject": "General",
     "is_failing": True, "warning": "Rớt môn"},
    # low-attendance student (grade ok but attendance < 0.6)
    {"student_id": "5", "gpa": 6.0, "grade": "C", "attendance_rate": 0.50,
     "midterm_score": 7.0, "final_score": 6.0, "subject": "General",
     "is_failing": False, "warning": None},
]


# ── at_risk_students ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_at_risk_includes_failing_student():
    result = await analytics_service.at_risk_students(SCORES_MIXED)
    ids = {r["student_id"] for r in result}
    assert "3" in ids   # failing: gpa < 5.0


@pytest.mark.asyncio
async def test_at_risk_includes_low_attendance():
    result = await analytics_service.at_risk_students(SCORES_MIXED)
    ids = {r["student_id"] for r in result}
    assert "5" in ids   # attendance_rate = 0.50 < 0.6


@pytest.mark.asyncio
async def test_at_risk_excludes_good_student():
    result = await analytics_service.at_risk_students(SCORES_MIXED)
    ids = {r["student_id"] for r in result}
    assert "1" not in ids  # gpa=7.76, attendance=0.80 → not at risk


@pytest.mark.asyncio
async def test_at_risk_failing_has_warning():
    result = await analytics_service.at_risk_students(SCORES_MIXED)
    failing = next(r for r in result if r["student_id"] == "3")
    assert failing["is_failing"] is True
    assert failing["warning"] == "Rớt môn"


@pytest.mark.asyncio
async def test_at_risk_non_failing_warning_none():
    result = await analytics_service.at_risk_students(SCORES_MIXED)
    low_att = next(r for r in result if r["student_id"] == "5")
    assert low_att["is_failing"] is False
    assert low_att["warning"] is None


# ── overview at_risk_count ────────────────────────────────────────────────────
# NOTE: get_overview counts at-risk students by gpa<5.0 or fails>=2 (no attendance check)

@pytest.mark.asyncio
async def test_overview_at_risk_count():
    overview = await analytics_service.get_overview(SCORES_MIXED)
    # Only student "3" has gpa < 5.0; student "5" is flagged by attendance in
    # at_risk_students but overview uses the simpler gpa/fail threshold.
    assert overview["at_risk_count"] == 1


@pytest.mark.asyncio
async def test_overview_pass_rate():
    overview = await analytics_service.get_overview(SCORES_MIXED)
    # grade F: student "3" → 1 fail, 2 pass → 66.7%
    assert abs(overview["pass_rate"] - 100.0 * 2 / 3) < 1.0


# ── gpa_distribution ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gpa_distribution_sums_to_100():
    dist = await analytics_service.gpa_distribution(SCORES_MIXED)
    total_pct = sum(d["percentage"] for d in dist)
    assert abs(total_pct - 100.0) < 1.0  # allow rounding margin

