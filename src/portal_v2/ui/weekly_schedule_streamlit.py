from __future__ import annotations

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

_VIEW_STATE_KEY = "weekly_schedule_portal_view"


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


def _preview_rows(view) -> list[dict]:
    return [
        {
            "Ngày dạy": row.teaching_date.strftime("%d/%m/%Y"),
            "Thứ": row.weekday,
            "Tiết TKB": row.timetable_period,
            "Lớp": row.class_id,
            "Môn": row.subject_ref,
            "Phân môn": row.component_ref or "",
            "Tiết PPCT": row.curriculum_period,
            "Mã bài": row.lesson_id,
            "Tên bài": row.lesson_title,
            "Tiết trong bài": row.period_in_lesson,
            "Thiết bị": ", ".join(row.teaching_equipment),
        }
        for row in view.rows
    ]


def render_weekly_schedule_workspace() -> None:
    st.title("Lịch báo giảng tự động theo tuần")

    st.caption(
        "Tải dữ liệu lên, chọn năm học, tuần và giáo viên "
        "để hệ thống tạo lịch báo giảng."
    )

    source_label = st.radio(
        "Nguồn dữ liệu",
        ("Tải từ máy", "Lấy từ hệ thống"),
        horizontal=True,
        key="weekly_schedule_source",
    )

    if source_label == "Lấy từ hệ thống":
        st.info(
            "Nguồn dữ liệu trong hệ thống sẽ được kết nối "
            "ở bước tiếp theo."
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
