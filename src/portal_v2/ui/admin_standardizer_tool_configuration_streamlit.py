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


def _show_configuration_storage_error(st, error: Exception) -> None:
    message = str(error)
    normalized = message.lower()
    if (
        "pgrst205" in normalized
        or "lesson_plan_configuration_profiles" in normalized
        or "lesson_plan_configuration_versions" in normalized
    ):
        st.error("Cơ sở dữ liệu chưa sẵn sàng cho cấu hình công cụ chuẩn hóa.")
        st.caption("Cần quản trị hệ thống kiểm tra kết nối dữ liệu cấu hình.")
    else:
        st.error("Không thể tải cấu hình công cụ chuẩn hóa.")
    with st.expander("Thông tin dành cho hỗ trợ kỹ thuật"):
        st.caption("Mã lỗi đã được ghi nhận để quản trị hệ thống xử lý.")


def _save_and_activate(*, service, profile, code, name, subject_ref, payload):
    if profile is None:
        profile, draft = service.create_profile_with_initial_draft(
            profile_code=code, profile_name=name, subject_ref=subject_ref,
            configuration_payload=payload, change_note="ADMIN tool configuration",
        )
        published = service.publish(
            configuration_version_id=str(draft.get("configuration_version_id") or "")
        )
        return service.activate_published_version(
            profile_id=str(profile["profile_id"]),
            configuration_version_id=str(published["configuration_version_id"]),
        )
    return service.save_and_activate(
        profile_id=str(profile["profile_id"]),
        configuration_payload=payload,
        change_note="ADMIN tool configuration",
    )


