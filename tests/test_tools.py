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


# ---------------------------------------------------------------------------
# compute_trend / compute_trend_hr  (pure functions — no DB needed)
# ---------------------------------------------------------------------------
from agent.tools import compute_trend, compute_trend_hr  # noqa: E402


class TestComputeTrend:
    def test_improving(self):
        assert compute_trend([100, 100, 100, 110, 120, 130, 140]) == "improving"

    def test_declining(self):
        assert compute_trend([140, 130, 120, 110, 100, 100, 100]) == "declining"

    def test_stable(self):
        assert compute_trend([100, 101, 99, 100, 101, 100, 100]) == "stable"

    def test_too_few_values(self):
        assert compute_trend([]) == "stable"
        assert compute_trend([100]) == "stable"
        assert compute_trend([100, 110]) == "stable"

    def test_all_zeros(self):
        assert compute_trend([0, 0, 0, 0, 0]) == "stable"


class TestComputeTrendHr:
    def test_decreasing_hr_is_improving(self):
        assert compute_trend_hr([90, 88, 85, 82, 80, 78, 75]) == "improving"

    def test_increasing_hr_is_declining(self):
        assert compute_trend_hr([60, 65, 70, 75, 80, 85, 90]) == "declining"

    def test_stable_hr(self):
        assert compute_trend_hr([70, 71, 70, 70, 71, 70, 70]) == "stable"
