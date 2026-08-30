from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts/teacher_portal/app.py"
WEEKLY = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_portal_navigation_radio_has_no_index_default():
    source = _text(APP)
    start = source.index("selected = st.sidebar.radio(")
    block = source[start:start + 600]
    assert 'key="portal_navigation"' in block
    assert "index=" not in block


def test_select_portal_page_emits_request_only():
    source = _text(APP)
    start = source.index("def select_portal_page(")
    end = source.index("def _resolve_portal_navigation_request(", start)
    block = source[start:end]
    assert 'session_state["portal_navigation_request"] = page' in block
    assert 'session_state["portal_page"] = page' not in block
    assert 'session_state["portal_navigation"] = page' not in block


def test_navigation_request_has_one_resolver():
    source = _text(APP)
    assert source.count('pop("portal_navigation_request", None)') == 1
    assert "def _resolve_portal_navigation_request(" in source


def test_weekly_navigation_uses_requests_not_widget_writes():
    source = _text(WEEKLY)
    assert 'st.session_state["portal_navigation"] =' not in source
    assert source.count('"portal_navigation_request"') == 3


def test_portal_page_stays_derived_after_widget_selection():
    source = _text(APP)
    assert 'st.session_state["portal_page"] = selected' in source


def test_widget_state_is_prepared_before_widget_without_default_index():
    source = _text(APP)
    assert 'st.session_state["portal_navigation"] = current_page' in source
    assert "index=PORTAL_PAGES.index(current_page)" not in source
