from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def text():
    return UI.read_text(encoding="utf-8-sig")


def test_a5j2_explainability_is_present_after_vietnamese_localization():
    value = text()
    assert "G1B_ENGLISH_PILOT01_A5J2A_AUDIT_EXPLAINABILITY" in value
    assert 'st.expander("5. Bằng chứng kiểm duyệt"' in value
    assert 'getattr(audit_result, "evidence", ())' in value
    assert 'getattr(item, "code", "")' in value
    assert 'getattr(item, "message", "")' in value

def test_a5j2_does_not_weaken_fail_save_block():
    value = text()
    assert "canonical_pass_100 = bool(canonical_field_rows) and all(" in value
    assert "admin_enforcement_pass = (" in value
    assert "release_allowed = (" in value
    assert "audit_blocks_save = not release_allowed" in value
    assert "disabled=(save_handler is None or not standardized_content)," in value
    assert "if audit_blocks_save:" in value
