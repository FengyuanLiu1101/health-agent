"""Short- and long-term memory backed by SQLite.

User preferences live in `user_profile`; feedback lives in `advice_feedback`.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import List

from data import db


def save_feedback(advice_summary: str, rating: int, tag: str | List[str]) -> None:
    """Persist a thumbs up (1) or thumbs down (-1) for a piece of advice.

    `tag` may be a single string or a list of tags (the agent's response
    typically covers multiple topics; storing one row per tag avoids biasing
    a multi-topic answer toward whichever tag matched first).
    """
    tags = tag if isinstance(tag, list) else [tag or "general"]
    if not tags:
        tags = ["general"]
    today = date.today().isoformat()
    for t in tags:
        db.insert_feedback(
            date=today,
            advice_summary=advice_summary,
            rating=int(rating),
            tag=t or "general",
        )


def get_negative_feedback_tags(min_count: int = 2) -> List[str]:
    """Return tags the user has rated down at least `min_count` times.

    Default of 2 prevents a single accidental thumbs-down from disabling a
    whole topic for the agent (which the system prompt instructs it to avoid).
    """
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
