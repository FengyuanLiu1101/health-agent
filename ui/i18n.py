"""Bilingual UI strings for the Streamlit app (default: Chinese)."""
from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "side_sub": "Personal Health Intelligence",
        "openai_ok": "OpenAI Connected",
        "openai_missing": "No API Key",
        "openai_hint": "Add OPENAI_API_KEY to .env and restart.",
        "week_steps": "This Week · Steps",
        "trends": "Trend Indicators",
        "memory": "Memory",
        "profile": "Profile",
        "edit_profile": "Edit profile",
        "name": "Name",
        "age": "Age",
        "health_goal": "Health goal",
        "save": "Save",
        "toast_profile": "Profile updated",
        "controls": "Controls",
        "reset_demo": "↻  Reset Demo",
        "toast_reset": "Demo reset",
        "live_data": "📡 Live Data Input",
        "hr_bpm": "Heart Rate (bpm)",
        "steps": "Steps",
        "sleep_h": "Sleep Hours",
        "calories": "Calories",
        "inject": "🚨 Inject Live Reading",
        "toast_inject": "Live reading injected",
        "inject_caption": "Quick scenarios",
        "scen_hr": "⚡  Simulate High HR Alert",
        "toast_hr": "High HR scenario injected",
        "scen_workout": "🏃  Simulate Post-Workout",
        "toast_workout": "Post-workout scenario injected",
        "scen_sleep": "😴  Simulate Poor Sleep",
        "toast_sleep": "Poor-sleep scenario injected",
        "live_note": "Changes trigger live agent analysis",
        "lang_label": "Language",
        "disclaimer_title": "Notice",
        "disclaimer_body": (
            "This demo is not medical advice and does not diagnose or treat "
            "any condition. For health concerns, consult a qualified clinician."
        ),
        "telemetry_title": "Session telemetry",
        "telemetry_empty": "No model runs yet this session.",
        "telemetry_row": "{kind}: {tokens} tokens · {tools} tool calls",
        "brand_sub": "Personal Health Intelligence · {d}",
        "dash_today": "Today's Dashboard",
        "tag_live": "Live readings",
        "no_today": "No data for today yet. Click **Reset Demo** in the sidebar to simulate.",
        "vitals": "Real-Time Vitals",
        "vitals_tag": "Updated {t} · tick #{n}",
        "refresh": "↻ Refresh",
        "summary": "Today's Summary",
        "tag_snapshot": "Health snapshot + AI briefing",
        "snapshot_label": "Health Snapshot",
        "briefing_title": "AI Daily Briefing",
        "briefing_placeholder": "Daily briefing will appear once the AI coach is connected.",
        "updated": "Updated",
        "refresh_analysis": "↻ Refresh Analysis",
        "gen_briefing": "Generating daily briefing…",
        "quick": "Quick Analysis",
        "tag_quick": "One-click questions",
        "qa1": "◐  Why am I tired today?",
        "qa2": "◈  Weekly health review",
        "qa3": "◉  What to focus on next",
        "chat_title": "Agent Conversation",
        "tag_chat": "Grounded on your wearable data",
        "tool_exp": "▸ tool trace · {n} call(s)",
        "helpful": "▲ helpful",
        "adjusting": "▽ noted — adjusting",
        "proactive": "Agent is analyzing your data…",
        "proactive_done": "Analysis complete",
        "chat_ph": "Ask about your health, symptoms, or goals…",
        "err_key": "Please set OPENAI_API_KEY in .env and restart.",
        "warming": "Warming up the AI coach…",
        "indexing_kb": "Indexing knowledge base…",
        "kb_warn": "Knowledge base unavailable: {e}",
        "pending1": "Why do I feel tired today?",
        "pending2": "How was my health this week?",
        "pending3": "What should I focus on to improve?",
        "trend_hr": "Heart Rate",
        "trend_steps": "Steps",
        "trend_sleep": "Sleep",
        "trend_calories": "Calories",
        "trend_dir_improving": "improving",
        "trend_dir_declining": "declining",
        "trend_dir_stable": "stable",
        "lbl_avoid": "Avoiding",
        "lbl_prefer": "Prefers",
        "metric_hr": "Heart Rate",
        "metric_steps": "Steps",
        "metric_sleep": "Sleep",
        "metric_cal": "Calories",
        "unit_bpm": "bpm",
        "unit_sleep_h": "h",
        "unit_kcal": "kcal",
        "live_badge": "Live",
        "help_up": "Helpful",
        "help_down": "Not useful",
        "hl_sleep_bad": "Sleep {h:.1f}h — well below 7-9h target",
        "hl_sleep_low": "Sleep {h:.1f}h — slightly below target",
        "hl_sleep_ok": "Sleep {h:.1f}h — on target",
        "hl_hr_high": "Heart rate elevated at {hr} bpm",
        "hl_hr_mid": "Heart rate slightly elevated at {hr} bpm",
        "hl_hr_ok": "Resting HR healthy at {hr} bpm",
        "hl_steps_low": "Steps low at {s:,} — target 7,000-10,000",
        "hl_steps_mid": "Steps at {s:,} — below daily target",
        "hl_steps_ok": "Steps on track at {s:,}",
        "vital_live_hr": "Live HR",
        "vital_hrv": "HRV",
        "vital_recovery": "Recovery",
        "vital_readiness": "Readiness",
        "vital_sub_hr": "Resting pulse (today)",
        "vital_sub_hrv": "HRV (estimated from HR)",
        "vital_sub_rec": "Estimated · sleep + HR",
        "vital_sub_ready": "Estimated · demo composite",
    },
    "zh": {
        "side_sub": "个人健康智能助手",
        "openai_ok": "已连接 OpenAI",
        "openai_missing": "未配置 API Key",
        "openai_hint": "请在 .env 中设置 OPENAI_API_KEY 并重启应用。",
        "week_steps": "本周 · 步数",
        "trends": "趋势指标",
        "memory": "记忆",
        "profile": "个人资料",
        "edit_profile": "编辑资料",
        "name": "姓名",
        "age": "年龄",
        "health_goal": "健康目标",
        "save": "保存",
        "toast_profile": "资料已更新",
        "controls": "控制",
        "reset_demo": "↻  重置演示",
        "toast_reset": "演示已重置",
        "live_data": "📡 实时数据录入",
        "hr_bpm": "心率 (bpm)",
        "steps": "步数",
        "sleep_h": "睡眠 (小时)",
        "calories": "消耗热量",
        "inject": "🚨 写入今日读数",
        "toast_inject": "已写入今日数据",
        "inject_caption": "快捷场景",
        "scen_hr": "⚡  模拟高心率警报",
        "toast_hr": "已注入高心率场景",
        "scen_workout": "🏃  模拟运动后",
        "toast_workout": "已注入运动后场景",
        "scen_sleep": "😴  模拟睡眠不足",
        "toast_sleep": "已注入睡眠不足场景",
        "live_note": "修改后将触发智能体重新分析",
        "lang_label": "界面语言",
        "disclaimer_title": "提示",
        "disclaimer_body": (
            "本演示仅供学习参考，不构成医疗建议，也不能用于诊断或治疗。"
            "如有健康问题请咨询正规医疗机构。"
        ),
        "telemetry_title": "本会话用量",
        "telemetry_empty": "本会话尚未调用模型。",
        "telemetry_row": "{kind}：{tokens} tokens · {tools} 次工具调用",
        "brand_sub": "个人健康智能 · {d}",
        "dash_today": "今日看板",
        "tag_live": "实时读数",
        "no_today": "今日尚无数据。请在侧栏点击 **重置演示** 以生成模拟数据。",
        "vitals": "实时体征",
        "vitals_tag": "更新于 {t} · 第 {n} 次刷新",
        "refresh": "↻ 刷新",
        "summary": "今日摘要",
        "tag_snapshot": "健康快照 + AI 简报",
        "snapshot_label": "健康快照",
        "briefing_title": "AI 每日简报",
        "briefing_placeholder": "连接 AI 教练后将显示每日简报。",
        "updated": "更新于",
        "refresh_analysis": "↻ 刷新分析",
        "gen_briefing": "正在生成每日简报…",
        "quick": "快捷分析",
        "tag_quick": "一键提问",
        "qa1": "◐  今天为什么很累？",
        "qa2": "◈  本周健康回顾",
        "qa3": "◉  接下来应关注什么",
        "chat_title": "智能体对话",
        "tag_chat": "基于可穿戴数据",
        "tool_exp": "▸ 工具轨迹 · {n} 次调用",
        "helpful": "▲ 有帮助",
        "adjusting": "▽ 已记录，将调整建议",
        "proactive": "智能体正在分析你的数据…",
        "proactive_done": "分析完成",
        "chat_ph": "询问健康、症状或目标…",
        "err_key": "请在 .env 中设置 OPENAI_API_KEY 并重启。",
        "warming": "正在启动 AI 教练…",
        "indexing_kb": "正在构建知识库索引…",
        "kb_warn": "知识库不可用：{e}",
        "pending1": "我今天为什么觉得累？",
        "pending2": "我这周的健康情况怎么样？",
        "pending3": "接下来我应该重点改善什么？",
        "trend_hr": "心率",
        "trend_steps": "步数",
        "trend_sleep": "睡眠",
        "trend_calories": "热量",
        "trend_dir_improving": "改善中",
        "trend_dir_declining": "变差",
        "trend_dir_stable": "平稳",
        "lbl_avoid": "不喜欢的建议类型",
        "lbl_prefer": "偏好的建议类型",
        "metric_hr": "心率",
        "metric_steps": "步数",
        "metric_sleep": "睡眠",
        "metric_cal": "消耗热量",
        "unit_bpm": "次/分",
        "unit_sleep_h": "小时",
        "unit_kcal": "千卡",
        "live_badge": "实时",
        "help_up": "有帮助",
        "help_down": "用处不大",
        "hl_sleep_bad": "睡眠 {h:.1f} 小时 — 明显低于 7–9 小时目标",
        "hl_sleep_low": "睡眠 {h:.1f} 小时 — 略低于目标",
        "hl_sleep_ok": "睡眠 {h:.1f} 小时 — 达标",
        "hl_hr_high": "心率偏高：{hr} 次/分",
        "hl_hr_mid": "心率略高：{hr} 次/分",
        "hl_hr_ok": "静息心率良好：{hr} 次/分",
        "hl_steps_low": "步数偏低：{s:,} — 建议目标 7,000–10,000",
        "hl_steps_mid": "步数 {s:,} — 低于每日目标",
        "hl_steps_ok": "步数达标：{s:,}",
        "vital_live_hr": "实时心率",
        "vital_hrv": "心率变异性",
        "vital_recovery": "恢复度",
        "vital_readiness": "准备度",
        "vital_sub_hr": "今日静息心率",
        "vital_sub_hrv": "由心率估算的 HRV",
        "vital_sub_rec": "估算 · 睡眠与心率",
        "vital_sub_ready": "估算 · 演示综合指标",
    },
}


