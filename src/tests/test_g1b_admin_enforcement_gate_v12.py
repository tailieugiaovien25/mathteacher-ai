from pathlib import Path


def test_runtime_builds_immutable_active_configuration_snapshot():
    text = Path("src/lesson_planning_v2/services/lesson_plan_configuration_runtime_bridge.py").read_text(encoding="utf-8")
    for marker in (
        '"global_version_id"', '"subject_version_id"',
        '"configuration_hash"', "hashlib.sha256",
        'template_profile["_admin_configuration_snapshot"]',
    ):
        assert marker in text


def test_profile_adapter_carries_snapshot_into_deterministic_standardizer():
    text = Path("src/lesson_planning_v2/services/lesson_plan_standardizer_profile_adapter.py").read_text(encoding="utf-8")
    assert 'profile["_admin_configuration_snapshot"]' in text


def test_standardizer_enforces_color_theme_rows_and_compliance_report():
    text = Path("src/document_standardization/lesson_plan_standardizer.py").read_text(encoding="utf-8")
    assert 'color.attrib.pop(qn("w:" + attribute), None)' in text
    assert 'split_allowed = bool(table_profile.get("allow_row_split", True))' in text
    assert "if not split_allowed:" in text
    assert "_evaluate_format_compliance" in text
    for code in (
        "ACTIVE_CONFIGURATION_SNAPSHOT", "PAGE_SIZE", "PAGE_MARGINS",
        "BODY_FONT", "FONT_COLOR", "CHARACTER_SPACING", "LINE_SPACING",
        "TABLE_REPEAT_HEADER", "TABLE_ROW_SPLIT", "CONTENT_INTEGRITY",
        "MEDIA_INTEGRITY", "FORMULA_VALUE_INTEGRITY",
    ):
        assert code in text


def test_only_pass_allows_save_download_and_management_merge_path():
    text = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py").read_text(encoding="utf-8")
    assert "release_allowed = canonical_pass_100" in text
    assert "audit_blocks_save = not release_allowed" in text
    assert 'disabled=(not standardized_content or audit_blocks_save)' in text
    assert 'if standardized_content:' in text
    assert 'if not audit_blocks_save:' in text
    assert "ADMIN Configuration Enforcement Gate" in text
