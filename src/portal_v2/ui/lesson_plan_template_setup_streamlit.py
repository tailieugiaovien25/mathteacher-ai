from __future__ import annotations

from dataclasses import replace

import streamlit as st

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.services.teacher_lesson_plan_subject_service import (
    TeacherLessonPlanSubjectService,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    SubjectLessonPlanProfile,
)

from lesson_planning_v2.lesson_plan_template_profile import (
    DraftingWeekday,
    LessonPlanAlignment,
    LessonPlanApprovalProfile,
    LessonPlanHeaderProfile,
    LessonPlanLayoutProfile,
    LessonPlanSchedulingPolicy,
    LessonPlanStructureProfile,
    LessonPlanStructureSection,
    LessonPlanTemplateProfile,
)


SESSION_KEY_PREFIX = (
    "lesson_plan_template_profile"
)

SUBJECT_PROFILE_KEY_PREFIX = (
    "subject_lesson_plan_profile"
)

SUBJECT_CONTEXT_KEY = (
    "lesson_plan_template_selected_subject"
)


SELECTION_MODE_LABELS = {
    LessonPlanSelectionMode.LESSON: (
        "Theo b\u00e0i"
    ),
    LessonPlanSelectionMode.PERIOD: (
        "Theo ti\u1ebft"
    ),
    LessonPlanSelectionMode.TOPIC: (
        "Theo ch\u1ee7 \u0111\u1ec1"
    ),
}


def _selection_mode_label(
    mode: LessonPlanSelectionMode,
) -> str:
    """Return a safe label for current and future selection modes."""
    configured = SELECTION_MODE_LABELS.get(
        mode
    )

    if configured:
        return configured

    value = str(
        getattr(mode, "value", mode)
    ).strip()

    fallback_labels = {
        "week_subject": "Theo tuần và môn",
    }

    return fallback_labels.get(
        value,
        value.replace("_", " ").strip().title(),
    )


def _context_session_key(
    *,
    prefix: str,
    teacher_id: str,
    academic_year: str,
    subject_id: str,
) -> str:
    return "::".join(
        (
            prefix,
            teacher_id,
            academic_year,
            subject_id,
        )
    )


def _template_profile_session_key(
    *,
    teacher_id: str,
    academic_year: str,
    subject_id: str,
) -> str:
    return _context_session_key(
        prefix=SESSION_KEY_PREFIX,
        teacher_id=teacher_id,
        academic_year=academic_year,
        subject_id=subject_id,
    )


def _subject_profile_session_key(
    *,
    teacher_id: str,
    academic_year: str,
    subject_id: str,
) -> str:
    return _context_session_key(
        prefix=SUBJECT_PROFILE_KEY_PREFIX,
        teacher_id=teacher_id,
        academic_year=academic_year,
        subject_id=subject_id,
    )


def _clear_template_widget_state() -> None:
    """
    Clear editor widget state when the teacher
    switches subject.

    The selected subject itself is intentionally
    preserved.
    """

    for key in tuple(
        st.session_state.keys()
    ):
        if (
            str(key).startswith(
                "lesson_plan_setup_"
            )
            or key
            == "lesson_plan_structure_editor"
        ):
            st.session_state.pop(
                key,
                None,
            )


WEEKDAY_LABELS = {
    DraftingWeekday.THURSDAY: "Thứ 5 tuần trước",
    DraftingWeekday.FRIDAY: "Thứ 6 tuần trước",
    DraftingWeekday.SATURDAY: "Thứ 7 tuần trước",
    DraftingWeekday.SUNDAY: "Chủ nhật tuần trước",
}


ALIGNMENT_LABELS = {
    LessonPlanAlignment.LEFT: "Căn trái",
    LessonPlanAlignment.CENTER: "Căn giữa",
    LessonPlanAlignment.RIGHT: "Căn phải",
    LessonPlanAlignment.JUSTIFY: "Căn đều",
}


def _load_profile(
    *,
    session_key: str,
) -> LessonPlanTemplateProfile:
    profile = st.session_state.get(
        session_key
    )

    if isinstance(
        profile,
        LessonPlanTemplateProfile,
    ):
        return profile

    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    st.session_state[
        session_key
    ] = profile

    return profile


