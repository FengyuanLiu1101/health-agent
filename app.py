"""Streamlit UI for HealthAgent.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

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
# Page config & theme
# =========================================================================
st.set_page_config(
    page_title="HealthAgent",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#0A7C6C"
GOOD = "#1F8F5F"
WARN = "#E08E2B"
ALERT = "#C83A3A"
MUTED = "#6B7280"

st.markdown(
    f"""
    <style>
        .metric-card {{
            border-radius: 14px;
            padding: 14px 16px;
            border: 1px solid rgba(0,0,0,0.06);
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .metric-label {{
            font-size: 12px; color: {MUTED}; text-transform: uppercase; letter-spacing: .5px;
        }}
        .metric-value {{
            font-size: 28px; font-weight: 700; margin-top: 2px;
        }}
        .metric-sub {{
            font-size: 12px; color: {MUTED};
        }}
        .pill {{
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 11px; font-weight: 600;
        }}
        .pill-good {{ background: #E7F6ED; color: {GOOD}; }}
        .pill-warn {{ background: #FDF1E0; color: {WARN}; }}
        .pill-alert {{ background: #FBE7E7; color: {ALERT}; }}
        .app-title {{
            color: {PRIMARY}; font-weight: 800; letter-spacing: -.5px;
        }}
        .demo-btn button {{
            white-space: normal !important;
            height: auto !important;
            min-height: 56px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================================
# Data + agent bootstrapping
# =========================================================================
@st.cache_resource(show_spinner=False)
def _bootstrap_data():
    """Initialize DB and simulate health data on first run."""
    simulator.ensure_data_present()
    return True


@st.cache_resource(show_spinner="Building knowledge base index…")
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
    """Return one of 'good', 'warn', 'alert'."""
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


def _tier_pill(tier: str, label: str) -> str:
    cls = {"good": "pill-good", "warn": "pill-warn", "alert": "pill-alert"}[tier]
    return f'<span class="pill {cls}">{label}</span>'


def metric_card(col, label: str, value: str, sub: str, tier: str):
    color = _tier_color(tier)
    pill_label = {"good": "Good", "warn": "Watch", "alert": "Alert"}[tier]
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color}">{value}</div>
            <div class="metric-sub">{sub} &nbsp; {_tier_pill(tier, pill_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def today_tiers(log: dict) -> dict:
    return {
        "hr": _tier(log["heart_rate_avg"], (60, 85), warn_below=50, warn_above=95),
        "steps": _tier(log["steps"], (7000, 12000), warn_below=4000, warn_above=20000),
        "sleep": _tier(log["sleep_hours"], (7.0, 9.0), warn_below=5.5, warn_above=10.5),
        "calories": _tier(
            log["calories_burned"], (1800, 2500), warn_below=1500, warn_above=3000
        ),
    }


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
    """Small heuristic to bucket advice into a topic tag for feedback."""
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


# =========================================================================
# Session state
# =========================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {role, content, tool_calls?, id}
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "proactive_done" not in st.session_state:
    st.session_state.proactive_done = False
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}  # msg_id -> rating


# =========================================================================
# Sidebar — Reset + profile tweaks
# =========================================================================
with st.sidebar:
    st.markdown("<h2 class='app-title'>HealthAgent 🫀</h2>", unsafe_allow_html=True)
    st.caption("Your AI-powered daily health coach")

    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    if not api_key_present:
        st.error("OPENAI_API_KEY is not set. Add it to a `.env` file and restart.")
    else:
        st.success("OpenAI key detected")

    st.divider()
    if st.button("🔄 Reset Demo", use_container_width=True):
        simulator.simulate_and_store(seed=None, today_is_bad=True)
        db.clear_feedback()
        st.session_state.messages = []
        st.session_state.proactive_done = False
        st.session_state.feedback_given = {}
        _get_agent.clear()
        st.toast("Demo reset: data re-simulated, chat cleared.", icon="🔄")
        st.rerun()


# =========================================================================
# Layout
# =========================================================================
left, right = st.columns([3, 1], gap="large")


# ----- Right column: weekly view, trends, feedback explainer, profile -----
with right:
    rows = db.get_last_n_logs(7)
    st.markdown("#### 📈 This Week at a Glance")
    if rows:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%a")
        chart_df = df.set_index("date")[["steps"]]
        st.bar_chart(chart_df, color=PRIMARY, height=180)
    else:
        st.info("No data yet.")

    st.markdown("#### 📊 Trend Indicators")
    trends = _compute_trends(rows) if rows else {}
    trend_rows = [
        ("Heart Rate", trends.get("hr", "stable")),
        ("Steps", trends.get("steps", "stable")),
        ("Sleep", trends.get("sleep", "stable")),
        ("Calories", trends.get("calories", "stable")),
    ]
    for name, direction in trend_rows:
        color = _trend_color(direction)
        arrow = _trend_arrow(direction)
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:4px 0;'>"
            f"<span>{name}</span>"
            f"<span style='color:{color};font-weight:700'>{arrow} {direction}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### 👤 User Profile")
    with st.expander("Edit profile", expanded=False):
        profile = memory.get_profile()
        name = st.text_input("Name", value=profile.get("name", "Alex"))
        age = st.text_input("Age", value=str(profile.get("age", "28")))
        goal = st.text_area(
            "Health goal",
            value=profile.get("goal", "Improve sleep and maintain consistent exercise"),
            height=70,
        )
        if st.button("Save profile", use_container_width=True):
            memory.update_profile("name", name)
            memory.update_profile("age", age)
            memory.update_profile("goal", goal)
            st.toast("Profile updated", icon="✅")

        disliked = profile.get("disliked_advice_tags") or []
        if disliked:
            st.caption("Avoiding topics based on your feedback:")
            st.write(", ".join(disliked))


# ----- Left column: dashboard + chat -----
with left:
    st.markdown(
        f"<h1 class='app-title' style='margin-bottom:0'>HealthAgent 🫀</h1>"
        f"<p style='color:{MUTED};margin-top:4px'>Personalized insights from your wearable data</p>",
        unsafe_allow_html=True,
    )

    today_log = db.get_log_by_date(date.today().isoformat())
    if today_log:
        tiers = today_tiers(today_log)
        c1, c2, c3, c4 = st.columns(4)
        metric_card(
            c1, "Heart Rate", f"{today_log['heart_rate_avg']} bpm",
            "Normal 60-100", tiers["hr"],
        )
        metric_card(
            c2, "Steps", f"{today_log['steps']:,}",
            "Target 7,000-12,000", tiers["steps"],
        )
        metric_card(
            c3, "Sleep", f"{today_log['sleep_hours']:.1f} h",
            "Target 7-9 h", tiers["sleep"],
        )
        metric_card(
            c4, "Calories", f"{today_log['calories_burned']:,}",
            "Typical 1,800-2,500", tiers["calories"],
        )

    st.write("")

    # Demo scenario quick-start buttons
    st.markdown("##### 💡 Try a demo question")
    b1, b2, b3 = st.columns(3)
    with b1:
        with st.container():
            st.markdown("<div class='demo-btn'>", unsafe_allow_html=True)
            if st.button("🚨 Why do I feel tired today?", use_container_width=True, key="demo1"):
                st.session_state.pending_input = "Why do I feel tired today?"
            st.markdown("</div>", unsafe_allow_html=True)
    with b2:
        with st.container():
            st.markdown("<div class='demo-btn'>", unsafe_allow_html=True)
            if st.button("📊 How was my health this week?", use_container_width=True, key="demo2"):
                st.session_state.pending_input = "How was my health this week?"
            st.markdown("</div>", unsafe_allow_html=True)
    with b3:
        with st.container():
            st.markdown("<div class='demo-btn'>", unsafe_allow_html=True)
            if st.button("🎯 What should I focus on to improve?", use_container_width=True, key="demo3"):
                st.session_state.pending_input = "What should I focus on to improve?"
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # -------- Chat rendering --------
    def render_message(msg: dict, idx: int):
        role = msg["role"]
        with st.chat_message(role, avatar="🫀" if role == "assistant" else None):
            if msg.get("tool_calls"):
                with st.expander(f"🛠️ Tool calls ({len(msg['tool_calls'])})", expanded=False):
                    for tc in msg["tool_calls"]:
                        st.markdown(f"**{tc['tool']}**")
                        st.code(str(tc.get("input", ""))[:300] or "(no args)", language="json")
                        if tc.get("output"):
                            st.caption("Output (truncated):")
                            st.code(tc["output"], language="json")
            st.markdown(msg["content"])

            # Feedback buttons for assistant messages
            if role == "assistant":
                msg_id = msg.get("id", f"m{idx}")
                already = st.session_state.feedback_given.get(msg_id)
                if already:
                    emoji = "👍" if already == 1 else "👎"
                    st.caption(f"{emoji} Thanks! I'll adjust future advice.")
                else:
                    fc1, fc2, _ = st.columns([1, 1, 6])
                    with fc1:
                        if st.button("👍", key=f"up_{msg_id}"):
                            tag = _tag_from_text(msg["content"])
                            memory.save_feedback(msg["content"][:240], 1, tag)
                            st.session_state.feedback_given[msg_id] = 1
                            st.rerun()
                    with fc2:
                        if st.button("👎", key=f"down_{msg_id}"):
                            tag = _tag_from_text(msg["content"])
                            memory.save_feedback(msg["content"][:240], -1, tag)
                            st.session_state.feedback_given[msg_id] = -1
                            st.rerun()

    # Proactive check on first load
    if api_key_present and not st.session_state.proactive_done and not st.session_state.messages:
        _bootstrap_kb()
        agent = _get_agent()
        with st.chat_message("assistant", avatar="🫀"):
            with st.status("Agent is analyzing your health data…", expanded=True) as status:
                step_box = st.empty()
                steps_seen: list[str] = []

                def _on_step(tool_name, tool_input):
                    steps_seen.append(f"• **{tool_name}** `{str(tool_input)[:80]}`")
                    step_box.markdown("\n".join(steps_seen))

                try:
                    result = agent.proactive_check(on_step=_on_step)
                    status.update(label="Analysis complete", state="complete", expanded=False)
                except Exception as e:
                    status.update(label=f"Error: {e}", state="error")
                    result = {"output": f"Sorry, I hit an error: {e}", "tool_calls": []}
            st.markdown(result["output"])
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

    # -------- Input handling --------
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
            with st.chat_message("user"):
                st.markdown(user_input)

            _bootstrap_kb()
            agent = _get_agent()
            with st.chat_message("assistant", avatar="🫀"):
                with st.status("Agent is analyzing your health data…", expanded=True) as status:
                    step_box = st.empty()
                    steps_seen: list[str] = []

                    def _on_step(tool_name, tool_input):
                        steps_seen.append(f"• **{tool_name}** `{str(tool_input)[:80]}`")
                        step_box.markdown("\n".join(steps_seen))

                    try:
                        result = agent.chat(user_input, on_step=_on_step)
                        status.update(label="Analysis complete", state="complete", expanded=False)
                    except Exception as e:
                        status.update(label=f"Error: {e}", state="error")
                        result = {"output": f"Sorry, I hit an error: {e}", "tool_calls": []}
                st.markdown(result["output"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["output"],
                    "tool_calls": result.get("tool_calls", []),
                    "id": f"msg{len(st.session_state.messages)}",
                }
            )
            st.rerun()
