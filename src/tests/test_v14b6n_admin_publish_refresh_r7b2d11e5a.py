from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"


def _publish_success_block() -> str:
    text = TARGET.read_text(encoding="utf-8")
    start = text.index(
        'st.success("Phiên bản đã chuyển sang PUBLISHED.")'
    )
    end = text.index("published_ids = [", start)
    return text[start:end]


def test_successful_publish_triggers_exactly_one_refresh():
    block = _publish_success_block()
    assert "V14B6N_R7B2D11E5A_REFRESH_AFTER_PUBLISH" in block
    assert block.count("st.rerun()") == 1


def test_refresh_occurs_before_published_ids_are_recomputed():
    text = TARGET.read_text(encoding="utf-8")
    success = text.index(
        'st.success("Phiên bản đã chuyển sang PUBLISHED.")'
    )
    refresh = text.index("st.rerun()", success)
    published_ids = text.index("published_ids = [", success)
    assert success < refresh < published_ids


def test_refresh_patch_has_no_publish_activate_or_direct_db_calls():
    block = _publish_success_block()
    for forbidden in (
        "activate_published_version(",
        ".insert(",
        ".update(",
        ".delete(",
    ):
        assert forbidden not in block
