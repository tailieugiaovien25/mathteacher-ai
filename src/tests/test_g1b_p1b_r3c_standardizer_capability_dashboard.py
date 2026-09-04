from types import SimpleNamespace

from portal_v2.ui import admin_subject_coordination_workspace_streamlit as workspace


def _resolved(*, payload=None, snapshot=None):
    return SimpleNamespace(
        source="ADMIN" if snapshot is not None else "CURRENT_DEFAULT",
        snapshot=snapshot,
        configuration_payload=payload or {},
    )


def _by_name(rows):
    return {row["Tính năng"]: row for row in rows}


def test_r3c_dashboard_preserves_vietnamese_governance_states():
    rows = workspace._g1b_p1b_r3a_standardizer_capabilities(
        subject_ref="MATH",
        component_ref="ALGEBRA",
        status="OK",
        value=_resolved(),
    )
    mapped = _by_name(rows)

    assert mapped["Cấu hình Chuẩn hóa giáo án đang áp dụng"]["Trạng thái"] == "Theo cấu hình Môn/Phân môn"
    assert mapped["Nhận diện thông tin giáo án theo môn"]["Trạng thái"] == "Hoạt động một phần"
    assert mapped["Giữ nguyên bảng biểu và hình ảnh trong giáo án Word"]["Trạng thái"] == "Chức năng lõi dùng chung"
    assert mapped["Bảo toàn công thức Toán học (MathType/OLE)"]["Trạng thái"] == "Chức năng lõi dùng chung"
    assert mapped["Gộp nhiều giáo án đã chuẩn hóa"]["Trạng thái"] == "Chức năng lõi dùng chung"
    assert mapped["Xác nhận hoạt động thực tế theo môn"]["Trạng thái"] == "Chưa xác định"


def test_r3c_subject_effective_only_when_effective_payload_contains_setting():
    payload = {
        "template_profile": {"profile_name": "Mau Toan"},
        "date_policy": {"drafting_before_monday_enabled": True},
        "approval_policy": {"approval_label": "To CM duyet"},
        "document_repository": {"google_drive_lesson_plan_folder_id": "folder-123"},
    }
    rows = workspace._g1b_p1b_r3a_standardizer_capabilities(
        subject_ref="MATH",
        component_ref="ALGEBRA",
        status="OK",
        value=_resolved(payload=payload),
    )
    mapped = _by_name(rows)

    for name in (
        "Ngày soạn và ngày duyệt",
        "Khối phê duyệt của Tổ chuyên môn",
        "Mẫu và định dạng trình bày",
        "Thư mục lưu giáo án",
    ):
        assert mapped[name]["Trạng thái"] == "Theo cấu hình Môn/Phân môn"


def test_r3c_missing_effective_payload_stays_unknown():
    rows = workspace._g1b_p1b_r3a_standardizer_capabilities(
        subject_ref="ENGLISH",
        component_ref="",
        status="OK",
        value=_resolved(),
    )
    mapped = _by_name(rows)

    for name in (
        "Ngày soạn và ngày duyệt",
        "Khối phê duyệt của Tổ chuyên môn",
        "Mẫu và định dạng trình bày",
        "Thư mục lưu giáo án",
        "Xác nhận hoạt động thực tế theo môn",
    ):
        assert mapped[name]["Trạng thái"] == "Chưa xác định"


def test_r3c_resolver_failure_does_not_invent_ready():
    rows = workspace._g1b_p1b_r3a_standardizer_capabilities(
        subject_ref="ENGLISH",
        component_ref="",
        status="UNKNOWN",
        value="resolver unavailable",
    )
    mapped = _by_name(rows)
    assert mapped["Cấu hình Chuẩn hóa giáo án đang áp dụng"]["Trạng thái"] == "Chưa xác định"


def test_r3c_dashboard_source_has_no_runtime_bridge_or_write_call():
    text = workspace.__file__
    from pathlib import Path
    source = Path(text).read_text(encoding="utf-8-sig")
    helper = source.split("# G1B_P1B_R3A_STANDARDIZER_SUBJECT_CAPABILITY_DASHBOARD", 1)[1]
    helper = helper.split("def _render_grouping_effective", 1)[0]

    assert "apply_active_admin_lesson_plan_configuration(" not in helper
    assert ".upsert(" not in helper
    assert ".insert(" not in helper
    assert ".delete(" not in helper
    assert "LessonPlanMergeService(" not in helper
