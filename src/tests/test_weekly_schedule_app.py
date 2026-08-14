from pathlib import Path

import pytest

from scripts.weekly_schedule.app import (
    academic_year_options,
    build_weekly_schedule,
    load_uploaded_workbook,
    schedule_rows,
    source_table_rows,
    teacher_options,
    week_options,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = (
    PROJECT_ROOT
    / "templates"
    / "weekly_schedule"
    / "mau_du_lieu_lich_bao_giang_v2.xlsx"
)


def _data():
    return load_uploaded_workbook(TEMPLATE.read_bytes(), TEMPLATE.name)


def test_upload_reads_template_and_returns_selection_options():
    data = _data()

    assert academic_year_options(data) == ("2026-2027",)
    assert week_options(data, "2026-2027") == (5, 6)
    assert teacher_options(data) == ("GV001",)


def test_app_builds_week_five_schedule_from_uploaded_template():
    schedule = build_weekly_schedule(
        data=_data(),
        teacher_id="GV001",
        academic_year="2026-2027",
        week_number=5,
    )

    rows = schedule_rows(schedule)
    assert len(rows) == 3
    assert [row["Tiết PPCT"] for row in rows] == [3, 2, 4]
    assert [row["Thứ"] for row in rows] == ["Thứ 2", "Thứ 3", "Thứ 4"]


def test_source_tables_are_available_to_the_user_interface():
    tables = source_table_rows(_data())

    assert tuple(tables) == ("Tuần học", "Thời khóa biểu", "PPCT", "Tiết đã dạy")
    assert len(tables["Tuần học"]) == 2
    assert len(tables["Thời khóa biểu"]) == 3
    assert len(tables["PPCT"]) == 6
    assert len(tables["Tiết đã dạy"]) == 3


@pytest.mark.parametrize("name", ("data.xls", "data.xlsm", "data.csv"))
def test_upload_rejects_non_xlsx_files(name):
    with pytest.raises(ValueError, match=".xlsx"):
        load_uploaded_workbook(b"content", name)


def test_upload_rejects_empty_file():
    with pytest.raises(ValueError, match="rỗng"):
        load_uploaded_workbook(b"", "data.xlsx")


def test_ui_module_keeps_excel_details_in_the_adapter():
    import inspect
    import scripts.weekly_schedule.app as app

    source = inspect.getsource(app).lower()
    assert "openpyxl" not in source
    assert "load_workbook" not in source
