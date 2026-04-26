"""LangChain tools exposed to the HealthAgent."""
from __future__ import annotations

import json
from datetime import date
from typing import List

from langchain_core.tools import tool

from data import db, knowledge_base
from data.simulator import (
    NORMAL_CALORIES,
    NORMAL_HR,
    NORMAL_SLEEP,
    NORMAL_STEPS,
)
from . import memory
from .scoring import score_log


# ---------- Tool 1 ----------
@tool
def assess_health_status(target_date: str = "") -> str:
    """Assess today's (or a given day's) wearable metrics and return a JSON string.

    Args:
        target_date: ISO date string like '2024-01-15'. Defaults to today.

    Returns:
        A JSON string with keys: score (0-100), flags (list[str]),
        date, metrics (raw readings), status ("excellent" | "good" | "caution" | "poor").
    """
    if not target_date:
        target_date = date.today().isoformat()

    row = db.get_log_by_date(target_date)
    if row is None:
        return json.dumps(
            {"error": f"No health log found for {target_date}.", "date": target_date}
        )

    result = score_log(row)

    return json.dumps(
        {
            "date": target_date,
            "score": result.score,
            "status": result.status,
            "flags": result.flags,
            "metrics": {
                "heart_rate_avg_bpm": row["heart_rate_avg"],
                "steps": row["steps"],
                "sleep_hours": row["sleep_hours"],
                "calories_burned": row["calories_burned"],
            },
            "healthy_ranges": {
                "heart_rate_avg_bpm": list(NORMAL_HR),
                "steps": list(NORMAL_STEPS),
                "sleep_hours": list(NORMAL_SLEEP),
                "calories_burned": list(NORMAL_CALORIES),
            },
        }
    )


# ---------- Tool 2 ----------
def _trend(values: List[float]) -> str:
    """Classify a trend from a list of values (oldest -> newest)."""
    if len(values) < 3:
        return "stable"
    first_half = sum(values[: len(values) // 2]) / max(1, len(values) // 2)
    second_half = sum(values[len(values) // 2 :]) / max(1, len(values) - len(values) // 2)
    if first_half == 0:
        return "stable"
    delta = (second_half - first_half) / abs(first_half)
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "declining"
    return "stable"


def _trend_for_hr(values: List[float]) -> str:
    """HR trends are inverted: lower is improving (within healthy range)."""
    raw = _trend(values)
    if raw == "improving":
        return "declining"
    if raw == "declining":
        return "improving"
    return "stable"


@tool
def get_health_trend(days: int = 7) -> str:
    """Summarize metric trends over the last N days (default 7).

    Args:
        days: How many recent days to look at (1-30).

    Returns:
        A JSON string with average, min, max and trend direction
        ("improving"/"declining"/"stable") for each metric, plus the count of
        anomalous days in the window.
    """
    days = max(1, min(int(days), 30))
    rows = db.get_last_n_logs(days)
    if not rows:
        return json.dumps({"error": "No health data available."})

    hr = [r["heart_rate_avg"] for r in rows]
    steps = [r["steps"] for r in rows]
    sleep = [r["sleep_hours"] for r in rows]
    cals = [r["calories_burned"] for r in rows]

    def stats(vals: list[float]) -> dict:
        return {
            "avg": round(sum(vals) / len(vals), 1),
            "min": min(vals),
            "max": max(vals),
        }

    return json.dumps(
        {
            "window_days": days,
            "start_date": rows[0]["date"],
            "end_date": rows[-1]["date"],
            "heart_rate": {**stats(hr), "trend": _trend_for_hr(hr)},
            "steps": {**stats(steps), "trend": _trend(steps)},
            "sleep_hours": {**stats(sleep), "trend": _trend(sleep)},
            "calories_burned": {**stats(cals), "trend": _trend(cals)},
            "anomalous_days": sum(1 for r in rows if r.get("anomaly_flag")),
        }
    )


# ---------- Tool 3 ----------
@tool
def query_knowledge_base(question: str) -> str:
    """Search the curated health knowledge base for evidence relevant to a question.

    Args:
        question: A natural-language question such as
            'how much sleep do adults need?' or 'is a 98 bpm resting heart rate high?'.

    Returns:
        A JSON string with a list of the top 3 relevant facts.
    """
    try:
        hits = knowledge_base.search(question, k=3)
    except Exception as e:  # gracefully degrade if embeddings/API unavailable
        return json.dumps({"error": f"Knowledge base unavailable: {e}", "facts": []})
    return json.dumps({"question": question, "facts": hits})


# ---------- Tool 4 ----------
@tool
def get_user_profile(_: str = "") -> str:
    """Return the user's profile including name, age, goal, and feedback-derived
    `disliked_advice_tags` that the agent MUST avoid emphasizing.

    Returns:
        A JSON string of the user profile dict.
    """
    profile = memory.get_profile()
    return json.dumps(profile, default=str)


ALL_TOOLS = [assess_health_status, get_health_trend, query_knowledge_base, get_user_profile]
