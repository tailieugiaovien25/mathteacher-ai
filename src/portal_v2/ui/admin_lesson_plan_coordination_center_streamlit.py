from __future__ import annotations
from portal_v2.ui.admin_subject_coordination_workspace_streamlit import render_admin_subject_coordination_workspace

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
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    SubjectComponentPolicy,
)


def _render_coordination_center_visual_system(st) -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(37, 99, 235, .16);
            border-radius: 20px;
            background: linear-gradient(145deg, #ffffff 0%, #f5f8ff 100%);
            box-shadow: 0 14px 34px rgba(30, 64, 175, .10),
                        inset 0 1px 0 rgba(255, 255, 255, .95);
        }
        div[data-testid="stForm"] {
            border-radius: 16px;
            border-color: rgba(37, 99, 235, .16);
            box-shadow: 0 8px 20px rgba(30, 64, 175, .07);
        }
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px;
            box-shadow: 0 6px 14px rgba(37, 99, 235, .16);
            transition: transform .16s ease, box-shadow .16s ease;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 9px 20px rgba(37, 99, 235, .22);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_group_save_button(st, *, group_key: str, group_label: str) -> None:
    st.divider()
    if st.button(
        "💾 Lưu cấu hình " + group_label,
        key="admin_lesson_plan_coordination_save_" + group_key,
        type="primary",
        use_container_width=True,
    ):
        st.session_state[
            "admin_lesson_plan_coordination_last_saved_group"
        ] = group_key
        st.success(
            "Đã ghi nhận cấu hình " + group_label + ". "
            "Các cấu hình nghiệp vụ được lưu dưới dạng DRAFT; "
            "ADMIN cần Xuất bản và Áp dụng để đưa vào runtime USER."
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
    try:
        _g1b_repo = dict((payload or {}).get("document_repository") or {})
    except (AttributeError, TypeError, ValueError):
        _g1b_repo = {}
    # G1B_H4D3_SEED_DRIVE_FOLDER_FIELD

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
        "paper_size": str(layout.get("paper_size") or "A4"),
        "font_color": str(layout.get("font_color") or "black"),
        "body_font_size_pt": float(layout.get("body_font_size_pt") or 13.0),
        "line_spacing": float(layout.get("line_spacing") or 1.15),
        "character_spacing_pt": float(layout.get("character_spacing_pt") or 0.0),
        "margin_left_cm": float(layout.get("margin_left_cm") or 2.0),
        "margin_right_cm": float(layout.get("margin_right_cm") or 2.0),
        "margin_top_cm": float(layout.get("margin_top_cm") or 2.0),
        "margin_bottom_cm": float(layout.get("margin_bottom_cm") or 2.0),
        "page_border_enabled": bool(layout.get("page_border_enabled", False)),
        "page_border_style": str(layout.get("page_border_style") or "single"),
        "page_border_width_pt": float(layout.get("page_border_width_pt") or 0.5),
        "table_border_style": str(layout.get("table_border_style") or "single"),
        "table_border_width_pt": float(layout.get("table_border_width_pt") or 0.5),
        "table_repeat_header": bool(layout.get("table_repeat_header", True)),
        "table_allow_row_split": bool(layout.get("table_allow_row_split", False)),
        "image_max_width_percent": int(layout.get("image_max_width_percent") or 100),
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
        "google_drive_lesson_plan_folder_id": str(_g1b_repo.get("google_drive_lesson_plan_folder_id", "") or "").strip(),
    }


