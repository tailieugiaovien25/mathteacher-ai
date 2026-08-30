from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DIR = ROOT / "portal_v2/context"


def test_user_scoped_store_has_no_streamlit_dependency():
    text = (
        CONTEXT_DIR / "user_scoped_store.py"
    ).read_text(encoding="utf-8")
    assert "streamlit" not in text.lower()
    assert "session_state" not in text


def test_store_reuses_existing_contextchange_model():
    text = (
        CONTEXT_DIR / "user_scoped_store.py"
    ).read_text(encoding="utf-8")
    assert "from .models import ContextChange, SystemContext" in text
    assert "current=current" in text
    assert "change=change" in text
    assert "result.context" in text


def test_d2_does_not_modify_portal_navigation_yet():
    app = (
        ROOT.parent / "scripts/teacher_portal/app.py"
    ).read_text(encoding="utf-8-sig")
    assert 'key="portal_navigation"' in app
