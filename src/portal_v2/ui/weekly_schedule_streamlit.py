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
) -> None:
    periods = " + ".join(
        str(value)
        for value in lesson["periods"]
    )

    classes = ", ".join(
        _class_display_name(
            class_id
        )
        for class_id in lesson["classes"]
    )

    columns = st.columns(3)

    columns[0].metric(
        "Ti\u1ebft PPCT",
        periods or "-",
    )

    columns[1].metric(
        "S\u1ed1 ti\u1ebft",
        len(
            lesson["periods"]
        ),
    )

    columns[2].metric(
        "L\u1edbp",
        classes or "-",
    )

    st.markdown(
        "**Ng\u00e0y d\u1ea1y**"
    )

    for (
        teaching_date,
        class_id,
    ) in lesson["teaching_dates"]:
        st.write(
            teaching_date.strftime(
                "%d/%m/%Y"
            )
            + " - L\u1edbp "
            + _class_display_name(
                class_id
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
) -> None:
    """
    Render the teacher-facing lesson-plan drafting
    workspace.

    Draft persistence is routed through the
    application service and repository boundary.
    """

    st.subheader(
        "SO\u1ea0N B\u00c0I"
    )

    st.caption(
        "So\u1ea1n v\u00e0 ch\u1ec9nh s\u1eeda "
        "n\u1ed9i dung gi\u00e1o \u00e1n "
        "tr\u1ef1c ti\u1ebfp."
    )

    mode = st.radio(
        "C\u00e1ch b\u1eaft \u0111\u1ea7u",
        (
            "So\u1ea1n m\u1edbi",
            "D\u00f9ng gi\u00e1o \u00e1n "
            "\u0111\u00e3 c\u00f3",
            "T\u1ea3i Word l\u00ean",
        ),
        horizontal=True,
        key="lbg_drafting_mode",
    )

    if mode == "T\u1ea3i Word l\u00ean":
        st.info(
            "Ch\u1ebf \u0111\u1ed9 T\u1ea3i Word "
            "l\u00ean s\u1ebd ti\u1ebfp t\u1ee5c "
            "s\u1eed d\u1ee5ng workspace "
            "chu\u1ea9n h\u00f3a hi\u1ec7n c\u00f3."
        )
        return

    if (
        mode
        == "D\u00f9ng gi\u00e1o \u00e1n "
        "\u0111\u00e3 c\u00f3"
    ):
        st.info(
            "Kho gi\u00e1o \u00e1n s\u1ebd "
            "\u0111\u01b0\u1ee3c n\u1ed1i "
            "\u1edf b\u01b0\u1edbc ti\u1ebfp theo. "
            "Hi\u1ec7n t\u1ea1i c\u00f3 th\u1ec3 "
            "so\u1ea1n v\u00e0 ch\u1ec9nh s\u1eeda "
            "n\u1ed9i dung tr\u1ef1c ti\u1ebfp."
        )

    if selected_lesson is not None:
        lesson_title = str(
            selected_lesson.get(
                "lesson_title",
                "",
            )
        ).strip()

        if lesson_title:
            st.markdown(
                "### "
                + lesson_title
            )

    draft = st.session_state.setdefault(
        "lbg_lesson_plan_draft",
        {
            "objectives": "",
            "materials": "",
            "process": "",
        },
    )

    st.markdown(
        "### I. M\u1ee4C TI\u00caU"
    )

    objectives = st.text_area(
        "M\u1ee5c ti\u00eau",
        value=draft.get(
            "objectives",
            "",
        ),
        height=180,
        key="lbg_drafting_objectives",
        label_visibility="collapsed",
    )

    st.markdown(
        "### II. THI\u1ebeT B\u1eca "
        "V\u00c0 H\u1eccC LI\u1ec6U"
    )

    materials = st.text_area(
        "Thi\u1ebft b\u1ecb "
        "v\u00e0 h\u1ecdc li\u1ec7u",
        value=draft.get(
            "materials",
            "",
        ),
        height=140,
        key="lbg_drafting_materials",
        label_visibility="collapsed",
    )

    st.markdown(
        "### III. TI\u1ebeN TR\u00ccNH "
        "D\u1ea0Y H\u1eccC"
    )

    process = st.text_area(
        "Ti\u1ebfn tr\u00ecnh d\u1ea1y h\u1ecdc",
        value=draft.get(
            "process",
            "",
        ),
        height=320,
        key="lbg_drafting_process",
        label_visibility="collapsed",
    )

    save_column, preview_column, export_column = (
        st.columns(3)
    )

    with save_column:
        save_clicked = st.button(
            "L\u01b0u b\u1ea3n nh\u00e1p",
            key="lbg_drafting_save",
            use_container_width=True,
        )

    with preview_column:
        preview_clicked = st.button(
            "Xem tr\u01b0\u1edbc",
            key="lbg_drafting_preview",
            use_container_width=True,
        )

    with export_column:
        st.button(
            "Xu\u1ea5t Word",
            key="lbg_drafting_export_word",
            use_container_width=True,
            disabled=True,
            help=(
                "Xu\u1ea5t Word s\u1ebd "
                "\u0111\u01b0\u1ee3c n\u1ed1i "
                "v\u1edbi renderer "
                "\u1edf b\u01b0\u1edbc ti\u1ebfp theo."
            ),
        )

    if save_clicked:
        repository_key = (
            "lesson_plan_workspace_draft_repository"
        )

        repository = st.session_state.get(
            repository_key
        )

        if repository is None:
            st.error(
                "Kho l?u b?n nh?p ch?a s?n s?ng. "
                "H?y ??ng nh?p l?i."
            )
            return

        service = (
            LessonPlanDraftWorkspaceService(
                repository
            )
        )

        normalized_teacher_user_id = str(
            teacher_user_id
        ).strip()

        normalized_academic_year = str(
            academic_year
        ).strip()

        normalized_selection_unit_id = str(
            selection_unit_id
        ).strip()

        try:
            normalized_week_number = int(
                week_number
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized_week_number = 0

        if (
            not normalized_teacher_user_id
            or not normalized_academic_year
            or normalized_week_number <= 0
            or not normalized_selection_unit_id
        ):
            st.error(
                "Kh\u00f4ng \u0111\u1ee7 "
                "th\u00f4ng tin \u0111\u1ec3 "
                "l\u01b0u b\u1ea3n nh\u00e1p."
            )

        else:
            lesson_title = str(
                selected_lesson.get(
                    "lesson_title",
                    "",
                )
                if selected_lesson
                else ""
            )

            classes = (
                selected_lesson.get(
                    "classes",
                    (),
                )
                if selected_lesson
                else ()
            )

            class_or_grade_ref = (
                str(classes[0])
                if classes
                else None
            )

            draft_id = (
                normalized_teacher_user_id
                + ":"
                + normalized_academic_year
                + ":W"
                + str(
                    normalized_week_number
                )
                + ":"
                + str(
                    selection_mode
                )
                + ":"
                + normalized_selection_unit_id
            )

            workspace_draft = (
                LessonPlanWorkspaceDraft(
                    draft_id=draft_id,
                    teacher_user_id=(
                        normalized_teacher_user_id
                    ),
                    academic_year=(
                        normalized_academic_year
                    ),
                    week_number=(
                        normalized_week_number
                    ),
                    subject_ref=str(
                        selected_lesson.get(
                            "subject_ref",
                            "",
                        )
                        if selected_lesson
                        else ""
                    ),
                    selection_mode=str(
                        selection_mode
                    ),
                    selection_unit_id=(
                        normalized_selection_unit_id
                    ),
                    objectives_text=(
                        objectives
                    ),
                    materials_text=(
                        materials
                    ),
                    teaching_process_text=(
                        process
                    ),
                    class_or_grade_ref=(
                        class_or_grade_ref
                    ),
                    lesson_id=(
                        normalized_selection_unit_id
                    ),
                    title=lesson_title,
                    metadata={
                        "source": (
                            "weekly_schedule_"
                            "drafting_workspace"
                        ),
                    },
                )
            )

            service.save_draft(
                workspace_draft
            )

            loaded_draft = (
                service.get_draft(
                    draft_id=(
                        workspace_draft.draft_id
                    ),
                    teacher_user_id=(
                        workspace_draft
                        .teacher_user_id
                    ),
                )
            )

            if (
                loaded_draft
                != workspace_draft
            ):
                st.error(
                    "Kh\u00f4ng th\u1ec3 "
                    "x\u00e1c nh\u1eadn "
                    "b\u1ea3n nh\u00e1p "
                    "\u0111\u00e3 l\u01b0u."
                )

            else:
                st.session_state[
                    "lbg_lesson_plan_draft"
                ] = {
                    "objectives": (
                        objectives
                    ),
                    "materials": (
                        materials
                    ),
                    "process": (
                        process
                    ),
                }

                st.session_state[
                    "lbg_drafting_saved_draft_id"
                ] = (
                    workspace_draft.draft_id
                )

                st.success(
                    "\u0110\u00e3 l\u01b0u "
                    "b\u1ea3n nh\u00e1p."
                )

    if preview_clicked:
        st.markdown("---")
        st.markdown(
            "## Xem tr\u01b0\u1edbc"
        )

        st.markdown(
            "### I. M\u1ee5c ti\u00eau"
        )
        st.write(
            objectives
            or "Ch\u01b0a c\u00f3 n\u1ed9i dung."
        )

        st.markdown(
            "### II. Thi\u1ebft b\u1ecb "
            "v\u00e0 h\u1ecdc li\u1ec7u"
        )
        st.write(
            materials
            or "Ch\u01b0a c\u00f3 n\u1ed9i dung."
        )

        st.markdown(
            "### III. Ti\u1ebfn tr\u00ecnh "
            "d\u1ea1y h\u1ecdc"
        )
        st.write(
            process
            or "Ch\u01b0a c\u00f3 n\u1ed9i dung."
        )


def _render_lesson_plan_standardization_workspace(
    view,
    teacher_user_id="",
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

    st.divider()

    st.subheader(
        "\U0001f4dd Chu\u1ea9n h\u00f3a "
        "gi\u00e1o \u00e1n theo "
        "L\u1ecbch b\u00e1o gi\u1ea3ng"
    )

    st.caption(
        "Ch\u1ecdn theo b\u00e0i, ti\u1ebft "
        "ho\u1eb7c ch\u1ee7 \u0111\u1ec1; "
        "sau \u0111\u00f3 t\u1ea3i "
        "gi\u00e1o \u00e1n Word."
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

    _render_selected_lesson_summary(
        selected_lesson
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
    )

    # Transitional compatibility.
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

    st.info(
        "\u0110\u00e3 ch\u1ecdn b\u00e0i: "
        + selected_lesson[
            "lesson_title"
        ]
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

    uploaded = st.file_uploader(
        "T\u1ea3i gi\u00e1o \u00e1n Word (.docx)",
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
            "File g\u1ed1c s\u1ebd "
            "\u0111\u01b0\u1ee3c gi\u1eef nguy\u00ean."
        )
        return

    st.success(
        "\u0110\u00e3 nh\u1eadn gi\u00e1o \u00e1n: "
        + uploaded.name
    )

    uploaded_content = uploaded.getvalue()

    st.divider()

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

    st.divider()

    workflow_identity = (
        LessonPlanWorkflowIdentity
        .from_upload(
            week_number=view.week_number,
            row_index=selected_index,
            source_name=uploaded.name,
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
                            selected_row.class_id
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

        render_lesson_plan_preview(
            st=st,
            view=preview_view,
        )

        canonical_values = {
            DocumentField.CLASS_NAME: (
                _class_display_name(
                    selected_row.class_id
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

        teacher_review_view = (
            LessonPlanTeacherReviewPresenter()
            .present(
                preview=preview_view,
                canonical_values=(
                    canonical_values
                ),
            )
        )

        teacher_review = (
            render_lesson_plan_teacher_review(
                st=st,
                view=teacher_review_view,
                key_prefix=(
                    workflow_identity
                    .widget_key_prefix
                ),
            )
        )

        review_resolution = (
            LessonPlanTeacherReviewResolver()
            .resolve(
                preview=preview_view,
                review=teacher_review,
            )
        )

        workflow_state = (
            workflow_state.with_review(
                review=teacher_review,
                resolution=review_resolution,
            )
        )

        st.session_state[
            workflow_identity.state_key
        ] = workflow_state

        review_accepted = (
            review_resolution.accepted
        )

        modification_plan = None

        if review_accepted:
            modification_plan = (
                LessonPlanModificationPlanner()
                .build(
                    resolution=review_resolution
                )
            )

        reviewed_row = None

        if review_accepted:
            resolved_metadata = {
                field: value
                for field, value
                in review_resolution.metadata.values
            }

            reviewed_row = (
                LessonPlanReviewedScheduleRow
                .from_schedule_row(
                    row=selected_row,
                    resolved_metadata=(
                        resolved_metadata
                    ),
                )
            )

        if review_accepted:
            st.success(
                "Gi\u00e1o vi\u00ean \u0111\u00e3 "
                "x\u00e1c nh\u1eadn "
                "th\u00f4ng tin gi\u00e1o \u00e1n."
            )
        else:
            st.warning(
                "C\u1ea7n ho\u00e0n t\u1ea5t "
                "x\u00e1c nh\u1eadn "
                "th\u00f4ng tin tr\u01b0\u1edbc "
                "khi t\u1ea1o gi\u00e1o \u00e1n "
                "chu\u1ea9n h\u00f3a."
            )

    except Exception as error:
        review_accepted = False
        modification_plan = None
        reviewed_row = None

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

    if process_clicked and not review_accepted:
        st.warning(
            "Ch\u01b0a th\u1ec3 t\u1ea1o "
            "gi\u00e1o \u00e1n chu\u1ea9n h\u00f3a "
            "khi th\u00f4ng tin ch\u01b0a "
            "\u0111\u01b0\u1ee3c gi\u00e1o vi\u00ean "
            "x\u00e1c nh\u1eadn."
        )

    if process_clicked and review_accepted:
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
                            uploaded.name
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
        "\U0001f4c5 L\u1ecbch b\u00e1o gi\u1ea3ng"
    )

    st.caption(
        "L\u1eadp v\u00e0 qu\u1ea3n l\u00fd "
        "L\u1ecbch b\u00e1o gi\u1ea3ng "
        "theo t\u1eebng tu\u1ea7n h\u1ecdc."
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
        st.markdown(
            "<div style='height:28px'></div>",
            unsafe_allow_html=True,
        )

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
    # TEACHER INFO
    # -----------------------------------------------------

    st.info(
        "Gi\u00e1o vi\u00ean: "
        + str(user_id)
    )

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
        st.info(
            "Ch\u01b0a c\u00f3 L\u1ecbch b\u00e1o gi\u1ea3ng "
            f"cho Tu\u1ea7n {week_number}. "
            "H\u1ec7 th\u1ed1ng s\u1ebd t\u1ef1 \u0111\u1ed9ng "
            "t\u1ea1o t\u1eeb TKB, Ph\u00e2n c\u00f4ng "
            "v\u00e0 PPCT sau khi ho\u00e0n thi\u1ec7n "
            "b\u01b0\u1edbc k\u1ebft n\u1ed1i d\u1eef li\u1ec7u."
        )
    else:
        _render_lbg_table(
            view,
            client=client,
            teacher_user_id=str(
                user_id
            ),
        )

    # -----------------------------------------------------
    # REVIEW / APPROVAL
    # -----------------------------------------------------

    st.text_area(
        (
            "Ki\u1ec3m tra, nh\u1eadn x\u00e9t "
            "c\u1ee7a t\u1ed5 chuy\u00ean m\u00f4n / "
            "Ban gi\u00e1m hi\u1ec7u (n\u1ebfu c\u00f3)"
        ),
        placeholder=(
            "Nh\u1eadp nh\u1eadn x\u00e9t, "
            "\u0111\u00e1nh gi\u00e1..."
        ),
        key=(
            "lbg_user_review_"
            + str(week_number)
        ),
    )

    # -----------------------------------------------------
    # ACTION BUTTONS
    # -----------------------------------------------------

    actions = st.columns(
        [1.25, 1.05, 1.15, 1.25],
        gap="small",
    )

    with actions[0]:
        st.button(
            "\U0001f4c1 L\u01b0u tr\u00ean Google Drive",
            width="stretch",
            key="lbg_user_google_drive",
            disabled=(
                view is None
            ),
        )

    with actions[1]:
        if (
            view is not None
            and getattr(
                view,
                "download",
                None,
            )
        ):
            st.download_button(
                "\U0001f4ca Xu\u1ea5t ra file Excel",
                data=view.download.content,
                file_name=(
                    view.download.file_name
                ),
                mime=(
                    view.download.mime_type
                ),
                width="stretch",
                key="lbg_user_excel",
            )
        else:
            st.button(
                "\U0001f4ca Xu\u1ea5t ra file Excel",
                width="stretch",
                disabled=True,
                key="lbg_user_excel_disabled",
            )

    with actions[2]:
        st.button(
            "\u270d\ufe0f Tr\u00ecnh k\u00ed tr\u00ean VTsmas",
            width="stretch",
            key="lbg_user_vtsmas",
            disabled=(
                view is None
            ),
        )

    with actions[3]:
        update_clicked = st.button(
            "\U0001f4be C\u1eadp nh\u1eadt "
            "L\u1ecbch b\u00e1o gi\u1ea3ng",
            type="primary",
            width="stretch",
            key="lbg_user_update",
        )

    if update_clicked:
        try:
            with st.spinner(
                "\u0110ang t\u1ea1o L\u1ecbch b\u00e1o gi\u1ea3ng "
                f"Tu\u1ea7n {week_number}..."
            ):
                runtime = (
                    SystemWeeklyScheduleRuntime(
                        client=client,
                        user_id=str(user_id),
                    )
                )

                schedule = runtime.generate(
                    request=(
                        SystemWeeklyScheduleRuntimeRequest(
                            schedule_id=(
                                f"lbg-{user_id}-"
                                f"{academic_year}-"
                                f"{week_number}"
                            ),
                            academic_year=academic_year,
                            week_number=int(
                                week_number
                            ),
                            ppct_scope_rules=(),
                        )
                    )
                )

                generation_result = (
                    WeeklyScheduleGenerationResult(
                        request=(
                            WeeklyScheduleGenerationRequest(
                                schedule_id=(
                                    f"lbg-{user_id}-"
                                    f"{academic_year}-"
                                    f"{week_number}"
                                ),
                                teacher_id=str(
                                    user_id
                                ),
                                academic_year=academic_year,
                                week_number=int(
                                    week_number
                                ),
                            )
                        ),
                        schedule=schedule,
                    )
                )

                output = (
                    WeeklyScheduleOutputService()
                    .export_excel(
                        generation=(
                            generation_result
                        )
                    )
                )

                presenter = (
                    WeeklySchedulePortalPresenter()
                )

                generated_view = (
                    presenter.present(
                        output=output,
                    )
                )

                st.session_state[
                    _VIEW_STATE_KEY
                ] = generated_view

            st.success(
                "\u0110\u00e3 c\u1eadp nh\u1eadt L\u1ecbch b\u00e1o gi\u1ea3ng "
                f"Tu\u1ea7n {week_number}."
            )

            st.rerun()

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 t\u1ea1o L\u1ecbch b\u00e1o gi\u1ea3ng "
                f"Tu\u1ea7n {week_number}: {error}"
            )
