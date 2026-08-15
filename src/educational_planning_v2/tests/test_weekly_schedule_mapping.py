from io import BytesIO

import pytest
from openpyxl import Workbook

from educational_planning_v2.adapters import (
    LocalWeeklyScheduleMappingRepository,
    WeeklyScheduleExcelAdapter,
    WeeklyScheduleMappingProfile,
    WeeklyScheduleWorkbookInspector,
    WeeklyScheduleWorkbookSchema,
)


def _mapped_workbook() -> bytes:
    workbook = Workbook()
    workbook.remove(workbook.active)
    tables = {
        "Tuần của trường": (
            ("NĂM", "TUẦN SỐ", "BẮT ĐẦU", "KẾT THÚC"),
            ("2026-2027", 5, "28/09/2026", "04/10/2026"),
        ),
        "TKB giáo viên": (
            ("GV", "LỚP", "MÔN", "THỨ", "TIẾT", "TỪ", "ĐẾN"),
            ("GV001", "6A1", "Toán", "Thứ 2", 1, "01/09/2026", "31/05/2027"),
        ),
        "Chương trình": (
            ("LỚP", "MÔN", "PPCT", "MÃ", "BÀI"),
            ("6A1", "Toán", 1, "TOAN6-001", "Bài mở đầu"),
        ),
        "Đã thực hiện": (
            ("GV", "LỚP", "MÔN", "NGÀY", "PPCT", "TRẠNG THÁI"),
            ("GV001", "6A1", "Toán", "21/09/2026", 1, "Đã dạy"),
        ),
    }
    for name, (headers, row) in tables.items():
        sheet = workbook.create_sheet(name)
        sheet.append((f"Tiêu đề {name}",))
        sheet.append(())
        sheet.append(headers)
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _schema() -> WeeklyScheduleWorkbookSchema:
    return WeeklyScheduleWorkbookSchema(
        academic_weeks_sheet="Tuần của trường",
        timetable_sheet="TKB giáo viên",
        curriculum_sheet="Chương trình",
        executions_sheet="Đã thực hiện",
        academic_weeks_header_row=3,
        timetable_header_row=3,
        curriculum_header_row=3,
        executions_header_row=3,
        academic_week_columns={
            "academic_year": "NĂM", "week_number": "TUẦN SỐ",
            "start_date": "BẮT ĐẦU", "end_date": "KẾT THÚC",
        },
        timetable_columns={
            "teacher_id": "GV", "class_id": "LỚP", "subject_ref": "MÔN",
            "component_ref": None, "weekday": "THỨ", "timetable_period": "TIẾT",
            "effective_from": "TỪ", "effective_to": "ĐẾN",
        },
        curriculum_columns={
            "class_id": "LỚP", "subject_ref": "MÔN", "component_ref": None,
            "period_number": "PPCT", "lesson_id": "MÃ", "lesson_title": "BÀI",
            "period_in_lesson": None, "total_lesson_periods": None,
            "teaching_equipment": None,
        },
        execution_columns={
            "teacher_id": "GV", "class_id": "LỚP", "subject_ref": "MÔN",
            "component_ref": None, "teaching_date": "NGÀY",
            "curriculum_period": "PPCT", "status": "TRẠNG THÁI",
        },
    )


def test_inspector_finds_sheets_and_header_row_without_changing_workbook():
    content = _mapped_workbook()
    original_content = bytes(content)
    inspections = WeeklyScheduleWorkbookInspector().inspect(content)

    assert tuple(item.name for item in inspections) == (
        "Tuần của trường", "TKB giáo viên", "Chương trình", "Đã thực hiện"
    )
    assert WeeklyScheduleWorkbookInspector.headers(inspections[0], 3) == (
        "NĂM", "TUẦN SỐ", "BẮT ĐẦU", "KẾT THÚC"
    )
    # Verify that inspection does not modify the supplied workbook bytes.
    # Do not regenerate a second XLSX archive for comparison because ZIP
    # metadata may differ between otherwise equivalent generated workbooks.
    assert content == original_content


def test_custom_mapping_loads_nonstandard_workbook_and_optional_columns():
    data = WeeklyScheduleExcelAdapter(_schema()).load(BytesIO(_mapped_workbook()))

    assert data.week(5, "2026-2027").start_date.isoformat() == "2026-09-28"
    assert data.timetable_slots[0].teacher_id == "GV001"
    assert data.curriculum_periods[0].component_ref is None
    assert data.curriculum_periods[0].teaching_equipment == ()


def test_mapping_profile_can_be_saved_and_reused(tmp_path):
    repository = LocalWeeklyScheduleMappingRepository(tmp_path)
    profile = WeeklyScheduleMappingProfile("Mẫu Trường A", _schema())

    repository.save(profile)

    assert repository.list_names() == ("Mẫu Trường A",)
    assert repository.get("Mẫu Trường A") == profile


@pytest.mark.parametrize("name", ("../secret", "a/b", "a\\b", ""))
def test_mapping_profile_rejects_unsafe_name(tmp_path, name):
    repository = LocalWeeklyScheduleMappingRepository(tmp_path)
    with pytest.raises(ValueError, match="unsafe"):
        repository.save(WeeklyScheduleMappingProfile(name, _schema()))
