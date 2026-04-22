"""Short- and long-term memory backed by SQLite.

User preferences live in `user_profile`; feedback lives in `advice_feedback`.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import List

from data import db


def save_feedback(advice_summary: str, rating: int, tag: str) -> None:
    """Persist a thumbs up (1) or thumbs down (-1) for a piece of advice."""
    db.insert_feedback(
        date=date.today().isoformat(),
        advice_summary=advice_summary,
        rating=int(rating),
        tag=tag or "general",
    )


def get_negative_feedback_tags(min_count: int = 1) -> List[str]:
    """Return a deduplicated list of tags the user has rated down."""
    rows = db.fetch_feedback_tags(rating_filter=-1)
    counter = Counter(r["tag"] for r in rows if r.get("tag"))
    return [tag for tag, c in counter.items() if c >= min_count]


def get_positive_feedback_tags() -> List[str]:
    rows = db.fetch_feedback_tags(rating_filter=1)
    counter = Counter(r["tag"] for r in rows if r.get("tag"))
    return [tag for tag, _ in counter.most_common()]


def get_feedback_history(limit: int = 20) -> list[dict]:
    rows = db.fetch_feedback_tags(rating_filter=None)
    return rows[:limit]


def get_profile() -> dict:
    """Return the user profile dict merged with feedback-derived fields."""
    profile = db.get_profile_dict()
    profile.setdefault("name", "there")
    profile.setdefault("age", "unknown")
    profile.setdefault("goal", "stay healthy")
    profile["disliked_advice_tags"] = get_negative_feedback_tags()
    profile["liked_advice_tags"] = get_positive_feedback_tags()
    profile["feedback_history"] = get_feedback_history(limit=10)
    return profile


def update_profile(key: str, value: str) -> None:
    db.upsert_profile(key, value)
