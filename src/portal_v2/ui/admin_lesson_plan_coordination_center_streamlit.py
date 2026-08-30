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


def _configuration_editor_defaults(payload: dict | None) -> dict:
    normalized = dict(payload or {})
    template_profile = normalized.get("template_profile")
    if not isinstance(template_profile, dict):
        template_profile = {}
    layout = template_profile.get("layout")
    if not isinstance(layout, dict):
        layout = {}

    date_policy = normalized.get("date_policy")
    if not isinstance(date_policy, dict):
        date_policy = {}

    approval_policy = normalized.get("approval_policy")
    if not isinstance(approval_policy, dict):
        approval_policy = {}

    return {
        "payload": normalized,
        "profile_name": str(
            template_profile.get("profile_name")
            or normalized.get("profile_name")
            or ""
        ),
        "font_name": str(layout.get("font_name") or "Times New Roman"),
        "body_font_size_pt": float(layout.get("body_font_size_pt") or 13.0),
        "line_spacing": float(layout.get("line_spacing") or 1.15),
        "margin_left_cm": float(layout.get("margin_left_cm") or 2.0),
        "margin_right_cm": float(layout.get("margin_right_cm") or 2.0),
        "margin_top_cm": float(layout.get("margin_top_cm") or 2.0),
        "margin_bottom_cm": float(layout.get("margin_bottom_cm") or 2.0),
        "drafting_before_monday_enabled": bool(
            date_policy.get("drafting_before_monday_enabled", True)
        ),
        "drafting_before_monday_days": int(
            date_policy.get("drafting_before_monday_days") or 3
        ),
        "approval_before_monday_enabled": bool(
            date_policy.get("approval_before_monday_enabled", True)
        ),
        "approval_before_monday_days": int(
            date_policy.get("approval_before_monday_days") or 1
        ),
        "approval_label": str(
            approval_policy.get("approval_label") or "TỔ CM DUYỆT"
        ),
        "alignment": str(approval_policy.get("alignment") or "right"),
        "approval_offset_days": int(
            approval_policy.get(
                "approval_offset_days",
                date_policy.get("approval_before_monday_days", 1),
            )
            or 1
        ),
    }


