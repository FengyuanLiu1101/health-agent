"""Unit tests for data/simulator.py — no DB writes required for pure functions."""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.simulator import generate_30_days, _is_anomalous
from config import NORMAL_HR, ANOMALY_STEPS_LOW, ANOMALY_SLEEP_LOW, ANOMALY_SLEEP_HIGH


class TestGenerateThirtyDays:
    def test_returns_30_rows(self):
        assert len(generate_30_days(seed=42)) == 30

    def test_last_row_is_today(self):
        assert generate_30_days(seed=42)[-1]["date"] == date.today().isoformat()

    def test_first_row_is_29_days_ago(self):
        expected = (date.today() - timedelta(days=29)).isoformat()
        assert generate_30_days(seed=42)[0]["date"] == expected

    def test_dates_are_consecutive(self):
        rows = generate_30_days(seed=42)
        for i in range(1, len(rows)):
            prev = date.fromisoformat(rows[i - 1]["date"])
            curr = date.fromisoformat(rows[i]["date"])
            assert (curr - prev).days == 1

    def test_today_is_bad_when_flag_true(self):
        today = generate_30_days(seed=42, today_is_bad=True)[-1]
        assert today["heart_rate_avg"] > 95
        assert today["sleep_hours"] < 5.5

    def test_today_can_be_non_bad(self):
        rows = generate_30_days(seed=42, today_is_bad=False)
        assert "heart_rate_avg" in rows[-1]

    def test_seeded_results_are_reproducible(self):
        assert generate_30_days(seed=7) == generate_30_days(seed=7)

    def test_different_seeds_differ(self):
        assert generate_30_days(seed=1) != generate_30_days(seed=2)

    def test_all_rows_have_required_keys(self):
        required = {"date", "heart_rate_avg", "steps", "sleep_hours",
                    "calories_burned", "anomaly_flag"}
        for row in generate_30_days(seed=42):
            assert required.issubset(row.keys())

    def test_anomaly_flag_is_0_or_1(self):
        for row in generate_30_days(seed=42):
            assert row["anomaly_flag"] in (0, 1)

    def test_bad_day_is_flagged_anomalous(self):
        assert generate_30_days(seed=42, today_is_bad=True)[-1]["anomaly_flag"] == 1


class TestIsAnomalous:
    def test_normal_values_not_anomalous(self):
        assert _is_anomalous(hr=70, steps=8000, sleep=7.5, cals=2000) == 0

    def test_low_steps_anomalous(self):
        assert _is_anomalous(hr=70, steps=ANOMALY_STEPS_LOW - 1, sleep=7.5, cals=2000) == 1

    def test_high_hr_anomalous(self):
        assert _is_anomalous(hr=NORMAL_HR[1] + 5, steps=8000, sleep=7.5, cals=2000) == 1

    def test_low_hr_anomalous(self):
        assert _is_anomalous(hr=NORMAL_HR[0] - 1, steps=8000, sleep=7.5, cals=2000) == 1

    def test_low_sleep_anomalous(self):
        assert _is_anomalous(hr=70, steps=8000, sleep=ANOMALY_SLEEP_LOW - 0.1, cals=2000) == 1

    def test_high_sleep_anomalous(self):
        assert _is_anomalous(hr=70, steps=8000, sleep=ANOMALY_SLEEP_HIGH + 0.1, cals=2000) == 1

    def test_low_calories_anomalous(self):
        assert _is_anomalous(hr=70, steps=8000, sleep=7.5, cals=1000) == 1

    def test_high_calories_anomalous(self):
        assert _is_anomalous(hr=70, steps=8000, sleep=7.5, cals=4000) == 1
