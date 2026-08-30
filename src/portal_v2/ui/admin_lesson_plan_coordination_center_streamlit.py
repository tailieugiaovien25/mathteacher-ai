from __future__ import annotations

from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_repository import (
    SupabaseLessonPlanConfigurationRepository,
)
from lesson_planning_v2.services.lesson_plan_configuration_service import (
    LessonPlanConfigurationService,
)
from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_admin_repository import (
    SupabaseLessonPlanConfigurationAdminRepository,
)
from lesson_planning_v2.services.lesson_plan_configuration_admin_service import (
    LessonPlanConfigurationAdminError,
    LessonPlanConfigurationAdminService,
)


def _parse_configuration_payload(raw_payload: str) -> dict:
    import json

    try:
        payload = json.loads(raw_payload or "{}")
    except json.JSONDecodeError as error:
        raise ValueError("Payload cấu hình phải là JSON hợp lệ.") from error

    if not isinstance(payload, dict):
        raise ValueError("Payload cấu hình phải là một JSON object.")
    return payload


def _render_admin_configuration_write_workspace(st, *, client) -> None:
    st.subheader("Quản trị cấu hình giáo án")
    st.caption(
        "ADMIN tạo và quản lý các phiên bản cấu hình. "
        "Luồng an toàn: DRAFT → PUBLISHED → đặt làm phiên bản hiện hành."
    )

    repository = SupabaseLessonPlanConfigurationAdminRepository(client)
    service = LessonPlanConfigurationAdminService(repository)

    with st.expander("Tạo cấu hình mới", expanded=False):
        with st.form("admin_lesson_plan_configuration_create_profile_form"):
            profile_code = st.text_input("Mã cấu hình", key="admin_lesson_plan_configuration_profile_code")
            profile_name = st.text_input("Tên cấu hình", key="admin_lesson_plan_configuration_profile_name")
            subject_ref = st.text_input("Môn", key="admin_lesson_plan_configuration_subject_ref")
            component_ref = st.text_input("Phân môn", key="admin_lesson_plan_configuration_component_ref")
            payload_text = st.text_area(
                "Payload cấu hình JSON",
                value="{}",
                height=220,
                key="admin_lesson_plan_configuration_create_payload",
            )
            change_note = st.text_input(
                "Ghi chú phiên bản",
                key="admin_lesson_plan_configuration_create_change_note",
            )
            create_submitted = st.form_submit_button("Tạo cấu hình và phiên bản nháp")

        if create_submitted:
            try:
                payload = _parse_configuration_payload(payload_text)
                profile, version = service.create_profile_with_initial_draft(
                    profile_code=profile_code,
                    profile_name=profile_name,
                    subject_ref=subject_ref,
                    component_ref=component_ref,
                    configuration_payload=payload,
                    change_note=change_note or None,
                )
            except Exception as error:
                st.error("Không thể tạo cấu hình: " + str(error))
            else:
                st.success("Đã tạo cấu hình DRAFT và phiên bản nháp số 1.")
                st.json(
                    {
                        "profile_id": profile.get("profile_id"),
                        "configuration_version_id": version.get("configuration_version_id"),
                        "version_status": version.get("version_status"),
                    }
                )

    with st.expander("Tạo phiên bản nháp mới", expanded=False):
        with st.form("admin_lesson_plan_configuration_create_version_form"):
            profile_id = st.text_input(
                "Profile ID",
                key="admin_lesson_plan_configuration_new_version_profile_id",
            )
            payload_text = st.text_area(
                "Payload JSON cho phiên bản mới",
                value="{}",
                height=220,
                key="admin_lesson_plan_configuration_new_version_payload",
            )
            change_note = st.text_input(
                "Ghi chú thay đổi",
                key="admin_lesson_plan_configuration_new_version_change_note",
            )
            submitted = st.form_submit_button("Tạo phiên bản DRAFT mới")

        if submitted:
            try:
                payload = _parse_configuration_payload(payload_text)
                version = service.create_next_draft_version(
                    profile_id=profile_id.strip(),
                    configuration_payload=payload,
                    change_note=change_note or None,
                )
            except Exception as error:
                st.error("Không thể tạo phiên bản nháp: " + str(error))
            else:
                st.success("Đã tạo phiên bản DRAFT mới.")
                st.json(version)

    with st.expander("Chỉnh sửa và lưu DRAFT", expanded=False):
        with st.form("admin_lesson_plan_configuration_update_draft_form"):
            version_id = st.text_input(
                "Configuration Version ID",
                key="admin_lesson_plan_configuration_update_version_id",
            )
            payload_text = st.text_area(
                "Payload JSON cập nhật",
                value="{}",
                height=220,
                key="admin_lesson_plan_configuration_update_payload",
            )
            change_note = st.text_input(
                "Ghi chú cập nhật",
                key="admin_lesson_plan_configuration_update_change_note",
            )
            submitted = st.form_submit_button("Lưu DRAFT")

        if submitted:
            try:
                payload = _parse_configuration_payload(payload_text)
                version = service.update_draft(
                    configuration_version_id=version_id.strip(),
                    configuration_payload=payload,
                    change_note=change_note or None,
                )
            except Exception as error:
                st.error("Không thể lưu DRAFT: " + str(error))
            else:
                st.success("Đã lưu phiên bản DRAFT.")
                st.json(version)

    with st.expander("Xuất bản phiên bản", expanded=False):
        with st.form("admin_lesson_plan_configuration_publish_form"):
            version_id = st.text_input(
                "Configuration Version ID cần xuất bản",
                key="admin_lesson_plan_configuration_publish_version_id",
            )
            submitted = st.form_submit_button("Xuất bản PUBLISHED")

        if submitted:
            try:
                version = service.publish(
                    configuration_version_id=version_id.strip()
                )
            except Exception as error:
                st.error("Không thể xuất bản phiên bản: " + str(error))
            else:
                st.success("Phiên bản đã chuyển sang PUBLISHED.")
                st.json(version)

    with st.expander("Kích hoạt phiên bản hiện hành", expanded=False):
        with st.form("admin_lesson_plan_configuration_activate_form"):
            profile_id = st.text_input(
                "Profile ID cần kích hoạt",
                key="admin_lesson_plan_configuration_activate_profile_id",
            )
            version_id = st.text_input(
                "Configuration Version ID PUBLISHED",
                key="admin_lesson_plan_configuration_activate_version_id",
            )
            retire_previous = st.checkbox(
                "Retire phiên bản hiện hành trước đó sau khi chuyển current",
                value=False,
                key="admin_lesson_plan_configuration_retire_previous",
            )
            submitted = st.form_submit_button("Đặt làm phiên bản hiện hành / ACTIVE")

        if submitted:
            try:
                result = service.activate_published_version(
                    profile_id=profile_id.strip(),
                    configuration_version_id=version_id.strip(),
                    retire_previous=retire_previous,
                )
            except Exception as error:
                st.error("Không thể kích hoạt phiên bản: " + str(error))
            else:
                st.success(
                    "Đã chuyển current_version_id sang phiên bản PUBLISHED được chọn."
                )
                st.json(
                    {
                        "profile": result.profile,
                        "current_version": result.current_version,
                        "retired_previous_version": result.retired_previous_version,
                    }
                )