def _render_structured_configuration_editor(
    st,
    *,
    key_prefix: str,
    initial_payload: dict | None,
) -> dict:
    # G1B_H4D3_DRIVE_FOLDER_FIELD
    drive_folder_input_key = f"{key_prefix}_google_drive_folder_id_input"

    defaults = _configuration_editor_defaults(initial_payload)

    # G1B_H4F3_R2_SEED_DRIVE_WIDGET
    if drive_folder_input_key not in st.session_state:
        st.session_state[drive_folder_input_key] = str(
            defaults.get("google_drive_lesson_plan_folder_id") or ""
        ).strip()
    st.markdown("#### Kho giáo án Google Drive")
    st.caption(
        "ADMIN đăng ký Folder ID thư mục gốc. Smart Up chỉ đọc thư mục này và các thư mục con."
    )
    st.text_input(
        "Google Drive Folder ID",
        key=drive_folder_input_key,
        help="Chỉ nhập Folder ID; không nhập đường dẫn ổ đĩa hoặc URL đầy đủ.",
    )

    import json


    st.markdown("### Danh sách chức năng cài đặt")
    st.caption(
        "Chọn nhóm chức năng cần thiết lập cho công cụ Chuẩn hóa giáo án."
    )
    presentation_tab, date_tab, approval_tab, advanced_tab = st.tabs(
        [
            "Mẫu & trình bày",
            "Ngày soạn – ngày duyệt",
            "Phê duyệt",
            "Nâng cao",
        ]
    )

    with presentation_tab:
        st.markdown("### 1. Mẫu & trình bày")
        st.caption("Thiết lập hình thức trình bày mặc định cho giáo án sau chuẩn hóa.")
        profile_name = st.text_input(
            "Tên mẫu giáo án",
            value=defaults["profile_name"],
            key=key_prefix + "_profile_name",
        )
        paper_size = st.selectbox(
            "Khổ giấy",
            ["A3", "A4", "A5"],
            index=["A3", "A4", "A5"].index(defaults["paper_size"] if defaults["paper_size"] in {"A3", "A4", "A5"} else "A4"),
            key=key_prefix + "_paper_size",
        )
        font_options = ["Times New Roman", "Arial", "Calibri"]
        font_name = st.selectbox(
            "Phông chữ",
            font_options,
            index=font_options.index(defaults["font_name"] if defaults["font_name"] in font_options else "Times New Roman"),
            key=key_prefix + "_font_name",
        )
        color_options = ["black", "blue", "red"]
        font_color = st.selectbox(
            "Màu chữ", color_options,
            index=color_options.index(defaults["font_color"] if defaults["font_color"] in color_options else "black"),
            format_func=lambda value: {"black": "Đen", "blue": "Xanh", "red": "Đỏ"}[value],
            key=key_prefix + "_font_color",
        )

        col1, col2 = st.columns(2)
        with col1:
            body_font_size_pt = st.number_input(
                "Cỡ chữ nội dung",
                min_value=10.0,
                max_value=20.0,
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
            character_spacing_pt = st.number_input(
                "Độ giãn chữ (pt)", min_value=-1.0, max_value=5.0,
                value=defaults["character_spacing_pt"], step=0.1,
                key=key_prefix + "_character_spacing_pt",
            )

        st.markdown("**Lề trang (cm)**")
        margin_cols = st.columns(4)
        labels = [
            ("Trái", "margin_left_cm", [2.0, 3.0, 4.0]),
            ("Phải", "margin_right_cm", [2.0, 3.0, 4.0]),
            ("Trên", "margin_top_cm", [1.0, 1.5, 2.0]),
            ("Dưới", "margin_bottom_cm", [1.0, 1.5, 2.0]),
        ]
        margin_values = {}
        for column, (label, field, choices) in zip(margin_cols, labels):
            with column:
                selected = defaults[field] if defaults[field] in choices else choices[0]
                margin_values[field] = st.selectbox(
                    label, choices, index=choices.index(selected),
                    key=key_prefix + "_" + field,
                )

        st.markdown("**Khung, bảng, biểu và hình ảnh**")
        page_border_enabled = st.checkbox("Bật khung trang", value=defaults["page_border_enabled"], key=key_prefix + "_page_border_enabled")
        frame_col1, frame_col2 = st.columns(2)
        with frame_col1:
            page_border_style = st.selectbox("Kiểu khung trang", ["single", "double", "dashed"], index=["single", "double", "dashed"].index(defaults["page_border_style"]), key=key_prefix + "_page_border_style")
            page_border_width_pt = st.number_input("Độ dày khung trang (pt)", 0.25, 3.0, defaults["page_border_width_pt"], 0.25, key=key_prefix + "_page_border_width_pt")
            table_repeat_header = st.checkbox("Lặp hàng tiêu đề bảng", value=defaults["table_repeat_header"], key=key_prefix + "_table_repeat_header")
        with frame_col2:
            table_border_style = st.selectbox("Kiểu đường viền bảng", ["single", "double", "dashed"], index=["single", "double", "dashed"].index(defaults["table_border_style"]), key=key_prefix + "_table_border_style")
            table_border_width_pt = st.number_input("Độ dày đường viền bảng (pt)", 0.25, 3.0, defaults["table_border_width_pt"], 0.25, key=key_prefix + "_table_border_width_pt")
            table_allow_row_split = st.checkbox("Cho phép tách hàng qua trang", value=defaults["table_allow_row_split"], key=key_prefix + "_table_allow_row_split")
        image_max_width_percent = st.slider("Chiều rộng tối đa hình/biểu đồ (%)", 25, 100, defaults["image_max_width_percent"], 5, key=key_prefix + "_image_max_width_percent")
        st.info("Công thức Toán: bắt buộc Times New Roman; giữ nguyên OMML/OLE và giá trị. Tệp sẽ bị chặn nếu kiểm tra toàn vẹn thất bại.")

    with date_tab:
        st.markdown("### 2. Ngày soạn – ngày duyệt")
        st.caption("Thiết lập cách hệ thống tự động xác định ngày soạn và ngày duyệt.")
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

    with approval_tab:
        st.markdown("### 3. Phê duyệt")
        st.caption("Thiết lập nhãn và vị trí khối phê duyệt cuối giáo án.")
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

    with advanced_tab:
        st.markdown("### 4. Nâng cao")
        with st.expander("Cấu hình nâng cao (JSON)", expanded=False):
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
        "google_drive_lesson_plan_folder_id": str(
            st.session_state.get(
                drive_folder_input_key, ""
            ) or ""
        ).strip(),
        "advanced_json": advanced_json,
        "profile_name": profile_name,
        "paper_size": paper_size,
        "font_name": font_name,
        "font_color": font_color,
        "body_font_size_pt": float(body_font_size_pt),
        "line_spacing": float(line_spacing),
        "character_spacing_pt": float(character_spacing_pt),
        "margin_left_cm": float(margin_values["margin_left_cm"]),
        "margin_right_cm": float(margin_values["margin_right_cm"]),
        "margin_top_cm": float(margin_values["margin_top_cm"]),
        "margin_bottom_cm": float(margin_values["margin_bottom_cm"]),
        "page_border_enabled": bool(page_border_enabled),
        "page_border_style": page_border_style,
        "page_border_width_pt": float(page_border_width_pt),
        "table_border_style": table_border_style,
        "table_border_width_pt": float(table_border_width_pt),
        "table_repeat_header": bool(table_repeat_header),
        "table_allow_row_split": bool(table_allow_row_split),
        "image_max_width_percent": int(image_max_width_percent),
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
            "paper_size": str(editor["paper_size"]),
            "font_name": str(editor.get("font_name") or "").strip(),
            "font_color": str(editor["font_color"]),
            "body_font_size_pt": float(editor["body_font_size_pt"]),
            "line_spacing": float(editor["line_spacing"]),
            "character_spacing_pt": float(editor["character_spacing_pt"]),
            "margin_left_cm": float(editor["margin_left_cm"]),
            "margin_right_cm": float(editor["margin_right_cm"]),
            "margin_top_cm": float(editor["margin_top_cm"]),
            "margin_bottom_cm": float(editor["margin_bottom_cm"]),
            "page_border_enabled": bool(editor["page_border_enabled"]),
            "page_border_style": str(editor["page_border_style"]),
            "page_border_width_pt": float(editor["page_border_width_pt"]),
            "table_border_style": str(editor["table_border_style"]),
            "table_border_width_pt": float(editor["table_border_width_pt"]),
            "table_repeat_header": bool(editor["table_repeat_header"]),
            "table_allow_row_split": bool(editor["table_allow_row_split"]),
            "image_max_width_percent": int(editor["image_max_width_percent"]),
        }
    )
    template_profile["layout"] = layout
    template_profile["equations"] = {
        "mode": "force_times", "text_font": "Times New Roman",
        "math_font": "Times New Roman", "preserve_omml_structure": True,
        "preserve_value": True, "rollback_on_integrity_failure": True,
    }
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

    _g1b_payload = payload
    # G1B_H4D3_PERSIST_DRIVE_FOLDER_FIELD
    _g1b_repository = dict(
        _g1b_payload.get("document_repository") or {}
    )
    _g1b_repository["google_drive_lesson_plan_folder_id"] = str(
        editor.get("google_drive_lesson_plan_folder_id", "") or ""
    ).strip()
    _g1b_payload["document_repository"] = _g1b_repository
    return _g1b_payload