def _lang() -> str:
    return st.session_state.get("language", "zh")


def t(key: str, **kwargs: Any) -> str:
    table = _STRINGS.get(_lang(), _STRINGS["en"])
    s = table.get(key) or _STRINGS["en"].get(key, key)
    return s.format(**kwargs) if kwargs else s


def format_header_date() -> str:
    if _lang() == "zh":
        return date.today().strftime("%Y年%m月%d日")
    return date.today().strftime("%A, %b %d")


def trend_direction_label(direction: str) -> str:
    key = {
        "improving": "trend_dir_improving",
        "declining": "trend_dir_declining",
        "stable": "trend_dir_stable",
    }.get(direction, "trend_dir_stable")
    return t(key)


def briefing_prompt() -> str:
    if _lang() == "zh":
        return (
            "请用恰好三句话给出今日健康简报，并尽量引用具体数字。"
            "格式：第一句=总体状态；第二句=最需要关注的问题；"
            "第三句=一条最重要的行动建议。不要使用项目符号或小标题，不要开场白。"
        )
    return (
        "Give me a 3-sentence daily health briefing for today. Be specific with "
        "numbers. Format: sentence 1 = overall status, sentence 2 = biggest "
        "concern, sentence 3 = top recommendation. No bullets, no headers, "
        "no preamble."
    )
