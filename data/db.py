"""SQLite initialization and CRUD helpers for HealthAgent.

The DB path is configurable via `set_db_path()` so a multi-user host (e.g.,
Streamlit Community Cloud) can give each session its own SQLite file.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable

# Default to the project-root file so local single-user runs are unchanged.
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "health_agent.db"
)
_db_path: str = os.environ.get("HEALTH_AGENT_DB_PATH", _DEFAULT_DB_PATH)


def set_db_path(path: str) -> None:
    """Override the DB path for this process. Call before any get_conn()."""
    global _db_path
    _db_path = path


def get_db_path() -> str:
    return _db_path


# Backwards-compat: a few callers may still import DB_PATH directly.
DB_PATH = _db_path


@contextmanager
def get_conn():
    """Context manager yielding a sqlite3 connection with row_factory set."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not yet exist."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS health_logs (
                date TEXT PRIMARY KEY,
                heart_rate_avg INTEGER,
                steps INTEGER,
                sleep_hours REAL,
                calories_burned INTEGER,
                anomaly_flag INTEGER DEFAULT 0
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS advice_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                advice_summary TEXT,
                rating INTEGER,
                tag TEXT
            )
            """
        )


def is_health_logs_empty() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) as c FROM health_logs").fetchone()
        return row["c"] == 0


def insert_health_log(row: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO health_logs
                (date, heart_rate_avg, steps, sleep_hours, calories_burned, anomaly_flag)
            VALUES (:date, :heart_rate_avg, :steps, :sleep_hours, :calories_burned, :anomaly_flag)
            """,
            row,
        )


def bulk_insert_health_logs(rows: Iterable[dict]) -> None:
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO health_logs
                (date, heart_rate_avg, steps, sleep_hours, calories_burned, anomaly_flag)
            VALUES (:date, :heart_rate_avg, :steps, :sleep_hours, :calories_burned, :anomaly_flag)
            """,
            list(rows),
        )


def clear_health_logs() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM health_logs")


def get_log_by_date(date: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM health_logs WHERE date = ?", (date,)).fetchone()
        return dict(row) if row else None


def get_last_n_logs(n: int = 7) -> list[dict]:
    """Return the most recent n logs ordered chronologically ascending."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM health_logs ORDER BY date DESC LIMIT ?", (n,)
        ).fetchall()
        rows = [dict(r) for r in rows]
        rows.reverse()
        return rows


def get_all_logs() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM health_logs ORDER BY date ASC").fetchall()
        return [dict(r) for r in rows]


# ---------- user_profile helpers ----------
def upsert_profile(key: str, value: Any) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)",
            (key, str(value)),
        )


def get_profile_dict() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM user_profile").fetchall()
        return {r["key"]: r["value"] for r in rows}


def seed_default_profile_if_empty() -> None:
    """Seed a default demo user profile if nothing exists."""
    profile = get_profile_dict()
    if profile:
        return
    defaults = {
        "name": "Alex",
        "age": "28",
        "goal": "Improve sleep and maintain consistent exercise",
        "disliked_advice_tags": "",
    }
    for k, v in defaults.items():
        upsert_profile(k, v)


# ---------- advice_feedback helpers ----------
def insert_feedback(date: str, advice_summary: str, rating: int, tag: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO advice_feedback (date, advice_summary, rating, tag)
            VALUES (?, ?, ?, ?)
            """,
            (date, advice_summary, rating, tag),
        )


def fetch_feedback_tags(rating_filter: int | None = None) -> list[dict]:
    with get_conn() as conn:
        if rating_filter is None:
            rows = conn.execute(
                "SELECT date, advice_summary, rating, tag FROM advice_feedback ORDER BY id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT date, advice_summary, rating, tag FROM advice_feedback WHERE rating = ? ORDER BY id DESC",
                (rating_filter,),
            ).fetchall()
        return [dict(r) for r in rows]


def clear_feedback() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM advice_feedback")
