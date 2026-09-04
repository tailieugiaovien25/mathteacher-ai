from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def test_format_report_is_not_discarded_when_canonical_bundle_is_incomplete():
    text = UI.read_text(encoding="utf-8")
    assert "standardization_report = evidence_bundle.standardization_report" in text
    assert "if evidence_bundle.ready\n                        else None" not in text
    assert "MISSING_STANDARDIZATION_REPORT" in text


def test_admin_configuration_task_has_expected_actual_cause_and_resolution():
    text = UI.read_text(encoding="utf-8")
    assert "G1B_V14A_ADMIN_CONFIGURATION_DIAGNOSTIC" in text
    assert "Chi tiết nhiệm vụ 1: Cấu hình ADMIN" in text
    assert "Yêu cầu bắt buộc:" in text
    assert "Mã phiên bản ACTIVE" in text
    assert "Mã kiểm tra cấu hình" in text
    assert "Nguyên nhân: thiếu" in text
    assert "Giải pháp: ADMIN phải Publish/Activate" in text


def test_admin_configuration_evidence_uses_real_compliance_check():
    text = UI.read_text(encoding="utf-8")
    assert 'evidence_by_code.get("ACTIVE_CONFIGURATION_SNAPSHOT", {})' in text
    assert 'details={"CONFIG":' in text
    assert 'actual.get("global_version_id")' in text
    assert 'actual.get("configuration_hash")' in text


def test_success_message_is_not_shown_when_release_gate_is_blocked():
    text = UI.read_text(encoding="utf-8")
    assert '"level": "success" if release_status == "pass" else "error"' in text
    assert "Pipeline đã tạo DOCX nhưng cổng kiểm duyệt chưa đạt" in text
    assert "release_allowed = canonical_pass_100" in text
    assert "audit_blocks_save = not release_allowed" in text
