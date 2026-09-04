from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def text():
    return UI.read_text(encoding="utf-8-sig")


def test_a5j2_explainability_is_present_after_vietnamese_localization():
    value = text()
    assert "G1B_ENGLISH_PILOT01_A5J2A_AUDIT_EXPLAINABILITY" in value
    assert (
        'st.expander("Chi tiet kiem duyet"' in value
        or 'st.expander("B\\u1eb1ng ch\\u1ee9ng k\\u1ef9 thu\\u1eadt"' in value
    )
    assert 'getattr(audit_result, "evidence", ())' in value
    assert 'getattr(item, "code", "")' in value
    assert 'getattr(item, "message", "")' in value


def test_a5j2_does_not_weaken_fail_save_block():
    value = text()
    assert "release_allowed = canonical_pass_100" in value
    assert "audit_blocks_save = not release_allowed" in value
    assert (
        "save_handler=(None if audit_blocks_save else save_handler)" in value
        or "disabled=(save_handler is None or not standardized_content or audit_blocks_save)" in value
        or "disabled=(not standardized_content or audit_blocks_save)" in value
        or "if audit_blocks_save:" in value
    )
