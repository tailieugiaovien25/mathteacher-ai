from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
import inspect

from educational_planning_v2.models import (
    TeachingSession,
)
from portal_v2.ui.weekly_schedule_portal import (
    WeeklySchedulePortalDownload,
    WeeklySchedulePortalPreviewRow,
    WeeklySchedulePortalSource,
    WeeklySchedulePortalViewModel,
    WeeklySchedulePortalPresenter,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def sample_row():
    return WeeklySchedulePortalPreviewRow(
        teaching_date=date(2026, 9, 28),
        weekday=1,
        timetable_period=1,
        session=TeachingSession.MORNING,
        class_id=" 6A1 ",
        subject_ref=" MATHEMATICS ",
        component_ref=None,
        curriculum_period=9,
        lesson_id=" LESSON-009 ",
        lesson_title=" Bai hoc thu 9 ",
        period_in_lesson=1,
        teaching_equipment=(),
    )


def sample_download():
    return WeeklySchedulePortalDownload(
        file_name=" lich-bao-giang.xlsx ",
        content=b"PK-test",
        mime_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


def run_contract():
    print("=" * 72)
    print(
        "MVP-OPS-003A.1 - "
        "WEEKLY SCHEDULE PORTAL PRESENTATION CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    row = sample_row()

    tests.append((
        "WPC1 Preview row accepted",
        isinstance(
            row,
            WeeklySchedulePortalPreviewRow,
        ),
    ))

    tests.append((
        "WPC2 Preview text normalized",
        (
            row.class_id == "6A1"
            and
            row.subject_ref == "MATHEMATICS"
            and
            row.lesson_id == "LESSON-009"
            and
            row.session is TeachingSession.MORNING
        ),
    ))

    download = sample_download()

    tests.append((
        "WPC3 Download artifact accepted",
        download.file_name
        == "lich-bao-giang.xlsx",
    ))

    tests.append((
        "WPC4 Download bytes preserved",
        download.content == b"PK-test",
    ))

    view = WeeklySchedulePortalViewModel(
        schedule_id=" SCHEDULE-W05 ",
        teacher_id=" GV001 ",
        academic_year=" 2026-2027 ",
        week_number=5,
        rows=(row,),
        download=download,
    )

    tests.append((
        "WPC5 View model accepted",
        isinstance(
            view,
            WeeklySchedulePortalViewModel,
        ),
    ))

    tests.append((
        "WPC6 View identity normalized",
        (
            view.schedule_id == "SCHEDULE-W05"
            and
            view.teacher_id == "GV001"
            and
            view.academic_year == "2026-2027"
        ),
    ))

    tests.append((
        "WPC7 Local upload source represented",
        WeeklySchedulePortalSource.LOCAL_UPLOAD.value
        == "LOCAL_UPLOAD",
    ))

    tests.append((
        "WPC8 System library source represented",
        WeeklySchedulePortalSource.SYSTEM_LIBRARY.value
        == "SYSTEM_LIBRARY",
    ))

    tests.append((
        "WPC9 Invalid week blocked",
        expect_error(
            ValueError,
            lambda: WeeklySchedulePortalViewModel(
                schedule_id="S",
                teacher_id="GV001",
                academic_year="2026-2027",
                week_number=0,
                rows=(row,),
                download=download,
            ),
        ),
    ))

    tests.append((
        "WPC10 Invalid row collection blocked",
        expect_error(
            TypeError,
            lambda: WeeklySchedulePortalViewModel(
                schedule_id="S",
                teacher_id="GV001",
                academic_year="2026-2027",
                week_number=5,
                rows=[row],
                download=download,
            ),
        ),
    ))

    tests.append((
        "WPC11 Empty download blocked",
        expect_error(
            ValueError,
            lambda: WeeklySchedulePortalDownload(
                file_name="x.xlsx",
                content=b"",
                mime_type="application/test",
            ),
        ),
    ))

    tests.append((
        "WPC12 Contracts immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                view,
                "week_number",
                6,
            ),
        ),
    ))

    presenter_source = inspect.getsource(
        WeeklySchedulePortalPresenter
    ).lower()

    presenter_module_source = inspect.getsource(
        inspect.getmodule(
            WeeklySchedulePortalPresenter
        )
    )

    presenter_import_lines = tuple(
        line.strip().lower()
        for line
        in presenter_module_source.splitlines()
        if line.strip().startswith(
            ("import ", "from ")
        )
    )

    tests.append((
        "WPC13 Presenter owns no Streamlit dependency",
        not any(
            "streamlit" in line
            for line
            in presenter_import_lines
        ),
    ))

    tests.append((
        "WPC14 Presenter owns no workbook rendering",
        not any(
            token
            in presenter_source
            for token in (
                "openpyxl",
                "workbook(",
                "load_workbook",
                "bytesio",
            )
        ),
    ))

    tests.append((
        "WPC15 Presenter owns no persistence dependency",
        not any(
            token
            in presenter_source
            for token in (
                "supabase",
                "sqlite3",
                "googleapiclient",
                "vtsmas",
            )
        ),
    ))

    tests.append((
        "WPC16 Presenter owns no schedule generation",
        "weeklyteachingscheduleservice"
        not in presenter_source,
    ))

    tests.append((
        "WPC17 Presenter owns no Excel exporter",
        "weeklyscheduleexcelexporter"
        not in presenter_source,
    ))

    tests.append((
        "WPC18 UI contract contains no fixed educational values",
        not any(
            token
            in presenter_source
            for token in (
                "140",
                "105",
                "70",
                "35",
                "kntt",
                "toán 6",
            )
        ),
    ))

    results = []

    for label, passed in tests:
        results.append(passed)
        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - WEEKLY SCHEDULE "
            "PORTAL PRESENTATION CONTRACT VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - WEEKLY SCHEDULE "
        "PORTAL PRESENTATION CONTRACT VIOLATED"
    )

    return False


def test_weekly_schedule_portal_contract():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
