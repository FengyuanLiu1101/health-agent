"""Single source of truth for health scoring.

Both the agent's `assess_health_status` tool and the dashboard summary read
from here so the textual status (e.g., "excellent") cannot drift from the
score the user sees.

All numeric thresholds are imported from ``config`` so they can be changed
in one place and immediately affect scoring, anomaly detection, and the UI.
"""
from __future__ import annotations

from typing import NamedTuple

from config import (
    SLEEP_CRITICAL_LOW, SLEEP_LOW, SLEEP_HIGH,
    HR_HIGH_CRITICAL, HR_HIGH_WARN, HR_LOW_WARN,
    STEPS_CRITICAL_LOW, STEPS_LOW,
    CALORIES_CRITICAL_LOW, CALORIES_HIGH,
    SCORE_EXCELLENT, SCORE_GOOD, SCORE_CAUTION,
)


class ScoreResult(NamedTuple):
    score: int       # 0-100
    status: str      # "excellent" | "good" | "caution" | "poor"
    label: str       # display capitalization
    flags: list[str]


def metric_deductions(hr: int, steps: int, sleep: float, cals: int) -> tuple[int, list[str]]:
    """Return (deduction, flags). Subtract deduction from a base of 100."""
    deduction = 0
    flags: list[str] = []

    if sleep < SLEEP_CRITICAL_LOW:
        deduction += 30
        flags.append(f"Low sleep: {sleep}h (target 7-9h)")
    elif sleep < SLEEP_LOW:
        deduction += 15
        flags.append(f"Slightly low sleep: {sleep}h (target 7-9h)")
    elif sleep > SLEEP_HIGH:
        deduction += 10
        flags.append(f"Unusually long sleep: {sleep}h")

    if hr > HR_HIGH_CRITICAL:
        deduction += 20
        flags.append(f"Elevated resting HR: {hr} bpm (target 60-100, well-rested <80)")
    elif hr > HR_HIGH_WARN:
        deduction += 10
        flags.append(f"Slightly elevated HR: {hr} bpm")
    elif hr < HR_LOW_WARN:
        deduction += 5
        flags.append(f"Unusually low HR: {hr} bpm")

    if steps < STEPS_CRITICAL_LOW:
        deduction += 20
        flags.append(f"Low activity: {steps} steps (target 7,000-10,000)")
    elif steps < STEPS_LOW:
        deduction += 10
        flags.append(f"Below-target activity: {steps} steps")

    if cals < CALORIES_CRITICAL_LOW:
        deduction += 10
        flags.append(f"Low caloric burn: {cals} kcal")
    elif cals > CALORIES_HIGH:
        deduction += 5
        flags.append(f"Very high caloric burn: {cals} kcal")

    return deduction, flags


def score_status(score: int) -> tuple[str, str]:
    """Return (status_token, display_label). Tokens are stable; labels are pretty."""
    if score >= SCORE_EXCELLENT:
        return "excellent", "Excellent"
    if score >= SCORE_GOOD:
        return "good", "Good"
    if score >= SCORE_CAUTION:
        return "caution", "Fair"
    return "poor", "Poor"


def score_log(log: dict) -> ScoreResult:
    """Score a single health-log row."""
    deduction, flags = metric_deductions(
        log["heart_rate_avg"], log["steps"], log["sleep_hours"], log["calories_burned"]
    )
    score = max(0, 100 - deduction)
    status, label = score_status(score)
    return ScoreResult(score=score, status=status, label=label, flags=flags)