def _render_structured_configuration_editor(
    st,
    *,
    key_prefix: str,
    initial_payload: dict | None,
) -> dict:
    import json

    defaults = _configuration_editor_defaults(initial_payload)

    st.markdown("#### Mẫu và trình bày giáo án")
    profile_name = st.text_input(
        "Tên mẫu giáo án",
        value=defaults["profile_name"],
        key=key_prefix + "_profile_name",
    )
    font_name = st.text_input(
        "Phông chữ",
        value=defaults["font_name"],
        key=key_prefix + "_font_name",
    )

    col1, col2 = st.columns(2)
    with col1:
        body_font_size_pt = st.number_input(
            "Cỡ chữ nội dung",
            min_value=8.0,
            max_value=24.0,
            value=defaults["body_font_size_pt"],
            step=0.5,
            key=key_prefix + "_body_font_size_pt",
        )
    with col2:
        line_spacing = st.number_input(
            "Giãn dòng",
            min_value=1.0,
            max_value=3.0,
            value=defaults["line_spacing"],
            step=0.05,
            key=key_prefix + "_line_spacing",
        )

    st.markdown("**Lề trang (cm)**")
    margin_cols = st.columns(4)
    labels = [
        ("Trái", "margin_left_cm"),
        ("Phải", "margin_right_cm"),
        ("Trên", "margin_top_cm"),
        ("Dưới", "margin_bottom_cm"),
    ]
    margin_values = {}
    for column, (label, field) in zip(margin_cols, labels):
        with column:
            margin_values[field] = st.number_input(
                label,
                min_value=0.5,
                max_value=5.0,
                value=defaults[field],
                step=0.05,
                key=key_prefix + "_" + field,
            )

    st.markdown("#### Quy tắc ngày soạn và ngày duyệt")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        drafting_enabled = st.checkbox(
            "Tự động tính ngày soạn trước thứ Hai",
            value=defaults["drafting_before_monday_enabled"],
            key=key_prefix + "_drafting_enabled",
        )
        drafting_days = st.number_input(
            "Số ngày soạn trước thứ Hai",
            min_value=0,
            max_value=14,
            value=defaults["drafting_before_monday_days"],
            step=1,
            key=key_prefix + "_drafting_days",
        )
    with date_col2:
        approval_enabled = st.checkbox(
            "Tự động tính ngày duyệt trước thứ Hai",
            value=defaults["approval_before_monday_enabled"],
            key=key_prefix + "_approval_enabled",
        )
        approval_days = st.number_input(
            "Số ngày duyệt trước thứ Hai",
            min_value=0,
            max_value=14,
            value=defaults["approval_before_monday_days"],
            step=1,
            key=key_prefix + "_approval_days",
        )

    st.markdown("#### Khối phê duyệt")
    approval_label = st.text_input(
        "Nhãn phê duyệt",
        value=defaults["approval_label"],
        key=key_prefix + "_approval_label",
    )
    alignment_options = ["right", "center", "left"]
    alignment_value = defaults["alignment"]
    if alignment_value not in alignment_options:
        alignment_value = "right"
    alignment = st.selectbox(
        "Căn khối phê duyệt",
        alignment_options,
        index=alignment_options.index(alignment_value),
        format_func=lambda value: {
            "right": "Căn phải",
            "center": "Căn giữa",
            "left": "Căn trái",
        }[value],
        key=key_prefix + "_approval_alignment",
    )

    with st.expander("Nâng cao: xem/chỉnh JSON", expanded=False):
        st.caption(
            "JSON chỉ dành cho trường hợp cần giữ hoặc bổ sung thuộc tính "
            "chưa có trên biểu mẫu. Các trường trực quan phía trên sẽ được "
            "ưu tiên khi lưu."
        )
        advanced_json = st.text_area(
            "JSON nâng cao",
            value=json.dumps(
                defaults["payload"],
                ensure_ascii=False,
                indent=2,
            ),
            height=220,
            key=key_prefix + "_advanced_json",
        )

    return {
        "advanced_json": advanced_json,
        "profile_name": profile_name,
        "font_name": font_name,
        "body_font_size_pt": float(body_font_size_pt),
        "line_spacing": float(line_spacing),
        "margin_left_cm": float(margin_values["margin_left_cm"]),
        "margin_right_cm": float(margin_values["margin_right_cm"]),
        "margin_top_cm": float(margin_values["margin_top_cm"]),
        "margin_bottom_cm": float(margin_values["margin_bottom_cm"]),
        "drafting_before_monday_enabled": bool(drafting_enabled),
        "drafting_before_monday_days": int(drafting_days),
        "approval_before_monday_enabled": bool(approval_enabled),
        "approval_before_monday_days": int(approval_days),
        "approval_label": approval_label,
        "alignment": alignment,
        "approval_offset_days": int(approval_days),
    }


def _build_configuration_payload_from_editor(editor: dict) -> dict:
    payload = _parse_configuration_payload(
        str(editor.get("advanced_json") or "{}")
    )

    template_profile = payload.get("template_profile")
    if not isinstance(template_profile, dict):
        template_profile = {}
    template_profile = dict(template_profile)
    template_profile["profile_name"] = str(
        editor.get("profile_name") or ""
    ).strip()
    layout = template_profile.get("layout")
    if not isinstance(layout, dict):
        layout = {}
    layout = dict(layout)
    layout.update(
        {
            "font_name": str(editor.get("font_name") or "").strip(),
            "body_font_size_pt": float(editor["body_font_size_pt"]),
            "line_spacing": float(editor["line_spacing"]),
            "margin_left_cm": float(editor["margin_left_cm"]),
            "margin_right_cm": float(editor["margin_right_cm"]),
            "margin_top_cm": float(editor["margin_top_cm"]),
            "margin_bottom_cm": float(editor["margin_bottom_cm"]),
        }
    )
    template_profile["layout"] = layout
    payload["template_profile"] = template_profile

    date_policy = payload.get("date_policy")
    if not isinstance(date_policy, dict):
        date_policy = {}
    date_policy = dict(date_policy)
    date_policy.update(
        {
            "drafting_before_monday_enabled": bool(
                editor["drafting_before_monday_enabled"]
            ),
            "drafting_before_monday_days": int(
                editor["drafting_before_monday_days"]
            ),
            "approval_before_monday_enabled": bool(
                editor["approval_before_monday_enabled"]
            ),
            "approval_before_monday_days": int(
                editor["approval_before_monday_days"]
            ),
        }
    )
    payload["date_policy"] = date_policy

    approval_policy = payload.get("approval_policy")
    if not isinstance(approval_policy, dict):
        approval_policy = {}
    approval_policy = dict(approval_policy)
    approval_policy.update(
        {
            "approval_label": str(
                editor.get("approval_label") or ""
            ).strip(),
            "alignment": str(editor.get("alignment") or "right"),
            "approval_offset_days": int(editor["approval_offset_days"]),
        }
    )
    payload["approval_policy"] = approval_policy

    return payload