def _alignment_selectbox(
    *,
    label: str,
    value: LessonPlanAlignment,
    key: str,
):
    options = list(
        LessonPlanAlignment
    )

    return st.selectbox(
        label,
        options=options,
        index=options.index(value),
        format_func=lambda item: (
            ALIGNMENT_LABELS[item]
        ),
        key=key,
    )


def _weekday_selectbox(
    *,
    value: DraftingWeekday,
):
    options = list(
        DraftingWeekday
    )

    return st.selectbox(
        "Ngày soạn mặc định",
        options=options,
        index=options.index(value),
        format_func=lambda item: (
            WEEKDAY_LABELS[item]
        ),
        key="lesson_plan_setup_drafting_weekday",
    )


def _render_structure_editor(
    profile: LessonPlanTemplateProfile,
):
    st.subheader(
        "1. Cấu trúc và đề mục"
    )

    st.caption(
        "Quy định các đề mục chuẩn mà AI và "
        "engine sẽ dùng để kiểm tra giáo án."
    )

    rows = []

    for section in sorted(
        profile.structure.sections,
        key=lambda item: item.order,
    ):
        rows.append(
            {
                "key": section.key,
                "Đề mục": section.title,
                "Bắt buộc": section.required,
                "Sử dụng": section.enabled,
                "Thứ tự": section.order,
            }
        )

    edited = st.data_editor(
        rows,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="lesson_plan_structure_editor",
        column_config={
            "key": st.column_config.TextColumn(
                "Mã",
                disabled=True,
            ),
            "Đề mục": st.column_config.TextColumn(
                "Tên đề mục",
                required=True,
            ),
            "Bắt buộc": (
                st.column_config.CheckboxColumn(
                    "Bắt buộc"
                )
            ),
            "Sử dụng": (
                st.column_config.CheckboxColumn(
                    "Sử dụng"
                )
            ),
            "Thứ tự": (
                st.column_config.NumberColumn(
                    "Thứ tự",
                    min_value=0,
                    step=10,
                )
            ),
        },
    )

    sections = []

    for index, row in enumerate(
        edited
    ):
        key = (
            str(
                row.get("key")
                or f"CUSTOM_{index + 1}"
            )
            .strip()
        )

        title = str(
            row.get("Đề mục")
            or ""
        ).strip()

        if not title:
            continue

        sections.append(
            LessonPlanStructureSection(
                key=key,
                title=title,
                required=bool(
                    row.get(
                        "Bắt buộc",
                        True,
                    )
                ),
                enabled=bool(
                    row.get(
                        "Sử dụng",
                        True,
                    )
                ),
                order=int(
                    row.get(
                        "Thứ tự",
                        (index + 1) * 10,
                    )
                ),
            )
        )

    return LessonPlanStructureProfile(
        sections=tuple(sections)
    )