def render_admin_lesson_plan_coordination_center(st, *, client) -> None:
    st.title("Trung tâm điều phối giáo án")
    st.caption(
        "ADMIN quản trị cấu hình dùng chung của giáo án. "
        "Giáo án, bản nháp, tệp tải lên và trạng thái làm việc của giáo viên "
        "vẫn thuộc phạm vi USER."
    )

    if client is None:
        st.warning("Chưa có kết nối dữ liệu.")
        return

    repository = SupabaseLessonPlanConfigurationRepository(client)
    service = LessonPlanConfigurationService(repository)

    _render_admin_configuration_write_workspace(st, client=client)

    st.divider()
    st.subheader("Cấu hình giáo án đang hoạt động")
    st.caption(
        "Tra cứu cấu hình ACTIVE/PUBLISHED theo Môn → Phân môn → mặc định Môn "
        "→ mặc định toàn hệ thống. Giai đoạn này chỉ đọc, chưa thay đổi dữ liệu."
    )

    subject_ref = st.text_input(
        "Mã môn",
        key="admin_lesson_plan_coordination_subject_ref",
    )
    component_ref = st.text_input(
        "Mã phân môn (nếu có)",
        key="admin_lesson_plan_coordination_component_ref",
    )

    if st.button(
        "Kiểm tra cấu hình đang áp dụng",
        key="admin_lesson_plan_coordination_resolve",
    ):
        try:
            resolved = service.resolve(
                subject_ref=subject_ref,
                component_ref=component_ref or None,
            )
        except Exception as error:
            st.error("Không thể đọc cấu hình giáo án: " + str(error))
            return

        if resolved.snapshot is None:
            st.info(
                "Chưa có cấu hình ADMIN phù hợp. Runtime sẽ tiếp tục dùng "
                "mặc định hiện hành để bảo toàn tương thích."
            )
        else:
            snapshot = resolved.snapshot
            st.success(
                "Đang dùng cấu hình ADMIN: "
                f"{snapshot.profile_name} · phiên bản {snapshot.version_number}"
            )
            st.json(dict(resolved.configuration_payload))

    st.divider()
    st.subheader("Chính sách nhóm giáo án")
    try:
        from portal_v2.ui.admin_canonical_code_catalog_streamlit import (
            render_admin_lesson_plan_grouping_policy,
        )

        render_admin_lesson_plan_grouping_policy(st, client=client)
    except Exception as error:
        st.error("Không thể tải chính sách nhóm giáo án: " + str(error))

    st.divider()
    st.subheader("Phạm vi chuyển giao từ USER")
    st.write(
        "Mẫu giáo án, quy tắc chuẩn hóa, quy tắc ngày soạn/ngày duyệt và "
        "khối phê duyệt là cấu hình toàn cục do ADMIN điều phối."
    )
    st.caption(
        "Chưa ẩn Thiết đặt giáo án phía USER cho đến khi đường đọc runtime "
        "ADMIN được kiểm thử và nối vào ứng dụng."
    )
