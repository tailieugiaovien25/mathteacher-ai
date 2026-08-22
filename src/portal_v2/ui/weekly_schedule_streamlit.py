from __future__ import annotations

from pathlib import Path

import streamlit as st

from educational_planning_v2.adapters.operational_weekly_schedule_workbook_intake import (
    WeeklyScheduleWorkbookIntakeAdapter,
)
from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
)
from educational_planning_v2.services.local_weekly_schedule_generation_service import (
    LocalWeeklyScheduleGenerationService,
    WeeklyScheduleGenerationRequest,
    WeeklyScheduleGenerationResult,
)
from educational_planning_v2.services.operational_input_selection_service import (
    OperationalInputSelection,
)
from educational_planning_v2.services.weekly_schedule_output_service import (
    WeeklyScheduleOutputService,
)
from portal_v2.ui.weekly_schedule_portal import (
    WeeklySchedulePortalPresenter,
)
from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_academic_week_repository import (
    SupabaseAcademicWeekRepository,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.ppct_scope_resolver import (
    PPCTScopeMappingRule,
)
from portal_v2.runtime.system_weekly_schedule_runtime import (
    SystemWeeklyScheduleRuntime,
    SystemWeeklyScheduleRuntimeRequest,
)
from lesson_planning_v2.services.lesson_plan_lesson_selector_service import LessonPlanLessonSelectorService
from lesson_planning_v2.services.lesson_plan_draft_workspace_service import (
    LessonPlanDraftWorkspaceService,
)
from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)

from lesson_planning_v2.services.lesson_plan_unit_selector_service import (
    LessonPlanSelectionMode,
    LessonPlanUnitSelectorService,
)
from lesson_planning_v2.services import (
    LessonPlanDocumentProcessingService,
)

from document_intelligence.lesson_plan_preview_upload import (
    LessonPlanPreviewUploadService,
)
from document_intelligence.validation import (
    CanonicalDocumentContext,
)
from portal_v2.ui.lesson_plan_preview_streamlit import (
    render_lesson_plan_preview,
)
from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_teacher_review_presenter import (
    LessonPlanTeacherReviewPresenter,
)
from document_intelligence.lesson_plan_teacher_review_resolver import (
    LessonPlanTeacherReviewResolver,
)
from document_intelligence.lesson_plan_modification_plan import (
    LessonPlanModificationPlanner,
)
from document_intelligence.lesson_plan_reviewed_schedule_row import (
    LessonPlanReviewedScheduleRow,
)
from document_intelligence.lesson_plan_workflow_state import (
    LessonPlanWorkflowIdentity,
    LessonPlanWorkflowState,
)
from portal_v2.ui.lesson_plan_teacher_review_streamlit import (
    render_lesson_plan_teacher_review,
)

from scripts.teacher_portal.lesson_plan_visual_viewer import (
    build_document_html,
)

_VIEW_STATE_KEY = "weekly_schedule_portal_view"

_LESSON_PLAN_PROFILE = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "word_standardizer"
    / "lesson_plan_profile.json"
)


def _local_selection() -> OperationalInputSelection:
    return OperationalInputSelection(
        reference=OperationalInputReference(
            location=OperationalInputLocation.LOCAL_UPLOAD,
        ),
        source=None,
    )


def _academic_year_options(intake) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                week.academic_year
                for week in intake.source_data.academic_weeks
            }
        )
    )


def _week_options(
    intake,
    academic_year: str,
) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                week.week_number
                for week in intake.source_data.academic_weeks
                if week.academic_year == academic_year
            }
        )
    )


def _teacher_options(intake) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                slot.teacher_id
                for slot in intake.source_data.timetable_slots
            }
        )
    )


