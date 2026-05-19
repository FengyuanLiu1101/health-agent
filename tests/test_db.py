"""Unit tests for data/db.py using a temporary SQLite database.

Uses db.set_db_path() for isolation so every test gets a fresh file and
the global DB path is restored afterward.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data import db as db_module


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    """Redirect the active DB to a fresh temp file for every test."""
    prev_path = db_module.get_db_path()
    new_path = str(tmp_path / "test_health.db")
    db_module.set_db_path(new_path)
    db_module.init_db()
    yield new_path
    db_module.set_db_path(prev_path)


# ---------------------------------------------------------------------------
# init_db / is_health_logs_empty
# ---------------------------------------------------------------------------
def test_init_db_creates_empty_tables():
    assert db_module.is_health_logs_empty()


# ---------------------------------------------------------------------------
# insert / get health log
# ---------------------------------------------------------------------------
SAMPLE_ROW = {
    "date": date.today().isoformat(),
    "heart_rate_avg": 72,
    "steps": 8500,
    "sleep_hours": 7.5,
    "calories_burned": 2100,
    "anomaly_flag": 0,
}


def test_insert_and_get_log():
    db_module.insert_health_log(SAMPLE_ROW)
    result = db_module.get_log_by_date(SAMPLE_ROW["date"])
    assert result is not None
    assert result["heart_rate_avg"] == 72
    assert result["steps"] == 8500


def test_get_log_missing_date_returns_none():
    assert db_module.get_log_by_date("1900-01-01") is None


def test_is_health_logs_empty_after_insert():
    assert db_module.is_health_logs_empty()
    db_module.insert_health_log(SAMPLE_ROW)
    assert not db_module.is_health_logs_empty()


def test_insert_replace_overwrites():
    db_module.insert_health_log(SAMPLE_ROW)
    updated = {**SAMPLE_ROW, "steps": 12000}
    db_module.insert_health_log(updated)
    assert db_module.get_log_by_date(SAMPLE_ROW["date"])["steps"] == 12000


# ---------------------------------------------------------------------------
# bulk_insert / clear
# ---------------------------------------------------------------------------
def _make_rows(n: int) -> list[dict]:
    today = date.today()
    return [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "heart_rate_avg": 70 + i,
            "steps": 7000 + i * 100,
            "sleep_hours": 7.0,
            "calories_burned": 2000,
            "anomaly_flag": 0,
        }
        for i in range(n)
    ]


def test_bulk_insert():
    db_module.bulk_insert_health_logs(_make_rows(10))
    assert not db_module.is_health_logs_empty()


def test_clear_health_logs():
    db_module.bulk_insert_health_logs(_make_rows(5))
    db_module.clear_health_logs()
    assert db_module.is_health_logs_empty()


# ---------------------------------------------------------------------------
# get_last_n_logs
# ---------------------------------------------------------------------------
def test_get_last_n_logs_chronological_order():
    db_module.bulk_insert_health_logs(_make_rows(7))
    result = db_module.get_last_n_logs(7)
    assert len(result) == 7
    dates = [r["date"] for r in result]
    assert dates == sorted(dates)  # oldest first


def test_get_last_n_logs_respects_limit():
    db_module.bulk_insert_health_logs(_make_rows(15))
    assert len(db_module.get_last_n_logs(5)) == 5


# ---------------------------------------------------------------------------
# user_profile helpers
# ---------------------------------------------------------------------------
def test_upsert_and_get_profile():
    db_module.upsert_profile("name", "Alice")
    assert db_module.get_profile_dict()["name"] == "Alice"


def test_upsert_profile_overwrites():
    db_module.upsert_profile("age", "25")
    db_module.upsert_profile("age", "30")
    assert db_module.get_profile_dict()["age"] == "30"


def test_seed_default_profile_if_empty():
    db_module.seed_default_profile_if_empty()
    profile = db_module.get_profile_dict()
    assert "name" in profile
    assert "goal" in profile


def test_seed_does_not_overwrite_existing():
    db_module.upsert_profile("name", "Bob")
    db_module.seed_default_profile_if_empty()
    assert db_module.get_profile_dict()["name"] == "Bob"


# ---------------------------------------------------------------------------
# advice_feedback helpers
# ---------------------------------------------------------------------------
def test_insert_and_fetch_feedback():
    db_module.insert_feedback(date.today().isoformat(), "Sleep more", 1, "sleep")
    tags = db_module.fetch_feedback_tags(rating_filter=1)
    assert len(tags) == 1
    assert tags[0]["tag"] == "sleep"


def test_fetch_feedback_rating_filter():
    db_module.insert_feedback(date.today().isoformat(), "Exercise daily", 1, "exercise")
    db_module.insert_feedback(date.today().isoformat(), "Sleep advice", -1, "sleep")
    assert len(db_module.fetch_feedback_tags(rating_filter=1)) == 1
    assert len(db_module.fetch_feedback_tags(rating_filter=-1)) == 1


def test_clear_feedback():
    db_module.insert_feedback(date.today().isoformat(), "Drink water", 1, "diet")
    db_module.clear_feedback()
    assert db_module.fetch_feedback_tags() == []
