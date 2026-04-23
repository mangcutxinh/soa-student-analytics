"""
CSV-backed score provider.

Reads the mock dataset, applies the README scoring formula, and returns
a list of score dicts compatible with what analytics-service expects.

Scoring formula (thang 100):
    quiz_total  = quiz1 + quiz2 + quiz3              (each 0-10, total 0-30)
    midterm_pct = midterm_marks / 30 * 20            (0-20)
    final_pct   = final_marks   / 50 * 50  = final   (0-50)
    total_score = quiz_total + midterm_pct + final_pct   (0-100)
    grade_10    = total_score / 10                   (0-10)

Fail-course threshold: grade_10 < 5.0 → is_failing=True, warning="Rớt môn"
"""
import csv
import os
from pathlib import Path
from typing import Optional

from app.core.config import settings

_GRADE_THRESHOLDS = (
    (8.5, "A"),
    (7.0, "B"),
    (5.5, "C"),
    (4.0, "D"),
)


def _letter_grade(grade_10: float) -> str:
    for threshold, letter in _GRADE_THRESHOLDS:
        if grade_10 >= threshold:
            return letter
    return "F"


def _compute_row(row: dict) -> dict:
    """Compute all derived fields for a single CSV row."""
    q1 = float(row["quiz1_marks"])
    q2 = float(row["quiz2_marks"])
    q3 = float(row["quiz3_marks"])
    midterm = float(row["midterm_marks"])
    final = float(row["final_marks"])
    lectures = int(row.get("lectures_attended", 0))
    labs = int(row.get("labs_attended", 0))

    # --- Formula per README ---
    quiz_total  = q1 + q2 + q3                     # 0..30
    midterm_pct = midterm / 30.0 * 20.0             # 0..20
    final_pct   = final / 50.0 * 50.0               # 0..50 (= final)
    total_score = quiz_total + midterm_pct + final_pct  # 0..100
    grade_10    = round(total_score / 10.0, 2)

    # Compatibility fields scaled to 0..10 for analytics-service
    midterm_score   = round(midterm / 30.0 * 10.0, 2)
    final_score     = round(final   / 50.0 * 10.0, 2)
    attendance_rate = round((lectures + labs) / settings.MAX_SESSIONS, 4)
    grade           = _letter_grade(grade_10)

    is_failing = grade_10 < 5.0
    warning: Optional[str] = "Rớt môn" if is_failing else None

    return {
        # Fields expected by analytics-service
        "student_id":      str(row["student_id"]),
        "subject":         "General",
        "semester":        "2024-1",
        "midterm_score":   midterm_score,
        "final_score":     final_score,
        "attendance_rate": attendance_rate,
        "gpa":             grade_10,          # analytics-service reads this as 0..10
        "grade":           grade,
        # Extra fields with explicit names
        "name":            row.get("name", ""),
        "total_score":     round(total_score, 2),
        "grade_10":        grade_10,
        "is_failing":      is_failing,
        "warning":         warning,
        "previous_gpa":    float(row.get("previous_gpa", 0)),
    }


def _resolve_csv_path() -> Path:
    """Resolve CSV_DATA_PATH relative to the repo root (4 levels up from this file)."""
    p = Path(settings.CSV_DATA_PATH)
    if p.is_absolute():
        return p
    # This file lives at services/score-service/app/services/csv_score_provider.py
    # Repo root is 4 directories up.
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / p


_cache: Optional[list] = None


def load_scores() -> list[dict]:
    """Load and cache all scores from the CSV dataset."""
    global _cache
    if _cache is not None:
        return _cache
    path = _resolve_csv_path()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _cache = [_compute_row(row) for row in reader]
    return _cache


def clear_cache() -> None:
    """Invalidate the in-memory cache (useful for testing)."""
    global _cache
    _cache = None
