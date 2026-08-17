from __future__ import annotations

import inspect

from portal_v2.ui.teacher_data_workspace_streamlit import (
    render_teacher_data_workspace,
)


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.4A - "
        "TEACHER DATA WORKSPACE STREAMLIT RENDERER TEST"
    )
    print("=" * 72)

    source = inspect.getsource(
        inspect.getmodule(
            render_teacher_data_workspace
        )
    )

    lower = source.lower()

    tests = []

    tests.append((
        "TDWR1 Renderer exists",
        callable(
            render_teacher_data_workspace
        ),
    ))

    tests.append((
        "TDWR2 Teacher workspace title rendered",
        "st.title"
        in source,
    ))

    tests.append((
        "TDWR3 Academic year rendered",
        "view.academic_year"
        in source,
    ))

    tests.append((
        "TDWR4 Workspace items rendered",
        "view.items"
        in source,
    ))

    tests.append((
        "TDWR5 READY state represented",
        "TeacherDataWorkspaceItemState.READY"
        in source,
    ))

    tests.append((
        "TDWR6 Missing state represented",
        "st.warning"
        in source,
    ))

    tests.append((
        "TDWR7 Source metadata rendered",
        (
            "item.source_name"
            in source
            and
            "item.source_version"
            in source
            and
            "item.status"
            in source
        ),
    ))

    tests.append((
        "TDWR8 Update action represented",
        "st.button"
        in source,
    ))

    tests.append((
        "TDWR9 Update action is conditionally disabled",
        "disabled=("
        in source
        and "not is_ppct"
        in source
        and "on_ppct_update is None"
        in source,
    ))

    tests.append((
        "TDWR10 Renderer owns no repository",
        "repository"
        not in lower,
    ))

    tests.append((
        "TDWR11 Renderer owns no Supabase access",
        "supabase"
        not in lower,
    ))

    tests.append((
        "TDWR12 Renderer owns no workbook parser",
        not any(
            token
            in lower
            for token in (
                "openpyxl",
                "load_workbook",
                "workbook(",
            )
        ),
    ))

    tests.append((
        "TDWR13 Renderer owns no payload",
        not any(
            token
            in lower
            for token in (
                "payload",
                "workbook_bytes",
                "document_bytes",
            )
        ),
    ))

    tests.append((
        "TDWR14 Renderer owns no schedule logic",
        not any(
            token
            in lower
            for token in (
                "completed_counts",
                "curriculum_index",
                "_completed_counts",
            )
        ),
    ))

    tests.append((
        "TDWR15 Renderer contains no fixed educational values",
        not any(
            token
            in source
            for token in (
                "140",
                "105",
                "70",
                "35",
                "KNTT",
                "To?n 6",
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
            "RESULT: PASS - TEACHER DATA WORKSPACE "
            "STREAMLIT RENDERER VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER DATA WORKSPACE "
        "STREAMLIT RENDERER VIOLATED"
    )

    return False


def test_teacher_data_workspace_streamlit_renderer():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
