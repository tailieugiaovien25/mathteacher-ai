from __future__ import annotations

import inspect

from portal_v2.ui.weekly_schedule_streamlit import (
    _academic_year_options,
    _teacher_options,
    _week_options,
    render_weekly_schedule_workspace,
)


def run_contract():
    print("=" * 72)
    print(
        "MVP-OPS-003A.2 - "
        "STREAMLIT WEEKLY SCHEDULE RENDERER TEST"
    )
    print("=" * 72)

    tests = []

    module = inspect.getmodule(
        render_weekly_schedule_workspace
    )

    source = inspect.getsource(
        module
    )

    lower = source.lower()

    tests.append((
        "WSR1 Streamlit renderer exists",
        callable(
            render_weekly_schedule_workspace
        ),
    ))

    tests.append((
        "WSR2 Local upload available",
        "file_uploader"
        in source,
    ))

    tests.append((
        "WSR3 System library option represented",
        "weekly_schedule_source"
        in source,
    ))

    tests.append((
        "WSR4 Academic year selector available",
        "weekly_schedule_academic_year"
        in source,
    ))

    tests.append((
        "WSR5 Week selector available",
        "weekly_schedule_week"
        in source,
    ))

    tests.append((
        "WSR6 Teacher selector available",
        "weekly_schedule_teacher"
        in source,
    ))

    tests.append((
        "WSR7 Generate action available",
        "weekly_schedule_generate"
        in source,
    ))

    tests.append((
        "WSR8 Preview available",
        "st.dataframe"
        in source,
    ))

    tests.append((
        "WSR9 Download available",
        "st.download_button"
        in source,
    ))

    tests.append((
        "WSR10 Existing intake adapter reused",
        "WeeklyScheduleWorkbookIntakeAdapter"
        in source,
    ))

    tests.append((
        "WSR11 Existing generation service reused",
        "LocalWeeklyScheduleGenerationService"
        in source,
    ))

    tests.append((
        "WSR12 Existing output service reused",
        "WeeklyScheduleOutputService"
        in source,
    ))

    tests.append((
        "WSR13 Portal presenter reused",
        "WeeklySchedulePortalPresenter"
        in source,
    ))

    tests.append((
        "WSR14 Renderer owns no workbook parsing",
        "load_workbook"
        not in source,
    ))

    tests.append((
        "WSR15 Renderer owns no workbook rendering",
        not any(
            token
            in source
            for token in (
                "Workbook(",
                "PatternFill",
                "Font(",
                "Alignment(",
                "merge_cells",
            )
        ),
    ))

    tests.append((
        "WSR16 Renderer owns no PPCT progression rules",
        not any(
            token
            in source
            for token in (
                "completed_counts",
                "curriculum_index",
                "_completed_counts",
            )
        ),
    ))

    tests.append((
        "WSR17 Renderer owns no physical file writing",
        not any(
            token
            in source
            for token in (
                "write_bytes",
                "write_text",
                "open(",
            )
        ),
    ))

    tests.append((
        "WSR18 Renderer owns no direct persistence",
        not any(
            token
            in lower
            for token in (
                "sqlite3",
                "supabase.",
                "googleapiclient",
                "vtsmas",
            )
        ),
    ))

    tests.append((
        "WSR19 Source option helpers exist",
        all(
            callable(item)
            for item in (
                _academic_year_options,
                _week_options,
                _teacher_options,
            )
        ),
    ))

    tests.append((
        "WSR20 Renderer contains no fixed educational values",
        not any(
            token
            in source
            for token in (
                "140",
                "105",
                "70",
                "35",
                "KNTT",
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
            "RESULT: PASS - STREAMLIT WEEKLY "
            "SCHEDULE RENDERER VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - STREAMLIT WEEKLY "
        "SCHEDULE RENDERER VIOLATED"
    )

    return False


def test_weekly_schedule_streamlit_renderer():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
