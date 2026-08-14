"""Local Streamlit interface for the weekly teaching schedule."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from educational_planning_v2.adapters import (
    WeeklyScheduleExcelAdapter,
    WeeklyScheduleSourceData,
    WeeklyScheduleWorkbookError,
)
from educational_planning_v2.models import WeeklyTeachingSchedule
from educational_planning_v2.exporters import WeeklyScheduleExcelExporter
from educational_planning_v2.services import WeeklyTeachingScheduleService


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
WEEKDAY_LABELS = {
    1: "Thứ 2",
    2: "Thứ 3",
    3: "Thứ 4",
    4: "Thứ 5",
    5: "Thứ 6",
    6: "Thứ 7",
    7: "Chủ nhật",
}


def load_uploaded_workbook(content: bytes, original_name: str) -> WeeklyScheduleSourceData:
    """Validate uploaded bytes and adapt the workbook to canonical data."""
    safe_name = Path(original_name).name
    if not safe_name.lower().endswith(".xlsx"):
        raise ValueError("Chỉ chấp nhận tệp Excel định dạng .xlsx.")
    if not content:
        raise ValueError("Tệp tải lên đang rỗng.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Tệp vượt quá giới hạn 20 MB.")

    try:
        return WeeklyScheduleExcelAdapter().load(BytesIO(content))
    except WeeklyScheduleWorkbookError:
        raise
    except Exception as error:
        raise ValueError(f"Không thể đọc tệp Excel: {error}") from error


def academic_year_options(data: WeeklyScheduleSourceData) -> tuple[str, ...]:
    return tuple(sorted({week.academic_year for week in data.academic_weeks}))


def week_options(
    data: WeeklyScheduleSourceData,
    academic_year: str,
) -> tuple[int, ...]:
    return tuple(
        sorted(
            week.week_number
            for week in data.academic_weeks
            if week.academic_year == academic_year
        )
    )


def teacher_options(data: WeeklyScheduleSourceData) -> tuple[str, ...]:
    return tuple(sorted({slot.teacher_id for slot in data.timetable_slots}))


def build_weekly_schedule(
    *,
    data: WeeklyScheduleSourceData,
    teacher_id: str,
    academic_year: str,
    week_number: int,
) -> WeeklyTeachingSchedule:
    week = data.week(week_number, academic_year)
    schedule_id = f"{teacher_id}-{academic_year}-W{week_number:02d}"
    return WeeklyTeachingScheduleService().build(
        schedule_id=schedule_id,
        teacher_id=teacher_id,
        academic_week=week,
        timetable_slots=data.timetable_slots,
        curriculum_periods=data.curriculum_periods,
        execution_records=data.execution_records,
    )


def schedule_rows(schedule: WeeklyTeachingSchedule) -> list[dict[str, object]]:
    return [
        {
            "Ngày dạy": entry.teaching_date.strftime("%d/%m/%Y"),
            "Thứ": WEEKDAY_LABELS[entry.weekday],
            "Tiết TKB": entry.timetable_period,
            "Lớp": entry.class_id,
            "Môn học": entry.subject_ref,
            "Phân môn": entry.component_ref or "",
            "Tiết PPCT": entry.curriculum_period,
            "Mã bài": entry.lesson_id,
            "Tên bài học": entry.lesson_title,
            "Tiết trong bài": (
                f"{entry.period_in_lesson}/{entry.total_lesson_periods}"
            ),
            "Thiết bị dạy học": "; ".join(entry.teaching_equipment),
        }
        for entry in schedule.entries
    ]


def export_weekly_schedule(schedule: WeeklyTeachingSchedule):
    """Create the downloadable system-template workbook."""
    return WeeklyScheduleExcelExporter().export(schedule)


def source_table_rows(
    data: WeeklyScheduleSourceData,
) -> dict[str, list[dict[str, object]]]:
    return {
        "Tuần học": [
            {
                "Năm học": item.academic_year,
                "Tuần": item.week_number,
                "Từ ngày": item.start_date.strftime("%d/%m/%Y"),
                "Đến ngày": item.end_date.strftime("%d/%m/%Y"),
            }
            for item in data.academic_weeks
        ],
        "Thời khóa biểu": [
            {
                "Mã giáo viên": item.teacher_id,
                "Lớp": item.class_id,
                "Môn học": item.subject_ref,
                "Phân môn": item.component_ref or "",
                "Thứ": WEEKDAY_LABELS[item.weekday],
                "Tiết": item.timetable_period,
                "Hiệu lực từ": item.effective_from.strftime("%d/%m/%Y"),
                "Hiệu lực đến": item.effective_to.strftime("%d/%m/%Y"),
            }
            for item in data.timetable_slots
        ],
        "PPCT": [
            {
                "Lớp": item.class_id,
                "Môn học": item.subject_ref,
                "Phân môn": item.component_ref or "",
                "Tiết PPCT": item.period_number,
                "Mã bài": item.lesson_id,
                "Tên bài học": item.lesson_title,
                "Tiết trong bài": (
                    f"{item.period_in_lesson}/{item.total_lesson_periods}"
                ),
                "Thiết bị dạy học": "; ".join(item.teaching_equipment),
            }
            for item in data.curriculum_periods
        ],
        "Tiết đã dạy": [
            {
                "Mã giáo viên": item.teacher_id,
                "Lớp": item.class_id,
                "Môn học": item.subject_ref,
                "Phân môn": item.component_ref or "",
                "Ngày dạy": item.teaching_date.strftime("%d/%m/%Y"),
                "Tiết PPCT": item.curriculum_period,
                "Trạng thái": item.status,
            }
            for item in data.execution_records
        ],
    }


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Lịch báo giảng tự động",
        page_icon="📅",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container {max-width: 1240px; padding-top: 1.5rem;}
        [data-testid="stFileUploaderDropzone"] {border: 2px dashed #2364aa;}
        .schedule-note {padding: .9rem 1rem; border-radius: .75rem;
          background: #edf6ff; border-left: 5px solid #2364aa;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Lịch báo giảng tự động theo tuần")
    st.caption(
        "MathTeacher-AI V2 · Excel là nguồn dữ liệu; hệ thống thực hiện "
        "kiểm tra, tìm kiếm và lập lịch"
    )

    with st.expander("Quy trình sử dụng", expanded=False):
        st.markdown(
            """
            1. Tải tệp dữ liệu theo mẫu của hệ thống.
            2. Kiểm tra bốn bảng dữ liệu đã được nhận diện.
            3. Chọn giáo viên, năm học và tuần.
            4. Tạo lịch và kiểm tra kết quả trước khi sử dụng.
            """
        )

    uploaded = st.file_uploader(
        "Tải dữ liệu lịch báo giảng",
        type=["xlsx"],
        help="Tệp tối đa 20 MB; tệp gốc không bị thay đổi.",
    )
    if uploaded is None:
        st.info("Hãy chọn tệp .xlsx theo mẫu để bắt đầu.")
        return

    content_digest = (
        uploaded.name,
        uploaded.size,
        sha256(uploaded.getvalue()).hexdigest(),
    )
    if st.session_state.get("weekly_source_digest") != content_digest:
        try:
            with st.spinner("Đang kiểm tra và chuẩn hóa dữ liệu..."):
                st.session_state["weekly_source_data"] = load_uploaded_workbook(
                    uploaded.getvalue(), uploaded.name
                )
                st.session_state["weekly_source_digest"] = content_digest
                st.session_state.pop("weekly_schedule", None)
        except Exception as error:
            st.error(f"Không thể sử dụng tệp dữ liệu: {error}")
            return

    data = st.session_state["weekly_source_data"]
    st.success(
        "Đã đọc dữ liệu: "
        f"{len(data.academic_weeks)} tuần · "
        f"{len(data.timetable_slots)} dòng TKB · "
        f"{len(data.curriculum_periods)} tiết PPCT · "
        f"{len(data.execution_records)} tiết đã dạy"
    )

    with st.expander("Xem dữ liệu nguồn", expanded=False):
        tables = source_table_rows(data)
        tabs = st.tabs(tuple(tables))
        for tab, (title, rows) in zip(tabs, tables.items()):
            with tab:
                st.dataframe(rows, use_container_width=True, hide_index=True)

    teachers = teacher_options(data)
    years = academic_year_options(data)
    if not teachers or not years:
        st.warning("Dữ liệu chưa có giáo viên hoặc tuần học để tạo lịch.")
        return

    left, middle, right = st.columns(3)
    teacher_id = left.selectbox("Giáo viên", teachers)
    academic_year = middle.selectbox("Năm học", years)
    available_weeks = week_options(data, academic_year)
    if not available_weeks:
        st.warning("Năm học đã chọn chưa có tuần học.")
        return
    week_number = right.selectbox("Tuần", available_weeks)
    selected_week = data.week(week_number, academic_year)
    st.markdown(
        '<div class="schedule-note">'
        f"<b>Tuần {week_number}</b>: "
        f"{selected_week.start_date.strftime('%d/%m/%Y')} – "
        f"{selected_week.end_date.strftime('%d/%m/%Y')}"
        "</div>",
        unsafe_allow_html=True,
    )

    selection = (uploaded.name, teacher_id, academic_year, week_number)
    if st.button("Tạo lịch báo giảng", type="primary", use_container_width=True):
        try:
            with st.spinner("Đang tìm thời khóa biểu và đối chiếu PPCT..."):
                st.session_state["weekly_schedule"] = build_weekly_schedule(
                    data=data,
                    teacher_id=teacher_id,
                    academic_year=academic_year,
                    week_number=week_number,
                )
                st.session_state["weekly_schedule_selection"] = selection
        except Exception as error:
            st.error(f"Không thể tạo lịch: {error}")

    schedule = st.session_state.get("weekly_schedule")
    if (
        schedule is None
        or st.session_state.get("weekly_schedule_selection") != selection
    ):
        return

    rows = schedule_rows(schedule)
    st.subheader(f"Lịch báo giảng tuần {week_number}")
    if not rows:
        st.warning("Không tìm thấy tiết dạy phù hợp trong tuần đã chọn.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Số tiết", len(rows))
    metric2.metric("Số lớp", len({row["Lớp"] for row in rows}))
    metric3.metric("Số môn/phân môn", len({(row["Môn học"], row["Phân môn"]) for row in rows}))
    excel_export = export_weekly_schedule(schedule)
    st.download_button(
        "Tải lịch báo giảng Excel",
        data=excel_export.content,
        file_name=excel_export.file_name,
        mime=excel_export.mime_type,
        type="primary",
        use_container_width=True,
    )
    st.info(
        "Tệp Excel sử dụng mẫu chuẩn của hệ thống. Giai đoạn tiếp theo sẽ "
        "bổ sung ánh xạ sang mẫu riêng do giáo viên tải lên."
    )


if __name__ == "__main__":
    main()
