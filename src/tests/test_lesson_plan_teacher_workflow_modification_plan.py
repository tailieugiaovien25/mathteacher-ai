import inspect

import portal_v2.ui.weekly_schedule_streamlit as module


def module_source():
    return inspect.getsource(
        module
    )


def test_workspace_imports_modification_planner():
    assert (
        "LessonPlanModificationPlanner"
        in module_source()
    )


def test_workspace_builds_plan_from_review_resolution():
    source = inspect.getsource(
        module._render_lesson_plan_standardization_workspace
    )

    assert (
        "LessonPlanModificationPlanner()"
        in source
    )

    assert (
        "resolution=review_resolution"
        in source
    )


def test_processing_helper_accepts_modification_plan():
    signature = inspect.signature(
        module._process_lesson_plan_upload
    )

    assert (
        "modification_plan"
        in signature.parameters
    )


def test_processing_helper_passes_plan_to_service():
    source = inspect.getsource(
        module._process_lesson_plan_upload
    )

    assert (
        "modification_plan=modification_plan"
        in source
    )


def test_workspace_passes_plan_to_processing_helper():
    source = inspect.getsource(
        module._render_lesson_plan_standardization_workspace
    )

    assert (
        "modification_plan=("
        in source
    )
