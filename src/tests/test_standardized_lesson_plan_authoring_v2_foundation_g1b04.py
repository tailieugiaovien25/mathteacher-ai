from pathlib import Path

from portal_v2.ui.standardized_lesson_plan_authoring_v2_streamlit import (
    GROUP_CONTEXT_KEY,
    selected_group_context,
)


ROOT = Path(__file__).resolve().parents[2]
WEEKLY = (ROOT / "src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8")
PAGE = (ROOT / "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py").read_text(encoding="utf-8")


def test_weekly_selection_carries_complete_read_only_group_snapshot():
    assert "def _group_context_payload(group, *, client=None) -> dict:" in WEEKLY
    assert 'st.session_state["lesson_plan_group_context_v2"] = payload' in WEEKLY
    for token in ("group_id", "subject_ref", "grade", "lesson_title", "curriculum_periods", "occurrences"):
        assert f'"{token}"' in WEEKLY


def test_v2_page_is_isolated_and_group_driven():
    assert "render_standardized_lesson_plan_authoring_v2" in PAGE
    assert "Chọn tuần soạn" not in PAGE
    assert "Tìm và tải giáo án từ máy (.docx)" in PAGE
    assert "Xem trước giáo án gốc" in PAGE
    assert "Xem giáo án đã chuẩn" in PAGE
    assert r"Chu\u1ea9n h\u00f3a" in PAGE


def test_group_context_requires_stable_group_id():
    assert selected_group_context({}) is None
    assert selected_group_context({GROUP_CONTEXT_KEY: {"subject_ref": "ENG"}}) is None
    value = selected_group_context({GROUP_CONTEXT_KEY: {"group_id": "8TA003", "subject_ref": "ENG"}})
    assert value == {"group_id": "8TA003", "subject_ref": "ENG"}