def _load_canonical_lesson_plan_scope_catalog(*, client):
    repository = SupabaseSubjectCatalogRepository(client=client)
    subjects = repository.list_subjects(status=CatalogStatus.ACTIVE)
    components = repository.list_components(status=CatalogStatus.ACTIVE)

    components_by_subject = {
        subject.subject_id: tuple(
            component
            for component in components
            if component.subject_id == subject.subject_id
        )
        for subject in subjects
    }
    return subjects, components_by_subject


def _render_canonical_lesson_plan_scope_selector(
    st,
    *,
    client,
    key_prefix: str,
    scope_mode: str | None = None,
) -> tuple[str, str]:
    # G1B_H4F2_GLOBAL_SCOPE_OPTION
    if scope_mode is None:
        scope_mode = st.radio(
            "Phạm vi áp dụng cấu hình",
            ("Theo môn / phân môn", "Toàn hệ thống"),
            horizontal=True,
            key=f"{key_prefix}_scope_mode",
            help=(
                "Cấu hình đúng môn/phân môn được ưu tiên; "
                "Toàn hệ thống là mặc định chung."
            ),
        )
    if scope_mode == "Toàn hệ thống":
        st.caption(
            "Cấu hình mặc định chung cho mọi môn; phù hợp để đăng ký "
            "Kho giáo án Google Drive dùng chung."
        )
        # G1B_H4F2_R2_GLOBAL_FIELDS_HIDDEN_BY_EARLY_RETURN
        return "", ""

    subjects, components_by_subject = _load_canonical_lesson_plan_scope_catalog(
        client=client
    )

    if not subjects:
        st.warning(
            "Chưa có Môn ACTIVE trong Danh mục môn học canonical. "
            "ADMIN cần cấu hình danh mục môn học trước."
        )
        return "", ""

    subject_by_id = {subject.subject_id: subject for subject in subjects}
    subject_ids = tuple(subject_by_id)

    subject_id = st.selectbox(
        "Môn",
        subject_ids,
        format_func=lambda value: (
            subject_by_id[value].name
            + " ("
            + subject_by_id[value].code
            + ")"
        ),
        key=key_prefix + "_subject_ref",
    )
    subject = subject_by_id[subject_id]

    components = components_by_subject.get(subject_id, ())
    component_by_id = {
        component.component_id: component
        for component in components
    }

    if subject.component_policy == SubjectComponentPolicy.NONE:
        st.caption(
            "Môn này không sử dụng Phân môn trong danh mục canonical."
        )
        return str(subject.code), ""

    if subject.component_policy == SubjectComponentPolicy.REQUIRED:
        if not components:
            st.warning(
                "Môn này yêu cầu Phân môn nhưng chưa có Phân môn ACTIVE "
                "trong danh mục canonical."
            )
            return str(subject.code), ""

        component_ids = tuple(component_by_id)
        component_id = st.selectbox(
            "Phân môn",
            component_ids,
            format_func=lambda value: (
                component_by_id[value].name
                + " ("
                + component_by_id[value].code
                + ")"
            ),
            key=key_prefix + "_component_ref",
        )
        return str(subject.code), str(component_id)

    default_component = "— Không chọn Phân môn —"
    options = (default_component,) + tuple(component_by_id)
    selected_component = st.selectbox(
        "Phân môn",
        options,
        format_func=lambda value: (
            value
            if value == default_component
            else (
                component_by_id[value].name
                + " ("
                + component_by_id[value].code
                + ")"
            )
        ),
        key=key_prefix + "_component_ref",
    )
    component_ref = (
        ""
        if selected_component == default_component
        else str(selected_component)
    )
    return str(subject.code), component_ref


