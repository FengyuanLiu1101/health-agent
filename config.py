"""Centralised health metric thresholds and constants for HealthAgent.

All hard-coded numeric limits live here so that every module (data layer,
agent scoring, agent tools, and UI) reads from one source of truth.
Changing a threshold here propagates automatically across scoring, anomaly
detection, simulation, and UI tier colours.
"""

# ---------------------------------------------------------------------------
# Healthy ranges  (lo, hi) — used for simulation AND agent output
# ---------------------------------------------------------------------------
NORMAL_HR: tuple[int, int] = (60, 100)
NORMAL_STEPS: tuple[int, int] = (7_000, 12_000)
NORMAL_SLEEP: tuple[float, float] = (7.0, 9.0)
NORMAL_CALORIES: tuple[int, int] = (1_800, 2_500)

# ---------------------------------------------------------------------------
# Scoring deduction thresholds  (agent/scoring.py  metric_deductions)
# ---------------------------------------------------------------------------
SLEEP_CRITICAL_LOW: float = 5.5    # deduct 30 pts
SLEEP_LOW: float = 7.0             # deduct 15 pts
SLEEP_HIGH: float = 10.0           # deduct 10 pts

HR_HIGH_CRITICAL: int = 95         # deduct 20 pts
HR_HIGH_WARN: int = 85             # deduct 10 pts
HR_LOW_WARN: int = 50              # deduct  5 pts

STEPS_CRITICAL_LOW: int = 4_000    # deduct 20 pts
STEPS_LOW: int = 6_000             # deduct 10 pts

CALORIES_CRITICAL_LOW: int = 1_500  # deduct 10 pts
CALORIES_HIGH: int = 3_000          # deduct  5 pts

# ---------------------------------------------------------------------------
# Score status thresholds  (agent/scoring.py  score_status)
# ---------------------------------------------------------------------------
SCORE_EXCELLENT: int = 85
SCORE_GOOD: int = 70
SCORE_CAUTION: int = 50

# ---------------------------------------------------------------------------
# Anomaly detection thresholds  (data/simulator.py  _is_anomalous)
# Also used in agent/tools.py  _anomaly_reasons
# ---------------------------------------------------------------------------
ANOMALY_STEPS_LOW: int = 5_000
ANOMALY_SLEEP_LOW: float = 6.0
ANOMALY_SLEEP_HIGH: float = 10.0
ANOMALY_CALORIES_LOW: int = 1_500
ANOMALY_CALORIES_HIGH: int = 3_000

# ---------------------------------------------------------------------------
# UI tier ranges  (app.py  today_tiers)
# ---------------------------------------------------------------------------
HR_GOOD: tuple[int, int] = (60, 85)
HR_WARN_BELOW: int = 50
HR_WARN_ABOVE: int = 95

STEPS_GOOD: tuple[int, int] = (7_000, 12_000)
STEPS_WARN_BELOW: int = 4_000

SLEEP_GOOD: tuple[float, float] = (7.0, 9.0)
SLEEP_WARN_BELOW: float = 5.5
SLEEP_WARN_ABOVE: float = 10.5

CALORIES_GOOD: tuple[int, int] = (1_800, 2_500)
CALORIES_WARN_BELOW: int = 1_500
CALORIES_WARN_ABOVE: int = 3_000