def render_admin_standardizer_tool_configuration(st, *, client) -> None:
    admin = SupabaseLessonPlanConfigurationAdminRepository(client)
    lifecycle = LessonPlanConfigurationAdminService(admin)
    resolver = StandardizerToolConfigurationService(admin)

    st.markdown("### Bật và chọn chức năng dùng chung")
    try:
        profiles = admin.list_profiles()
        common = resolver.resolve().common_payload
    except Exception as error:
        _show_configuration_storage_error(st, error)
        return

    common_settings = dict(common.get("tool_common") or {})
    common_profile = next(
        (
            row
            for row in profiles
            if row.get("profile_code") == COMMON_PROFILE_CODE
        ),
        None,
    )
    st.caption("Chọn các chức năng bằng ô đánh dấu. Nhấn Lưu để áp dụng ngay.")
    with st.form("standardizer_tool_common_form"):
        enabled = st.checkbox("Kích hoạt công cụ", value=bool(common_settings.get("enabled", True)))
        ai_enabled = st.checkbox("Cho phép AI hỗ trợ", value=bool(common_settings.get("ai_enabled", True)))
        saved_actions = common_settings.get("allowed_actions")
        if not isinstance(saved_actions, list):
            saved_actions = list(ACTIONS)
        selected_actions = set(item for item in saved_actions if item in ACTIONS)
        st.markdown("**Chức năng được phép**")
        action_columns = st.columns(2)
        allowed_actions = []
        for index, action in enumerate(ACTIONS):
            if action_columns[index % 2].checkbox(
                action,
                value=action in selected_actions,
                key="standardizer_tool_common_action_" + str(index),
            ):
                allowed_actions.append(action)
        confirmation_options = ["Bắt buộc", "Cảnh báo", "Không yêu cầu"]
        saved_confirmation = str(common_settings.get("confirmation_policy") or "Bắt buộc")
        confirmation = st.selectbox(
            "Xác nhận kết quả AI", confirmation_options,
            index=confirmation_options.index(saved_confirmation if saved_confirmation in confirmation_options else "Bắt buộc"),
        )
        integrity_gate = st.checkbox("Chặn lưu khi kiểm tra toàn vẹn thất bại", value=bool(common_settings.get("integrity_gate", True)), disabled=True)
        preserve_formula = st.checkbox("Giữ nguyên giá trị công thức Toán", value=True, disabled=True)
        system_instruction = "Tuân thủ cấu hình ADMIN và không thay đổi nội dung ngoài phạm vi được giao."
        st.caption("AI luôn tuân thủ cấu hình ADMIN và không tự sửa nội dung giáo án.")
        save_common = st.form_submit_button("💾 Lưu", type="primary", use_container_width=True)
    if save_common:
        try:
            _save_and_activate(service=lifecycle, profile=common_profile, code=COMMON_PROFILE_CODE, name="Công cụ chuẩn giáo án chung", subject_ref="", payload={
                "configuration_kind": "STANDARDIZER_TOOL", "tool_common": {
                    "enabled": enabled, "ai_enabled": ai_enabled,
                    "allowed_actions": list(allowed_actions), "confirmation_policy": confirmation,
                    "integrity_gate": integrity_gate, "preserve_formula_value": preserve_formula,
                    "system_instruction": system_instruction.strip(),
                },
            })
        except Exception as error:
            _show_configuration_storage_error(st, error)
            return
        st.success("Đã lưu và áp dụng cấu hình công cụ chung ngay.")
        st.rerun()

    st.markdown("### Chọn chức năng theo môn")
    try:
        from portal_v2.ui.admin_lesson_plan_coordination_center_streamlit import (
            _load_canonical_lesson_plan_scope_catalog,
        )

        subjects, _ = _load_canonical_lesson_plan_scope_catalog(client=client)
    except Exception as error:
        _show_configuration_storage_error(st, error)
        return
    subject_options = {"": "Dùng thiết lập chung cho mọi môn"}
    for subject in subjects:
        subject_code = str(getattr(subject, "code", "") or "").strip().upper()
        if subject_code:
            subject_name = str(getattr(subject, "name", "") or subject_code).strip()
            subject_options[subject_code] = subject_name
    subject_ref = st.selectbox(
        "Môn học",
        options=list(subject_options),
        format_func=lambda value: subject_options.get(value, value),
        key="standardizer_tool_subject_ref_choice",
        help="Chọn tên môn; mã kỹ thuật được hệ thống tự xác định.",
    )
    try:
        resolved = resolver.resolve(subject_ref=subject_ref)
    except Exception as error:
        _show_configuration_storage_error(st, error)
        return
    inherited_actions = list(
        (resolved.common_payload.get("tool_common") or {}).get("allowed_actions", ACTIONS)
    )
    inherited_actions = [item for item in inherited_actions if item in ACTIONS]
    st.caption("Thiết lập chung đang cho phép: " + (", ".join(inherited_actions) or "chưa chọn chức năng"))
    if not subject_ref:
        st.info("Chọn một môn cụ thể ở trên để thiết lập quyền dùng riêng cho môn đó.")
        return
    subject_code = resolver.profile_code(subject_ref)
    subject_profile = next(
        (
            row
            for row in profiles
            if row.get("profile_code") == subject_code
        ),
        None,
    )
    controls = dict(resolved.subject_payload.get("subject_controls") or {})
    common_actions = list((resolved.common_payload.get("tool_common") or {}).get("allowed_actions", ACTIONS))
    common_actions = [item for item in common_actions if item in ACTIONS]
    saved_subject_actions = controls.get("allowed_actions")
    if not isinstance(saved_subject_actions, list):
        saved_subject_actions = common_actions
    st.caption("Thiết lập riêng của môn có thể thu hẹp các chức năng đang được phép dùng chung.")
    with st.form("standardizer_tool_subject_form"):
        subject_enabled = st.checkbox("Kích hoạt công cụ cho môn " + subject_options.get(subject_ref, subject_ref), value=bool(controls.get("enabled", True)))
        st.markdown("**Chức năng được phép cho môn này**")
        subject_columns = st.columns(2)
        selected_subject_actions = set(item for item in saved_subject_actions if item in common_actions)
        subject_actions = []
        for index, action in enumerate(common_actions):
            if subject_columns[index % 2].checkbox(
                action,
                value=action in selected_subject_actions,
                key="standardizer_tool_subject_action_" + subject_ref + "_" + str(index),
            ):
                subject_actions.append(action)
        subject_instruction = st.text_area("Chỉ dẫn AI riêng của môn", value=str(controls.get("subject_instruction") or ""))
        proposal_count = st.number_input("Số phương án AI tối đa", 1, 5, int(controls.get("proposal_count") or 2))
        require_review = st.checkbox("Bắt buộc giáo viên duyệt đề xuất AI", value=bool(controls.get("require_review", True)))
        save_subject = st.form_submit_button("💾 Lưu", type="primary", use_container_width=True)
    if save_subject:
        try:
            _save_and_activate(service=lifecycle, profile=subject_profile, code=subject_code, name="Công cụ chuẩn giáo án – " + subject_ref, subject_ref=subject_ref, payload={
                "configuration_kind": "STANDARDIZER_TOOL", "subject_controls": {
                    "enabled": subject_enabled, "allowed_actions": list(subject_actions),
                    "subject_instruction": subject_instruction.strip(),
                    "proposal_count": int(proposal_count), "require_review": require_review,
                },
            })
        except Exception as error:
            _show_configuration_storage_error(st, error)
            return
        st.success("Đã lưu và áp dụng cấu hình công cụ theo môn ngay.")
        st.rerun()
