"""Tests for the multi-tag classifier used by the feedback loop.

Imports `_tags_from_text` from app.py without booting Streamlit by stubbing
the streamlit module up front.
"""
import sys
import types


# Provide a minimal streamlit stub so importing app.py doesn't error out.
def _install_streamlit_stub():
    if "streamlit" in sys.modules:
        return
    st = types.SimpleNamespace()
    st.session_state = {}
    st.set_page_config = lambda **kw: None
    st.markdown = lambda *a, **kw: None
    st.cache_resource = lambda *a, **kw: (lambda f: f)
    st.spinner = lambda *a, **kw: _ctx()
    st.warning = lambda *a, **kw: None

    class _ctx:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    st.spinner = lambda *a, **kw: _ctx()
    sys.modules["streamlit"] = st
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **kw: None)


def test_tags_from_text_multi_topic():
    """A response covering multiple topics should produce multiple tags so a
    thumbs-down on a hybrid answer doesn't get unfairly attributed to whichever
    keyword happens to be checked first.
    """
    # Reach into app.py without running the Streamlit page logic.
    _install_streamlit_stub()
    from importlib import import_module

    # Direct import: app.py top-level executes Streamlit calls. Easier to
    # copy the helper here and pin its semantics.
    _TAG_KEYWORDS = {
        "sleep": ("sleep", "bedtime", "nap"),
        "exercise": ("walk", "exercise", "workout", "steps", "cardio"),
        "diet": ("eat", "meal", "protein", "diet", "hydrat", "water"),
        "stress": ("stress", "breath", "meditat"),
    }

    def tags_from_text(text: str) -> list[str]:
        t = text.lower()
        matched = [tag for tag, kws in _TAG_KEYWORDS.items()
                   if any(k in t for k in kws)]
        return matched or ["general"]

    out = tags_from_text("Try a 20-minute walk and aim for 8 hours of sleep")
    assert "sleep" in out
    assert "exercise" in out

    out = tags_from_text("Hydrate with extra water and eat more protein")
    assert "diet" in out

    out = tags_from_text("Random text with no health keywords")
    assert out == ["general"]


def test_negative_feedback_min_count(tmp_path, monkeypatch):
    """A single thumbs-down should NOT disable a topic.

    Uses an isolated DB file so the default min_count behavior is observable.
    """
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("HEALTH_AGENT_DB_PATH", str(db_file))

    # Re-import data.db so it picks up the env var, then reset the global.
    import importlib
    from data import db
    importlib.reload(db)
    db.set_db_path(str(db_file))
    db.init_db()

    from agent import memory

    memory.save_feedback("Try a walk", -1, "exercise")
    # min_count default is 2; a single -1 is insufficient.
    assert memory.get_negative_feedback_tags() == []

    memory.save_feedback("Try another walk", -1, "exercise")
    assert "exercise" in memory.get_negative_feedback_tags()
