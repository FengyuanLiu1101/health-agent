"""Streamlit UI for HealthAgent — WHOOP-inspired dark premium theme.

Run with:
    streamlit run app.py

Only the visual layer is changed; all agent logic, tools, memory,
simulator, and feedback persistence remain identical.
"""
from __future__ import annotations

import html as _html
import os
from datetime import date

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
BG = "#0D0D0D"
SURFACE = "#1A1A1A"
BORDER = "#2A2A2A"
TEXT = "#E0E0E0"
MUTED = "#7A7A7A"
MUTED_DIM = "#4A4A4A"
ACCENT = "#C8F135"       # WHOOP lime
ACCENT_DIM = "#4A7C00"   # muted lime for tool trace
WARN = "#F5A623"
ALERT = "#FF4444"


# =========================================================================
# Global CSS — dark premium theme
# =========================================================================
st.markdown(
    f"""
    <style>
        /* ---------- Global reset ---------- */
        html, body, [data-testid="stAppViewContainer"], .stApp {{
            background-color: {BG} !important;
            color: {TEXT};
            font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
            font-feature-settings: "cv11", "ss01";
        }}
        * {{ color: {TEXT}; }}
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
            max-width: 1400px;
        }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
            height: 0 !important;
        }}
        footer, #MainMenu {{ visibility: hidden; }}

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background-color: #111111 !important;
            border-right: 1px solid {BORDER};
        }}
        section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem; }}

        /* ---------- Typography ---------- */
        h1, h2, h3, h4, h5, h6 {{ color: #FFFFFF; letter-spacing: -0.01em; }}
        p, span, div, li {{ color: {TEXT}; }}

        /* ---------- Top bar ---------- */
        .top-bar {{
            display: flex;
            align-items: baseline;
            gap: 20px;
            padding: 0 0 20px 0;
            border-bottom: 1px solid {BORDER};
            margin-bottom: 28px;
        }}
        .brand {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.22em;
            color: #FFFFFF;
            text-transform: uppercase;
        }}
        .brand-sub {{
            font-size: 10px;
            color: {MUTED};
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }}
        .live-indicator {{
            margin-left: auto;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 10px;
            color: {ACCENT};
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }}
        .pulse-dot {{
            width: 7px; height: 7px; border-radius: 50%;
            background: {ACCENT};
            box-shadow: 0 0 0 0 rgba(200,241,53,0.6);
            animation: ha-pulse 2s infinite;
            display: inline-block;
        }}
        @keyframes ha-pulse {{
            0%   {{ box-shadow: 0 0 0 0 rgba(200,241,53,0.55); }}
            70%  {{ box-shadow: 0 0 0 9px rgba(200,241,53,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(200,241,53,0); }}
        }}

        /* ---------- Metric cards ---------- */
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 28px;
        }}
        .metric-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 18px 20px 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 120px;
        }}
        .metric-label {{
            font-size: 10px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: {MUTED};
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 48px;
            font-weight: 300;
            line-height: 1;
            color: #FFFFFF;
            letter-spacing: -0.02em;
        }}
        .metric-unit {{
            font-size: 18px;
            color: {MUTED};
            font-weight: 400;
            margin-left: 6px;
        }}
        .metric-status {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: {MUTED};
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        .status-dot {{
            width: 7px; height: 7px; border-radius: 50%;
            display: inline-block;
        }}

        /* ---------- Section headers ---------- */
        .section-head {{
            font-size: 10px;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: {MUTED};
            font-weight: 600;
            margin: 24px 0 12px 0;
        }}

        /* ---------- Quick action buttons ---------- */
        .st-key-qa_row .stButton > button {{
            background: {SURFACE} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid transparent !important;
            border-radius: 8px !important;
            padding: 14px 16px !important;
            font-size: 13px !important;
            font-weight: 400 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            min-height: 64px !important;
            transition: all 0.18s ease !important;
            box-shadow: none !important;
        }}
        .st-key-qa_row .stButton > button p {{
            color: {TEXT} !important;
            text-align: left !important;
        }}
        .st-key-qa_row .stButton > button:hover {{
            border-left: 3px solid {ACCENT} !important;
            color: #FFFFFF !important;
            background: #202020 !important;
        }}
        .st-key-qa_row .stButton > button:hover p {{ color: #FFFFFF !important; }}

        /* ---------- Reset demo button (sidebar) ---------- */
        .st-key-reset_btn .stButton > button {{
            background: transparent !important;
            color: {ACCENT} !important;
            border: 1px solid {ACCENT} !important;
            border-radius: 8px !important;
            font-size: 11px !important;
            letter-spacing: 0.2em !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            box-shadow: none !important;
        }}
        .st-key-reset_btn .stButton > button p {{
            color: {ACCENT} !important;
            letter-spacing: 0.2em !important;
        }}
        .st-key-reset_btn .stButton > button:hover {{
            background: rgba(200,241,53,0.08) !important;
        }}

        /* ---------- Profile save button ---------- */
        .st-key-save_profile .stButton > button {{
            background: transparent !important;
            color: {ACCENT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 6px !important;
            font-size: 11px !important;
            letter-spacing: 0.16em !important;
            text-transform: uppercase !important;
        }}

        /* ---------- Feedback buttons ---------- */
        [class*="st-key-fb_"] .stButton > button {{
            background: transparent !important;
            border: none !important;
            color: {MUTED_DIM} !important;
            font-size: 14px !important;
            padding: 2px 8px !important;
            min-height: 0 !important;
            box-shadow: none !important;
            transition: color 0.15s ease !important;
        }}
        [class*="st-key-fb_"] .stButton > button:hover {{
            color: {ACCENT} !important;
            background: transparent !important;
        }}

        /* ---------- Chat messages ---------- */
        .user-msg {{
            text-align: right;
            color: #FFFFFF;
            font-size: 15px;
            line-height: 1.5;
            margin: 18px 0 18px auto;
            max-width: 75%;
            padding: 6px 0;
        }}
        .agent-msg {{
            background: {SURFACE};
            border-left: 2px solid {ACCENT};
            border-radius: 4px;
            padding: 16px 20px;
            margin: 14px 0 6px 0;
            font-size: 14px;
            line-height: 1.6;
        }}
        .agent-msg p, .agent-msg li {{
            color: {TEXT} !important;
            margin-bottom: 8px;
        }}
        .agent-msg strong {{ color: #FFFFFF; }}
        .agent-msg ul {{ padding-left: 18px; margin: 6px 0; }}

        /* ---------- Tool trace expander ---------- */
        [class*="st-key-tt_"] details {{
            background: transparent !important;
            border: none !important;
        }}
        [class*="st-key-tt_"] summary {{
            font-family: 'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace !important;
            font-size: 11px !important;
            color: {ACCENT_DIM} !important;
            letter-spacing: 0.08em !important;
            padding: 6px 0 !important;
        }}
        .tool-trace {{
            font-family: 'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace;
            font-size: 11px;
            color: {ACCENT_DIM};
            padding: 4px 0 4px 12px;
            border-left: 1px solid {BORDER};
            margin: 2px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .tool-trace .tk {{ color: {ACCENT}; }}

        /* ---------- Chat input ---------- */
        [data-testid="stChatInput"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
            transition: border-color 0.18s ease !important;
        }}
        [data-testid="stChatInput"]:focus-within {{
            border: 1px solid {ACCENT} !important;
            box-shadow: 0 0 0 3px rgba(200,241,53,0.08);
        }}
        [data-testid="stChatInput"] textarea {{
            background: transparent !important;
            color: {TEXT} !important;
            font-size: 14px !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{
            color: {MUTED_DIM} !important;
        }}
        [data-testid="stChatInput"] button {{
            background: {ACCENT} !important;
            border: none !important;
            border-radius: 50% !important;
            color: #0D0D0D !important;
            width: 34px !important; height: 34px !important;
        }}
        [data-testid="stChatInput"] button svg {{ color: #0D0D0D !important; fill: #0D0D0D !important; }}

        /* ---------- Bar chart (custom) ---------- */
        .bar-chart {{
            display: flex;
            align-items: flex-end;
            gap: 6px;
            height: 140px;
            padding: 8px 4px;
            border-bottom: 1px solid {BORDER};
        }}
        .bar-col {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            height: 100%;
            gap: 6px;
        }}
        .bar {{
            width: 100%;
            border-radius: 2px;
            min-height: 2px;
            transition: background 0.2s ease;
        }}
        .bar-label {{
            font-size: 10px;
            color: {MUTED};
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        .bar-label.active {{ color: {ACCENT}; }}

        /* ---------- Trend rows ---------- */
        .trend-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid {BORDER};
            font-size: 13px;
        }}
        .trend-row:last-child {{ border-bottom: none; }}
        .trend-name {{ color: {TEXT}; }}
        .trend-val {{
            display: inline-flex; align-items: center; gap: 8px;
            font-size: 11px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
        }}

        /* ---------- Profile / key-value list ---------- */
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

        /* ---------- Sidebar status ---------- */
        .side-status {{
            display: inline-flex; align-items: center; gap: 10px;
            font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase;
            color: {ACCENT};
            font-weight: 600;
        }}
        .side-status.off {{ color: {ALERT}; }}
        .side-head {{
            font-size: 14px; font-weight: 700; letter-spacing: 0.22em;
            color: #FFFFFF; text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .side-sub {{
            font-size: 10px; color: {MUTED}; letter-spacing: 0.18em;
            text-transform: uppercase; margin-bottom: 24px;
        }}

        /* ---------- Streamlit expanders (generic) ---------- */
        [data-testid="stExpander"] {{
            background: transparent !important;
            border: 1px solid {BORDER} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stExpander"] summary {{ color: {MUTED} !important; }}

        /* ---------- Status widget (agent thinking) ---------- */
        [data-testid="stStatusWidget"], div[data-testid="stStatus"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 8px !important;
        }}

        /* ---------- Text inputs / areas ---------- */
        input, textarea {{
            background: {SURFACE} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 6px !important;
        }}
        input:focus, textarea:focus {{
            border-color: {ACCENT} !important;
            outline: none !important;
        }}
        label {{ color: {MUTED} !important; font-size: 11px !important;
                letter-spacing: 0.14em !important; text-transform: uppercase !important; }}

        /* ---------- Dividers ---------- */
        hr {{ border-color: {BORDER} !important; }}

        /* ---------- Toast ---------- */
        [data-testid="stToast"] {{
            background: {SURFACE} !important;
            border: 1px solid {ACCENT} !important;
            color: {TEXT} !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================================
# Data + agent bootstrapping (unchanged)
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
# Helpers
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
    return {"good": ACCENT, "warn": WARN, "alert": ALERT}[tier]


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


def metric_card_html(label: str, value: str, unit: str, tier: str) -> str:
    color = _tier_color(tier)
    status = _tier_label(tier)
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div>
            <span class="metric-value">{value}</span><span class="metric-unit">{unit}</span>
        </div>
        <div class="metric-status">
            <span class="status-dot" style="background:{color}"></span>
            <span style="color:{color}">{status}</span>
        </div>
    </div>
    """


def _trend_arrow(direction: str) -> str:
    return {"improving": "↑", "declining": "↓", "stable": "→"}.get(direction, "→")


def _trend_color(direction: str) -> str:
    return {"improving": ACCENT, "declining": ALERT, "stable": MUTED}.get(direction, MUTED)


def _compute_trends(rows: list[dict]) -> dict:
    if len(rows) < 2:
        return {k: "stable" for k in ["hr", "steps", "sleep", "calories"]}

    def direction(vals, invert=False) -> str:
        mid = len(vals) // 2
        a = sum(vals[:mid]) / max(1, mid)
        b = sum(vals[mid:]) / max(1, len(vals) - mid)
        if a == 0:
            return "stable"
        delta = (b - a) / abs(a)
        if delta > 0.05:
            return "declining" if invert else "improving"
        if delta < -0.05:
            return "improving" if invert else "declining"
        return "stable"

    return {
        "hr": direction([r["heart_rate_avg"] for r in rows], invert=True),
        "steps": direction([r["steps"] for r in rows]),
        "sleep": direction([r["sleep_hours"] for r in rows]),
        "calories": direction([r["calories_burned"] for r in rows]),
    }


def _tag_from_text(text: str) -> str:
    t = text.lower()
    if "sleep" in t or "bedtime" in t or "nap" in t:
        return "sleep"
    if "walk" in t or "exercise" in t or "workout" in t or "steps" in t or "cardio" in t:
        return "exercise"
    if "eat" in t or "meal" in t or "protein" in t or "diet" in t or "hydrat" in t or "water" in t:
        return "diet"
    if "stress" in t or "breath" in t or "meditat" in t:
        return "stress"
    return "general"


def bar_chart_html(rows: list[dict]) -> str:
    if not rows:
        return '<div class="bar-chart"></div>'
    today_iso = date.today().isoformat()
    max_steps = max(r["steps"] for r in rows) or 1
    cols = []
    for r in rows:
        pct = max(4.0, (r["steps"] / max_steps) * 100)
        is_today = r["date"] == today_iso
        color = ACCENT if is_today else "#2F2F2F"
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
        f'<span class="trend-name">{name}</span>'
        f'<span class="trend-val" style="color:{color}">{arrow}&nbsp;{direction}</span>'
        f"</div>"
    )


