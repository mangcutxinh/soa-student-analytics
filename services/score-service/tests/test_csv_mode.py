"""
CSV-mode integration tests for score-service.
These tests exercise the new CSV-backed endpoints and the scoring formula.
Run: pytest tests/test_csv_mode.py -v
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.csv_score_provider import clear_cache


@pytest.fixture(autouse=True)
def reset_csv_cache():
    """Ensure the CSV cache is fresh before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_csv_mode(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["mode"] == "csv"


# ── list-all ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_all_returns_300(client):
    r = await client.get("/api/v1/scores")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 300
    assert len(body["items"]) == 300


@pytest.mark.asyncio
async def test_list_all_page_size(client):
    r = await client.get("/api/v1/scores?page_size=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 300          # real total
    assert len(body["items"]) == 10      # sliced


# ── scoring formula ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scoring_formula_student_1(client):
    """
    Student 1 CSV row:
      quiz1=8, quiz2=5.7, quiz3=7.4, midterm=30, final=36.5
      quiz_total  = 8+5.7+7.4 = 21.1
      midterm_pct = 30/30*20  = 20.0
      final_pct   = 36.5      = 36.5
      total_score = 77.6  → grade_10 = 7.76
    """
    r = await client.get("/api/v1/scores/student/1")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert abs(item["grade_10"] - 7.76) < 0.01
    assert abs(item["gpa"] - 7.76) < 0.01   # gpa mirrors grade_10
    assert item["grade"] == "B"
    assert item["is_failing"] is False
    assert item["warning"] is None


# ── fail-course warning ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_failing_student_flag(client):
    """Student 3 has grade_10 ≈ 4.34 → is_failing=True, warning='Rớt môn'."""
    r = await client.get("/api/v1/scores/student/3")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["is_failing"] is True
    assert item["warning"] == "Rớt môn"
    assert item["grade_10"] < 5.0


# ── by-subject (no subject dimension) ────────────────────────────────────────

@pytest.mark.asyncio
async def test_by_subject_returns_empty(client):
    r = await client.get("/api/v1/scores/subject/Math")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


# ── summary ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summary_failing_student(client):
    r = await client.get("/api/v1/scores/summary/3")
    assert r.status_code == 200
    body = r.json()
    assert body["fail_count"] == 1
    assert body["pass_count"] == 0


@pytest.mark.asyncio
async def test_summary_unknown_student_404(client):
    r = await client.get("/api/v1/scores/summary/999999")
    assert r.status_code == 404