def _render_admin_configuration_write_workspace(st, *, client) -> None:
    st.subheader("Quản trị cấu hình giáo án")
    st.caption(
        "ADMIN quản lý cấu hình theo hồ sơ và phiên bản. "
        "Luồng an toàn: DRAFT → PUBLISHED → đặt làm phiên bản hiện hành."
    )

    repository = SupabaseLessonPlanConfigurationAdminRepository(client)
    service = LessonPlanConfigurationAdminService(repository)

    try:
        profiles = repository.list_profiles()
    except Exception as error:
        st.error("Không thể tải danh sách cấu hình: " + str(error))
        profiles = []

    with st.expander("Tạo cấu hình mới", expanded=not profiles):
        with st.form("admin_lesson_plan_configuration_create_profile_form"):
            profile_code = st.text_input(
                "Mã cấu hình",
                key="admin_lesson_plan_configuration_profile_code",
            )
            profile_name = st.text_input(
                "Tên cấu hình",
                key="admin_lesson_plan_configuration_profile_name",
            )
            subject_ref = st.text_input(
                "Môn",
                key="admin_lesson_plan_configuration_subject_ref",
            )
            component_ref = st.text_input(
                "Phân môn",
                key="admin_lesson_plan_configuration_component_ref",
            )
            editor = _render_structured_configuration_editor(
                st,
                key_prefix="admin_lesson_plan_configuration_create",
                initial_payload={},
            )
            change_note = st.text_input(
                "Ghi chú phiên bản",
                key="admin_lesson_plan_configuration_create_change_note",
            )
            create_submitted = st.form_submit_button(
                "Tạo cấu hình và phiên bản nháp"
            )

        if create_submitted:
            try:
                payload = _build_configuration_payload_from_editor(editor)
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
                st.success(
                    "Đã tạo cấu hình DRAFT và phiên bản nháp số 1."
                )
                st.json(
                    {
                        "profile_id": profile.get("profile_id"),
                        "configuration_version_id": version.get(
                            "configuration_version_id"
                        ),
                        "version_status": version.get("version_status"),
                    }
                )

    if not profiles:
        st.info(
            "Chưa có cấu hình để quản lý. "
            "Hãy tạo cấu hình đầu tiên ở khu vực phía trên."
        )
        return

    profile_by_id = {
        str(row.get("profile_id") or ""): row
        for row in profiles
        if str(row.get("profile_id") or "").strip()
    }
    profile_ids = list(profile_by_id)

    def _profile_label(profile_id: str) -> str:
        row = profile_by_id[profile_id]
        scope = str(row.get("subject_ref") or "Toàn hệ thống")
        component = str(row.get("component_ref") or "").strip()
        if component:
            scope += " / " + component
        status = str(row.get("lifecycle_status") or "DRAFT")
        name = str(row.get("profile_name") or row.get("profile_code") or profile_id)
        return f"{name} · {scope} · {status}"

    selected_profile_id = st.selectbox(
        "Chọn cấu hình cần quản lý",
        profile_ids,
        format_func=_profile_label,
        key="admin_lesson_plan_configuration_selected_profile_id",
    )
    selected_profile = profile_by_id[selected_profile_id]

    st.caption(
        "Mã: "
        + str(selected_profile.get("profile_code") or "")
        + " · Trạng thái: "
        + str(selected_profile.get("lifecycle_status") or "")
    )

    try:
        versions = repository.list_versions(profile_id=selected_profile_id)
    except Exception as error:
        st.error("Không thể tải các phiên bản cấu hình: " + str(error))
        return

    version_by_id = {
        str(row.get("configuration_version_id") or ""): row
        for row in versions
        if str(row.get("configuration_version_id") or "").strip()
    }

    def _version_label(version_id: str) -> str:
        row = version_by_id[version_id]
        number = int(row.get("version_number") or 0)
        status = str(row.get("version_status") or "")
        current = (
            " · HIỆN HÀNH"
            if version_id == str(selected_profile.get("current_version_id") or "")
            else ""
        )
        return f"Phiên bản {number} · {status}{current}"

    if versions:
        st.markdown("**Các phiên bản**")
        for row in versions:
            version_id = str(row.get("configuration_version_id") or "")
            st.write("• " + _version_label(version_id))

    with st.expander("Tạo phiên bản nháp mới", expanded=False):
        source_ids = list(version_by_id)
        if source_ids:
            source_version_id = st.selectbox(
                "Tạo từ phiên bản",
                source_ids,
                format_func=_version_label,
                key="admin_lesson_plan_configuration_new_version_source",
            )
            source_payload = version_by_id[source_version_id].get(
                "configuration_payload"
            ) or {}
        else:
            source_payload = {}

        with st.form("admin_lesson_plan_configuration_create_version_form"):
            editor = _render_structured_configuration_editor(
                st,
                key_prefix="admin_lesson_plan_configuration_new_version",
                initial_payload=source_payload,
            )
            change_note = st.text_input(
                "Ghi chú thay đổi",
                key="admin_lesson_plan_configuration_new_version_change_note",
            )
            submitted = st.form_submit_button("Tạo phiên bản DRAFT mới")

        if submitted:
            try:
                payload = _build_configuration_payload_from_editor(editor)
                version = service.create_next_draft_version(
                    profile_id=selected_profile_id,
                    configuration_payload=payload,
                    change_note=change_note or None,
                )
            except Exception as error:
                st.error("Không thể tạo phiên bản nháp: " + str(error))
            else:
                st.success("Đã tạo phiên bản DRAFT mới.")
                st.json(version)

    draft_ids = [
        version_id
        for version_id, row in version_by_id.items()
        if row.get("version_status") == "DRAFT"
    ]
    if draft_ids:
        with st.expander("Chỉnh sửa và lưu DRAFT", expanded=False):
            selected_draft_id = st.selectbox(
                "Chọn phiên bản DRAFT",
                draft_ids,
                format_func=_version_label,
                key="admin_lesson_plan_configuration_update_version_id",
            )
            draft_payload = version_by_id[selected_draft_id].get(
                "configuration_payload"
            ) or {}

            with st.form("admin_lesson_plan_configuration_update_draft_form"):
                editor = _render_structured_configuration_editor(
                    st,
                    key_prefix="admin_lesson_plan_configuration_update",
                    initial_payload=draft_payload,
                )
                change_note = st.text_input(
                    "Ghi chú cập nhật",
                    key="admin_lesson_plan_configuration_update_change_note",
                )
                submitted = st.form_submit_button("Lưu DRAFT")

            if submitted:
                try:
                    payload = _build_configuration_payload_from_editor(editor)
                    version = service.update_draft(
                        configuration_version_id=selected_draft_id,
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
                publish_version_id = st.selectbox(
                    "Chọn phiên bản DRAFT cần xuất bản",
                    draft_ids,
                    format_func=_version_label,
                    key="admin_lesson_plan_configuration_publish_version_id",
                )
                submitted = st.form_submit_button("Xuất bản PUBLISHED")

            if submitted:
                try:
                    version = service.publish(
                        configuration_version_id=publish_version_id
                    )
                except Exception as error:
                    st.error(
                        "Không thể xuất bản phiên bản: " + str(error)
                    )
                else:
                    st.success("Phiên bản đã chuyển sang PUBLISHED.")
                    st.json(version)

    published_ids = [
        version_id
        for version_id, row in version_by_id.items()
        if row.get("version_status") == "PUBLISHED"
    ]
    if published_ids:
        with st.expander(
            "Kích hoạt phiên bản hiện hành",
            expanded=False,
        ):
            with st.form(
                "admin_lesson_plan_configuration_activate_form"
            ):
                activate_version_id = st.selectbox(
                    "Chọn phiên bản PUBLISHED",
                    published_ids,
                    format_func=_version_label,
                    key="admin_lesson_plan_configuration_activate_version_id",
                )
                retire_previous = st.checkbox(
                    "Ngừng sử dụng phiên bản hiện hành trước đó "
                    "sau khi chuyển phiên bản",
                    value=False,
                    key="admin_lesson_plan_configuration_retire_previous",
                )
                submitted = st.form_submit_button(
                    "Đặt làm phiên bản hiện hành / ACTIVE"
                )

            if submitted:
                try:
                    result = service.activate_published_version(
                        profile_id=selected_profile_id,
                        configuration_version_id=activate_version_id,
                        retire_previous=retire_previous,
                    )
                except Exception as error:
                    st.error(
                        "Không thể kích hoạt phiên bản: " + str(error)
                    )
                else:
                    st.success(
                        "Đã chuyển sang phiên bản PUBLISHED được chọn."
                    )
                    st.json(
                        {
                            "profile": result.profile,
                            "current_version": result.current_version,
                            "retired_previous_version": (
                                result.retired_previous_version
                            ),
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
