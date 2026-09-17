from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def test_format_report_is_not_discarded_when_canonical_bundle_is_incomplete():
    text = UI.read_text(encoding="utf-8")
    assert "standardization_report = evidence_bundle.standardization_report" in text
    assert "if evidence_bundle.ready\n                        else None" not in text
    assert "MISSING_STANDARDIZATION_REPORT" in text


def test_admin_configuration_task_has_expected_actual_cause_and_resolution():
    text = UI.read_text(encoding="utf-8")
    assert "ACTIVE_CONFIGURATION_SNAPSHOT" in text
    assert "Bản chụp cấu hình ACTIVE bất biến" in text
    assert "**Yêu cầu:**" in text
    assert "**Dữ liệu thực tế:**" in text
    assert "Mã phiên bản ACTIVE" in text
    assert "Mã kiểm tra cấu hình" in text

def test_admin_configuration_evidence_uses_real_compliance_check():
    text = UI.read_text(encoding="utf-8")
    assert 'evidence_by_code.get("ACTIVE_CONFIGURATION_SNAPSHOT", {})' in text
    assert 'details={"CONFIG":' in text
    assert 'actual.get("global_version_id")' in text
    assert 'actual.get("configuration_hash")' in text


def test_success_message_is_not_shown_when_release_gate_is_blocked():
    text = UI.read_text(encoding="utf-8")
    assert '"level": "success" if release_status == "pass" else "error"' in text
    assert "Pipeline da tao DOCX; kiem duyet chua dat." in text
    assert "Luu, Tai xuong, Danh sach quan ly va Gop giao an van kha dung." in text
    assert "canonical_pass_100 = bool(canonical_field_rows) and all(" in text
    assert "admin_enforcement_pass = (" in text
    assert "release_allowed = (" in text
    assert "audit_blocks_save = not release_allowed" in text
