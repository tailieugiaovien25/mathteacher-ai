from pathlib import Path

from lesson_planning_v2.services.standardizer_tool_configuration_service import (
    COMMON_PROFILE_CODE,
    StandardizerToolConfigurationService,
)


class Repository:
    def list_profiles(self):
        return [
            {"profile_id": "g", "profile_code": COMMON_PROFILE_CODE, "lifecycle_status": "ACTIVE", "current_version_id": "gv"},
            {"profile_id": "m", "profile_code": "STANDARDIZER_TOOL::MATH", "lifecycle_status": "ACTIVE", "current_version_id": "mv"},
        ]

    def get_version(self, *, configuration_version_id):
        payloads = {
            "gv": {"configuration_kind": "STANDARDIZER_TOOL", "tool_common": {"ai_enabled": True, "allowed_actions": ["Xem trước", "Đề xuất bằng AI"]}},
            "mv": {"configuration_kind": "STANDARDIZER_TOOL", "subject_controls": {"allowed_actions": ["Xem trước", "Gộp giáo án"], "subject_instruction": "Toán"}},
        }
        return {"version_status": "PUBLISHED", "configuration_payload": payloads[configuration_version_id]}


def test_tool_subject_depends_only_on_common_tool_configuration():
    result = StandardizerToolConfigurationService(Repository()).resolve(subject_ref="MATH")
    assert result.common_payload["tool_common"]["ai_enabled"] is True
    assert result.effective_payload["subject_controls"]["allowed_actions"] == ["Xem trước"]
    assert result.effective_payload["subject_controls"]["subject_instruction"] == "Toán"
    assert "template_profile" not in result.effective_payload


def test_admin_page_wires_persistent_common_and_subject_tool_panels_once():
    center = Path("src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py").read_text(encoding="utf-8")
    panel = Path("src/portal_v2/ui/admin_standardizer_tool_configuration_streamlit.py").read_text(encoding="utf-8")
    assert center.count("render_admin_standardizer_tool_configuration(st, client=client)") == 1
    assert "III-A. Cấu hình Công cụ chuẩn giáo án chung" in panel
    assert "III-B. Cấu hình Công cụ chuẩn giáo án theo môn" in panel
    assert "Giá trị kế thừa từ Công cụ chung — chỉ đọc" in panel
    assert '"configuration_kind": "STANDARDIZER_TOOL"' in panel
    assert "Lưu cấu hình III-A" in panel and "Lưu cấu hình III-B" in panel
    assert "Xuất bản và áp dụng" in panel


def test_runtime_projects_tool_tree_separately_from_lesson_tree():
    bridge = Path("src/lesson_planning_v2/services/lesson_plan_configuration_runtime_bridge.py").read_text(encoding="utf-8")
    assert 'STANDARDIZER_TOOL_RUNTIME_PAYLOAD_KEY = "standardizer_tool_admin_runtime_configuration"' in bridge
    assert "_project_active_standardizer_tool_configuration" in bridge
