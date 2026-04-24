"""
Analytics Service — pulls from score-service and computes class statistics.
All fields match the real CSV: quiz1/2/3_marks, midterm_marks, final_marks,
total_score, pass_fail, grade, attendance_rate.
"""
import httpx
from collections import defaultdict
from fastapi import HTTPException
from app.core.config import settings


class AnalyticsService:

    async def _fetch_all_scores(self) -> list[dict]:
        """Get all score records from score-service."""
        url = f"{settings.SCORE_SERVICE_URL}/api/v1/scores?page_size=1000"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("items", [])
            except httpx.RequestError:
                raise HTTPException(503, "score-service unreachable")
            except httpx.HTTPStatusError as e:
                raise HTTPException(e.response.status_code, "score-service error")

    async def _fetch_student_score(self, student_id: int) -> dict:
        url = f"{settings.SCORE_SERVICE_URL}/api/v1/scores/student/{student_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(404, f"Student {student_id} not found in score-service")

    # ── Overview KPIs ─────────────────────────────────────────────────────────
    async def overview(self, scores: list[dict]) -> dict:
        if not scores:
            return {"error": "no data"}

        total      = len(scores)
        pass_list  = [s for s in scores if s.get("pass_fail") == "PASS"]
        fail_list  = [s for s in scores if s.get("pass_fail") == "FAIL"]
        totals     = [s["total_score"] for s in scores if s.get("total_score") is not None]

        grade_dist = defaultdict(int)
        for s in scores:
            grade_dist[s.get("grade") or "?"] += 1

        tier_dist = defaultdict(int)
        for s in scores:
            tier_dist[s.get("performance_tier") or "?"] += 1

        return {
            "total_students":   total,
            "pass_count":       len(pass_list),
            "fail_count":       len(fail_list),
            "pass_rate_pct":    round(len(pass_list) / total * 100, 2),
            "fail_rate_pct":    round(len(fail_list) / total * 100, 2),
            "avg_total_score":  round(sum(totals) / len(totals), 2) if totals else 0,
            "max_total_score":  max(totals) if totals else 0,
            "min_total_score":  min(totals) if totals else 0,
            "grade_distribution":       dict(sorted(grade_dist.items())),
            "performance_distribution": dict(sorted(tier_dist.items())),
        }

    # ── Score band distribution ───────────────────────────────────────────────
    async def score_bands(self, scores: list[dict]) -> list[dict]:
        bands = {
            "90-100": 0, "80-89": 0, "70-79": 0,
            "60-69":  0, "50-59": 0, "40-49": 0,
            "30-39":  0, "0-29":  0,
        }
        for s in scores:
            t = s.get("total_score") or 0
            if   t >= 90: bands["90-100"] += 1
            elif t >= 80: bands["80-89"]  += 1
            elif t >= 70: bands["70-79"]  += 1
            elif t >= 60: bands["60-69"]  += 1
            elif t >= 50: bands["50-59"]  += 1
            elif t >= 40: bands["40-49"]  += 1
            elif t >= 30: bands["30-39"]  += 1
            else:         bands["0-29"]   += 1

        total = len(scores) or 1
        return [
            {"band": k, "count": v, "pct": round(v / total * 100, 1)}
            for k, v in bands.items()
        ]

    # ── Gender performance breakdown ──────────────────────────────────────────
    async def gender_breakdown(self, scores: list[dict]) -> list[dict]:
        by_gender = defaultdict(list)
        for s in scores:
            by_gender[s.get("gender") or "Unknown"].append(s)

        result = []
        for gender, ss in by_gender.items():
            totals    = [s["total_score"] for s in ss if s.get("total_score") is not None]
            pass_count = sum(1 for s in ss if s.get("pass_fail") == "PASS")
            result.append({
                "gender":       gender,
                "count":        len(ss),
                "avg_score":    round(sum(totals) / len(totals), 2) if totals else 0,
                "pass_count":   pass_count,
                "fail_count":   len(ss) - pass_count,
                "pass_rate_pct": round(pass_count / len(ss) * 100, 1),
            })
        return sorted(result, key=lambda x: x["avg_score"], reverse=True)

    # ── Attendance vs performance ─────────────────────────────────────────────
    async def attendance_impact(self, scores: list[dict]) -> list[dict]:
        buckets = defaultdict(list)
        for s in scores:
            att = s.get("attendance_rate") or 0
            if   att >= 0.9:  key = "90-100%"
            elif att >= 0.75: key = "75-89%"
            elif att >= 0.5:  key = "50-74%"
            else:             key = "<50%"
            buckets[key].append(s)

        result = []
        for bucket, ss in buckets.items():
            totals     = [s["total_score"] for s in ss if s.get("total_score") is not None]
            pass_count = sum(1 for s in ss if s.get("pass_fail") == "PASS")
            result.append({
                "attendance_bucket": bucket,
                "student_count":     len(ss),
                "avg_total_score":   round(sum(totals)/len(totals), 2) if totals else 0,
                "pass_rate_pct":     round(pass_count / len(ss) * 100, 1),
            })
        return sorted(result, key=lambda x: x["attendance_bucket"])

    # ── At-risk students ──────────────────────────────────────────────────────
    async def at_risk(self, scores: list[dict]) -> list[dict]:
        result = []
        for s in scores:
            t   = s.get("total_score") or 0
            att = s.get("attendance_rate") or 0
            if t < 50 or att < 0.5:
                result.append({
                    "student_id":    s["student_id"],
                    "name":          s.get("name"),
                    "total_score":   t,
                    "pass_fail":     s.get("pass_fail"),
                    "grade":         s.get("grade"),
                    "attendance_rate": att,
                    "risk_level":    "HIGH" if t < 40 else "MEDIUM",
                    "reason":        "Low score" if t < 50 else "Low attendance",
                })
        return sorted(result, key=lambda x: x["total_score"])

    # ── Top & bottom students ─────────────────────────────────────────────────
    async def top_students(self, scores: list[dict], n: int = 10) -> list[dict]:
        sorted_s = sorted(scores, key=lambda x: x.get("total_score") or 0, reverse=True)
        return [
            {
                "rank":        i + 1,
                "student_id":  s["student_id"],
                "name":        s.get("name"),
                "total_score": s.get("total_score"),
                "grade":       s.get("grade"),
                "pass_fail":   s.get("pass_fail"),
            }
            for i, s in enumerate(sorted_s[:n])
        ]

    # ── Single student report ─────────────────────────────────────────────────
    async def student_report(self, student_id: int) -> dict:
        score = await self._fetch_student_score(student_id)
        return {
            "student_id":   score["student_id"],
            "name":         score.get("name"),
            "score_breakdown": {
                "quiz1":    score.get("quiz1_marks"),
                "quiz2":    score.get("quiz2_marks"),
                "quiz3":    score.get("quiz3_marks"),
                "midterm":  score.get("midterm_marks"),
                "final":    score.get("final_marks"),
                "quiz_weighted":    score.get("quiz_score"),
                "midterm_weighted": score.get("midterm_score"),
                "final_weighted":   score.get("final_score"),
                "total_score":      score.get("total_score"),
            },
            "result": {
                "grade":            score.get("grade"),
                "grade_point":      score.get("grade_point"),
                "pass_fail":        score.get("pass_fail"),
                "is_pass":          score.get("is_pass"),
                "performance_tier": score.get("performance_tier"),
            },
            "attendance": {
                "lectures_attended": score.get("lectures_attended"),
                "labs_attended":     score.get("labs_attended"),
                "attendance_rate":   score.get("attendance_rate"),
            },
            "previous_gpa": score.get("previous_gpa"),
            "message": f"{'✅ PASSED' if score.get('is_pass') else '❌ FAILED'} — {score.get('total_score')}/100",
        }


analytics_service = AnalyticsService()
