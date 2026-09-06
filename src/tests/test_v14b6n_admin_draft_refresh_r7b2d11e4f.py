from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"


def _success_block() -> str:
    text = TARGET.read_text(encoding="utf-8")
    start = text.index(
        'st.success("Đã tạo phiên bản DRAFT mới.")'
    )
    end = text.index("draft_ids = [", start)
    return text[start:end]


def test_successful_draft_create_triggers_refresh():
    block = _success_block()
    assert "V14B6N_R7B2D11E4F_REFRESH_AFTER_DRAFT_CREATE" in block
    assert block.count("st.rerun()") == 1


def test_refresh_occurs_before_draft_ids_are_recomputed():
    text = TARGET.read_text(encoding="utf-8")
    success = text.index(
        'st.success("Đã tạo phiên bản DRAFT mới.")'
    )
    refresh = text.index("st.rerun()", success)
    draft_ids = text.index("draft_ids = [", success)
    assert success < refresh < draft_ids


def test_refresh_patch_has_no_publish_activate_or_direct_db_calls():
    block = _success_block()
    for forbidden in (
        "publish(",
        "activate_published_version(",
        ".insert(",
        ".update(",
        ".delete(",
    ):
        assert forbidden not in block
