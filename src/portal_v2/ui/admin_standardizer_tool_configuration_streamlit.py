from __future__ import annotations

from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_admin_repository import (
    SupabaseLessonPlanConfigurationAdminRepository,
)
from lesson_planning_v2.services.lesson_plan_configuration_admin_service import (
    LessonPlanConfigurationAdminService,
)
from lesson_planning_v2.services.standardizer_tool_configuration_service import (
    COMMON_PROFILE_CODE,
    StandardizerToolConfigurationService,
)


ACTIONS = (
    "Tải giáo án", "Xem trước", "Chuẩn hóa định dạng", "Đề xuất bằng AI",
    "Kiểm tra toàn vẹn", "Lưu hệ thống", "Tải xuống", "Gộp giáo án",
)


def _save_draft(*, admin, service, profile, code, name, subject_ref, payload):
    if profile is None:
        return service.create_profile_with_initial_draft(
            profile_code=code, profile_name=name, subject_ref=subject_ref,
            configuration_payload=payload, change_note="ADMIN tool configuration",
        )[1]
    versions = admin.list_versions(profile_id=str(profile["profile_id"]))
    drafts = [row for row in versions if row.get("version_status") == "DRAFT"]
    if drafts:
        drafts.sort(key=lambda row: int(row.get("version_number") or 0), reverse=True)
        return service.update_draft(
            configuration_version_id=str(drafts[0]["configuration_version_id"]),
            configuration_payload=payload, change_note="ADMIN tool configuration",
        )
    return service.create_next_draft_version(
        profile_id=str(profile["profile_id"]), configuration_payload=payload,
        change_note="ADMIN tool configuration",
    )


def _publish_and_activate(st, *, admin, service, profile, key):
    if profile is None:
        return
    versions = admin.list_versions(profile_id=str(profile["profile_id"]))
    drafts = [row for row in versions if row.get("version_status") == "DRAFT"]
    if not drafts:
        st.caption("Không có phiên bản DRAFT chờ xuất bản.")
        return
    drafts.sort(key=lambda row: int(row.get("version_number") or 0), reverse=True)
    draft = drafts[0]
    if st.button("Xuất bản và áp dụng", key=key, use_container_width=True):
        published = service.publish(
            configuration_version_id=str(draft["configuration_version_id"])
        )
        service.activate_published_version(
            profile_id=str(profile["profile_id"]),
            configuration_version_id=str(published["configuration_version_id"]),
        )
        st.success("Đã xuất bản và áp dụng cấu hình công cụ.")
        st.rerun()


