"""Tests for agent tools (no OpenAI calls)."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from agent.tools import get_anomaly_report
from data import db
from data import source


@pytest.fixture()
def isolated_db():
    prev = db.get_db_path()
    path = os.path.join(tempfile.gettempdir(), f"ha_test_tools_{os.getpid()}.db")
    try:
        os.remove(path)
    except OSError:
        pass
    db.set_db_path(path)
    db.init_db()
    db.bulk_insert_health_logs(
        [
            {
                "date": "2026-01-01",
                "heart_rate_avg": 70,
                "steps": 9000,
                "sleep_hours": 7.5,
                "calories_burned": 2000,
                "anomaly_flag": 0,
            },
            {
                "date": "2026-01-02",
                "heart_rate_avg": 110,
                "steps": 2000,
                "sleep_hours": 4.0,
                "calories_burned": 1400,
                "anomaly_flag": 1,
            },
        ]
    )
    yield path
    db.set_db_path(prev)
    try:
        os.remove(path)
    except OSError:
        pass


def test_get_anomaly_report_lists_flagged_days(isolated_db):
    raw = get_anomaly_report.invoke({"days": 30})
    data = json.loads(raw)
    assert data["anomaly_count"] == 1
    assert data["anomalies"][0]["date"] == "2026-01-02"
    assert "heart_rate_out_of_range" in data["anomalies"][0]["reasons"]


def test_health_source_delegates_to_sqlite(isolated_db):
    assert source.get_log_by_date("2026-01-01")["steps"] == 9000