def _resolve_lbg_display_names(
    *,
    client,
    view,
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    class_names: dict[str, str] = {}
    subject_names: dict[str, str] = {}
    component_names: dict[str, str] = {}

    if client is None:
        return (
            class_names,
            subject_names,
            component_names,
        )

    class_repository = (
        SupabaseClassCatalogRepository(
            client=client,
        )
    )

    subject_repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    class_ids = {
        row.class_id
        for row in view.rows
        if row.class_id
    }

    subject_ids = {
        row.subject_ref
        for row in view.rows
        if row.subject_ref
    }

    component_ids = {
        row.component_ref
        for row in view.rows
        if row.component_ref
    }

    for class_id in class_ids:
        try:
            item = class_repository.get(
                class_id=class_id,
            )

            if item is not None:
                class_names[class_id] = (
                    item.display_name
                )

        except Exception:
            pass

    for subject_id in subject_ids:
        try:
            item = (
                subject_repository.get_subject(
                    subject_id=subject_id,
                )
            )

            if item is not None:
                subject_names[subject_id] = (
                    item.name
                )

        except Exception:
            pass

    for component_id in component_ids:
        try:
            item = (
                subject_repository.get_component(
                    component_id=component_id,
                )
            )

            if item is not None:
                component_names[component_id] = (
                    item.name
                )

        except Exception:
            pass

    return (
        class_names,
        subject_names,
        component_names,
    )


def _preview_rows(
    view,
    *,
    class_names: dict[str, str] | None = None,
    subject_names: dict[str, str] | None = None,
    component_names: dict[str, str] | None = None,
) -> list[dict]:
    class_names = class_names or {}
    subject_names = subject_names or {}
    component_names = component_names or {}

    return [
        {
            "Th\u1ee9/ng\u00e0y":
                (
                    f"{row.weekday} - "
                    f"{row.teaching_date.strftime('%d/%m/%Y')}"
                ),

            "Ti\u1ebft TKB":
                row.timetable_period,

            "M\u00f4n/Ph\u00e2n m\u00f4n":
                (
                    component_names.get(
                        row.component_ref,
                        row.component_ref,
                    )
                    if row.component_ref
                    else subject_names.get(
                        row.subject_ref,
                        row.subject_ref,
                    )
                    or ""
                ),

            "L\u1edbp":
                class_names.get(
                    row.class_id,
                    row.class_id,
                ),

            "Ti\u1ebft PPCT":
                row.curriculum_period,

            "T\u00ean b\u00e0i d\u1ea1y":
                row.lesson_title,

            "Chu\u1ea9n b\u1ecb, \u0111i\u1ec1u ch\u1ec9nh":
                ", ".join(
                    row.teaching_equipment
                ),

            "Ghi ch\u00fa":
                "",
        }
        for row in view.rows
    ]


def _render_lbg_table(
    view,
    *,
    client=None,
    teacher_user_id="",
) -> None:
    (
        class_names,
        subject_names,
        component_names,
    ) = _resolve_lbg_display_names(
        client=client,
        view=view,
    )

    rows = _preview_rows(
        view,
        class_names=class_names,
        subject_names=subject_names,
        component_names=component_names,
    )

    if not rows:
        st.info(
            "Tu\u1ea7n n\u00e0y ch\u01b0a c\u00f3 "
            "ti\u1ebft d\u1ea1y trong L\u1ecbch b\u00e1o gi\u1ea3ng."
        )
        return

    st.data_editor(
        rows,
        width="stretch",
        hide_index=True,
        disabled=(
            "Th\u1ee9/ng\u00e0y",
            "Ti\u1ebft TKB",
            "M\u00f4n/Ph\u00e2n m\u00f4n",
            "L\u1edbp",
            "Ti\u1ebft PPCT",
            "T\u00ean b\u00e0i d\u1ea1y",
        ),
        key=(
            "lbg_user_editor_"
            + str(view.week_number)
        ),
    )

    _render_lesson_plan_standardization_workspace(
        view,
        teacher_user_id=teacher_user_id,

        client=client,
)




def _process_lesson_plan_upload(
    *,
    row,
    drafting_date,
    content: bytes,
    original_name: str,
    modification_plan=None,
) -> tuple[
    str,
    bytes,
    tuple[str, ...],
]:
    service = (
        LessonPlanDocumentProcessingService(
            profile_path=(
                _LESSON_PLAN_PROFILE
            )
        )
    )

    result = service.process(
        row=row,
        drafting_date=drafting_date,
        content=content,
        original_name=original_name,
        modification_plan=modification_plan,
    )

    return (
        result.output_name,
        result.output_bytes,
        result.unresolved_fields,
    )



def _lesson_plan_lesson_options_from_rows(
    rows,
):
    """
    Build lesson-level choices from the current
    weekly schedule.

    Transitional adapter:
    downstream processing still receives one
    representative schedule row.
    """

    grouped = {}

    for index, row in enumerate(rows):
        lesson_title = str(
            getattr(
                row,
                "lesson_title",
                "",
            )
            or ""
        ).strip()

        curriculum_period = getattr(
            row,
            "curriculum_period",
            None,
        )

        if (
            not lesson_title
            or curriculum_period is None
        ):
            continue

        item = grouped.setdefault(
            lesson_title,
            {
                "lesson_title": lesson_title,
                "periods": set(),
                "classes": set(),
                "teaching_dates": [],
                "row_indices": [],
            },
        )

        item["periods"].add(
            int(curriculum_period)
        )

        class_id = str(
            getattr(
                row,
                "class_id",
                "",
            )
            or ""
        ).strip()

        if class_id:
            item["classes"].add(
                class_id
            )

        teaching_date = getattr(
            row,
            "teaching_date",
            None,
        )

        if teaching_date is not None:
            item["teaching_dates"].append(
                (
                    teaching_date,
                    class_id,
                )
            )

        item["row_indices"].append(
            index
        )

    result = []

    for item in grouped.values():
        periods = tuple(
            sorted(
                item["periods"]
            )
        )

        classes = tuple(
            sorted(
                item["classes"]
            )
        )

        teaching_dates = tuple(
            sorted(
                set(
                    item[
                        "teaching_dates"
                    ]
                ),
                key=lambda value: (
                    value[0],
                    value[1],
                ),
            )
        )

        row_indices = tuple(
            item["row_indices"]
        )

        if not row_indices:
            continue

        period_text = " + ".join(
            str(value)
            for value in periods
        )

        result.append(
            {
                "lesson_title": (
                    item["lesson_title"]
                ),
                "periods": periods,
                "classes": classes,
                "teaching_dates": (
                    teaching_dates
                ),
                "row_indices": (
                    row_indices
                ),
                "representative_index": (
                    row_indices[0]
                ),
                "label": (
                    f"{item['lesson_title']} "
                    f"(Ti\u1ebft {period_text})"
                ),
            }
        )

    return tuple(
        sorted(
            result,
            key=lambda item: (
                (
                    item["periods"][0]
                    if item["periods"]
                    else 10**9
                ),
                item["lesson_title"],
            ),
        )
    )


def _class_display_name(
    class_id: str,
    *,
    client=None,
) -> str:
    """
    Resolve canonical class_id to the teacher-facing
    class name.

    class_id remains the internal canonical identifier.
    Only the UI/document-facing value is converted.
    """
    value = str(
        class_id or ""
    ).strip()

    if not value:
        return "-"

    if client is not None:
        try:
            item = (
                SupabaseClassCatalogRepository(
                    client=client
                )
                .get(
                    class_id=value
                )
            )

            if item is not None:
                class_name = str(
                    getattr(
                        item,
                        "class_name",
                        "",
                    )
                    or ""
                ).strip()

                if class_name:
                    return class_name

                class_code = str(
                    getattr(
                        item,
                        "class_code",
                        "",
                    )
                    or ""
                ).strip()

                if class_code:
                    return class_code

        except Exception:
            pass

    try:
        runtime = st.session_state.get(
            "_system_weekly_schedule_runtime"
        )

        repository = getattr(
            runtime,
            "_class_repository",
            None,
        )

        if repository is not None:
            item = repository.get(
                class_id=value,
            )

            if item is not None:
                class_name = str(
                    getattr(
                        item,
                        "class_name",
                        "",
                    )
                    or ""
                ).strip()

                if class_name:
                    return class_name

                class_code = str(
                    getattr(
                        item,
                        "class_code",
                        "",
                    )
                    or ""
                ).strip()

                if class_code:
                    return class_code

    except Exception:
        pass

    return value


def _render_selected_lesson_summary(
    lesson,
    *,
    drafting_date=None,
    client=None,
) -> None:
    lesson_title = str(
        lesson.get(
            "lesson_title",
            "",
        )
        or ""
    ).strip()

    periods = tuple(
        lesson.get(
            "periods",
            (),
        )
        or ()
    )

    teaching_dates = tuple(
        lesson.get(
            "teaching_dates",
            (),
        )
        or ()
    )

    st.markdown(
        "**B\u00e0i:** "
        + (
            lesson_title
            or "-"
        )
    )

    st.markdown(
        "**S\u1ed1 ti\u1ebft:** "
        + str(
            len(periods)
        )
    )

    st.markdown(
        "**Ng\u00e0y d\u1ea1y - L\u1edbp**"
    )

    if not teaching_dates:
        st.write("-")
        return

    for (
        teaching_date,
        class_id,
    ) in teaching_dates:
        try:
            date_text = (
                teaching_date.strftime(
                    "%d/%m/%Y"
                )
            )
        except Exception:
            date_text = str(
                teaching_date
            )

        st.write(
            date_text
            + " - "
            + _class_display_name(
                class_id,
                client=client,
            )
        )



def _lesson_plan_row_label(
    row,
) -> str:
    return (
        f"{row.teaching_date.strftime('%d/%m/%Y')}"
        f" | Ti\u1ebft TKB {row.timetable_period}"
        f" | {row.class_id}"
        f" | PPCT {row.curriculum_period}"
        f" | {row.lesson_title}"
    )



def _render_lesson_plan_drafting_workspace(
    selected_lesson=None,
    teacher_user_id="",
    academic_year="",
    week_number=0,
    selection_mode="LESSON",
    selection_unit_id="",
    client=None,
) -> None:
    """
    Complete V1 teacher-facing lesson-plan editor.

    Draft identity is scoped by teacher, academic year,
    week, subject, selection mode and selection unit.
    """
    from lesson_planning_v2.services.lesson_plan_draft_workspace_service import (
        LessonPlanDraftWorkspaceService,
    )
    from lesson_planning_v2.services.lesson_plan_workspace_v1_service import (
        LessonPlanDocxTextImporter,
        LessonPlanDocxWholeDocumentImporter,
        LessonPlanFullDocumentDocxAdapter,
        LessonPlanLibrarySourceService,
        LessonPlanSimpleDocxExporter,
        LessonPlanWorkspaceContent,
        LessonPlanWorkspaceContext,
        LessonPlanWorkspaceV1Service,
    )

    st.subheader("✨ SOẠN BÀI CÙNG AI")

    selected = (
        selected_lesson
        if isinstance(
            selected_lesson,
            dict,
        )
        else {}
    )

    normalized_teacher = str(
        teacher_user_id
    ).strip()

    normalized_year = str(
        academic_year
    ).strip()

    try:
        normalized_week = int(
            week_number
        )
    except (
        TypeError,
        ValueError,
    ):
        normalized_week = 0

    normalized_unit = str(
        selection_unit_id
    ).strip()

    normalized_mode = (
        getattr(
            selection_mode,
            "value",
            selection_mode,
        )
    )

    normalized_mode = str(
        normalized_mode
    ).strip() or "LESSON"

    subject_ref = str(
        selected.get(
            "subject_ref",
            selected.get(
                "subject_id",
                selected.get(
                    "subject",
                    "general",
                ),
            ),
        )
    ).strip() or "general"

    class_id = str(
        selected.get(
            "class_id",
            "",
        )
    ).strip()

    grade_level = str(
        selected.get(
            "grade_level",
            "",
        )
    ).strip()

    class_ref = str(
        selected.get(
            "class_name",
            "",
        )
    ).strip()

    if (
        not class_ref
        and class_id
        and client is not None
    ):
        try:
            class_item = (
                SupabaseClassCatalogRepository(
                    client=client
                )
                .get(
                    class_id=class_id
                )
            )

            if class_item is not None:
                class_ref = str(
                    class_item.class_name
                ).strip()

                if not grade_level:
                    grade_level = str(
                        class_item.grade_level
                    ).strip()

        except Exception:
            # Display-name resolution must never
            # destroy the lesson-plan workspace.
            pass

    if not class_ref:
        class_ref = (
            grade_level
            or class_id
            or "N/A"
        )

    lesson_title = str(
        selected.get(
            "lesson_title",
            selected.get(
                "title",
                "",
            ),
        )
    ).strip()

    curriculum_period = (
        selected.get(
            "curriculum_period"
        )
    )

    teaching_date = (
        selected.get(
            "teaching_date"
        )
    )

    if (
        not normalized_teacher
        or not normalized_year
        or normalized_week <= 0
        or not normalized_unit
    ):
        st.info(
            "Ch\u1ecdn \u0111\u1ea7y \u0111\u1ee7 b\u00e0i/ti\u1ebft v\u00e0 tu\u1ea7n "
            "\u0111\u1ec3 b\u1eaft \u0111\u1ea7u so\u1ea1n b\u00e0i."
        )
        return

    try:
        context = (
            LessonPlanWorkspaceContext(
                teacher_user_id=(
                    normalized_teacher
                ),
                academic_year=(
                    normalized_year
                ),
                week_number=(
                    normalized_week
                ),
                subject_ref=subject_ref,
                selection_mode=(
                    normalized_mode
                ),
                selection_unit_id=(
                    normalized_unit
                ),
                class_or_grade_ref=(
                    class_ref
                ),
                lesson_id=(
                    normalized_unit
                ),
                title=lesson_title,
            )
        )
    except ValueError as error:
        st.error(str(error))
        return

    repository = st.session_state.get(
        "lesson_plan_workspace_draft_repository"
    )

    if repository is None:
        st.error(
            "Kho l\u01b0u b\u1ea3n nh\u00e1p ch\u01b0a s\u1eb5n s\u00e0ng. "
            "H\u00e3y \u0111\u0103ng nh\u1eadp l\u1ea1i."
        )
        return

    draft_service = (
        LessonPlanDraftWorkspaceService(
            repository
        )
    )

    workspace_service = (
        LessonPlanWorkspaceV1Service(
            draft_service=draft_service
        )
    )

    try:
        persisted = (
            workspace_service.load(
                context=context
            )
        )
    except Exception as error:
        st.warning(
            "Chưa thể đọc bản nháp đã lưu: "
            + str(error)
        )
        persisted = None

    prefix = context.widget_prefix

    objectives_key = (
        prefix + "_objectives"
    )
    materials_key = (
        prefix + "_materials"
    )
    process_key = (
        prefix + "_process"
    )

    full_document_key = (
        prefix + "_full_document"
    )

    source_key = (
        prefix + "_source_mode"
    )

    standardization_transfer_key = (
        prefix
        + "_standardization_transfer"
    )

    standardization_transfer_ready_key = (
        prefix
        + "_standardization_transfer_ready"
    )

    # Initialize each lesson independently.
    if objectives_key not in st.session_state:
        st.session_state[
            objectives_key
        ] = (
            persisted.objectives_text
            if persisted is not None
            else ""
        )

    if materials_key not in st.session_state:
        st.session_state[
            materials_key
        ] = (
            persisted.materials_text
            if persisted is not None
            else ""
        )

    if process_key not in st.session_state:
        st.session_state[
            process_key
        ] = (
            persisted.teaching_process_text
            if persisted is not None
            else ""
        )

    if full_document_key not in st.session_state:
        persisted_full_document = ""

        if persisted is not None:
            persisted_full_document = str(
                getattr(
                    persisted,
                    "full_document_text",
                    "",
                )
                or ""
            ).strip()

        if persisted_full_document:
            st.session_state[
                full_document_key
            ] = persisted_full_document

        else:
            legacy_parts = []

            if st.session_state[
                objectives_key
            ].strip():
                legacy_parts.extend(
                    (
                        "I. M\u1ee4C TI\u00caU",
                        st.session_state[
                            objectives_key
                        ].strip(),
                    )
                )

            if st.session_state[
                materials_key
            ].strip():
                legacy_parts.extend(
                    (
                        (
                            "II. THI\u1ebeT B\u1eca "
                            "V\u00c0 H\u1eccC LI\u1ec6U"
                        ),
                        st.session_state[
                            materials_key
                        ].strip(),
                    )
                )

            if st.session_state[
                process_key
            ].strip():
                legacy_parts.extend(
                    (
                        (
                            "III. TI\u1ebeN TR\u00ccNH "
                            "D\u1ea0Y H\u1eccC"
                        ),
                        st.session_state[
                            process_key
                        ].strip(),
                    )
                )

            st.session_state[
                full_document_key
            ] = "\n\n".join(
                legacy_parts
            ).strip()


    st.caption(
        "Bản nháp được lưu riêng theo "
        "giáo viên và bài/tiết đang chọn."
    )

    mode = st.radio(
        "Cách bắt đầu",
        (
            "Soạn mới cùng AI",
            "Tải & chỉnh sửa giáo án cũ",
        ),
        horizontal=True,
        key=source_key,
    )

    uploaded = None

    if mode == "Tải & chỉnh sửa giáo án cũ":
        uploaded = st.file_uploader(
            "Tải giáo án cũ để chỉnh sửa",
            type=("docx",),
            key=prefix + "_upload",
        )

        if uploaded is not None:
            import_clicked = st.button(
                "Đưa giáo án vào trình chỉnh sửa",
                key=prefix + "_import_word",
            )

            if import_clicked:
                try:
                    imported = (
                        LessonPlanDocxWholeDocumentImporter()
                        .import_bytes(
                            uploaded.getvalue()
                        )
                    )

                    st.session_state[
                        full_document_key
                    ] = imported

                    st.session_state[
                        objectives_key
                    ] = ""

                    st.session_state[
                        materials_key
                    ] = ""

                    st.session_state[
                        process_key
                    ] = ""

                    st.session_state[
                        prefix
                        + "_source_docx"
                    ] = uploaded.getvalue()

                    st.session_state[
                        prefix
                        + "_source_name"
                    ] = uploaded.name

                    st.success(
                        "Đã đưa nội dung Word "
                        "vào trình soạn."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        "Không thể đọc file Word: "
                        + str(error)
                    )

    st.markdown("---")

    st.markdown(
        "### Không gian làm việc"
    )

    st.caption(
        "Giáo án được "
        "chỉnh sửa ở khung bên trái. "
        "Khung bên phải dành cho AI "
        "phân tích, đề xuất "
        "và tiếp nhận yêu cầu "
        "của giáo viên."
    )

    editor_col, ai_col = st.columns(
        [7, 3],
        gap="large",
    )

    with editor_col:
        st.markdown(
            '#### \U0001f4c4 Gi\xe1o \xe1n \u0111ang l\xe0m vi\u1ec7c'
        )

        st.caption(
            'To\xe0n b\u1ed9 gi\xe1o \xe1n \u0111\u01b0\u1ee3c hi\u1ec3n th\u1ecb v\xe0 ch\u1ec9nh s\u1eeda li\xean t\u1ee5c trong m\u1ed9t v\xf9ng.'
        )

        full_document = st.text_area(
            'N\u1ed9i dung gi\xe1o \xe1n',
            key=full_document_key,
            height=1000,
            label_visibility="collapsed",
            placeholder=(
                'N\u1ed9i dung gi\xe1o \xe1n s\u1ebd xu\u1ea5t hi\u1ec7n t\u1ea1i \u0111\xe2y. B\u1ea1n c\xf3 th\u1ec3 so\u1ea1n m\u1edbi ho\u1eb7c t\u1ea3i gi\xe1o \xe1n c\u0169 \u0111\u1ec3 ti\u1ebfp t\u1ee5c ch\u1ec9nh s\u1eeda.'
            ),
        )

    with ai_col:
        st.markdown(
            "#### ✨ Trợ lý AI"
        )

        st.caption(
            "AI đọc giáo án "
            "và chủ động "
            "đề xuất trước. "
            "Giáo viên quyết định "
            "nội dung nào được "
            "áp dụng."
        )

        st.info(
            "AI sẽ phân tích "
            "giáo án đang làm việc "
            "và đưa ra các "
            "đề xuất về "
            "mục tiêu, học liệu "
            "và tiến trình dạy học."
        )

        st.markdown(
            "##### Đề xuất của AI"
        )

        ai_suggestion_box = st.container(
            border=True
        )

        with ai_suggestion_box:
            st.markdown(
                "**Chưa có "
                "đề xuất.**"
            )

            st.write(
                "Ở bước tiếp theo, "
                "AI sẽ chủ động "
                "phân tích nội dung "
                "giáo án và hiển thị "
                "đề xuất tại đây."
            )

        st.markdown(
            "##### Yêu cầu AI "
            "chỉnh sửa"
        )

        ai_request = st.text_area(
            "Yêu cầu AI",
            key=prefix + "_ai_request",
            height=220,
            placeholder=(
                "Ví dụ: Bổ sung "
                "hoạt động khởi "
                "động; điều chỉnh "
                "mục tiêu theo yêu cầu "
                "cần đạt; làm rõ "
                "sản phẩm học tập..."
            ),
            label_visibility="collapsed",
        )

        ai_request_clicked = st.button(
            "Gửi yêu cầu cho AI",
            key=prefix + "_ai_request_submit",
            use_container_width=True,
            disabled=True,
        )

        st.caption(
            "Chức năng AI sẽ "
            "được kết nối "
            "ở bước tiếp theo. "
            "Hiện tại AI chưa "
            "tự động thay đổi "
            "nội dung giáo án."
        )


    content = (
        LessonPlanWorkspaceContent(
            objectives_text="",
            materials_text="",
            teaching_process_text="",
            full_document_text=(
                full_document
            ),
        )
    )

    st.markdown("---")

    st.markdown(
        '### B\u01b0\u1edbc ti\u1ebfp theo'
    )

    st.caption(
        'Khi n\u1ed9i dung gi\xe1o \xe1n \u0111\xe3 ph\xf9 h\u1ee3p, chuy\u1ec3n tr\u1ef1c ti\u1ebfp sang c\xf4ng c\u1ee5 Chu\u1ea9n h\xf3a gi\xe1o \xe1n theo L\u1ecbch b\xe1o gi\u1ea3ng. Kh\xf4ng c\u1ea7n xu\u1ea5t Word trung gian.'
    )

    transfer_clicked = st.button(
        '\u27a1\ufe0f Chuy\u1ec3n sang Chu\u1ea9n h\xf3a gi\xe1o \xe1n theo L\u1ecbch b\xe1o gi\u1ea3ng',
        key=(
            prefix
            + "_transfer_to_standardization"
        ),
        type="primary",
        use_container_width=True,
        disabled=(
            not str(
                full_document
            ).strip()
        ),
    )

    if transfer_clicked:
        try:
            source_docx_bytes = (
                st.session_state.get(
                    prefix + "_source_docx"
                )
            )

            if (
                isinstance(
                    source_docx_bytes,
                    bytes,
                )
                and source_docx_bytes
            ):
                # Preservation-first:
                # preserve the uploaded DOCX package.
                internal_docx_bytes = (
                    source_docx_bytes
                )

            else:
                # Fallback for lesson plans created
                # without an uploaded DOCX source.
                internal_docx_bytes = (
                    LessonPlanFullDocumentDocxAdapter()
                    .build_bytes(
                        full_document
                    )
                )

        except Exception as error:
            st.error(
                "Không thể chuẩn bị "
                "giáo án để "
                "chuyển sang bước "
                "chuẩn hóa: "
                + str(error)
            )

            internal_docx_bytes = None

        if internal_docx_bytes is not None:
            transfer_source_name = (
                (
                    str(
                        lesson_title
                    ).strip()
                    or "giao-an-ai"
                )
                + ".docx"
            )

            st.session_state[
                standardization_transfer_key
            ] = {
                "source": "AI_DRAFT",
                "docx_bytes": (
                    internal_docx_bytes
                ),
                "source_name": (
                    transfer_source_name
                ),
                "teacher_user_id": (
                    normalized_teacher
                ),
                "academic_year": (
                    normalized_year
                ),
                "week_number": (
                    normalized_week
                ),
                "subject_ref": (
                    subject_ref
                ),
                "selection_mode": (
                    normalized_mode
                ),
                "selection_unit_id": (
                    normalized_unit
                ),
                "lesson_title": (
                    lesson_title
                ),
                "class_ref": (
                    class_ref
                ),
                "full_document_text": str(
                    full_document
                ),
            }

            st.session_state[
                standardization_transfer_ready_key
            ] = True

            st.success(
                "Đã chuyển giáo án "
                "đang làm việc sang "
                "bước Chuẩn hóa "
                "giáo án theo "
                "Lịch báo giảng."
            )

    save_clicked = st.button(
        "Lưu bản nháp",
        key=prefix + "_save",
        use_container_width=True,
    )

    if save_clicked:
        try:
            saved = workspace_service.save(
                context=context,
                content=content,
                source=mode,
            )

            verified = (
                workspace_service.load(
                    context=context
                )
            )

            if verified != saved:
                st.error(
                    "Không thể xác nhận "
                    "bản nháp để lưu."
                )
            else:
                st.success(
                    "Đã lưu bản nháp."
                )

        except Exception as error:
            st.error(
                "Không thể lưu bản nháp: "
                + str(error)
            )








def _render_lesson_plan_standardization_workspace(
    view,
    teacher_user_id="",
    client=None,
) -> None:
    if (
        view is None
        or not getattr(
            view,
            "rows",
            None,
        )
    ):
        return

    st.markdown(
        '<div class="mt-workspace-section-separator"></div>',
        unsafe_allow_html=True,
    )

    st.subheader(
        "\U0001f4c5 TH\u00d4NG TIN B\u00c0I SO\u1ea0N"
    )

    st.caption(
        "Ch\u1ecdn b\u00e0i, ti\u1ebft ho\u1eb7c "
        "ch\u1ee7 \u0111\u1ec1 c\u1ea7n x\u1eed l\u00fd."
    )

    schedule_rows = tuple(
        view.rows
    )

    selector = (
        LessonPlanUnitSelectorService()
    )

    available_modes = (
        selector.available_modes(
            rows=schedule_rows
        )
    )

    mode_labels = {
        LessonPlanSelectionMode.LESSON: (
            "Theo b\u00e0i"
        ),
        LessonPlanSelectionMode.PERIOD: (
            "Theo ti\u1ebft"
        ),
        LessonPlanSelectionMode.TOPIC: (
            "Theo ch\u1ee7 \u0111\u1ec1"
        ),
        LessonPlanSelectionMode.WEEK_SUBJECT: (
            "Theo tu\u1ea7n / m\u00f4n h\u1ecdc"
        ),
    }

    selection_mode = st.selectbox(
        "C\u00e1ch ch\u1ecdn n\u1ed9i dung "
        "gi\u00e1o \u00e1n",
        options=available_modes,
        format_func=lambda value: (
            mode_labels[value]
        ),
        key=(
            "lbg_lesson_plan_selection_mode_"
            + str(view.week_number)
        ),
    )

    lesson_units = (
        selector.build_units(
            rows=schedule_rows,
            mode=selection_mode,
        )
    )

    if not lesson_units:
        if (
            selection_mode
            is LessonPlanSelectionMode.TOPIC
        ):
            st.warning(
                "D\u1eef li\u1ec7u PPCT hi\u1ec7n "
                "ch\u01b0a c\u00f3 th\u00f4ng tin "
                "ch\u1ee7 \u0111\u1ec1."
            )
        else:
            st.warning(
                "Kh\u00f4ng c\u00f3 n\u1ed9i dung "
                "ph\u00f9 h\u1ee3p \u0111\u1ec3 "
                "chu\u1ea9n h\u00f3a "
                "gi\u00e1o \u00e1n."
            )

        return

    unit_label = {
        LessonPlanSelectionMode.LESSON: (
            "B\u00e0i d\u1ea1y"
        ),
        LessonPlanSelectionMode.PERIOD: (
            "Ti\u1ebft d\u1ea1y"
        ),
        LessonPlanSelectionMode.TOPIC: (
            "Ch\u1ee7 \u0111\u1ec1"
        ),
        LessonPlanSelectionMode.WEEK_SUBJECT: (
            "Tu\u1ea7n / m\u00f4n h\u1ecdc"
        ),
    }[selection_mode]

    selected_unit_index = st.selectbox(
        unit_label,
        options=tuple(
            range(
                len(
                    lesson_units
                )
            )
        ),
        format_func=lambda index: (
            lesson_units[
                index
            ].selection_label
        ),
        key=(
            "lbg_lesson_plan_unit_"
            + selection_mode.value
            + "_"
            + str(
                view.week_number
            )
        ),
    )

    selected_unit = (
        lesson_units[
            selected_unit_index
        ]
    )

    selected_lesson = {
        "lesson_title": (
            selected_unit.title
        ),
        "periods": (
            selected_unit.curriculum_periods
        ),
        "classes": (
            selected_unit.class_ids
        ),
        "teaching_dates": tuple(
            (
                item.teaching_date,
                item.class_id,
            )
            for item
            in selected_unit.teaching_dates
        ),
        "representative_index": (
            selected_unit
            .representative_index
        ),
    }

    selected_index = int(
        selected_lesson[
            "representative_index"
        ]
    )

    selected_row = (
        schedule_rows[
            selected_index
        ]
    )

    # Preserve the canonical representative schedule-row
    # context when crossing from weekly scheduling into the
    # lesson drafting workspace.
    selected_lesson.update(
        {
            "class_id": str(
                getattr(
                    selected_row,
                    "class_id",
                    "",
                )
                or ""
            ),
            "curriculum_period": getattr(
                selected_row,
                "curriculum_period",
                None,
            ),
            "teaching_date": getattr(
                selected_row,
                "teaching_date",
                None,
            ),
            "lesson_title": str(
                getattr(
                    selected_row,
                    "lesson_title",
                    "",
                )
                or selected_lesson.get(
                    "lesson_title",
                    ""
                )
            ),
        }
    )

    drafting_date = st.date_input(
        "Ng\u00e0y so\u1ea1n",
        value=selected_row.teaching_date,
        max_value=selected_row.teaching_date,
        key=(
            "lbg_lesson_plan_drafting_date_"
            + str(view.week_number)
            + "_"
            + str(selected_index)
        ),
    )

    _render_selected_lesson_summary(
        selected_lesson,
        drafting_date=drafting_date,
        client=client,
    )

    _render_lesson_plan_drafting_workspace(
        selected_lesson=selected_lesson,
        teacher_user_id=teacher_user_id,
        academic_year=str(
            getattr(
                view,
                "academic_year",
                "",
            )
        ),
        week_number=int(
            getattr(
                view,
                "week_number",
                0,
            )
        ),
        selection_mode=str(
            selection_mode.value
            if hasattr(
                selection_mode,
                "value",
            )
            else selection_mode
        ),
        selection_unit_id=str(
            selected_unit.selection_id
            if hasattr(
                selected_unit,
                "selection_id",
            )
            else selected_unit.title
        ),
        client=client,
    )

    st.markdown(
        '<div class="mt-workspace-section-separator"></div>',
        unsafe_allow_html=True,
    )

    st.subheader(
        "\U0001f4dd Chu\u1ea9n h\u00f3a "
        "gi\u00e1o \u00e1n theo "
        "L\u1ecbch b\u00e1o gi\u1ea3ng"
    )

    st.caption(
        "T\u1ea3i gi\u00e1o \u00e1n Word g\u1ed1c; "
        "h\u1ec7 th\u1ed1ng s\u1ebd b\u1ed5 sung "
        "th\u00f4ng tin t\u1eeb L\u1ecbch b\u00e1o gi\u1ea3ng "
        "v\u00e0 chu\u1ea9n h\u00f3a gi\u00e1o \u00e1n."
    )

    st.info(
        "\u2139\ufe0f Quy tr\u00ecnh: "
        "B\u1ed5 sung th\u00f4ng tin t\u1eeb "
        "L\u1ecbch b\u00e1o gi\u1ea3ng "
        "\u2192 Chu\u1ea9n h\u00f3a gi\u00e1o \u00e1n "
        "\u2192 Xem tr\u01b0\u1edbc "
        "\u2192 L\u01b0u tr\u00ean h\u1ec7 th\u1ed1ng / "
        "T\u1ea3i xu\u1ed1ng. "
        "File g\u1ed1c ch\u1ec9 d\u00f9ng l\u00e0m "
        "\u0111\u1ea7u v\u00e0o, kh\u00f4ng l\u01b0u "
        "v\u00e0o Kho gi\u00e1o \u00e1n."
    )

    input_mode = st.radio(
        "Nguồn giáo án",
        (
            "Tải giáo án lên",
            "Dùng giáo án "
            "vừa xử lý cùng AI",
        ),
        horizontal=True,
        key=(
            "lbg_lesson_plan_input_mode_"
            + str(view.week_number)
            + "_"
            + str(selected_index)
        ),
    )

    uploaded = None
    uploaded_content = None
    source_name = ""
    source_kind = ""

    if (
        input_mode
        == "Tải giáo án lên"
    ):
        uploaded = st.file_uploader(
            "Tải giáo án Word (.docx)",
            type=("docx",),
            accept_multiple_files=False,
            key=(
                "lbg_lesson_plan_upload_"
                + str(view.week_number)
                + "_"
                + str(selected_index)
            ),
        )

        if uploaded is None:
            st.caption(
                "File gốc chỉ được "
                "dùng làm đầu vào "
                "và sẽ được "
                "giữ nguyên."
            )
            return

        source_name = str(
            uploaded.name
        )

        uploaded_content = (
            uploaded.getvalue()
        )

        source_kind = "UPLOAD"

        st.success(
            "Đã nhận giáo án: "
            + source_name
        )

    else:
        transfer_candidates = []

        for key, value in (
            st.session_state.items()
        ):
            if not str(key).endswith(
                "_standardization_transfer"
            ):
                continue

            if not isinstance(
                value,
                dict,
            ):
                continue

            if (
                value.get("source")
                != "AI_DRAFT"
            ):
                continue

            transfer_candidates.append(
                value
            )

        transfer_payload = (
            transfer_candidates[-1]
            if transfer_candidates
            else None
        )

        if transfer_payload is None:
            st.info(
                "Chưa có giáo án "
                "được chuyển từ "
                "công cụ Soạn bài "
                "cùng AI."
            )
            return

        ai_docx_bytes = (
            transfer_payload.get(
                "docx_bytes"
            )
        )

        if not isinstance(
            ai_docx_bytes,
            (
                bytes,
                bytearray,
            ),
        ):
            st.info(
                "Đã nhận giáo án "
                "vừa xử lý cùng AI."
            )

            st.warning(
                "Giáo án AI chưa có "
                "tài liệu DOCX làm việc "
                "nội bộ."
            )

            st.caption(
                "Giáo viên không cần "
                "xuất Word. Hệ thống sẽ "
                "tự tạo tài liệu "
                "làm việc ở bước "
                "tiếp theo."
            )

            return

        uploaded_content = bytes(
            ai_docx_bytes
        )

        source_name = str(
            transfer_payload.get(
                "source_name",
                "",
            )
            or (
                str(
                    transfer_payload.get(
                        "lesson_title",
                        "giao-an-ai",
                    )
                )
                + ".docx"
            )
        )

        source_kind = "AI_DRAFT"

        st.success(
            "Đã nhận giáo án "
            "vừa xử lý cùng AI."
        )


    st.markdown(
        '<div class="mt-workspace-section-separator"></div>',
        unsafe_allow_html=True,
    )

    st.subheader(
        "Xem to\u00e0n b\u1ed9 gi\u00e1o \u00e1n"
    )

    st.caption(
        "Hi\u1ec3n th\u1ecb tr\u1ef1c quan file Word g\u1ed1c tr\u01b0\u1edbc khi "
        "ki\u1ec3m tra v\u00e0 chu\u1ea9n h\u00f3a."
    )

    try:
        viewer_html = build_document_html(
            uploaded_content
        )

        st.components.v1.html(
            viewer_html,
            height=900,
            scrolling=True,
        )

    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 hi\u1ec3n th\u1ecb tr\u1ef1c quan gi\u00e1o \u00e1n: "
            + str(error)
        )

    st.markdown(
        '<div class="mt-workspace-section-separator"></div>',
        unsafe_allow_html=True,
    )

    workflow_identity = (
        LessonPlanWorkflowIdentity
        .from_upload(
            week_number=view.week_number,
            row_index=selected_index,
            source_name=source_name,
            content=uploaded_content,
        )
    )

    workflow_state = st.session_state.get(
        workflow_identity.state_key
    )

    if (
        not isinstance(
            workflow_state,
            LessonPlanWorkflowState,
        )
        or not workflow_state.matches(
            workflow_identity
        )
    ):
        workflow_state = LessonPlanWorkflowState(
            identity=workflow_identity
        )

        st.session_state[
            workflow_identity.state_key
        ] = workflow_state

    reviewed_row = None
    modification_plan = None
    preparation_error = None

    try:
        preview_view = workflow_state.preview

        if preview_view is None:
            preview_view = (
                LessonPlanPreviewUploadService()
                .prepare(
                    content=uploaded_content,
                    canonical=CanonicalDocumentContext(
                    class_name=(
                        _class_display_name(
                            selected_row.class_id,
                            client=client,
                        )
                    ),
                    curriculum_period=(
                        selected_row.curriculum_period
                    ),
                    lesson_title=(
                        selected_row.lesson_title
                    ),
                    drafting_date=(
                        drafting_date.strftime(
                            "%d/%m/%Y"
                        )
                    ),
                        teaching_date=(
                            selected_row.teaching_date.strftime(
                                "%d/%m/%Y"
                            )
                        ),
                    ),
                )
            )

            workflow_state = (
                workflow_state.with_preview(
                    preview_view
                )
            )

            st.session_state[
                workflow_identity.state_key
            ] = workflow_state

        canonical_values = {
            DocumentField.CLASS_NAME: (
                _class_display_name(
                    selected_row.class_id,
                    client=client,
                )
            ),
            DocumentField.CURRICULUM_PERIOD: (
                str(
                    selected_row.curriculum_period
                )
            ),
            DocumentField.LESSON_TITLE: (
                selected_row.lesson_title
            ),
            DocumentField.DRAFTING_DATE: (
                drafting_date.strftime(
                    "%d/%m/%Y"
                )
            ),
            DocumentField.TEACHING_DATE: (
                selected_row.teaching_date.strftime(
                    "%d/%m/%Y"
                )
            ),
        }

        modification_plan = (
            LessonPlanModificationPlanner()
            .build_from_values(
                values=canonical_values
            )
        )

        reviewed_row = (
            LessonPlanReviewedScheduleRow
            .from_schedule_row(
                row=selected_row,
                resolved_metadata=(
                    canonical_values
                ),
            )
        )



    except Exception as error:
        reviewed_row = None
        modification_plan = None
        preparation_error = error
        modification_plan = None

        st.warning(
            "Kh\u00f4ng th\u1ec3 xem tr\u01b0\u1edbc "
            "ho\u1eb7c x\u00e1c nh\u1eadn "
            "th\u00f4ng tin gi\u00e1o \u00e1n: "
            f"{error}"
        )

    process_clicked = st.button(
        "\u2699\ufe0f T\u1ea1o gi\u00e1o \u00e1n "
        "chu\u1ea9n h\u00f3a",
        type="primary",
        width="stretch",
        key=(
            "lbg_lesson_plan_process_"
            + str(view.week_number)
            + "_"
            + str(selected_index)
        ),
    )


    processing_ready = (
        reviewed_row is not None
        and modification_plan is not None
        and preparation_error is None
    )

    if process_clicked and not processing_ready:
        st.error(
            "Canonical lesson data preparation failed; "
            "standardization cannot continue."
        )

    if process_clicked and processing_ready:
        try:
            with st.spinner(
                "\u0110ang b\u1ed5 sung "
                "th\u00f4ng tin v\u00e0 "
                "chu\u1ea9n h\u00f3a gi\u00e1o \u00e1n..."
            ):
                result = (
                    _process_lesson_plan_upload(
                        row=reviewed_row,
                        drafting_date=(
                            drafting_date
                        ),
                        content=(
                            uploaded_content
                        ),
                        original_name=(
                            source_name
                        ),
                        modification_plan=(
                            modification_plan
                        ),
                    )
                )

                workflow_state = (
                    workflow_state.with_result(
                        result
                    )
                )

                st.session_state[
                    workflow_identity.state_key
                ] = workflow_state

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 "
                "chu\u1ea9n h\u00f3a "
                f"gi\u00e1o \u00e1n: {error}"
            )

    workflow_state = st.session_state.get(
        workflow_identity.state_key
    )

    if (
        not isinstance(
            workflow_state,
            LessonPlanWorkflowState,
        )
        or not workflow_state.matches(
            workflow_identity
        )
        or workflow_state.result is None
    ):
        return

    result = workflow_state.result

    (
        output_name,
        output_bytes,
        unresolved_fields,
    ) = result


    st.markdown(
        '<div class="mt-workspace-section-separator"></div>',
        unsafe_allow_html=True,
    )

    st.subheader(
        "Xem tr\u01b0\u1edbc gi\u00e1o \u00e1n \u0111\u00e3 chu\u1ea9n h\u00f3a"
    )

    st.caption(
        "\u0110\u00e2y l\u00e0 b\u1ea3n gi\u00e1o \u00e1n sau khi \u0111\u00e3 b\u1ed5 sung "
        "th\u00f4ng tin t\u1eeb L\u1ecbch b\u00e1o gi\u1ea3ng v\u00e0 chu\u1ea9n h\u00f3a."
    )

    try:
        standardized_viewer_html = (
            build_document_html(
                output_bytes
            )
        )

        st.components.v1.html(
            standardized_viewer_html,
            height=900,
            scrolling=True,
        )

    except Exception as error:
        st.warning(
            "Kh\u00f4ng th\u1ec3 hi\u1ec3n th\u1ecb tr\u1ef1c quan "
            "b\u1ea3n gi\u00e1o \u00e1n \u0111\u00e3 chu\u1ea9n h\u00f3a: "
            + str(error)
        )

    if unresolved_fields:
        st.warning(
            "Ch\u01b0a t\u1ef1 \u0111\u1ed9ng "
            "c\u1eadp nh\u1eadt \u0111\u01b0\u1ee3c: "
            + ", ".join(
                unresolved_fields
            )
        )
    else:
        st.success(
            "\u0110\u00e3 b\u1ed5 sung "
            "c\u00e1c th\u00f4ng tin "
            "L\u1ecbch b\u00e1o gi\u1ea3ng "
            "v\u00e0 chu\u1ea9n h\u00f3a "
            "gi\u00e1o \u00e1n."
        )


    st.markdown("---")

    st.markdown(
        "### Gi\u00e1o \u00e1n \u0111\u00e3 chu\u1ea9n h\u00f3a"
    )

    st.caption(
        "B\u1ea1n c\u00f3 th\u1ec3 l\u01b0u b\u1ea3n \u0111\u00e3 chu\u1ea9n h\u00f3a "
        "tr\u00ean h\u1ec7 th\u1ed1ng ho\u1eb7c t\u1ea3i xu\u1ed1ng m\u00e1y."
    )

    save_standardized_clicked = st.button(
        "L\u01b0u v\u00e0o Kho gi\u00e1o \u00e1n",
        type="secondary",
        key=(
            "lbg_lesson_plan_save_standardized_"
            + str(view.week_number)
            + "_"
            + str(selected_index)
        ),
        width="stretch",
    )

    if save_standardized_clicked:
        upload_service = (
            st.session_state.get(
                "document_library_upload_service"
            )
        )

        if upload_service is None:
            st.warning(
                "Kho gi\u00e1o \u00e1n ch\u01b0a s\u1eb5n s\u00e0ng. "
                "B\u1ea1n v\u1eabn c\u00f3 th\u1ec3 t\u1ea3i file v\u1ec1 m\u00e1y."
            )

        else:
            try:
                from teacher_document_library_v2 import (
                    DocumentCategory,
                    DocumentUploadMetadata,
                )

                categories = tuple(
                    DocumentCategory
                )

                category = next(
                    (
                        item
                        for item in categories
                        if (
                            "lesson"
                            in item.value.casefold()
                            or "giao"
                            in item.value.casefold()
                        )
                    ),
                    categories[0],
                )

                class_name = (
                    _class_display_name(
                        selected_row.class_id,
                        client=client,
                    )
                )

                academic_year = str(
                    getattr(
                        view,
                        "academic_year",
                        "",
                    )
                    or ""
                ).strip()

                subject = str(
                    getattr(
                        selected_row,
                        "subject",
                        "",
                    )
                    or getattr(
                        selected_row,
                        "subject_name",
                        "",
                    )
                    or "N/A"
                ).strip()

                grade_level = str(
                    getattr(
                        selected_row,
                        "grade_level",
                        "",
                    )
                    or "N/A"
                ).strip()

                lesson_title = str(
                    getattr(
                        selected_row,
                        "lesson_title",
                        "",
                    )
                    or output_name
                ).strip()

                metadata = (
                    DocumentUploadMetadata(
                        title=lesson_title,
                        category=category,
                        academic_year=(
                            academic_year
                            or "N/A"
                        ),
                        subject=subject,
                        grade_level=grade_level,
                        class_name=(
                            class_name
                            if class_name != "-"
                            else None
                        ),
                        description=(
                            "Gi\u00e1o \u00e1n \u0111\u00e3 \u0111\u01b0\u1ee3c b\u1ed5 sung "
                            "th\u00f4ng tin t\u1eeb L\u1ecbch b\u00e1o gi\u1ea3ng "
                            "v\u00e0 chu\u1ea9n h\u00f3a tr\u00ean h\u1ec7 th\u1ed1ng."
                        ),
                        tags=(
                            "lesson-plan",
                            "standardized",
                        ),
                    )
                )

                saved_document = (
                    upload_service.upload(
                        content=output_bytes,
                        file_name=output_name,
                        mime_type=(
                            "application/vnd.openxmlformats-"
                            "officedocument.wordprocessingml.document"
                        ),
                        metadata=metadata,
                    )
                )

                st.success(
                    "\u0110\u00e3 l\u01b0u gi\u00e1o \u00e1n chu\u1ea9n h\u00f3a "
                    "v\u00e0o Kho gi\u00e1o \u00e1n."
                )

                link = getattr(
                    saved_document,
                    "web_view_link",
                    None,
                )

                if link:
                    st.link_button(
                        "M\u1edf gi\u00e1o \u00e1n \u0111\u00e3 l\u01b0u",
                        link,
                    )

            except Exception as error:
                st.error(
                    "Kh\u00f4ng th\u1ec3 l\u01b0u gi\u00e1o \u00e1n "
                    "\u0111\u00e3 chu\u1ea9n h\u00f3a: "
                    + str(error)
                )

    st.download_button(
        "\U0001f4e5 T\u1ea3i gi\u00e1o \u00e1n "
        "chu\u1ea9n h\u00f3a",
        data=output_bytes,
        file_name=output_name,
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
        width="stretch",
        key=(
            "lbg_lesson_plan_download_"
            + str(view.week_number)
            + "_"
            + str(selected_index)
        ),
    )