def _render_header_editor(
    profile: LessonPlanTemplateProfile,
):
    st.subheader(
        "2. Đầu giáo án"
    )

    st.caption(
        "Ngày soạn và ngày dạy ở bên trái; "
        "Tiết và tên bài ở giữa."
    )

    drafting_teaching_alignment = (
        _alignment_selectbox(
            label=(
                "Căn lề Ngày soạn / "
                "Ngày dạy / Lớp"
            ),
            value=(
                profile.header
                .drafting_teaching_alignment
            ),
            key=(
                "lesson_plan_setup_"
                "drafting_alignment"
            ),
        )
    )

    period_alignment = (
        _alignment_selectbox(
            label="Căn lề dòng Tiết",
            value=(
                profile.header
                .period_alignment
            ),
            key=(
                "lesson_plan_setup_"
                "period_alignment"
            ),
        )
    )

    period_bold = st.checkbox(
        "Tiết in đậm",
        value=profile.header.period_bold,
        key="lesson_plan_setup_period_bold",
    )

    lesson_title_alignment = (
        _alignment_selectbox(
            label="Căn lề tên bài",
            value=(
                profile.header
                .lesson_title_alignment
            ),
            key=(
                "lesson_plan_setup_"
                "title_alignment"
            ),
        )
    )

    col1, col2 = st.columns(2)

    lesson_title_uppercase = (
        col1.checkbox(
            "Tên bài viết HOA",
            value=(
                profile.header
                .lesson_title_uppercase
            ),
            key=(
                "lesson_plan_setup_"
                "title_uppercase"
            ),
        )
    )

    lesson_title_bold = (
        col2.checkbox(
            "Tên bài in đậm",
            value=(
                profile.header
                .lesson_title_bold
            ),
            key=(
                "lesson_plan_setup_"
                "title_bold"
            ),
        )
    )

    return LessonPlanHeaderProfile(
        drafting_teaching_alignment=(
            drafting_teaching_alignment
        ),
        period_alignment=period_alignment,
        period_bold=period_bold,
        lesson_title_alignment=(
            lesson_title_alignment
        ),
        lesson_title_uppercase=(
            lesson_title_uppercase
        ),
        lesson_title_bold=(
            lesson_title_bold
        ),
    )


def _render_layout_editor(
    profile: LessonPlanTemplateProfile,
):
    st.subheader(
        "3. Định dạng trang và văn bản"
    )

    col1, col2, col3 = st.columns(3)

    page_size = col1.selectbox(
        "Khổ giấy",
        options=("A4",),
        index=0,
        key="lesson_plan_setup_page_size",
    )

    font_name = col2.text_input(
        "Font chung",
        value=profile.layout.font_name,
        key="lesson_plan_setup_font_name",
    )

    body_font_size_pt = (
        col3.number_input(
            "Cỡ chữ chung",
            min_value=8.0,
            max_value=24.0,
            value=float(
                profile.layout
                .body_font_size_pt
            ),
            step=0.5,
            key=(
                "lesson_plan_setup_"
                "font_size"
            ),
        )
    )

    line_spacing = st.number_input(
        "Giãn dòng",
        min_value=0.8,
        max_value=3.0,
        value=float(
            profile.layout.line_spacing
        ),
        step=0.05,
        key=(
            "lesson_plan_setup_"
            "line_spacing"
        ),
    )

    st.markdown(
        "**Lề trang (cm)**"
    )

    c1, c2, c3, c4 = st.columns(4)

    margin_top_cm = c1.number_input(
        "Trên",
        min_value=0.0,
        value=float(
            profile.layout.margin_top_cm
        ),
        step=0.1,
        key="lesson_plan_margin_top",
    )

    margin_bottom_cm = c2.number_input(
        "Dưới",
        min_value=0.0,
        value=float(
            profile.layout.margin_bottom_cm
        ),
        step=0.1,
        key="lesson_plan_margin_bottom",
    )

    margin_left_cm = c3.number_input(
        "Trái",
        min_value=0.0,
        value=float(
            profile.layout.margin_left_cm
        ),
        step=0.1,
        key="lesson_plan_margin_left",
    )

    margin_right_cm = c4.number_input(
        "Phải",
        min_value=0.0,
        value=float(
            profile.layout.margin_right_cm
        ),
        step=0.1,
        key="lesson_plan_margin_right",
    )

    return LessonPlanLayoutProfile(
        page_size=page_size,
        font_name=font_name,
        body_font_size_pt=(
            body_font_size_pt
        ),
        line_spacing=line_spacing,
        margin_top_cm=margin_top_cm,
        margin_bottom_cm=(
            margin_bottom_cm
        ),
        margin_left_cm=margin_left_cm,
        margin_right_cm=margin_right_cm,
    )


