"""Streamlit UI for HealthAgent — light theme with real-time dashboard.

Run with:
    streamlit run app.py

Visual layer only; all agent, tool, memory, and simulator logic are unchanged.
"""
from __future__ import annotations

import hashlib
import html as _html
import os
import tempfile
import uuid
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- Per-session DB isolation ----------------------------------------------
# Streamlit Community Cloud runs one process for many visitors; without this
# every visitor would share the same SQLite file (and stomp on each other's
# health logs / feedback). Set the DB path BEFORE importing modules that
# touch the DB.
from data import db as _db  # noqa: E402

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:16]
if "language" not in st.session_state:
    st.session_state.language = "zh"
if "telemetry_events" not in st.session_state:
    st.session_state.telemetry_events = []
_db.set_db_path(
    os.path.join(tempfile.gettempdir(), f"health_agent_{st.session_state.session_id}.db")
)

from agent.core import HealthAgent  # noqa: E402
from agent import memory  # noqa: E402
from data import db, simulator  # noqa: E402
from data import knowledge_base  # noqa: E402
from ui.i18n import briefing_prompt, format_header_date, trend_direction_label, t  # noqa: E402


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

        /* Inject live-data buttons */
        .st-key-inject_main .stButton > button {{
            background: {ALERT} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 11px !important;
            letter-spacing: 0.16em !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
            padding: 10px 14px !important;
            box-shadow: none !important;
        }}
        .st-key-inject_main .stButton > button:hover {{ background: #B91C1C !important; }}
        .st-key-inject_main .stButton > button p {{ color: #FFFFFF !important; }}
        [class*="st-key-inject_scen_"] .stButton > button {{
            background: {SURFACE} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid transparent !important;
            border-radius: 8px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 10px 12px !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
        }}
        [class*="st-key-inject_scen_"] .stButton > button:hover {{
            border-left: 3px solid {PRIMARY} !important;
            background: #F0FBF8 !important;
        }}
        [class*="st-key-inject_scen_"] .stButton > button p {{
            color: {TEXT} !important; text-align: left !important;
        }}
        .inject-caption {{
            font-size: 10px; color: {MUTED_SOFT};
            letter-spacing: 0.14em; text-transform: uppercase;
            margin-top: 6px;
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


_AGENT_MODEL = os.getenv("HEALTH_AGENT_MODEL", "gpt-4o-mini")


def _record_telemetry(kind: str, result: dict) -> None:
    """Append OpenAI usage + tool counts for the current Streamlit session."""
    ev = {
        "kind": kind,
        "tool_call_count": int(result.get("tool_call_count", 0)),
    }
    u = result.get("usage")
    if isinstance(u, dict):
        ev["total_tokens"] = u.get("total_tokens", 0)
        ev["prompt_tokens"] = u.get("prompt_tokens", 0)
        ev["completion_tokens"] = u.get("completion_tokens", 0)
        ev["total_cost_usd"] = u.get("total_cost_usd", 0.0)
    st.session_state.setdefault("telemetry_events", []).append(ev)
    st.session_state.telemetry_events = st.session_state.telemetry_events[-50:]


# =========================================================================
# Bootstrap
# =========================================================================
def _bootstrap_data():
    """Per-session DB bootstrap. Cheap (creates tables + seeds if empty)."""
    if not st.session_state.get("data_bootstrapped"):
        simulator.ensure_data_present()
        st.session_state.data_bootstrapped = True


# Knowledge base is a process-wide read-only artifact and safe to share.
@st.cache_resource(show_spinner="Indexing knowledge base / 正在构建知识库…")
def _bootstrap_kb():
    try:
        knowledge_base.load_or_build_index()
        return True
    except Exception as e:
        st.warning(t("kb_warn", e=e))
        return False


def _get_agent() -> HealthAgent:
    """Per-session agent. Holds chat history; must NOT be shared across users."""
    if "agent" not in st.session_state:
        with st.spinner(t("warming")):
            st.session_state.agent = HealthAgent(
                model=_AGENT_MODEL, temperature=0.3, verbose=True
            )
    return st.session_state.agent


def _get_briefing_agent() -> HealthAgent:
    """Separate executor from chat so daily briefing never mutates chat memory."""
    if "briefing_agent" not in st.session_state:
        with st.spinner(t("warming")):
            st.session_state.briefing_agent = HealthAgent(
                model=_AGENT_MODEL, temperature=0.3, verbose=False
            )
    return st.session_state.briefing_agent


def _reset_agent() -> None:
    st.session_state.pop("agent", None)
    st.session_state.pop("briefing_agent", None)


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


_STATUS_COLORS = {
    "excellent": GOOD,
    "good": GOOD,
    "caution": WARN,
    "poor": ALERT,
}


def overall_score(log: dict) -> tuple[int, str, str]:
    """Single source of truth: delegates to agent.scoring so the dashboard
    label cannot drift from the agent's status."""
    from agent.scoring import score_log
    result = score_log(log)
    return result.score, result.label, _STATUS_COLORS[result.status]


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


_TAG_KEYWORDS = {
    "sleep": ("sleep", "bedtime", "nap"),
    "exercise": ("walk", "exercise", "workout", "steps", "cardio"),
    "diet": ("eat", "meal", "protein", "diet", "hydrat", "water"),
    "stress": ("stress", "breath", "meditat"),
}


def _tags_from_text(text: str) -> list[str]:
    """Return ALL matching topic tags. A multi-topic answer that gets a
    thumbs-down should not be falsely attributed to whichever tag happened
    to be checked first.
    """
    t = text.lower()
    matched = [tag for tag, kws in _TAG_KEYWORDS.items() if any(k in t for k in kws)]
    return matched or ["general"]


def _escape(s: str) -> str:
    return _html.escape(str(s), quote=False)


def inject_today_reading(hr: int, steps: int, sleep: float, cals: int) -> None:
    """Write (or overwrite) today's row in health_logs with the given values.

    anomaly_flag is auto-set: 1 if HR > 100 OR sleep < 6.0 OR steps < 3000.
    Also clears chat / briefing / proactive state so the agent re-triggers
    on the next render.
    """
    hr = int(hr); steps = int(steps); cals = int(cals)
    sleep = round(float(sleep), 1)
    anomaly = 1 if (hr > 100 or sleep < 6.0 or steps < 3000) else 0
    db.insert_health_log(
        {
            "date": date.today().isoformat(),
            "heart_rate_avg": hr,
            "steps": steps,
            "sleep_hours": sleep,
            "calories_burned": cals,
            "anomaly_flag": anomaly,
        }
    )
    # Reset agent-facing state so the proactive re-fires with the new values.
    st.session_state.messages = []
    st.session_state.proactive_done = False
    st.session_state.feedback_given = {}
    st.session_state.daily_briefing = None
    st.session_state.daily_briefing_ts = None
    try:
        _get_agent().reset_history()
    except Exception:
        pass
    st.session_state.pop("briefing_agent", None)


# =========================================================================
# HTML component builders
# =========================================================================
def metric_card_html(label: str, value: str, unit: str, tier: str,
                     arrow: str, pct_str: str, trend_cls: str) -> str:
    color = _tier_color(tier)
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{_escape(label)}</div>'
        f'<div><span class="metric-value">{_escape(value)}</span>'
        f'<span class="metric-unit">{_escape(unit)}</span></div>'
        f'<div class="metric-trend {trend_cls}">'
        f'<span>{_escape(arrow)}</span><span>{_escape(pct_str)}</span></div>'
        f'<div class="metric-statusbar" style="background:{color}"></div>'
        f'</div>'
    )


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
    ring_recovery = score_ring_html(vitals['recovery'])
    ring_readiness = score_ring_html(vitals['readiness'])
    return (
        '<div class="vitals-strip">'
            '<div class="vital-item">'
                '<div class="vital-label">'
                    f'<span class="pulse-dot {hr_color_cls}"></span>{_escape(t("vital_live_hr"))}'
                '</div>'
                f'<div><span class="vital-value">{vitals["hr"]}</span>'
                f'<span class="vital-unit">{_escape(t("unit_bpm"))}</span></div>'
                f'<div class="vital-sub">{_escape(t("vital_sub_hr"))}</div>'
            '</div>'
            '<div class="vital-item">'
                f'<div class="vital-label">{_escape(t("vital_hrv"))}</div>'
                f'<div><span class="vital-value">{vitals["hrv"]}</span>'
                '<span class="vital-unit">ms</span></div>'
                f'<div class="vital-sub">{_escape(t("vital_sub_hrv"))}</div>'
            '</div>'
            '<div class="vital-item">'
                f'<div class="vital-label">{_escape(t("vital_recovery"))}</div>'
                '<div style="display:flex;align-items:center;gap:10px;">'
                    f'{ring_recovery}'
                    f'<div class="vital-sub">{_escape(t("vital_sub_rec"))}</div>'
                '</div>'
            '</div>'
            '<div class="vital-item">'
                f'<div class="vital-label">{_escape(t("vital_readiness"))}</div>'
                '<div style="display:flex;align-items:center;gap:10px;">'
                    f'{ring_readiness}'
                    f'<div class="vital-sub">{_escape(t("vital_sub_ready"))}</div>'
                '</div>'
            '</div>'
        '</div>'
    )


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
        day_letter = datetime.fromisoformat(r["date"]).strftime("%a")[:3].upper()
        lbl_cls = "bar-label active" if is_today else "bar-label"
        cols.append(
            f'<div class="bar-col">'
            f'<div class="bar" style="height:{pct}%;background:{color}"></div>'
            f'<div class="{lbl_cls}">{day_letter}</div>'
            f"</div>"
        )
    return f'<div class="bar-chart">{"".join(cols)}</div>'


def trend_row_html(name: str, direction: str, direction_display: str | None = None) -> str:
    color = _trend_color(direction)
    arrow = _trend_arrow(direction)
    label = direction_display if direction_display is not None else direction
    return (
        f'<div class="trend-row">'
        f'<span>{_escape(name)}</span>'
        f'<span class="trend-val" style="color:{color}">{arrow}&nbsp;{_escape(label)}</span>'
        f"</div>"
    )


def highlight_items(log: dict, prev: dict | None) -> list[tuple[str, str]]:
    """Return up to 3 (color, text) bullets summarizing today's notable points."""
    out: list[tuple[str, str]] = []
    hr, steps, sleep = log["heart_rate_avg"], log["steps"], log["sleep_hours"]

    if sleep < 5.5:
        out.append((ALERT, t("hl_sleep_bad", h=sleep)))
    elif sleep < 7.0:
        out.append((WARN, t("hl_sleep_low", h=sleep)))
    else:
        out.append((GOOD, t("hl_sleep_ok", h=sleep)))

    if hr > 95:
        out.append((ALERT, t("hl_hr_high", hr=hr)))
    elif hr > 85:
        out.append((WARN, t("hl_hr_mid", hr=hr)))
    else:
        out.append((GOOD, t("hl_hr_ok", hr=hr)))

    if steps < 4000:
        out.append((ALERT, t("hl_steps_low", s=steps)))
    elif steps < 7000:
        out.append((WARN, t("hl_steps_mid", s=steps)))
    else:
        out.append((GOOD, t("hl_steps_ok", s=steps)))

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
def _today_log_fingerprint() -> str:
    """Stable hash of today's metrics. Used to invalidate the briefing cache
    only when the underlying data actually changes."""
    log = db.get_log_by_date(date.today().isoformat())
    if not log:
        return "no-data"
    payload = (
        f"{log['heart_rate_avg']}|{log['steps']}|"
        f"{log['sleep_hours']}|{log['calories_burned']}"
    )
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def generate_daily_briefing() -> str:
    """Run a standalone agent invocation for the briefing.

    Cached by (date, today's-log-hash) so a page refresh with no underlying
    data change does NOT re-trigger another full ReAct loop (each invocation
    is ~3-5 OpenAI calls).

    Does NOT mutate the main chat history (bypasses HealthAgent.chat's append).
    """
    cache_key = f"{date.today().isoformat()}:{_today_log_fingerprint()}"
    cached_key = st.session_state.get("daily_briefing_key")
    cached_text = st.session_state.get("daily_briefing")
    if cached_key == cache_key and cached_text:
        return cached_text

    agent = _get_briefing_agent()
    try:
        result = agent.run_ephemeral(briefing_prompt(), on_step=None)
        text = (result.get("output") or "").strip()
        _record_telemetry("briefing", result)
    except Exception as e:
        text = f"Briefing unavailable: {e}"

    st.session_state.daily_briefing_key = cache_key
    return text


# =========================================================================
# Sidebar
# =========================================================================
with st.sidebar:
    st.markdown(
        "<div class='side-head'>HealthAgent</div>"
        f"<div class='side-sub'>{_escape(t('side_sub'))}</div>",
        unsafe_allow_html=True,
    )

    _lang_opts = ["zh", "en"]
    _cur_lang = st.session_state.language if st.session_state.language in _lang_opts else "zh"
    st.session_state.language = st.selectbox(
        t("lang_label"),
        _lang_opts,
        index=_lang_opts.index(_cur_lang),
        format_func=lambda x: "中文" if x == "zh" else "English",
    )

    st.markdown(f"**{_escape(t('disclaimer_title'))}**")
    st.caption(t("disclaimer_body"))

    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    if api_key_present:
        st.markdown(
            "<div class='side-status'>"
            f"<span class='pulse-dot'></span>{_escape(t('openai_ok'))}"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='side-status off'>"
            f"<span class='pulse-dot alert'></span>{_escape(t('openai_missing'))}"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(t("openai_hint"))

    with st.expander(t("telemetry_title"), expanded=False):
        _evs = st.session_state.get("telemetry_events") or []
        if not _evs:
            st.caption(t("telemetry_empty"))
        else:
            for _ev in reversed(_evs[-20:]):
                st.caption(
                    t(
                        "telemetry_row",
                        kind=_ev.get("kind", "?"),
                        tokens=_ev.get("total_tokens", 0),
                        tools=_ev.get("tool_call_count", 0),
                    )
                )

    # Weekly steps chart in the sidebar as well
    rows7 = db.get_last_n_logs(7)
    st.markdown(
        f"<div class='section-head'>{_escape(t('week_steps'))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(bar_chart_html(rows7), unsafe_allow_html=True)

    st.markdown(f"<div class='section-head'>{_escape(t('trends'))}</div>", unsafe_allow_html=True)
    trends = _compute_trends(rows7) if rows7 else {}
    _dhr = trends.get("hr", "stable")
    _dst = trends.get("steps", "stable")
    _dsl = trends.get("sleep", "stable")
    _dca = trends.get("calories", "stable")
    trend_block = "".join(
        [
            trend_row_html(t("trend_hr"), _dhr, trend_direction_label(_dhr)),
            trend_row_html(t("trend_steps"), _dst, trend_direction_label(_dst)),
            trend_row_html(t("trend_sleep"), _dsl, trend_direction_label(_dsl)),
            trend_row_html(t("trend_calories"), _dca, trend_direction_label(_dca)),
        ]
    )
    st.markdown(trend_block, unsafe_allow_html=True)

    st.markdown(f"<div class='section-head'>{_escape(t('memory'))}</div>", unsafe_allow_html=True)
    profile = memory.get_profile()
    kv_rows = [
        (t("name"), _escape(str(profile.get("name", "—")))),
        (t("age"), _escape(str(profile.get("age", "—")))),
        (t("health_goal"), _escape(str(profile.get("goal", "—")))[:60]),
    ]
    disliked = profile.get("disliked_advice_tags") or []
    if disliked:
        kv_rows.append((t("lbl_avoid"), _escape(", ".join(disliked))))
    liked = profile.get("liked_advice_tags") or []
    if liked:
        kv_rows.append((t("lbl_prefer"), _escape(", ".join(liked))))
    kv_html = "<div class='kv-list'>" + "".join(
        f"<div class='kv-row'><span class='kv-key'>{_escape(k)}</span>"
        f"<span class='kv-val'>{v}</span></div>"
        for k, v in kv_rows
    ) + "</div>"
    st.markdown(kv_html, unsafe_allow_html=True)

    st.markdown(f"<div class='section-head'>{_escape(t('profile'))}</div>", unsafe_allow_html=True)
    with st.expander(t("edit_profile"), expanded=False):
        name = st.text_input(t("name"), value=profile.get("name", "Alex"))
        age = st.text_input(t("age"), value=str(profile.get("age", "28")))
        goal = st.text_area(
            t("health_goal"),
            value=profile.get("goal", "Improve sleep and maintain consistent exercise"),
            height=70,
        )
        with st.container(key="save_profile"):
            if st.button(t("save"), use_container_width=True):
                memory.update_profile("name", name)
                memory.update_profile("age", age)
                memory.update_profile("goal", goal)
                st.toast(t("toast_profile"), icon="✓")

    st.markdown(f"<div class='section-head'>{_escape(t('controls'))}</div>", unsafe_allow_html=True)
    with st.container(key="reset_btn"):
        if st.button(t("reset_demo"), use_container_width=True):
            simulator.simulate_and_store(seed=None, today_is_bad=True)
            db.clear_feedback()
            st.session_state.messages = []
            st.session_state.proactive_done = False
            st.session_state.feedback_given = {}
            st.session_state.daily_briefing = None
            st.session_state.daily_briefing_ts = None
            _reset_agent()
            st.toast(t("toast_reset"), icon="↻")
            st.rerun()

    # ---------------- Live Data Input ----------------
    with st.expander(t("live_data"), expanded=False):
        live_today = db.get_log_by_date(date.today().isoformat()) or {
            "heart_rate_avg": 72, "steps": 8000,
            "sleep_hours": 7.5, "calories_burned": 2000,
        }

        in_hr = st.number_input(
            t("hr_bpm"),
            min_value=40, max_value=220,
            value=int(live_today["heart_rate_avg"]), step=1,
        )
        in_steps = st.number_input(
            t("steps"),
            min_value=0, max_value=30000,
            value=int(live_today["steps"]), step=100,
        )
        in_sleep = st.number_input(
            t("sleep_h"),
            min_value=0.0, max_value=12.0,
            value=float(live_today["sleep_hours"]), step=0.1, format="%.1f",
        )
        in_cals = st.number_input(
            t("calories"),
            min_value=0, max_value=5000,
            value=int(live_today["calories_burned"]), step=50,
        )

        with st.container(key="inject_main"):
            if st.button(t("inject"), use_container_width=True):
                inject_today_reading(in_hr, in_steps, in_sleep, in_cals)
                st.toast(t("toast_inject"), icon="📡")
                st.rerun()

        st.markdown(
            f"<div class='inject-caption'>{_escape(t('inject_caption'))}</div>",
            unsafe_allow_html=True,
        )

        with st.container(key="inject_scen_hr"):
            if st.button(t("scen_hr"), use_container_width=True):
                inject_today_reading(
                    hr=118,
                    steps=int(live_today["steps"]),
                    sleep=float(live_today["sleep_hours"]),
                    cals=int(live_today["calories_burned"]),
                )
                st.toast(t("toast_hr"), icon="⚡")
                st.rerun()

        with st.container(key="inject_scen_workout"):
            if st.button(t("scen_workout"), use_container_width=True):
                inject_today_reading(
                    hr=142,
                    steps=int(live_today["steps"]) + 4500,
                    sleep=float(live_today["sleep_hours"]),
                    cals=int(live_today["calories_burned"]) + 380,
                )
                st.toast(t("toast_workout"), icon="🏃")
                st.rerun()

        with st.container(key="inject_scen_sleep"):
            if st.button(t("scen_sleep"), use_container_width=True):
                inject_today_reading(
                    hr=int(live_today["heart_rate_avg"]) + 12,
                    steps=int(live_today["steps"]),
                    sleep=3.8,
                    cals=int(live_today["calories_burned"]),
                )
                st.toast(t("toast_sleep"), icon="😴")
                st.rerun()

    st.caption(t("live_note"))


# =========================================================================
# Main area
# =========================================================================
# Top bar
st.markdown(
    "<div class='top-bar'>"
    f"<span class='brand'>HealthAgent</span>"
    f"<span class='brand-sub'>{_escape(t('brand_sub', d=format_header_date()))}</span>"
    f"<span class='live-indicator'><span class='pulse-dot'></span>{_escape(t('live_badge'))}</span>"
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
    f"<span>{_escape(t('dash_today'))}</span>"
    f"<span class='tag'>{_escape(t('tag_live'))}</span>"
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
        + metric_card_html(
            t("metric_hr"), str(today_log["heart_rate_avg"]), t("unit_bpm"),
            tiers["hr"], hr_arrow, hr_pct, hr_cls,
        )
        + metric_card_html(
            t("metric_steps"), f"{today_log['steps']:,}", "",
            tiers["steps"], steps_arrow, steps_pct, steps_cls,
        )
        + metric_card_html(
            t("metric_sleep"), f"{today_log['sleep_hours']:.1f}", t("unit_sleep_h"),
            tiers["sleep"], sleep_arrow, sleep_pct, sleep_cls,
        )
        + metric_card_html(
            t("metric_cal"), f"{today_log['calories_burned']:,}", t("unit_kcal"),
            tiers["calories"], cal_arrow, cal_pct, cal_cls,
        )
        + "</div>"
    )
    st.markdown(cards_html, unsafe_allow_html=True)

    # Vitals strip (real-time simulation)
    vitals_header_cols = st.columns([6, 1])
    with vitals_header_cols[0]:
        st.markdown(
            "<div class='section-head' style='margin-top:6px'>"
            f"<span>{_escape(t('vitals'))}</span>"
            f"<span class='tag'>{_escape(t('vitals_tag', t=datetime.now().strftime('%H:%M:%S'), n=st.session_state.vitals_refresh_tick))}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with vitals_header_cols[1]:
        with st.container(key="refresh_vitals"):
            if st.button(t("refresh"), use_container_width=True, key="btn_refresh_vitals"):
                st.session_state.vitals_refresh_tick += 1
                st.rerun()

    vitals = derive_vitals(today_log)
    st.markdown(vitals_strip_html(vitals), unsafe_allow_html=True)
else:
    st.info(t("no_today"))


# -------- Today's Summary --------
st.markdown(
    "<div class='section-head'>"
    f"<span>{_escape(t('summary'))}</span>"
    f"<span class='tag'>{_escape(t('tag_snapshot'))}</span>"
    "</div>",
    unsafe_allow_html=True,
)

if today_log:
    score, score_label, score_color = overall_score(today_log)
    highlights = highlight_items(today_log, yday_log)

    sum_l, sum_r = st.columns([1, 1.3], gap="medium")

    with sum_l:
        snapshot_html = (
            '<div class="summary-card">'
            f'<div style="font-size:10px;letter-spacing:0.18em;'
            f'text-transform:uppercase;color:{MUTED};font-weight:600;'
            f'margin-bottom:10px">{_escape(t("snapshot_label"))}</div>'
            f'<div class="summary-score" style="color:{score_color}">{score}</div>'
            f'<div class="summary-score-sub" style="color:{score_color}">{score_label}</div>'
            f'{highlights_html(highlights)}'
            '</div>'
        )
        st.markdown(snapshot_html, unsafe_allow_html=True)

    with sum_r:
        # Generate briefing on demand / once per session
        if (
            api_key_present
            and st.session_state.daily_briefing is None
        ):
            with st.spinner(t("gen_briefing")):
                st.session_state.daily_briefing = generate_daily_briefing()
                st.session_state.daily_briefing_ts = datetime.now().strftime("%H:%M")

        briefing_text = st.session_state.daily_briefing or (
            t("briefing_placeholder")
        )
        briefing_ts = st.session_state.daily_briefing_ts or "—"

        briefing_html = (
            '<div class="briefing-card">'
            '<div class="briefing-head">'
            f'<span class="briefing-title">{_escape(t("briefing_title"))}</span>'
            f'<span class="briefing-time">{_escape(t("updated"))} {briefing_ts}</span>'
            '</div>'
            f'<div class="briefing-body">{_escape(briefing_text)}</div>'
            '</div>'
        )
        st.markdown(briefing_html, unsafe_allow_html=True)

        refresh_cols = st.columns([1, 3])
        with refresh_cols[0]:
            with st.container(key="refresh_briefing"):
                if st.button(t("refresh_analysis"), use_container_width=True,
                             key="btn_refresh_briefing", disabled=not api_key_present):
                    st.session_state.daily_briefing = None
                    st.session_state.daily_briefing_ts = None
                    st.rerun()


# -------- Quick actions --------
st.markdown(
    "<div class='section-head'>"
    f"<span>{_escape(t('quick'))}</span>"
    f"<span class='tag'>{_escape(t('tag_quick'))}</span>"
    "</div>",
    unsafe_allow_html=True,
)
with st.container(key="qa_row"):
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button(t("qa1"), use_container_width=True, key="demo1"):
            st.session_state.pending_input = t("pending1")
    with qa2:
        if st.button(t("qa2"), use_container_width=True, key="demo2"):
            st.session_state.pending_input = t("pending2")
    with qa3:
        if st.button(t("qa3"), use_container_width=True, key="demo3"):
            st.session_state.pending_input = t("pending3")


# -------- Chat area --------
st.markdown(
    "<div class='section-head'>"
    f"<span>{_escape(t('chat_title'))}</span>"
    f"<span class='tag'>{_escape(t('tag_chat'))}</span>"
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
                t("tool_exp", n=len(msg["tool_calls"])), expanded=False
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
        msg_text = t("helpful") if already == 1 else t("adjusting")
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
                if st.button("▲", key=f"up_{msg_id}", help=t("help_up")):
                    tags = _tags_from_text(msg["content"])
                    memory.save_feedback(msg["content"][:240], 1, tags)
                    st.session_state.feedback_given[msg_id] = 1
                    st.rerun()
            with fc2:
                if st.button("▽", key=f"down_{msg_id}", help=t("help_down")):
                    tags = _tags_from_text(msg["content"])
                    memory.save_feedback(msg["content"][:240], -1, tags)
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
    with st.status(t("proactive"), expanded=True) as status:
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
            _record_telemetry("proactive", result)
            status.update(label=t("proactive_done"), state="complete", expanded=False)
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
user_input = st.chat_input(t("chat_ph"))

if st.session_state.pending_input and not user_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    if not api_key_present:
        st.error(t("err_key"))
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
        with st.status(t("proactive"), expanded=True) as status:
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
                _record_telemetry("chat", result)
                status.update(label=t("proactive_done"), state="complete", expanded=False)
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