def _render_weekly_schedule_technical_workspace(
    *,
    client=None,
    user_id: str | None = None,
) -> None:
    st.title(
        "\U0001f4c5 L\u1ecbch b\u00e1o gi\u1ea3ng"
    )

    st.caption(
        "L\u1eadp v\u00e0 qu\u1ea3n l\u00fd "
        "l\u1ecbch b\u00e1o gi\u1ea3ng "
        "theo t\u1eebng tu\u1ea7n h\u1ecdc."
    )

    source_label = st.radio(
        "\u004e\u0067\u0075\u1ed3\u006e "
        "\u0064\u1eef "
        "\u006c\u0069\u1ec7\u0075",
        (
            "\u0054\u1ea3\u0069 "
            "\u0074\u1eeb "
            "\u006d\u00e1\u0079",
            "\u004c\u1ea5\u0079 "
            "\u0074\u1eeb "
            "\u0068\u1ec7 "
            "\u0074\u0068\u1ed1\u006e\u0067",
        ),
        horizontal=True,
        key="weekly_schedule_source",
    )

    if (
        source_label
        == (
            "\u004c\u1ea5\u0079 "
            "\u0074\u1eeb "
            "\u0068\u1ec7 "
            "\u0074\u0068\u1ed1\u006e\u0067"
        )
    ):
        if client is None or not user_id:
            st.error(
                "\u0050\u0068\u0069\u00ea\u006e "
                "\u0111\u0103\u006e\u0067 "
                "\u006e\u0068\u1ead\u0070 "
                "\u0063\u0068\u01b0\u0061 "
                "\u0063\u00f3 "
                "\u006e\u0067\u1eef "
                "\u0063\u1ea3\u006e\u0068 "
                "\u0064\u1eef "
                "\u006c\u0069\u1ec7\u0075 "
                "\u0068\u1ec7 "
                "\u0074\u0068\u1ed1\u006e\u0067."
            )
            return

        st.subheader(
            "\u0054\u1ea1\u006f "
            "\u006c\u1ecb\u0063\u0068 "
            "\u0074\u1eeb "
            "\u0064\u1eef "
            "\u006c\u0069\u1ec7\u0075 "
            "\u0111\u00e3 "
            "\u006c\u01b0\u0075"
        )

        academic_year = st.text_input(
            "\u004e\u0103\u006d "
            "\u0068\u1ecdc",
            value=st.session_state.get(
                "portal_academic_year",
                "",
            ),
            key="system_weekly_academic_year",
        ).strip()

        week_number = st.selectbox(
            "Tu\u1ea7n h\u1ecdc",
            options=tuple(
                range(1, 41)
            ),
            format_func=lambda value: (
                f"Tu\u1ea7n {value}"
            ),
            key="system_weekly_week_number",
        )

        if not academic_year:
            st.info(
                "\u0048\u00e3\u0079 "
                "\u006e\u0068\u1ead\u0070 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc "
                "\u0111\u1ec3 "
                "\u0074\u0069\u1ebf\u0070 "
                "\u0074\u1ee5\u0063."
            )
            return

        try:
            assignment_repository = (
                SupabaseTeachingAssignmentRepository(
                    client=client,
                    user_id=str(user_id),
                )
            )

            assignments = (
                assignment_repository.list_assignments(
                    owner_id=str(user_id),
                    academic_year=academic_year,
                    role=TeachingAssignmentRole.TEACHING,
                    status=TeachingAssignmentStatus.ACTIVE,
                )
            )

        except Exception as error:
            st.error(
                "\u004b\u0068\u00f4\u006e\u0067 "
                "\u0074\u0068\u1ec3 "
                "\u0111\u1ecdc "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u0067\u0069\u1ea3\u006e\u0067 "
                "\u0064\u1ea1\u0079: "
                f"{error}"
            )
            return

        if not assignments:
            st.warning(
                "\u0043\u0068\u01b0\u0061 "
                "\u0063\u00f3 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u0067\u0069\u1ea3\u006e\u0067 "
                "\u0064\u1ea1\u0079 "
                "\u0111\u0061\u006e\u0067 "
                "\u0068\u0069\u1ec7\u0075 "
                "\u006c\u1ef1\u0063 "
                "\u0063\u0068\u006f "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc "
                "\u006e\u00e0\u0079."
            )
            return

        st.caption(
            "\u0047\u0068\u00e9\u0070 "
            "\u006d\u1ed7\u0069 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u0076\u1edb\u0069 "
            "\u006e\u0068\u00f3\u006d "
            "\u0064\u1eef "
            "\u006c\u0069\u1ec7\u0075 "
            "\u0050\u0050\u0043\u0054 "
            "\u0074\u01b0\u01a1\u006e\u0067 "
            "\u1ee9\u006e\u0067."
        )

        try:
            runtime = (
                SystemWeeklyScheduleRuntime(
                    client=client,
                    user_id=str(user_id),
                )
            )

            ppct_scope_options = (
                runtime.list_ppct_scope_options(
                    academic_year=academic_year,
                )
            )

        except Exception as error:
            st.error(
                "\u004b\u0068\u00f4\u006e\u0067 "
                "\u0074\u0068\u1ec3 "
                "\u0111\u1ecdc "
                "\u0064\u0061\u006e\u0068 "
                "\u0073\u00e1\u0063\u0068 "
                "\u006e\u0068\u00f3\u006d "
                "\u0050\u0050\u0043\u0054: "
                f"{error}"
            )
            return

        if not ppct_scope_options:
            st.warning(
                "\u0050\u0050\u0043\u0054 "
                "\u0111\u0061\u006e\u0067 "
                "\u0068\u0069\u1ec7\u0075 "
                "\u006c\u1ef1\u0063 "
                "\u006b\u0068\u00f4\u006e\u0067 "
                "\u0063\u00f3 "
                "\u006e\u0068\u00f3\u006d "
                "\u0064\u1eef "
                "\u006c\u0069\u1ec7\u0075 "
                "\u0068\u1ee3\u0070 "
                "\u006c\u1ec7."
            )
            return

        scope_rules = []

        option_by_label = {
            option.label: option
            for option in ppct_scope_options
        }

        option_labels = (
            "\u2014 "
            "\u0043\u0068\u1ecdn "
            "\u006e\u0068\u00f3\u006d "
            "\u0050\u0050\u0043\u0054 "
            "\u2014",
            *tuple(
                option_by_label.keys()
            ),
        )

        for assignment in assignments:
            with st.container(
                border=True
            ):
                st.write(
                    " | ".join(
                        part
                        for part in (
                            assignment.class_id,
                            assignment.subject_ref,
                            assignment.component_ref,
                        )
                        if part
                    )
                )

                selected_label = st.selectbox(
                    "\u004e\u0068\u00f3\u006d "
                    "\u0050\u0050\u0043\u0054",
                    option_labels,
                    key=(
                        "weekly_ppct_scope_"
                        + assignment.assignment_id
                    ),
                )

                if (
                    selected_label
                    != option_labels[0]
                ):
                    selected = (
                        option_by_label[
                            selected_label
                        ]
                    )

                    scope_rules.append(
                        PPCTScopeMappingRule(
                            class_id=assignment.class_id,
                            subject_ref=(
                                assignment.subject_ref
                                or ""
                            ),
                            component_ref=(
                                assignment.component_ref
                            ),
                            subject_grade=(
                                selected.subject_grade
                            ),
                            sub_subject=(
                                selected.sub_subject
                            ),
                        )
                    )

        if st.button(
            "C\u1eadp nh\u1eadt "
            "L\u1ecbch b\u00e1o gi\u1ea3ng",
            type="primary",
            width="stretch",
            key="system_weekly_generate",
        ):
            if (
                len(scope_rules)
                != len(assignments)
            ):
                st.error(
                    "\u0048\u00e3\u0079 "
                    "\u006b\u0068\u0061\u0069 "
                    "\u0062\u00e1\u006f "
                    "\u006e\u0068\u00f3\u006d "
                    "\u0050\u0050\u0043\u0054 "
                    "\u0063\u0068\u006f "
                    "\u0074\u1ea5\u0074 "
                    "\u0063\u1ea3 "
                    "\u0070\u0068\u00e2\u006e "
                    "\u0063\u00f4\u006e\u0067."
                )
                return

            try:
                schedule_id = (
                    "SYSTEM-"
                    + str(user_id)
                    + "-"
                    + academic_year
                    + "-W"
                    + str(week_number)
                )

                runtime = (
                    SystemWeeklyScheduleRuntime(
                        client=client,
                        user_id=str(user_id),
                    )
                )

                schedule = runtime.generate(
                    request=(
                        SystemWeeklyScheduleRuntimeRequest(
                            schedule_id=schedule_id,
                            academic_year=academic_year,
                            week_number=week_number,
                            ppct_scope_rules=tuple(
                                scope_rules
                            ),
                        )
                    )
                )

                generation = (
                    WeeklyScheduleGenerationResult(
                        request=(
                            WeeklyScheduleGenerationRequest(
                                schedule_id=schedule_id,
                                teacher_id=str(user_id),
                                academic_year=academic_year,
                                week_number=week_number,
                            )
                        ),
                        schedule=schedule,
                    )
                )

                output = (
                    WeeklyScheduleOutputService()
                    .export_excel(
                        generation=generation
                    )
                )

                view = (
                    WeeklySchedulePortalPresenter()
                    .present(
                        output=output
                    )
                )

                st.session_state[
                    _VIEW_STATE_KEY
                ] = view

            except Exception as error:
                st.error(
                    "\u004b\u0068\u00f4\u006e\u0067 "
                    "\u0074\u0068\u1ec3 "
                    "\u0074\u1ea1\u006f "
                    "\u006c\u1ecb\u0063\u0068 "
                    "\u0062\u00e1\u006f "
                    "\u0067\u0069\u1ea3\u006e\u0067 "
                    "\u0074\u1eeb "
                    "\u0064\u1eef "
                    "\u006c\u0069\u1ec7\u0075 "
                    "\u0068\u1ec7 "
                    "\u0074\u0068\u1ed1\u006e\u0067: "
                    f"{error}"
                )
                return

        view = st.session_state.get(
            _VIEW_STATE_KEY
        )

        if view is None:
            return

        st.success(
            "\u0110\u00e3 "
            "\u0074\u1ea1\u006f "
            "\u006c\u1ecb\u0063\u0068 "
            "\u0062\u00e1\u006f "
            "\u0067\u0069\u1ea3\u006e\u0067 "
            "\u0074\u1eeb "
            "\u0064\u1eef "
            "\u006c\u0069\u1ec7\u0075 "
            "\u0068\u1ec7 "
            "\u0074\u0068\u1ed1\u006e\u0067."
        )

        st.subheader(
            f"\u004c\u1ecb\u0063\u0068 "
            f"\u0062\u00e1\u006f "
            f"\u0067\u0069\u1ea3\u006e\u0067 "
            f"- "
            f"\u0054\u0075\u1ea7\u006e "
            f"{view.week_number}"
        )

        rows = _preview_rows(
            view
        )

        if rows:
            st.data_editor(
                rows,
                width="stretch",
                hide_index=True,
                disabled=(
                    "Th\u1ee9/ng\u00e0y",
                    "Ti\u1ebft TKB",
                    "M\u00f4n/Ph\u00e2n m\u00f4n",
                    "L\u1edbp",
                    "Ti\u1ebft PPCT",
                    "T\u00ean b\u00e0i d\u1ea1y",
                ),
                key=(
                    "system_weekly_schedule_editor_"
                    + str(view.week_number)
                ),
            )
        else:
            st.warning(
                "\u004c\u1ecb\u0063\u0068 "
                "\u0111\u01b0\u1ee3\u0063 "
                "\u0074\u1ea1\u006f "
                "\u006e\u0068\u01b0\u006e\u0067 "
                "\u006b\u0068\u00f4\u006e\u0067 "
                "\u0063\u00f3 "
                "\u0074\u0069\u1ebf\u0074 "
                "\u0064\u1ea1\u0079 "
                "\u0070\u0068\u00f9 "
                "\u0068\u1ee3\u0070 "
                "\u0074\u0072\u006f\u006e\u0067 "
                "\u0074\u0075\u1ea7\u006e "
                "\u006e\u00e0\u0079."
            )

        st.download_button(
            "\u0054\u1ea3\u0069 "
            "\u006c\u1ecb\u0063\u0068 "
            "\u0062\u00e1\u006f "
            "\u0067\u0069\u1ea3\u006e\u0067 "
            "\u0045\u0078\u0063\u0065\u006c",
            data=view.download.content,
            file_name=view.download.file_name,
            mime=view.download.mime_type,
            use_container_width=True,
            key="system_weekly_download",
        )

        return

    uploaded = st.file_uploader(
        "Tải workbook dữ liệu lịch báo giảng",
        type=("xlsx",),
        key="weekly_schedule_upload",
    )

    if uploaded is None:
        st.info("Hãy tải file Excel dữ liệu để bắt đầu.")
        return

    try:
        intake = WeeklyScheduleWorkbookIntakeAdapter().load(
            selection=_local_selection(),
            workbook_bytes=uploaded.getvalue(),
        )
    except Exception as error:
        st.error(f"Không thể đọc dữ liệu: {error}")
        return

    academic_years = _academic_year_options(intake)
    teachers = _teacher_options(intake)

    if not academic_years:
        st.warning("Không tìm thấy năm học trong dữ liệu.")
        return

    if not teachers:
        st.warning("Không tìm thấy giáo viên trong thời khóa biểu.")
        return

    academic_year = st.selectbox(
        "Năm học",
        academic_years,
        key="weekly_schedule_academic_year",
    )

    weeks = _week_options(intake, academic_year)

    if not weeks:
        st.warning("Không tìm thấy tuần học phù hợp.")
        return

    col_week, col_teacher = st.columns(2)

    with col_week:
        week_number = st.selectbox(
            "Tuần",
            weeks,
            format_func=lambda value: f"Tuần {value}",
            key="weekly_schedule_week",
        )

    with col_teacher:
        teacher_id = st.selectbox(
            "Giáo viên",
            teachers,
            key="weekly_schedule_teacher",
        )

    if st.button(
        "Tạo lịch báo giảng",
        type="primary",
        use_container_width=True,
        key="weekly_schedule_generate",
    ):
        schedule_id = (
            f"{teacher_id}-{academic_year}-W{week_number:02d}"
        )

        try:
            generation = (
                LocalWeeklyScheduleGenerationService().generate(
                    intake=intake,
                    request=WeeklyScheduleGenerationRequest(
                        schedule_id=schedule_id,
                        teacher_id=teacher_id,
                        academic_year=academic_year,
                        week_number=week_number,
                    ),
                )
            )

            output = WeeklyScheduleOutputService().export_excel(
                generation=generation
            )

            view = WeeklySchedulePortalPresenter().present(
                output=output
            )

            st.session_state[_VIEW_STATE_KEY] = view

        except Exception as error:
            st.error(
                f"Không thể tạo lịch báo giảng: {error}"
            )
            return

    view = st.session_state.get(_VIEW_STATE_KEY)

    if view is None:
        return

    st.success("Đã tạo lịch báo giảng.")

    st.subheader(
        f"Lịch báo giảng - Tuần {view.week_number}"
    )

    st.caption(
        f"Giáo viên: {view.teacher_id} | "
        f"Năm học: {view.academic_year}"
    )

    preview = _preview_rows(view)

    if preview:
        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(
            "Lịch được tạo nhưng không có tiết dạy "
            "phù hợp trong tuần này."
        )

    st.download_button(
        "Tải lịch báo giảng Excel",
        data=view.download.content,
        file_name=view.download.file_name,
        mime=view.download.mime_type,
        use_container_width=True,
        key="weekly_schedule_download",
    )