def _render_scheduling_editor(
    profile: LessonPlanTemplateProfile,
):
    st.subheader(
        "4. Ngày soạn, ngày dạy và ngày duyệt"
    )

    st.info(
        "Ngày dạy lấy tự động từ Lịch báo giảng "
        "theo từng lớp. Giáo viên chỉ cấu hình "
        "Ngày soạn và Ngày duyệt."
    )

    drafting_weekday = (
        _weekday_selectbox(
            value=(
                profile.scheduling
                .drafting_weekday
            )
        )
    )

    approval_offset_days = (
        st.number_input(
            "Ngày duyệt sau Ngày soạn "
            "bao nhiêu ngày?",
            min_value=1,
            max_value=30,
            value=int(
                profile.scheduling
                .approval_offset_days
            ),
            step=1,
            key=(
                "lesson_plan_setup_"
                "approval_offset"
            ),
        )
    )

    allow_projected = st.checkbox(
        "Cho phép suy ra lịch dạy tuần kế tiếp "
        "khi chưa có TKB mới",
        value=(
            profile.scheduling
            .allow_projected_teaching_dates
        ),
        key=(
            "lesson_plan_setup_"
            "allow_projected"
        ),
    )

    projected_horizon = (
        st.number_input(
            "Số tuần tối đa được suy ra",
            min_value=0,
            max_value=8,
            value=int(
                profile.scheduling
                .projected_schedule_horizon_weeks
            ),
            step=1,
            disabled=not allow_projected,
            key=(
                "lesson_plan_setup_"
                "projected_horizon"
            ),
        )
    )

    return LessonPlanSchedulingPolicy(
        drafting_weekday=drafting_weekday,
        approval_offset_days=int(
            approval_offset_days
        ),
        allow_projected_teaching_dates=(
            allow_projected
        ),
        projected_schedule_horizon_weeks=int(
            projected_horizon
        ),
    )


def _render_approval_editor(
    profile: LessonPlanTemplateProfile,
):
    st.subheader(
        "5. Phê duyệt cuối giáo án"
    )

    alignment = (
        _alignment_selectbox(
            label=(
                "Vị trí Ngày duyệt / "
                "Tổ CM duyệt"
            ),
            value=(
                profile.approval.alignment
            ),
            key=(
                "lesson_plan_setup_"
                "approval_alignment"
            ),
        )
    )

    approval_label = st.text_input(
        "Nhãn phê duyệt",
        value=(
            profile.approval
            .approval_label
        ),
        key=(
            "lesson_plan_setup_"
            "approval_label"
        ),
    )

    signature_blank_lines = (
        st.number_input(
            "Số dòng trống dành cho ký duyệt",
            min_value=0,
            max_value=15,
            value=int(
                profile.approval
                .signature_blank_lines
            ),
            step=1,
            key=(
                "lesson_plan_setup_"
                "signature_blank_lines"
            ),
        )
    )

    return LessonPlanApprovalProfile(
        alignment=alignment,
        approval_label=approval_label,
        signature_blank_lines=int(
            signature_blank_lines
        ),
    )