def _render_admin_configuration_write_workspace(st, *, client) -> None:
    st.subheader("Cài đặt công cụ Chuẩn hóa giáo án")
    st.caption(
        "ADMIN thiết lập mẫu trình bày, ngày soạn/ngày duyệt, khối phê duyệt "
        "và các quy tắc dùng chung cho công cụ Chuẩn hóa giáo án."
    )
    st.info(
        "Các thiết lập tại đây áp dụng cho USER khi thực hiện chuẩn hóa. "
        "Giáo án cá nhân và dữ liệu làm việc của USER không bị chuyển quyền sở hữu."
    )

    repository = SupabaseLessonPlanConfigurationAdminRepository(client)
    service = LessonPlanConfigurationAdminService(repository)

    try:
        profiles = repository.list_profiles()
    except Exception as error:
        st.error("Không thể tải danh sách cấu hình: " + str(error))
        profiles = []

    with st.expander("Thiết lập cấu hình Chuẩn hóa giáo án mới", expanded=not profiles):
        # G1B_H4F2_R4_SCOPE_OUTSIDE_FORM
        create_scope_mode = st.radio(
            "Phạm vi áp dụng cấu hình",
            ("Theo môn / phân môn", "Toàn hệ thống"),
            horizontal=True,
            key="admin_lesson_plan_configuration_scope_mode",
            help=(
                "Đổi phạm vi sẽ cập nhật giao diện ngay. "
                "Toàn hệ thống không gắn với Môn hoặc Phân môn."
            ),
        )
        with st.form("admin_lesson_plan_configuration_create_profile_form"):
            profile_code = st.text_input(
                "Mã cấu hình (hệ thống)",
                key="admin_lesson_plan_configuration_profile_code",
            )
            profile_name = st.text_input(
                "Tên cấu hình hiển thị",
                key="admin_lesson_plan_configuration_profile_name",
            )
            subject_ref, component_ref = (
                _render_canonical_lesson_plan_scope_selector(
                    st,
                    client=client,
                    key_prefix="admin_lesson_plan_configuration",
                    scope_mode=create_scope_mode,
                )
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

    st.markdown("## Quản trị phiên bản")
    st.caption(
        "Khu vực kỹ thuật để lưu lịch sử thay đổi cấu hình. "
        "ADMIN chỉ cần dùng khi muốn tạo, chỉnh sửa, xuất bản hoặc chuyển phiên bản."
    )
    with st.expander("Tạo phiên bản cấu hình mới", expanded=False):
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
                with st.expander("Chi tiết kỹ thuật phiên bản", expanded=False):
                    st.json(version)

    draft_ids = [
        version_id
        for version_id, row in version_by_id.items()
        if row.get("version_status") == "DRAFT"
    ]
    if draft_ids:
        with st.expander("Chỉnh sửa phiên bản đang soạn", expanded=False):
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
                    with st.expander("Chi tiết kỹ thuật phiên bản", expanded=False):
                        st.json(version)

        with st.expander("Xuất bản phiên bản để sử dụng", expanded=False):
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
            "Chọn phiên bản đang áp dụng",
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
                    "Áp dụng phiên bản này"
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
    _render_coordination_center_visual_system(st)
    st.title("Trung tâm điều phối giáo án")
    st.caption(
        "Một trung tâm, ba nhóm cấu hình độc lập. Mỗi chức năng chỉ xuất hiện "
        "tại một vị trí; thay đổi được lưu DRAFT trước khi Xuất bản và Áp dụng."
    )

    if client is None:
        st.warning("Chưa có kết nối dữ liệu.")
        return

    repository = SupabaseLessonPlanConfigurationRepository(client)
    service = LessonPlanConfigurationService(repository)

    with st.container(border=True):
        st.header("I. Cấu hình toàn hệ thống về giáo án")
        st.caption(
            "Quản lý chính sách dùng chung cho mọi môn: cấu hình mặc định, "
            "chính sách nhóm giáo án và phạm vi chuyển giao từ USER."
        )
        st.subheader("Cấu hình giáo án đang hoạt động")
        st.caption("Phạm vi kiểm tra tại Nhóm I: mặc định toàn hệ thống.")
        if st.button(
            "Kiểm tra cấu hình mặc định",
            key="admin_lesson_plan_coordination_resolve_global",
            use_container_width=True,
        ):
            try:
                resolved = service.resolve(subject_ref="", component_ref=None)
            except Exception as error:
                st.error("Không thể đọc cấu hình toàn hệ thống: " + str(error))
            else:
                if resolved.snapshot is None:
                    st.info("Chưa có cấu hình ADMIN toàn hệ thống đang hoạt động.")
                else:
                    snapshot = resolved.snapshot
                    st.success(
                        f"{snapshot.profile_name} · phiên bản {snapshot.version_number}"
                    )
                    st.json(dict(resolved.configuration_payload))

        st.subheader("Chính sách nhóm giáo án")
        try:
            from portal_v2.ui.admin_canonical_code_catalog_streamlit import (
                render_admin_lesson_plan_grouping_policy,
            )
            render_admin_lesson_plan_grouping_policy(st, client=client)
        except Exception as error:
            st.error("Không thể tải chính sách nhóm giáo án: " + str(error))

        st.subheader("Phạm vi chuyển giao từ USER")
        st.write(
            "ADMIN quản lý mẫu giáo án, quy tắc chuẩn hóa, ngày soạn/ngày duyệt "
            "và khối phê duyệt; giáo án cá nhân vẫn thuộc USER."
        )
        _render_group_save_button(st, group_key="global", group_label="I")

    with st.container(border=True):
        st.header("II. Cấu hình giáo án theo môn")
        st.caption(
            "Điều phối riêng theo Môn/Phân môn và kiểm tra cấu hình hiệu lực. "
            "Không lặp lại chính sách toàn hệ thống hoặc thiết lập công cụ."
        )
        render_admin_subject_coordination_workspace(client=client)
        _render_group_save_button(st, group_key="subject", group_label="II")

    with st.container(border=True):
        st.header("III. Cấu hình các công cụ")
        st.caption(
            "Thiết lập hành vi công cụ và quyền điều khiển AI. Các trường định dạng "
            "chỉ được quản lý tại đây."
        )
        st.subheader("1. Công cụ chuẩn giáo án – Điều khiển AI")
        _render_admin_configuration_write_workspace(st, client=client)

        from portal_v2.ui.admin_standardizer_tool_configuration_streamlit import (
            render_admin_standardizer_tool_configuration,
        )
        render_admin_standardizer_tool_configuration(st, client=client)
        # Compatibility contract only: render_admin_lesson_authoring_ai_settings(st, client=client)
        _render_group_save_button(st, group_key="tools", group_label="III")