# =========================================================
# USER WEEKLY SCHEDULE WORKSPACE
# =========================================================

def render_weekly_schedule_workspace(
    *,
    client=None,
    user_id: str | None = None,
) -> None:
    if client is None or not user_id:
        st.error(
            "Phi\u00ean \u0111\u0103ng nh\u1eadp "
            "ch\u01b0a s\u1eb5n s\u00e0ng."
        )
        return

    st.title(
        "\u270d\ufe0f C\u00f4ng c\u1ee5 so\u1ea1n b\u00e0i"
    )

    st.caption(
        "Ch\u1ecdn b\u00e0i theo tu\u1ea7n, so\u1ea1n c\u00f9ng AI "
        "v\u00e0 chu\u1ea9n h\u00f3a gi\u00e1o \u00e1n."
    )

    try:
        academic_year_repository = (
            SupabaseAcademicYearConfigurationRepository(
                client=client,
            )
        )

        current_year = (
            academic_year_repository.get_current()
        )

    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "c\u1ea5u h\u00ecnh n\u0103m h\u1ecdc "
            f"hi\u1ec7n h\u00e0nh: {error}"
        )
        return

    if current_year is None:
        st.warning(
            "Ch\u01b0a c\u00f3 n\u0103m h\u1ecdc "
            "hi\u1ec7n h\u00e0nh trong h\u1ec7 th\u1ed1ng."
        )
        return

    academic_year = (
        current_year.academic_year
    )

    # =====================================================
    # CANONICAL ACADEMIC WEEKS FROM ADMIN
    # =====================================================

    try:
        academic_week_repository = (
            SupabaseAcademicWeekRepository(
                client=client,
            )
        )

        academic_weeks = (
            academic_week_repository.list_weeks(
                academic_year_id=(
                    current_year.academic_year_id
                )
            )
        )

    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "l\u1ecbch tu\u1ea7n t\u1eeb ADMIN: "
            f"{error}"
        )
        return

    active_weeks = tuple(
        item
        for item in academic_weeks
        if item.status.value == "ACTIVE"
    )

    if not active_weeks:
        st.warning(
            "ADMIN ch\u01b0a thi\u1ebft l\u1eadp "
            "l\u1ecbch tu\u1ea7n cho "
            f"n\u0103m h\u1ecdc {academic_year}."
        )
        return

    week_by_number = {
        item.week_number: item
        for item in active_weeks
    }

    week_numbers = tuple(
        week_by_number.keys()
    )

    # -----------------------------------------------------
    # FILTER BAR
    # -----------------------------------------------------

    controls = st.columns(
        [1.25, 1.1, 1.1, 1.1, 0.9],
        gap="medium",
    )

    with controls[0]:
        st.text_input(
            "N\u0103m h\u1ecdc",
            value=academic_year,
            disabled=True,
            key="lbg_user_academic_year",
        )

    with controls[1]:
        week_number = st.selectbox(
            "Tu\u1ea7n h\u1ecdc",
            options=week_numbers,
            format_func=lambda value: (
                f"Tu\u1ea7n {value}"
            ),
            key="lbg_user_week_number",
        )

    selected_academic_week = (
        week_by_number[
            week_number
        ]
    )

    with controls[2]:
        st.text_input(
            "T\u1eeb ng\u00e0y",
            value=(
                selected_academic_week
                .start_date
                .strftime("%d/%m/%Y")
            ),
            disabled=True,
            key="lbg_user_from_date",
        )

    with controls[3]:
        st.text_input(
            "\u0110\u1ebfn ng\u00e0y",
            value=(
                selected_academic_week
                .end_date
                .strftime("%d/%m/%Y")
            ),
            disabled=True,
            key="lbg_user_to_date",
        )

    with controls[4]:
        reload_data = st.button(
            "\U0001f504 T\u1ea3i l\u1ea1i d\u1eef li\u1ec7u",
            width="stretch",
            key="lbg_user_reload",
        )

    if reload_data:
        st.session_state.pop(
            _VIEW_STATE_KEY,
            None,
        )
        st.rerun()

    # -----------------------------------------------------
    # CURRENT WEEKLY SCHEDULE VIEW
    # -----------------------------------------------------

    view = st.session_state.get(
        _VIEW_STATE_KEY
    )

    if (
        view is not None
        and (
            str(view.academic_year)
            != academic_year
            or int(view.week_number)
            != int(week_number)
        )
    ):
        view = None

    if view is None:
        try:
            schedule_id = (
                "SYSTEM-"
                + str(user_id)
                + "-"
                + academic_year
                + "-W"
                + str(week_number)
            )

            runtime = (
                SystemWeeklyScheduleRuntime(
                    client=client,
                    user_id=str(user_id),
                )
            )

            schedule = runtime.generate(
                request=(
                    SystemWeeklyScheduleRuntimeRequest(
                        schedule_id=schedule_id,
                        academic_year=academic_year,
                        week_number=week_number,

                        # Empty by design:
                        # SystemWeeklyScheduleRuntime
                        # automatically resolves PPCT scope
                        # rules from active assignments and
                        # active PPCT data.
                        ppct_scope_rules=(),
                    )
                )
            )

            generation = (
                WeeklyScheduleGenerationResult(
                    request=(
                        WeeklyScheduleGenerationRequest(
                            schedule_id=schedule_id,
                            teacher_id=str(user_id),
                            academic_year=academic_year,
                            week_number=week_number,
                        )
                    ),
                    schedule=schedule,
                )
            )

            output = (
                WeeklyScheduleOutputService()
                .export_excel(
                    generation=generation
                )
            )

            view = (
                WeeklySchedulePortalPresenter()
                .present(
                    output=output
                )
            )

            st.session_state[
                _VIEW_STATE_KEY
            ] = view

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 t\u1ef1 \u0111\u1ed9ng "
                "t\u1ea1o d\u1eef li\u1ec7u b\u00e0i d\u1ea1y "
                f"cho Tu\u1ea7n {week_number}: "
                + str(error)
            )
            return

    if view is None:
        st.info(
            "Ch\u01b0a c\u00f3 d\u1eef li\u1ec7u b\u00e0i d\u1ea1y "
            f"cho Tu\u1ea7n {week_number}."
        )
        return

    _render_lbg_table(
        view,
        client=client,
        teacher_user_id=str(
            user_id
        ),
    )
