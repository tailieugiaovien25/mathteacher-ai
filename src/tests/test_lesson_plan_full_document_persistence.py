
from lesson_planning_v2.services.lesson_plan_workspace_v1_service import (
    LessonPlanWorkspaceContent,
)


class _Draft:
    objectives_text = "Objective"
    materials_text = "Material"
    teaching_process_text = "Process"


def test_content_supports_full_document_text():
    content = LessonPlanWorkspaceContent(
        full_document_text=(
            "WHOLE DOCUMENT"
        )
    )

    assert (
        content.full_document_text
        == "WHOLE DOCUMENT"
    )


def test_from_draft_builds_legacy_full_document():
    content = (
        LessonPlanWorkspaceContent.from_draft(
            _Draft()
        )
    )

    assert (
        "I. M?C TI?U"
        in content.full_document_text
    )

    assert (
        "Objective"
        in content.full_document_text
    )

    assert (
        "II. THI?T B? V? H?C LI?U"
        in content.full_document_text
    )

    assert (
        "Material"
        in content.full_document_text
    )

    assert (
        "III. TI?N TR?NH D?Y H?C"
        in content.full_document_text
    )

    assert (
        "Process"
        in content.full_document_text
    )


def test_full_document_takes_precedence_for_workspace_content():
    content = LessonPlanWorkspaceContent(
        teaching_process_text=(
            "LEGACY PROCESS"
        ),
        full_document_text=(
            "OFFICIAL FULL DOCUMENT"
        ),
    )

    assert (
        content.full_document_text
        == "OFFICIAL FULL DOCUMENT"
    )
