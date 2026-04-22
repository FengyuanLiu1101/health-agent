"""Simulate 30 days of realistic wearable data for the HealthAgent demo."""
from __future__ import annotations

import random
from datetime import date, timedelta

from . import db


# Healthy baselines used both for generation and later comparison.
NORMAL_HR = (60, 100)
NORMAL_STEPS = (7000, 12000)
NORMAL_SLEEP = (7.0, 9.0)
NORMAL_CALORIES = (1800, 2500)


def _is_anomalous(hr: int, steps: int, sleep: float, cals: int) -> int:
    bad_hr = hr < NORMAL_HR[0] or hr > NORMAL_HR[1]
    bad_steps = steps < 5000
    bad_sleep = sleep < 6.0 or sleep > 10.0
    bad_cals = cals < 1500 or cals > 3000
    return 1 if (bad_hr or bad_steps or bad_sleep or bad_cals) else 0


def _normal_day(rng: random.Random) -> dict:
    return {
        "heart_rate_avg": rng.randint(62, 82),
        "steps": rng.randint(7500, 11500),
        "sleep_hours": round(rng.uniform(7.0, 8.8), 1),
        "calories_burned": rng.randint(1900, 2400),
    }


def _bad_day(rng: random.Random) -> dict:
    return {
        "heart_rate_avg": rng.randint(96, 108),
        "steps": rng.randint(1800, 3900),
        "sleep_hours": round(rng.uniform(4.2, 5.4), 1),
        "calories_burned": rng.randint(1450, 1700),
    }


def _excellent_day(rng: random.Random) -> dict:
    return {
        "heart_rate_avg": rng.randint(60, 66),
        "steps": rng.randint(11000, 12500),
        "sleep_hours": round(rng.uniform(7.8, 8.8), 1),
        "calories_burned": rng.randint(2200, 2500),
    }


def generate_30_days(seed: int | None = 42, today_is_bad: bool = True) -> list[dict]:
    """Generate 30 days of data ending today.

    Rules:
      - Most days are normal, with slight random variation.
      - 3 additional randomly-placed "bad days" (sleep<5.5, HR>95, steps<4000).
      - 1 randomly-placed "excellent day".
      - Today (last entry) is itself a bad day when `today_is_bad=True`, great
        for the demo opening alert.
    """
    rng = random.Random(seed)
    today = date.today()
    dates = [(today - timedelta(days=i)) for i in range(29, -1, -1)]

    day_types = ["normal"] * 30

    candidate_idx = list(range(0, 29))  # exclude today (index 29); set explicitly
    rng.shuffle(candidate_idx)
    bad_idx = candidate_idx[:3]
    excellent_idx = candidate_idx[3:4]
    for i in bad_idx:
        day_types[i] = "bad"
    for i in excellent_idx:
        day_types[i] = "excellent"

    if today_is_bad:
        day_types[29] = "bad"

    rows: list[dict] = []
    for d, kind in zip(dates, day_types):
        if kind == "bad":
            m = _bad_day(rng)
        elif kind == "excellent":
            m = _excellent_day(rng)
        else:
            m = _normal_day(rng)
        anomaly = _is_anomalous(
            m["heart_rate_avg"], m["steps"], m["sleep_hours"], m["calories_burned"]
        )
        rows.append(
            {
                "date": d.isoformat(),
                "heart_rate_avg": m["heart_rate_avg"],
                "steps": m["steps"],
                "sleep_hours": m["sleep_hours"],
                "calories_burned": m["calories_burned"],
                "anomaly_flag": anomaly,
            }
        )
    return rows


def simulate_and_store(seed: int | None = 42, today_is_bad: bool = True) -> list[dict]:
    """Generate data and (re)populate the `health_logs` table."""
    db.init_db()
    db.clear_health_logs()
    rows = generate_30_days(seed=seed, today_is_bad=today_is_bad)
    db.bulk_insert_health_logs(rows)
    return rows


def ensure_data_present() -> None:
    """Initialize DB and simulate data if none exists yet."""
    db.init_db()
    db.seed_default_profile_if_empty()
    if db.is_health_logs_empty():
        simulate_and_store()


if __name__ == "__main__":
    rows = simulate_and_store()
    print(f"Inserted {len(rows)} rows.")
    for r in rows[-5:]:
        print(r)