def render_lesson_plan_template_setup(
    *,
    client=None,
    teacher_id: str | None = None,
    academic_year: str | None = None,
    embedded: bool = False,
):
    if not embedded:
        st.title(
            "M\u1eabu gi\u00e1o \u00e1n"
        )

        st.caption(
            "Thi\u1ebft l\u1eadp ri\u00eang "
            "theo t\u1eebng m\u00f4n: "
            "c\u1ea5u tr\u00fac, \u0111\u1ec1 m\u1ee5c, "
            "b\u1ed1 c\u1ee5c, \u0111\u1ecbnh d\u1ea1ng, "
            "l\u1ecbch so\u1ea1n v\u00e0 ph\u00ea duy\u1ec7t."
        )

    resolved_client = (
        client
        or st.session_state.get(
            "portal_supabase_client"
        )
    )

    resolved_teacher_id = str(
        teacher_id
        or st.session_state.get(
            "portal_user_id"
        )
        or ""
    ).strip()

    if (
        resolved_client is None
        or not resolved_teacher_id
    ):
        st.error(
            "Kh\u00f4ng x\u00e1c \u0111\u1ecbnh "
            "\u0111\u01b0\u1ee3c phi\u00ean "
            "gi\u00e1o vi\u00ean."
        )
        return None

    resolved_academic_year = str(
        academic_year
        or ""
    ).strip()

    if not resolved_academic_year:
        resolved_academic_year = (
            st.text_input(
                "N\u0103m h\u1ecdc",
                key=(
                    "lesson_plan_template_"
                    "academic_year"
                ),
                placeholder="2026-2027",
            )
            .strip()
        )

    if not resolved_academic_year:
        st.info(
            "Nh\u1eadp n\u0103m h\u1ecdc "
            "\u0111\u1ec3 t\u1ea3i c\u00e1c m\u00f4n "
            "\u0111ang \u0111\u01b0\u1ee3c "
            "ph\u00e2n c\u00f4ng."
        )
        return None

    assignment_repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=resolved_client
        )
    )

    subject_repository = (
        SupabaseSubjectCatalogRepository(
            client=resolved_client
        )
    )

    subject_service = (
        TeacherLessonPlanSubjectService(
            assignment_repository=(
                assignment_repository
            ),
            subject_repository=(
                subject_repository
            ),
        )
    )

    try:
        subjects = (
            subject_service.list_subjects(
                teacher_id=(
                    resolved_teacher_id
                ),
                academic_year=(
                    resolved_academic_year
                ),
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 t\u1ea3i "
            "danh s\u00e1ch m\u00f4n "
            "\u0111\u01b0\u1ee3c ph\u00e2n c\u00f4ng: "
            + str(error)
        )
        return None

    if not subjects:
        st.warning(
            "Gi\u00e1o vi\u00ean ch\u01b0a c\u00f3 "
            "m\u00f4n \u0111ang ho\u1ea1t \u0111\u1ed9ng "
            "trong ph\u00e2n c\u00f4ng "
            "c\u1ee7a n\u0103m h\u1ecdc n\u00e0y."
        )
        return None

    subject_by_id = {
        item.subject_id: item
        for item in subjects
    }

    selected_subject_id = st.selectbox(
        "M\u00f4n \u00e1p d\u1ee5ng",
        options=tuple(
            subject_by_id.keys()
        ),
        format_func=lambda value: (
            subject_by_id[value].name
        ),
        key=(
            "lesson_plan_template_subject"
        ),
    )

    previous_subject_id = (
        st.session_state.get(
            SUBJECT_CONTEXT_KEY
        )
    )

    if (
        previous_subject_id
        and previous_subject_id
        != selected_subject_id
    ):
        _clear_template_widget_state()

    st.session_state[
        SUBJECT_CONTEXT_KEY
    ] = selected_subject_id

    selected_subject = (
        subject_by_id[
            selected_subject_id
        ]
    )

    st.caption(
        "C\u1ea5u h\u00ecnh hi\u1ec7n t\u1ea1i: "
        + selected_subject.name
        + " \u00b7 "
        + resolved_academic_year
    )

    profile_session_key = (
        _template_profile_session_key(
            teacher_id=(
                resolved_teacher_id
            ),
            academic_year=(
                resolved_academic_year
            ),
            subject_id=(
                selected_subject_id
            ),
        )
    )

    subject_profile_session_key = (
        _subject_profile_session_key(
            teacher_id=(
                resolved_teacher_id
            ),
            academic_year=(
                resolved_academic_year
            ),
            subject_id=(
                selected_subject_id
            ),
        )
    )

    stored_subject_profile = (
        st.session_state.get(
            subject_profile_session_key
        )
    )

    if isinstance(
        stored_subject_profile,
        SubjectLessonPlanProfile,
    ):
        subject_profile = (
            stored_subject_profile
        )
    else:
        default_template = (
            LessonPlanTemplateProfile
            .default()
        )

        subject_profile = (
            SubjectLessonPlanProfile(
                teacher_id=(
                    resolved_teacher_id
                ),
                subject_id=(
                    selected_subject_id
                ),
                templates=(
                    default_template,
                ),
            )
        )

        st.session_state[
            subject_profile_session_key
        ] = subject_profile

    profile = _load_profile(
        session_key=(
            profile_session_key
        )
    )

    st.subheader(
        "Ph\u1ea1m vi v\u00e0 c\u00e1ch "
        "t\u1ed5 ch\u1ee9c gi\u00e1o \u00e1n"
    )

    selected_modes = tuple(
        st.multiselect(
            "C\u00e1c c\u00e1ch ch\u1ecdn "
            "\u0111\u01b0\u1ee3c ph\u00e9p",
            options=tuple(
                LessonPlanSelectionMode
            ),
            default=(
                subject_profile
                .allowed_selection_modes
            ),
            format_func=lambda item: (
                _selection_mode_label(item)
            ),
            key=(
                "lesson_plan_setup_"
                "allowed_selection_modes"
            ),
        )
    )

    if not selected_modes:
        st.warning(
            "Ph\u1ea3i cho ph\u00e9p "
            "\u00edt nh\u1ea5t m\u1ed9t "
            "c\u00e1ch ch\u1ecdn."
        )

        selected_modes = (
            LessonPlanSelectionMode.LESSON,
        )

    default_mode = (
        subject_profile
        .default_selection_mode
    )

    if (
        default_mode
        not in selected_modes
    ):
        default_mode = (
            selected_modes[0]
        )

    default_mode = st.selectbox(
        "C\u00e1ch ch\u1ecdn m\u1eb7c \u0111\u1ecbnh",
        options=selected_modes,
        index=selected_modes.index(
            default_mode
        ),
        format_func=lambda item: (
            _selection_mode_label(item)
        ),
        key=(
            "lesson_plan_setup_"
            "default_selection_mode"
        ),
    )

    st.divider()

    profile_name = st.text_input(
        "Tên mẫu giáo án",
        value=profile.profile_name,
        key=(
            "lesson_plan_setup_"
            "profile_name"
        ),
    )

    with st.expander(
        "Cấu trúc và đề mục",
        expanded=True,
    ):
        structure = (
            _render_structure_editor(
                profile
            )
        )

    with st.expander(
        "Đầu giáo án",
        expanded=True,
    ):
        header = (
            _render_header_editor(
                profile
            )
        )

    with st.expander(
        "Định dạng Word",
        expanded=False,
    ):
        layout = (
            _render_layout_editor(
                profile
            )
        )

    with st.expander(
        "Ngày soạn - Ngày dạy - Ngày duyệt",
        expanded=True,
    ):
        scheduling = (
            _render_scheduling_editor(
                profile
            )
        )

    with st.expander(
        "Phê duyệt cuối giáo án",
        expanded=True,
    ):
        approval = (
            _render_approval_editor(
                profile
            )
        )

    candidate = (
        LessonPlanTemplateProfile(
            profile_name=(
                profile_name.strip()
                or profile.profile_name
            ),
            structure=structure,
            header=header,
            layout=layout,
            scheduling=scheduling,
            approval=approval,
            is_default=profile.is_default,
        )
    )

    st.divider()

    col_save, col_reset = (
        st.columns(2)
    )

    if col_save.button(
        "Lưu Mẫu giáo án",
        type="primary",
        use_container_width=True,
    ):
        st.session_state[
            profile_session_key
        ] = candidate

        st.session_state[
            subject_profile_session_key
        ] = SubjectLessonPlanProfile(
            teacher_id=(
                resolved_teacher_id
            ),
            subject_id=(
                selected_subject_id
            ),
            templates=(
                candidate,
            ),
            default_selection_mode=(
                default_mode
            ),
            allowed_selection_modes=(
                tuple(
                    selected_modes
                )
            ),
        )

        st.success(
            "Đã lưu Mẫu giáo án "
            "trong phiên làm việc."
        )

    if col_reset.button(
        "Khôi phục mẫu mặc định",
        use_container_width=True,
    ):
        default_profile = (
            LessonPlanTemplateProfile
            .default()
        )

        st.session_state[
            profile_session_key
        ] = default_profile

        st.session_state[
            subject_profile_session_key
        ] = SubjectLessonPlanProfile(
            teacher_id=(
                resolved_teacher_id
            ),
            subject_id=(
                selected_subject_id
            ),
            templates=(
                default_profile,
            ),
        )

        _clear_template_widget_state()

        st.rerun()

    return candidate
