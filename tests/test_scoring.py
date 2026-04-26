"""Boundary tests for the scoring module.

These pin the thresholds so the dashboard label and the agent's status
token cannot diverge again.
"""
from agent.scoring import metric_deductions, score_log, score_status


def test_perfect_day_no_deduction():
    deduction, flags = metric_deductions(hr=65, steps=10_000, sleep=8.0, cals=2200)
    assert deduction == 0
    assert flags == []


def test_low_sleep_threshold():
    # 5.5 is the cutoff: < 5.5 → 30 point deduction.
    d_below, _ = metric_deductions(hr=65, steps=10_000, sleep=5.4, cals=2200)
    d_at, _ = metric_deductions(hr=65, steps=10_000, sleep=5.5, cals=2200)
    assert d_below == 30
    assert d_at == 15  # 5.5 falls into the "slightly low" band (5.5 <= sleep < 7.0)


def test_elevated_hr_threshold():
    # > 95 → 20pt; > 85 → 10pt; < 50 → 5pt
    assert metric_deductions(96, 10_000, 8.0, 2200)[0] == 20
    assert metric_deductions(86, 10_000, 8.0, 2200)[0] == 10
    assert metric_deductions(95, 10_000, 8.0, 2200)[0] == 10  # boundary: not >95
    assert metric_deductions(85, 10_000, 8.0, 2200)[0] == 0
    assert metric_deductions(49, 10_000, 8.0, 2200)[0] == 5


def test_low_steps():
    assert metric_deductions(65, 3_999, 8.0, 2200)[0] == 20
    assert metric_deductions(65, 5_999, 8.0, 2200)[0] == 10
    assert metric_deductions(65, 6_000, 8.0, 2200)[0] == 0


def test_score_status_buckets():
    # Tokens are stable across the dashboard and the agent's tool output.
    assert score_status(85) == ("excellent", "Excellent")
    assert score_status(84) == ("good", "Good")
    assert score_status(70) == ("good", "Good")
    assert score_status(69) == ("caution", "Fair")
    assert score_status(50) == ("caution", "Fair")
    assert score_status(49) == ("poor", "Poor")
    assert score_status(0) == ("poor", "Poor")


def test_score_log_combined():
    # Bad-day fixture mirrors data/simulator._bad_day:
    #   HR 100 (>95 → 20), steps 3000 (<4000 → 20), sleep 4.5 (<5.5 → 30),
    #   cals 1600 (in range → 0). Expect score = 100 - 70 = 30 -> "poor".
    log = {
        "heart_rate_avg": 100,
        "steps": 3000,
        "sleep_hours": 4.5,
        "calories_burned": 1600,
    }
    result = score_log(log)
    assert result.score == 30
    assert result.status == "poor"
    assert result.label == "Poor"
    assert any("Low sleep" in f for f in result.flags)
    assert any("Elevated resting HR" in f for f in result.flags)