# =========================================================================
# Session state (unchanged)
# =========================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "proactive_done" not in st.session_state:
    st.session_state.proactive_done = False
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}


# =========================================================================
# Sidebar
# =========================================================================
with st.sidebar:
    st.markdown(
        "<div class='side-head'>HEALTHAGENT</div>"
        "<div class='side-sub'>AI Health Intelligence</div>",
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
            "<span class='status-dot' style='background:#FF4444'></span>No API Key"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Add OPENAI_API_KEY to .env and restart.")

    st.markdown("<div class='section-head'>Controls</div>", unsafe_allow_html=True)
    with st.container(key="reset_btn"):
        if st.button("↻  Reset Demo", use_container_width=True):
            simulator.simulate_and_store(seed=None, today_is_bad=True)
            db.clear_feedback()
            st.session_state.messages = []
            st.session_state.proactive_done = False
            st.session_state.feedback_given = {}
            _get_agent.clear()
            st.toast("Demo reset", icon="↻")
            st.rerun()

    st.markdown("<div class='section-head'>Profile</div>", unsafe_allow_html=True)
    with st.expander("Edit profile", expanded=False):
        profile = memory.get_profile()
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

        disliked = profile.get("disliked_advice_tags") or []
        if disliked:
            st.caption("Avoiding: " + ", ".join(disliked))


# =========================================================================
# Main layout
# =========================================================================
left, right = st.columns([3, 1], gap="large")

# ---------------- Left column ----------------
with left:
    # Top bar
    st.markdown(
        "<div class='top-bar'>"
        "<span class='brand'>HEALTHAGENT</span>"
        "<span class='brand-sub'>Personal Health Intelligence</span>"
        "<span class='live-indicator'><span class='pulse-dot'></span>Live</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Metric cards
    today_log = db.get_log_by_date(date.today().isoformat())
    if today_log:
        tiers = today_tiers(today_log)
        cards_html = (
            "<div class='metric-grid'>"
            + metric_card_html("Heart Rate", str(today_log["heart_rate_avg"]), "bpm", tiers["hr"])
            + metric_card_html("Steps", f"{today_log['steps']:,}", "", tiers["steps"])
            + metric_card_html("Sleep", f"{today_log['sleep_hours']:.1f}", "hr", tiers["sleep"])
            + metric_card_html("Calories", f"{today_log['calories_burned']:,}", "kcal", tiers["calories"])
            + "</div>"
        )
        st.markdown(cards_html, unsafe_allow_html=True)

    # Quick actions
    st.markdown("<div class='section-head'>Quick Analysis</div>", unsafe_allow_html=True)
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

    st.markdown("<div class='section-head'>Agent Conversation</div>", unsafe_allow_html=True)

    # ---------------- Chat rendering ----------------
    def _escape(s: str) -> str:
        return _html.escape(str(s), quote=False)

    def render_user_message(content: str):
        st.markdown(
            f"<div class='user-msg'>{_escape(content)}</div>",
            unsafe_allow_html=True,
        )

    def render_agent_message(msg: dict, idx: int):
        content = msg["content"] or ""
        # Agent card with markdown content. Blank lines around content allow
        # Streamlit's markdown parser to render bullets/bold inside the div.
        st.markdown(
            f"<div class='agent-msg'>\n\n{content}\n\n</div>",
            unsafe_allow_html=True,
        )

        # Tool trace (collapsed by default)
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

        # Feedback
        already = st.session_state.feedback_given.get(msg_id)
        if already:
            emoji = "▲ helpful" if already == 1 else "▽ noted — adjusting"
            st.markdown(
                f"<div style='color:{ACCENT_DIM};font-size:11px;"
                f"letter-spacing:0.14em;text-transform:uppercase;margin:4px 0 18px 0;'>"
                f"{emoji}</div>",
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

    # Render prior history
    for i, m in enumerate(st.session_state.messages):
        render_message(m, i)

    # ---------------- Input ----------------
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


# ---------------- Right column ----------------
with right:
    rows = db.get_last_n_logs(7)

    st.markdown("<div class='section-head'>This Week · Steps</div>", unsafe_allow_html=True)
    st.markdown(bar_chart_html(rows), unsafe_allow_html=True)

    st.markdown("<div class='section-head'>Trend Indicators</div>", unsafe_allow_html=True)
    trends = _compute_trends(rows) if rows else {}
    trend_block = "".join(
        [
            trend_row_html("Heart Rate", trends.get("hr", "stable")),
            trend_row_html("Steps", trends.get("steps", "stable")),
            trend_row_html("Sleep", trends.get("sleep", "stable")),
            trend_row_html("Calories", trends.get("calories", "stable")),
        ]
    )
    st.markdown(trend_block, unsafe_allow_html=True)

    # Memory / profile snapshot
    profile = memory.get_profile()
    st.markdown("<div class='section-head'>Memory</div>", unsafe_allow_html=True)
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
