"""Streamlit UI for HealthAgent — light theme with real-time dashboard.

Run with:
    streamlit run app.py

Visual layer only; all agent, tool, memory, and simulator logic are unchanged.
"""
from __future__ import annotations

import html as _html
import os
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.core import HealthAgent  # noqa: E402
from agent import memory  # noqa: E402
from data import db, simulator  # noqa: E402
from data import knowledge_base  # noqa: E402


# =========================================================================
# Page config
# =========================================================================
st.set_page_config(
    page_title="HealthAgent",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Design tokens -------------------------------------------------------
BG = "#F8F9FA"
SURFACE = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT = "#0D2137"
MUTED = "#64748B"
MUTED_SOFT = "#94A3B8"
PRIMARY = "#0A7C6C"        # teal
PRIMARY_SOFT = "#12B8A3"   # lighter teal
GOOD = "#0A7C6C"
WARN = "#F59E0B"
ALERT = "#DC2626"


# =========================================================================
# Global CSS
# =========================================================================
st.markdown(
    f"""
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {{
            background-color: {BG} !important;
            color: {TEXT};
            font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
        }}
        * {{ color: {TEXT}; }}
        .block-container {{
            padding-top: 1.2rem !important;
            padding-bottom: 4rem !important;
            max-width: 1400px;
        }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
            height: 0 !important;
        }}
        footer, #MainMenu {{ visibility: hidden; }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {SURFACE} !important;
            border-right: 1px solid {BORDER};
        }}
        section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}

        /* Typography */
        h1, h2, h3, h4, h5, h6 {{ color: {TEXT}; letter-spacing: -0.01em; }}

        /* ---------- Top bar ---------- */
        .top-bar {{
            display: flex;
            align-items: baseline;
            gap: 20px;
            padding: 0 0 16px 0;
            border-bottom: 1px solid {BORDER};
            margin-bottom: 24px;
        }}
        .brand {{
            font-size: 20px;
            font-weight: 700;
            color: {PRIMARY};
            letter-spacing: -0.01em;
        }}
        .brand-sub {{
            font-size: 12px;
            color: {MUTED};
        }}
        .live-indicator {{
            margin-left: auto;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 10px;
            color: {PRIMARY};
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .pulse-dot {{
            width: 8px; height: 8px; border-radius: 50%;
            background: {PRIMARY_SOFT};
            box-shadow: 0 0 0 0 rgba(18,184,163,0.55);
            animation: ha-pulse 1.8s infinite;
            display: inline-block;
        }}
        .pulse-dot.alert {{ background: {ALERT}; box-shadow: 0 0 0 0 rgba(220,38,38,0.55); animation-name: ha-pulse-alert; }}
        @keyframes ha-pulse {{
            0%   {{ box-shadow: 0 0 0 0 rgba(18,184,163,0.55); }}
            70%  {{ box-shadow: 0 0 0 10px rgba(18,184,163,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(18,184,163,0); }}
        }}
        @keyframes ha-pulse-alert {{
            0%   {{ box-shadow: 0 0 0 0 rgba(220,38,38,0.55); }}
            70%  {{ box-shadow: 0 0 0 10px rgba(220,38,38,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(220,38,38,0); }}
        }}

        /* ---------- Section header ---------- */
        .section-head {{
            display: flex; align-items: baseline; justify-content: space-between;
            font-size: 11px;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: {MUTED};
            font-weight: 600;
            margin: 24px 0 12px 0;
        }}
        .section-head .tag {{
            font-size: 10px; color: {MUTED_SOFT}; letter-spacing: 0.16em;
        }}

        /* ---------- Metric cards ---------- */
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 18px;
        }}
        .metric-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 18px 20px 0 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 140px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            overflow: hidden;
            position: relative;
        }}
        .metric-label {{
            font-size: 10px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: {MUTED};
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 40px;
            font-weight: 600;
            line-height: 1;
            color: {TEXT};
            letter-spacing: -0.02em;
        }}
        .metric-unit {{
            font-size: 16px;
            color: {MUTED};
            font-weight: 500;
            margin-left: 5px;
        }}
        .metric-trend {{
            font-size: 12px;
            color: {MUTED};
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: auto;
            padding-bottom: 14px;
        }}
        .metric-trend.up   {{ color: {GOOD}; }}
        .metric-trend.down {{ color: {ALERT}; }}
        .metric-trend.flat {{ color: {MUTED}; }}
        .metric-statusbar {{
            position: absolute; left: 0; right: 0; bottom: 0;
            height: 3px;
        }}

        /* ---------- Vitals strip ---------- */
        .vitals-strip {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }}
        .vital-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 4px 14px 4px 0;
            border-right: 1px solid {BORDER};
        }}
        .vital-item:last-child {{ border-right: none; }}
        .vital-label {{
            font-size: 10px; color: {MUTED};
            letter-spacing: 0.16em; text-transform: uppercase;
            font-weight: 600;
            display: inline-flex; align-items: center; gap: 8px;
        }}
        .vital-value {{
            font-size: 26px; font-weight: 600; color: {TEXT};
            line-height: 1.1;
        }}
        .vital-unit {{ font-size: 13px; color: {MUTED}; font-weight: 500; margin-left: 4px; }}
        .vital-sub {{ font-size: 11px; color: {MUTED_SOFT}; }}

        /* Score ring */
        .score-ring {{
            position: relative;
            width: 54px; height: 54px;
        }}
        .score-ring svg {{ transform: rotate(-90deg); }}
        .score-ring .bg-track {{ stroke: {BORDER}; }}
        .score-ring .fg-track {{ stroke: {PRIMARY}; stroke-linecap: round; transition: stroke-dashoffset .6s ease; }}
        .score-ring .fg-track.warn {{ stroke: {WARN}; }}
        .score-ring .fg-track.alert {{ stroke: {ALERT}; }}
        .score-ring-label {{
            position: absolute; inset: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; font-weight: 700; color: {TEXT};
        }}

        /* ---------- Summary split ---------- */
        .summary-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 20px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
        }}
        .summary-score {{
            font-size: 56px; font-weight: 700; line-height: 1;
            letter-spacing: -0.02em;
        }}
        .summary-score-sub {{
            font-size: 13px; color: {MUTED}; margin-top: 2px;
            letter-spacing: 0.12em; text-transform: uppercase; font-weight: 600;
        }}
        .highlight-list {{ margin-top: 18px; padding: 0; }}
        .highlight-row {{
            display: flex; align-items: flex-start; gap: 10px;
            padding: 9px 0;
            border-top: 1px solid {BORDER};
            font-size: 13px;
            color: {TEXT};
        }}
        .highlight-row:first-child {{ border-top: none; padding-top: 4px; }}
        .highlight-dot {{
            width: 7px; height: 7px; border-radius: 50%;
            margin-top: 7px; flex-shrink: 0;
        }}
        .briefing-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-left: 4px solid {PRIMARY};
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
            display: flex; flex-direction: column;
        }}
        .briefing-head {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 10px;
        }}
        .briefing-title {{
            font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase;
            color: {PRIMARY}; font-weight: 700;
        }}
        .briefing-time {{
            font-size: 10px; color: {MUTED_SOFT};
            letter-spacing: 0.14em; text-transform: uppercase;
        }}
        .briefing-body {{
            color: {TEXT}; font-size: 14px; line-height: 1.6;
            flex: 1;
        }}

        /* ---------- Quick action buttons ---------- */
        .st-key-qa_row .stButton > button {{
            background: {SURFACE} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid transparent !important;
            border-radius: 10px !important;
            padding: 14px 16px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            min-height: 60px !important;
            transition: all 0.18s ease !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        }}
        .st-key-qa_row .stButton > button p {{ text-align: left !important; color: {TEXT} !important; }}
        .st-key-qa_row .stButton > button:hover {{
            border-left: 3px solid {PRIMARY} !important;
            color: {PRIMARY} !important;
            background: #F0FBF8 !important;
        }}
        .st-key-qa_row .stButton > button:hover p {{ color: {PRIMARY} !important; }}

        /* Reset demo button */
        .st-key-reset_btn .stButton > button {{
            background: transparent !important;
            color: {PRIMARY} !important;
            border: 1px solid {PRIMARY} !important;
            border-radius: 8px !important;
            font-size: 11px !important;
            letter-spacing: 0.2em !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }}
        .st-key-reset_btn .stButton > button:hover {{
            background: #F0FBF8 !important;
        }}

        /* Refresh buttons (briefing + vitals) */
        .st-key-refresh_briefing .stButton > button,
        .st-key-refresh_vitals .stButton > button {{
            background: {PRIMARY} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 11px !important;
            letter-spacing: 0.16em !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
            padding: 8px 14px !important;
            box-shadow: none !important;
        }}
        .st-key-refresh_briefing .stButton > button:hover,
        .st-key-refresh_vitals .stButton > button:hover {{
            background: {PRIMARY_SOFT} !important;
        }}
        .st-key-refresh_briefing .stButton > button p,
        .st-key-refresh_vitals .stButton > button p {{ color: #FFFFFF !important; }}

        /* Save profile button */
        .st-key-save_profile .stButton > button {{
            background: transparent !important;
            color: {PRIMARY} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 6px !important;
            font-size: 11px !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
        }}

        /* Feedback buttons */
        [class*="st-key-fb_"] .stButton > button {{
            background: transparent !important;
            border: none !important;
            color: {MUTED_SOFT} !important;
            font-size: 14px !important;
            padding: 2px 8px !important;
            min-height: 0 !important;
            box-shadow: none !important;
        }}
        [class*="st-key-fb_"] .stButton > button:hover {{
            color: {PRIMARY} !important;
            background: transparent !important;
        }}

        /* ---------- Chat messages ---------- */
        .user-msg {{
            text-align: right;
            color: {TEXT};
            font-size: 14.5px;
            line-height: 1.55;
            margin: 14px 0 14px auto;
            max-width: 75%;
            padding: 10px 14px;
            background: #E6F4F1;
            border-radius: 12px 12px 0 12px;
            display: inline-block;
            float: right;
            clear: both;
        }}
        .user-msg-wrap {{ display: flow-root; }}
        .agent-msg {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-left: 3px solid {PRIMARY};
            border-radius: 10px;
            padding: 14px 18px;
            margin: 14px 0 6px 0;
            font-size: 14px;
            line-height: 1.6;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .agent-msg p, .agent-msg li {{ color: {TEXT} !important; margin-bottom: 6px; }}
        .agent-msg strong {{ color: {TEXT}; font-weight: 700; }}
        .agent-msg ul {{ padding-left: 18px; margin: 6px 0; }}

        /* Tool trace */
        .tool-trace {{
            font-family: 'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace;
            font-size: 11px;
            color: {MUTED};
            padding: 3px 0 3px 10px;
            border-left: 1px solid {BORDER};
            margin: 2px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .tool-trace .tk {{ color: {PRIMARY}; }}

        /* Chat input */
        [data-testid="stChatInput"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
            transition: border-color 0.18s ease !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        }}
        [data-testid="stChatInput"]:focus-within {{
            border: 1px solid {PRIMARY} !important;
            box-shadow: 0 0 0 3px rgba(10,124,108,0.12) !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background: transparent !important; color: {TEXT} !important; font-size: 14px !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{ color: {MUTED_SOFT} !important; }}
        [data-testid="stChatInput"] button {{
            background: {PRIMARY} !important; border: none !important;
            border-radius: 50% !important; color: #FFFFFF !important;
            width: 34px !important; height: 34px !important;
        }}
        [data-testid="stChatInput"] button svg {{ color: #FFFFFF !important; fill: #FFFFFF !important; }}

        /* ---------- Bar chart (sidebar-right) ---------- */
        .bar-chart {{
            display: flex; align-items: flex-end; gap: 6px;
            height: 130px; padding: 8px 4px;
            border-bottom: 1px solid {BORDER};
        }}
        .bar-col {{
            flex: 1; display: flex; flex-direction: column;
            align-items: center; justify-content: flex-end;
            height: 100%; gap: 6px;
        }}
        .bar {{
            width: 100%; border-radius: 3px 3px 0 0;
            min-height: 2px; transition: background 0.2s ease;
        }}
        .bar-label {{
            font-size: 10px; color: {MUTED};
            letter-spacing: 0.1em; text-transform: uppercase;
        }}
        .bar-label.active {{ color: {PRIMARY}; font-weight: 600; }}

        /* Trend rows */
        .trend-row {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid {BORDER};
            font-size: 13px;
        }}
        .trend-row:last-child {{ border-bottom: none; }}
        .trend-val {{
            display: inline-flex; align-items: center; gap: 8px;
            font-size: 11px; letter-spacing: 0.12em;
            text-transform: uppercase; font-weight: 600;
        }}

        /* KV list */
        .kv-list {{ padding: 4px 0; }}
        .kv-row {{
            display: flex; justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid {BORDER};
            font-size: 13px;
        }}
        .kv-row:last-child {{ border-bottom: none; }}
        .kv-key {{
            color: {MUTED}; font-size: 10px; letter-spacing: 0.14em;
            text-transform: uppercase; font-weight: 600;
        }}
        .kv-val {{ color: {TEXT}; text-align: right; max-width: 60%; }}

        /* Sidebar status */
        .side-status {{
            display: inline-flex; align-items: center; gap: 10px;
            font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase;
            color: {PRIMARY}; font-weight: 600;
        }}
        .side-status.off {{ color: {ALERT}; }}
        .side-head {{
            font-size: 16px; font-weight: 700; color: {PRIMARY};
            margin-bottom: 2px;
        }}
        .side-sub {{
            font-size: 11px; color: {MUTED}; margin-bottom: 18px;
        }}

        /* Streamlit expander tweaks */
        [data-testid="stExpander"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }}
        [data-testid="stExpander"] summary {{ color: {MUTED} !important; }}

        /* Status widget (agent thinking) */
        [data-testid="stStatusWidget"], div[data-testid="stStatus"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
        }}

        /* Text inputs */
        input, textarea {{
            background: {SURFACE} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 6px !important;
        }}
        input:focus, textarea:focus {{
            border-color: {PRIMARY} !important;
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(10,124,108,0.08) !important;
        }}
        label {{
            color: {MUTED} !important; font-size: 11px !important;
            letter-spacing: 0.12em !important; text-transform: uppercase !important;
        }}

        hr {{ border-color: {BORDER} !important; }}
        [data-testid="stToast"] {{
            background: {SURFACE} !important;
            border: 1px solid {PRIMARY} !important;
            color: {TEXT} !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================================
# Bootstrap (unchanged)
# =========================================================================
@st.cache_resource(show_spinner=False)
def _bootstrap_data():
    simulator.ensure_data_present()
    return True


@st.cache_resource(show_spinner="Indexing knowledge base…")
def _bootstrap_kb():
    try:
        knowledge_base.load_or_build_index()
        return True
    except Exception as e:
        st.warning(f"Knowledge base unavailable: {e}")
        return False


@st.cache_resource(show_spinner="Warming up the AI coach…")
def _get_agent() -> HealthAgent:
    return HealthAgent(model="gpt-4o", temperature=0.3, verbose=True)


_bootstrap_data()


# =========================================================================
# Scoring / derived-metric helpers
# =========================================================================
def _tier(value, good_range, warn_below=None, warn_above=None) -> str:
    lo, hi = good_range
    if lo <= value <= hi:
        return "good"
    if warn_below is not None and value < warn_below:
        return "alert"
    if warn_above is not None and value > warn_above:
        return "alert"
    return "warn"


def _tier_color(tier: str) -> str:
    return {"good": GOOD, "warn": WARN, "alert": ALERT}[tier]


def _tier_label(tier: str) -> str:
    return {"good": "Optimal", "warn": "Watch", "alert": "Alert"}[tier]


def today_tiers(log: dict) -> dict:
    return {
        "hr": _tier(log["heart_rate_avg"], (60, 85), warn_below=50, warn_above=95),
        "steps": _tier(log["steps"], (7000, 12000), warn_below=4000, warn_above=20000),
        "sleep": _tier(log["sleep_hours"], (7.0, 9.0), warn_below=5.5, warn_above=10.5),
        "calories": _tier(
            log["calories_burned"], (1800, 2500), warn_below=1500, warn_above=3000
        ),
    }


def overall_score(log: dict) -> tuple[int, str, str]:
    """Reuses the same deduction logic as agent/tools.py for consistency."""
    hr = log["heart_rate_avg"]
    steps = log["steps"]
    sleep = log["sleep_hours"]
    cals = log["calories_burned"]
    deduction = 0

    if sleep < 5.5: deduction += 30
    elif sleep < 7.0: deduction += 15
    elif sleep > 10.0: deduction += 10

    if hr > 95: deduction += 20
    elif hr > 85: deduction += 10
    elif hr < 50: deduction += 5

    if steps < 4000: deduction += 20
    elif steps < 6000: deduction += 10

    if cals < 1500: deduction += 10
    elif cals > 3000: deduction += 5

    score = max(0, 100 - deduction)
    if score >= 90:   label, color = "Excellent", GOOD
    elif score >= 70: label, color = "Good",       GOOD
    elif score >= 50: label, color = "Fair",       WARN
    else:             label, color = "Poor",       ALERT
    return score, label, color


def derive_vitals(log: dict) -> dict:
    """Calculate HRV estimate, recovery, and readiness from a day's log."""
    hr = log["heart_rate_avg"]
    steps = log["steps"]
    sleep = log["sleep_hours"]

    # Rough HRV estimate: lower HR generally correlates with higher HRV.
    hrv = int(max(25, min(110, 95 - (hr - 65) * 0.9)))

    # Recovery (per spec)
    recovery = (sleep / 9 * 40) + ((100 - hr) / 40 * 60)
    recovery = int(max(0, min(100, recovery)))

    # Readiness (per spec, averaged)
    readiness_raw = (
        (steps / 10000 * 100) + (sleep / 8 * 100) + (100 - hr + 60)
    ) / 3
    readiness = int(max(0, min(100, readiness_raw)))

    return {"hr": hr, "hrv": hrv, "recovery": recovery, "readiness": readiness}


def score_to_color(v: int) -> str:
    if v >= 75: return PRIMARY
    if v >= 50: return WARN
    return ALERT


def score_to_class(v: int) -> str:
    if v >= 75: return ""
    if v >= 50: return "warn"
    return "alert"


def pct_delta(today_v: float, prev_v: float | None) -> tuple[str, str, str]:
    """Return (arrow, pct_str, css_class) comparing today vs prior day."""
    if prev_v is None or prev_v == 0:
        return ("→", "no prior data", "flat")
    delta = (today_v - prev_v) / prev_v * 100
    if abs(delta) < 1.5:
        return ("→", "flat vs yday", "flat")
    if delta > 0:
        return ("↑", f"+{delta:.0f}% vs yday", "up")
    return ("↓", f"{delta:.0f}% vs yday", "down")


def pct_delta_inverted(today_v: float, prev_v: float | None) -> tuple[str, str, str]:
    """For heart rate: lower is better."""
    arrow, pct, cls = pct_delta(today_v, prev_v)
    if cls == "up":   cls = "down"
    elif cls == "down": cls = "up"
    return (arrow, pct, cls)


def _trend_arrow(direction: str) -> str:
    return {"improving": "↑", "declining": "↓", "stable": "→"}.get(direction, "→")


def _trend_color(direction: str) -> str:
    return {"improving": GOOD, "declining": ALERT, "stable": MUTED}.get(direction, MUTED)


def _compute_trends(rows: list[dict]) -> dict:
    if len(rows) < 2:
        return {k: "stable" for k in ["hr", "steps", "sleep", "calories"]}

    def direction(vals, invert=False) -> str:
        mid = len(vals) // 2
        a = sum(vals[:mid]) / max(1, mid)
        b = sum(vals[mid:]) / max(1, len(vals) - mid)
        if a == 0: return "stable"
        delta = (b - a) / abs(a)
        if delta > 0.05: return "declining" if invert else "improving"
        if delta < -0.05: return "improving" if invert else "declining"
        return "stable"

    return {
        "hr": direction([r["heart_rate_avg"] for r in rows], invert=True),
        "steps": direction([r["steps"] for r in rows]),
        "sleep": direction([r["sleep_hours"] for r in rows]),
        "calories": direction([r["calories_burned"] for r in rows]),
    }


def _tag_from_text(text: str) -> str:
    t = text.lower()
    if "sleep" in t or "bedtime" in t or "nap" in t:   return "sleep"
    if "walk" in t or "exercise" in t or "workout" in t or "steps" in t or "cardio" in t: return "exercise"
    if "eat" in t or "meal" in t or "protein" in t or "diet" in t or "hydrat" in t or "water" in t: return "diet"
    if "stress" in t or "breath" in t or "meditat" in t: return "stress"
    return "general"


def _escape(s: str) -> str:
    return _html.escape(str(s), quote=False)


# =========================================================================
# HTML component builders
# =========================================================================
def metric_card_html(label: str, value: str, unit: str, tier: str,
                     arrow: str, pct_str: str, trend_cls: str) -> str:
    color = _tier_color(tier)
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div>
            <span class="metric-value">{value}</span><span class="metric-unit">{unit}</span>
        </div>
        <div class="metric-trend {trend_cls}">
            <span>{arrow}</span><span>{pct_str}</span>
        </div>
        <div class="metric-statusbar" style="background:{color}"></div>
    </div>
    """


def score_ring_html(value: int, size: int = 54, stroke: int = 6) -> str:
    r = (size - stroke) / 2
    c = 2 * 3.14159265 * r
    off = c * (1 - max(0, min(100, value)) / 100)
    cls = score_to_class(value)
    cx = size / 2
    return (
        f'<div class="score-ring" style="width:{size}px;height:{size}px">'
        f'<svg width="{size}" height="{size}">'
        f'<circle class="bg-track" cx="{cx}" cy="{cx}" r="{r}" '
        f'stroke-width="{stroke}" fill="none"/>'
        f'<circle class="fg-track {cls}" cx="{cx}" cy="{cx}" r="{r}" '
        f'stroke-width="{stroke}" fill="none" '
        f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}"/>'
        f'</svg>'
        f'<div class="score-ring-label">{value}</div>'
        f'</div>'
    )


def vitals_strip_html(vitals: dict) -> str:
    hr_color_cls = "" if vitals["hr"] <= 85 else "alert"
    return f"""
    <div class="vitals-strip">
        <div class="vital-item">
            <div class="vital-label">
                <span class="pulse-dot {hr_color_cls}"></span>Live HR
            </div>
            <div><span class="vital-value">{vitals['hr']}</span><span class="vital-unit">bpm</span></div>
            <div class="vital-sub">Resting pulse (today)</div>
        </div>
        <div class="vital-item">
            <div class="vital-label">HRV</div>
            <div><span class="vital-value">{vitals['hrv']}</span><span class="vital-unit">ms</span></div>
            <div class="vital-sub">Heart rate variability</div>
        </div>
        <div class="vital-item">
            <div class="vital-label">Recovery</div>
            <div style="display:flex;align-items:center;gap:10px;">
                {score_ring_html(vitals['recovery'])}
                <div class="vital-sub">Sleep + HR composite</div>
            </div>
        </div>
        <div class="vital-item">
            <div class="vital-label">Readiness</div>
            <div style="display:flex;align-items:center;gap:10px;">
                {score_ring_html(vitals['readiness'])}
                <div class="vital-sub">Whole-body composite</div>
            </div>
        </div>
    </div>
    """


def bar_chart_html(rows: list[dict]) -> str:
    if not rows:
        return '<div class="bar-chart"></div>'
    today_iso = date.today().isoformat()
    max_steps = max(r["steps"] for r in rows) or 1
    cols = []
    for r in rows:
        pct = max(4.0, (r["steps"] / max_steps) * 100)
        is_today = r["date"] == today_iso
        color = PRIMARY if is_today else "#CBD5E1"
        day_letter = pd.to_datetime(r["date"]).strftime("%a")[:3].upper()
        lbl_cls = "bar-label active" if is_today else "bar-label"
        cols.append(
            f'<div class="bar-col">'
            f'<div class="bar" style="height:{pct}%;background:{color}"></div>'
            f'<div class="{lbl_cls}">{day_letter}</div>'
            f"</div>"
        )
    return f'<div class="bar-chart">{"".join(cols)}</div>'


def trend_row_html(name: str, direction: str) -> str:
    color = _trend_color(direction)
    arrow = _trend_arrow(direction)
    return (
        f'<div class="trend-row">'
        f'<span>{name}</span>'
        f'<span class="trend-val" style="color:{color}">{arrow}&nbsp;{direction}</span>'
        f"</div>"
    )


def highlight_items(log: dict, prev: dict | None) -> list[tuple[str, str]]:
    """Return up to 3 (color, text) bullets summarizing today's notable points."""
    out: list[tuple[str, str]] = []
    hr, steps, sleep = log["heart_rate_avg"], log["steps"], log["sleep_hours"]

    if sleep < 5.5:
        out.append((ALERT, f"Sleep {sleep:.1f}h — well below 7-9h target"))
    elif sleep < 7.0:
        out.append((WARN, f"Sleep {sleep:.1f}h — slightly below target"))
    else:
        out.append((GOOD, f"Sleep {sleep:.1f}h — on target"))

    if hr > 95:
        out.append((ALERT, f"Heart rate elevated at {hr} bpm"))
    elif hr > 85:
        out.append((WARN, f"Heart rate slightly elevated at {hr} bpm"))
    else:
        out.append((GOOD, f"Resting HR healthy at {hr} bpm"))

    if steps < 4000:
        out.append((ALERT, f"Steps low at {steps:,} — target 7,000-10,000"))
    elif steps < 7000:
        out.append((WARN, f"Steps at {steps:,} — below daily target"))
    else:
        out.append((GOOD, f"Steps on track at {steps:,}"))

    return out[:3]


def highlights_html(items: list[tuple[str, str]]) -> str:
    rows = "".join(
        f'<div class="highlight-row">'
        f'<span class="highlight-dot" style="background:{color}"></span>'
        f'<span>{_escape(text)}</span></div>'
        for color, text in items
    )
    return f'<div class="highlight-list">{rows}</div>'


# =========================================================================
# Session state
# =========================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "proactive_done" not in st.session_state:
    st.session_state.proactive_done = False
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}
if "daily_briefing" not in st.session_state:
    st.session_state.daily_briefing = None
if "daily_briefing_ts" not in st.session_state:
    st.session_state.daily_briefing_ts = None
if "vitals_refresh_tick" not in st.session_state:
    st.session_state.vitals_refresh_tick = 0


# =========================================================================
# Daily-briefing helper
# =========================================================================
BRIEFING_PROMPT = (
    "Give me a 3-sentence daily health briefing for today. Be specific with "
    "numbers. Format: sentence 1 = overall status, sentence 2 = biggest "
    "concern, sentence 3 = top recommendation. No bullets, no headers, "
    "no preamble."
)


def generate_daily_briefing() -> str:
    """Run a standalone agent invocation for the briefing.

    Does NOT mutate the main chat history (bypasses HealthAgent.chat's append).
    """
    agent = _get_agent()
    try:
        result = agent.executor.invoke({"input": BRIEFING_PROMPT, "chat_history": []})
        return (result.get("output") or "").strip()
    except Exception as e:
        return f"Briefing unavailable: {e}"


# =========================================================================
# Sidebar
# =========================================================================
with st.sidebar:
    st.markdown(
        "<div class='side-head'>HealthAgent</div>"
        "<div class='side-sub'>Personal Health Intelligence</div>",
        unsafe_allow_html=True,
    )

    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    if api_key_present:
        st.markdown(
            "<div class='side-status'>"
            "<span class='pulse-dot'></span>OpenAI Connected"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='side-status off'>"
            "<span class='pulse-dot alert'></span>No API Key"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Add OPENAI_API_KEY to .env and restart.")

    # Weekly steps chart in the sidebar as well
    rows7 = db.get_last_n_logs(7)
    st.markdown("<div class='section-head'>This Week · Steps</div>", unsafe_allow_html=True)
    st.markdown(bar_chart_html(rows7), unsafe_allow_html=True)

    st.markdown("<div class='section-head'>Trend Indicators</div>", unsafe_allow_html=True)
    trends = _compute_trends(rows7) if rows7 else {}
    trend_block = "".join(
        [
            trend_row_html("Heart Rate", trends.get("hr", "stable")),
            trend_row_html("Steps", trends.get("steps", "stable")),
            trend_row_html("Sleep", trends.get("sleep", "stable")),
            trend_row_html("Calories", trends.get("calories", "stable")),
        ]
    )
    st.markdown(trend_block, unsafe_allow_html=True)

    st.markdown("<div class='section-head'>Memory</div>", unsafe_allow_html=True)
    profile = memory.get_profile()
    kv_rows = [
        ("Name", _escape(str(profile.get("name", "—")))),
        ("Age", _escape(str(profile.get("age", "—")))),
        ("Goal", _escape(str(profile.get("goal", "—")))[:60]),
    ]
    disliked = profile.get("disliked_advice_tags") or []
    if disliked:
        kv_rows.append(("Avoiding", _escape(", ".join(disliked))))
    liked = profile.get("liked_advice_tags") or []
    if liked:
        kv_rows.append(("Prefers", _escape(", ".join(liked))))
    kv_html = "<div class='kv-list'>" + "".join(
        f"<div class='kv-row'><span class='kv-key'>{k}</span>"
        f"<span class='kv-val'>{v}</span></div>"
        for k, v in kv_rows
    ) + "</div>"
    st.markdown(kv_html, unsafe_allow_html=True)

    st.markdown("<div class='section-head'>Profile</div>", unsafe_allow_html=True)
    with st.expander("Edit profile", expanded=False):
        name = st.text_input("Name", value=profile.get("name", "Alex"))
        age = st.text_input("Age", value=str(profile.get("age", "28")))
        goal = st.text_area(
            "Health goal",
            value=profile.get("goal", "Improve sleep and maintain consistent exercise"),
            height=70,
        )
        with st.container(key="save_profile"):
            if st.button("Save", use_container_width=True):
                memory.update_profile("name", name)
                memory.update_profile("age", age)
                memory.update_profile("goal", goal)
                st.toast("Profile updated", icon="✓")

    st.markdown("<div class='section-head'>Controls</div>", unsafe_allow_html=True)
    with st.container(key="reset_btn"):
        if st.button("↻  Reset Demo", use_container_width=True):
            simulator.simulate_and_store(seed=None, today_is_bad=True)
            db.clear_feedback()
            st.session_state.messages = []
            st.session_state.proactive_done = False
            st.session_state.feedback_given = {}
            st.session_state.daily_briefing = None
            st.session_state.daily_briefing_ts = None
            _get_agent.clear()
            st.toast("Demo reset", icon="↻")
            st.rerun()


# =========================================================================
# Main area
# =========================================================================
# Top bar
st.markdown(
    "<div class='top-bar'>"
    f"<span class='brand'>HealthAgent</span>"
    f"<span class='brand-sub'>Personal Health Intelligence · {date.today().strftime('%A, %b %d')}</span>"
    "<span class='live-indicator'><span class='pulse-dot'></span>Live</span>"
    "</div>",
    unsafe_allow_html=True,
)


# -------- Today's Dashboard --------
today_iso = date.today().isoformat()
yday_iso = (date.today() - timedelta(days=1)).isoformat()
today_log = db.get_log_by_date(today_iso)
yday_log = db.get_log_by_date(yday_iso)

st.markdown(
    "<div class='section-head'>"
    "<span>Today's Dashboard</span>"
    "<span class='tag'>Live readings</span>"
    "</div>",
    unsafe_allow_html=True,
)

if today_log:
    tiers = today_tiers(today_log)

    # HR uses inverted delta (lower = better)
    hr_arrow, hr_pct, hr_cls = pct_delta_inverted(
        today_log["heart_rate_avg"],
        yday_log["heart_rate_avg"] if yday_log else None,
    )
    steps_arrow, steps_pct, steps_cls = pct_delta(
        today_log["steps"], yday_log["steps"] if yday_log else None
    )
    sleep_arrow, sleep_pct, sleep_cls = pct_delta(
        today_log["sleep_hours"], yday_log["sleep_hours"] if yday_log else None
    )
    cal_arrow, cal_pct, cal_cls = pct_delta(
        today_log["calories_burned"], yday_log["calories_burned"] if yday_log else None
    )

    cards_html = (
        "<div class='metric-grid'>"
        + metric_card_html("Heart Rate", str(today_log["heart_rate_avg"]), "bpm",
                           tiers["hr"], hr_arrow, hr_pct, hr_cls)
        + metric_card_html("Steps", f"{today_log['steps']:,}", "",
                           tiers["steps"], steps_arrow, steps_pct, steps_cls)
        + metric_card_html("Sleep", f"{today_log['sleep_hours']:.1f}", "hr",
                           tiers["sleep"], sleep_arrow, sleep_pct, sleep_cls)
        + metric_card_html("Calories", f"{today_log['calories_burned']:,}", "kcal",
                           tiers["calories"], cal_arrow, cal_pct, cal_cls)
        + "</div>"
    )
    st.markdown(cards_html, unsafe_allow_html=True)

    # Vitals strip (real-time simulation)
    vitals_header_cols = st.columns([6, 1])
    with vitals_header_cols[0]:
        st.markdown(
            "<div class='section-head' style='margin-top:6px'>"
            "<span>Real-Time Vitals</span>"
            f"<span class='tag'>Updated {datetime.now().strftime('%H:%M:%S')} · "
            f"tick #{st.session_state.vitals_refresh_tick}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with vitals_header_cols[1]:
        with st.container(key="refresh_vitals"):
            if st.button("↻ Refresh", use_container_width=True, key="btn_refresh_vitals"):
                st.session_state.vitals_refresh_tick += 1
                st.rerun()

    vitals = derive_vitals(today_log)
    st.markdown(vitals_strip_html(vitals), unsafe_allow_html=True)
else:
    st.info("No data for today yet. Click **Reset Demo** in the sidebar to simulate.")


# -------- Today's Summary --------
st.markdown(
    "<div class='section-head'>"
    "<span>Today's Summary</span>"
    "<span class='tag'>Health snapshot + AI briefing</span>"
    "</div>",
    unsafe_allow_html=True,
)

if today_log:
    score, score_label, score_color = overall_score(today_log)
    highlights = highlight_items(today_log, yday_log)

    sum_l, sum_r = st.columns([1, 1.3], gap="medium")

    with sum_l:
        st.markdown(
            f"""
            <div class="summary-card">
                <div style="font-size:10px;letter-spacing:0.18em;
                            text-transform:uppercase;color:{MUTED};
                            font-weight:600;margin-bottom:10px">
                    Health Snapshot
                </div>
                <div class="summary-score" style="color:{score_color}">{score}</div>
                <div class="summary-score-sub" style="color:{score_color}">{score_label}</div>
                {highlights_html(highlights)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with sum_r:
        # Generate briefing on demand / once per session
        if (
            api_key_present
            and st.session_state.daily_briefing is None
        ):
            with st.spinner("Generating daily briefing…"):
                st.session_state.daily_briefing = generate_daily_briefing()
                st.session_state.daily_briefing_ts = datetime.now().strftime("%H:%M")

        briefing_text = st.session_state.daily_briefing or (
            "Daily briefing will appear once the AI coach is connected."
        )
        briefing_ts = st.session_state.daily_briefing_ts or "—"

        st.markdown(
            f"""
            <div class="briefing-card">
                <div class="briefing-head">
                    <span class="briefing-title">AI Daily Briefing</span>
                    <span class="briefing-time">Updated {briefing_ts}</span>
                </div>
                <div class="briefing-body">{_escape(briefing_text)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        refresh_cols = st.columns([1, 3])
        with refresh_cols[0]:
            with st.container(key="refresh_briefing"):
                if st.button("↻ Refresh Analysis", use_container_width=True,
                             key="btn_refresh_briefing", disabled=not api_key_present):
                    st.session_state.daily_briefing = None
                    st.session_state.daily_briefing_ts = None
                    st.rerun()


# -------- Quick actions --------
st.markdown(
    "<div class='section-head'>"
    "<span>Quick Analysis</span>"
    "<span class='tag'>One-click questions</span>"
    "</div>",
    unsafe_allow_html=True,
)
with st.container(key="qa_row"):
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("◐  Why am I tired today?", use_container_width=True, key="demo1"):
            st.session_state.pending_input = "Why do I feel tired today?"
    with qa2:
        if st.button("◈  Weekly health review", use_container_width=True, key="demo2"):
            st.session_state.pending_input = "How was my health this week?"
    with qa3:
        if st.button("◉  What to focus on next", use_container_width=True, key="demo3"):
            st.session_state.pending_input = "What should I focus on to improve?"


# -------- Chat area --------
st.markdown(
    "<div class='section-head'>"
    "<span>Agent Conversation</span>"
    "<span class='tag'>Grounded on your wearable data</span>"
    "</div>",
    unsafe_allow_html=True,
)


def render_user_message(content: str):
    st.markdown(
        f"<div class='user-msg-wrap'><div class='user-msg'>{_escape(content)}</div></div>",
        unsafe_allow_html=True,
    )


def render_agent_message(msg: dict, idx: int):
    content = msg["content"] or ""
    st.markdown(
        f"<div class='agent-msg'>\n\n{content}\n\n</div>",
        unsafe_allow_html=True,
    )

    msg_id = msg.get("id", f"m{idx}")
    if msg.get("tool_calls"):
        with st.container(key=f"tt_{msg_id}"):
            with st.expander(
                f"▸ tool trace · {len(msg['tool_calls'])} call(s)", expanded=False
            ):
                for tc in msg["tool_calls"]:
                    tool_name = _escape(tc.get("tool", "?"))
                    tool_input = _escape(str(tc.get("input", ""))[:280])
                    st.markdown(
                        f"<div class='tool-trace'>"
                        f"<span class='tk'>▸</span> {tool_name}({tool_input})"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if tc.get("output"):
                        out = _escape(str(tc["output"])[:500])
                        st.markdown(
                            f"<div class='tool-trace' style='opacity:0.75'>"
                            f"  ← {out}</div>",
                            unsafe_allow_html=True,
                        )

    already = st.session_state.feedback_given.get(msg_id)
    if already:
        msg_text = "▲ helpful" if already == 1 else "▽ noted — adjusting"
        st.markdown(
            f"<div style='color:{PRIMARY};font-size:11px;"
            f"letter-spacing:0.14em;text-transform:uppercase;margin:4px 0 18px 0;'>"
            f"{msg_text}</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.container(key=f"fb_{msg_id}"):
            fc1, fc2, _fc3 = st.columns([1, 1, 10])
            with fc1:
                if st.button("▲", key=f"up_{msg_id}", help="Helpful"):
                    tag = _tag_from_text(msg["content"])
                    memory.save_feedback(msg["content"][:240], 1, tag)
                    st.session_state.feedback_given[msg_id] = 1
                    st.rerun()
            with fc2:
                if st.button("▽", key=f"down_{msg_id}", help="Not useful"):
                    tag = _tag_from_text(msg["content"])
                    memory.save_feedback(msg["content"][:240], -1, tag)
                    st.session_state.feedback_given[msg_id] = -1
                    st.rerun()


def render_message(msg: dict, idx: int):
    if msg["role"] == "user":
        render_user_message(msg["content"])
    else:
        render_agent_message(msg, idx)


# Proactive check on first load
if api_key_present and not st.session_state.proactive_done and not st.session_state.messages:
    _bootstrap_kb()
    agent = _get_agent()
    with st.status("Agent is analyzing your data…", expanded=True) as status:
        step_box = st.empty()
        steps_seen: list[str] = []

        def _on_step(tool_name, tool_input):
            steps_seen.append(
                f"<div class='tool-trace'><span class='tk'>▸</span> "
                f"{_escape(tool_name)}({_escape(str(tool_input)[:80])})</div>"
            )
            step_box.markdown("".join(steps_seen), unsafe_allow_html=True)

        try:
            result = agent.proactive_check(on_step=_on_step)
            status.update(label="Analysis complete", state="complete", expanded=False)
        except Exception as e:
            status.update(label=f"Error: {e}", state="error")
            result = {"output": f"Sorry, I hit an error: {e}", "tool_calls": []}

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["output"],
            "tool_calls": result.get("tool_calls", []),
            "id": f"msg{len(st.session_state.messages)}",
        }
    )
    st.session_state.proactive_done = True
    st.rerun()

# Render history
for i, m in enumerate(st.session_state.messages):
    render_message(m, i)

# Chat input
user_input = st.chat_input("Ask about your health, symptoms, or goals…")

if st.session_state.pending_input and not user_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    if not api_key_present:
        st.error("Please set OPENAI_API_KEY in .env and restart.")
    else:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input,
                "id": f"msg{len(st.session_state.messages)}",
            }
        )
        render_user_message(user_input)

        _bootstrap_kb()
        agent = _get_agent()
        with st.status("Agent is analyzing your data…", expanded=True) as status:
            step_box = st.empty()
            steps_seen: list[str] = []

            def _on_step(tool_name, tool_input):
                steps_seen.append(
                    f"<div class='tool-trace'><span class='tk'>▸</span> "
                    f"{_escape(tool_name)}({_escape(str(tool_input)[:80])})</div>"
                )
                step_box.markdown("".join(steps_seen), unsafe_allow_html=True)

            try:
                result = agent.chat(user_input, on_step=_on_step)
                status.update(label="Analysis complete", state="complete", expanded=False)
            except Exception as e:
                status.update(label=f"Error: {e}", state="error")
                result = {"output": f"Sorry, I hit an error: {e}", "tool_calls": []}

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["output"],
                "tool_calls": result.get("tool_calls", []),
                "id": f"msg{len(st.session_state.messages)}",
            }
        )
        st.rerun()