def render_admin_standardizer_tool_configuration(st, *, client) -> None:
    admin = SupabaseLessonPlanConfigurationAdminRepository(client)
    lifecycle = LessonPlanConfigurationAdminService(admin)
    resolver = StandardizerToolConfigurationService(admin)

    st.markdown("### III-A. Cấu hình Công cụ chuẩn giáo án chung")
    common = resolver.resolve().common_payload
    common_settings = dict(common.get("tool_common") or {})
    common_profile = next((row for row in admin.list_profiles() if row.get("profile_code") == COMMON_PROFILE_CODE), None)
    with st.form("standardizer_tool_common_form"):
        enabled = st.checkbox("Kích hoạt công cụ", value=bool(common_settings.get("enabled", True)))
        ai_enabled = st.checkbox("Cho phép AI hỗ trợ", value=bool(common_settings.get("ai_enabled", True)))
        allowed_actions = st.multiselect("Chức năng được phép", ACTIONS, default=common_settings.get("allowed_actions") or list(ACTIONS))
        confirmation_options = ["Bắt buộc", "Cảnh báo", "Không yêu cầu"]
        saved_confirmation = str(common_settings.get("confirmation_policy") or "Bắt buộc")
        confirmation = st.selectbox(
            "Xác nhận kết quả AI", confirmation_options,
            index=confirmation_options.index(saved_confirmation if saved_confirmation in confirmation_options else "Bắt buộc"),
        )
        integrity_gate = st.checkbox("Chặn lưu khi kiểm tra toàn vẹn thất bại", value=bool(common_settings.get("integrity_gate", True)), disabled=True)
        preserve_formula = st.checkbox("Giữ nguyên giá trị công thức Toán", value=True, disabled=True)
        system_instruction = st.text_area("Chỉ dẫn bắt buộc cho AI", value=str(common_settings.get("system_instruction") or "Tuân thủ cấu hình ADMIN và không thay đổi nội dung ngoài phạm vi được giao."))
        save_common = st.form_submit_button("💾 Lưu cấu hình III-A", type="primary", use_container_width=True)
    if save_common:
        _save_draft(admin=admin, service=lifecycle, profile=common_profile, code=COMMON_PROFILE_CODE, name="Công cụ chuẩn giáo án chung", subject_ref="", payload={
            "configuration_kind": "STANDARDIZER_TOOL", "tool_common": {
                "enabled": enabled, "ai_enabled": ai_enabled,
                "allowed_actions": list(allowed_actions), "confirmation_policy": confirmation,
                "integrity_gate": integrity_gate, "preserve_formula_value": preserve_formula,
                "system_instruction": system_instruction.strip(),
            },
        })
        st.success("Đã lưu cấu hình công cụ chung dưới dạng DRAFT.")
        st.rerun()
    _publish_and_activate(st, admin=admin, service=lifecycle, profile=common_profile, key="publish_standardizer_tool_common")

    st.markdown("### III-B. Cấu hình Công cụ chuẩn giáo án theo môn")
    subject_ref = st.text_input("Mã môn áp dụng", key="standardizer_tool_subject_ref").strip().upper()
    resolved = resolver.resolve(subject_ref=subject_ref)
    st.caption("Giá trị kế thừa từ Công cụ chung — chỉ đọc")
    st.json(dict(resolved.common_payload.get("tool_common") or {}))
    if not subject_ref:
        st.info("Nhập mã môn để mở bảng điều khiển chức năng riêng.")
        return
    subject_code = resolver.profile_code(subject_ref)
    subject_profile = next((row for row in admin.list_profiles() if row.get("profile_code") == subject_code), None)
    controls = dict(resolved.subject_payload.get("subject_controls") or {})
    common_actions = list((resolved.common_payload.get("tool_common") or {}).get("allowed_actions") or ACTIONS)
    with st.form("standardizer_tool_subject_form"):
        subject_enabled = st.checkbox("Kích hoạt công cụ cho môn " + subject_ref, value=bool(controls.get("enabled", True)))
        subject_actions = st.multiselect("Chức năng áp dụng cho môn", common_actions, default=controls.get("allowed_actions") or common_actions)
        subject_instruction = st.text_area("Chỉ dẫn AI riêng của môn", value=str(controls.get("subject_instruction") or ""))
        proposal_count = st.number_input("Số phương án AI tối đa", 1, 5, int(controls.get("proposal_count") or 2))
        require_review = st.checkbox("Bắt buộc giáo viên duyệt đề xuất AI", value=bool(controls.get("require_review", True)))
        save_subject = st.form_submit_button("💾 Lưu cấu hình III-B", type="primary", use_container_width=True)
    if save_subject:
        _save_draft(admin=admin, service=lifecycle, profile=subject_profile, code=subject_code, name="Công cụ chuẩn giáo án – " + subject_ref, subject_ref=subject_ref, payload={
            "configuration_kind": "STANDARDIZER_TOOL", "subject_controls": {
                "enabled": subject_enabled, "allowed_actions": list(subject_actions),
                "subject_instruction": subject_instruction.strip(),
                "proposal_count": int(proposal_count), "require_review": require_review,
            },
        })
        st.success("Đã lưu cấu hình công cụ theo môn dưới dạng DRAFT.")
        st.rerun()
    _publish_and_activate(st, admin=admin, service=lifecycle, profile=subject_profile, key="publish_standardizer_tool_subject_" + subject_ref)
