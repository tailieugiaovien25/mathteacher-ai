from dataclasses import replace

from lesson_planning_v2.adapters.in_memory_lesson_plan_workspace_draft_repository import (
    InMemoryLessonPlanWorkspaceDraftRepository,
)
from lesson_planning_v2.services.lesson_plan_draft_workspace_service import (
    LessonPlanDraftWorkspaceService,
)
from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


def _draft(
    *,
    teacher_user_id="teacher-001",
):
    return LessonPlanWorkspaceDraft(
        draft_id="draft-001",
        teacher_user_id=teacher_user_id,
        academic_year="2026-2027",
        week_number=1,
        subject_ref="subject-math",
        selection_mode="LESSON",
        selection_unit_id="lesson-007",
        class_or_grade_ref="class-6a2",
        lesson_id="lesson-007",
        title="Bài 7. Thứ tự thực hiện các phép tính",
        objectives_text="Mục tiêu ban đầu",
        materials_text="SGK và học liệu",
        teaching_process_text="Tiến trình ban đầu",
    )


def _service():
    repository = (
        InMemoryLessonPlanWorkspaceDraftRepository()
    )

    return (
        LessonPlanDraftWorkspaceService(
            repository
        ),
        repository,
    )


def test_save_then_get_returns_same_draft():
    service, _ = _service()

    draft = _draft()

    saved = service.save_draft(
        draft
    )

    loaded = service.get_draft(
        draft_id=draft.draft_id,
        teacher_user_id=draft.teacher_user_id,
    )

    assert saved == draft
    assert loaded == draft


def test_save_same_identity_updates_existing_draft():
    service, _ = _service()

    original = _draft()

    service.save_draft(
        original
    )

    updated = replace(
        original,
        objectives_text="Mục tiêu đã chỉnh sửa",
    )

    service.save_draft(
        updated
    )

    loaded = service.get_draft(
        draft_id=updated.draft_id,
        teacher_user_id=updated.teacher_user_id,
    )

    assert loaded == updated
    assert (
        loaded.objectives_text
        == "Mục tiêu đã chỉnh sửa"
    )


def test_teacher_cannot_read_another_teacher_draft():
    service, _ = _service()

    draft = _draft(
        teacher_user_id="teacher-a"
    )

    service.save_draft(
        draft
    )

    loaded = service.get_draft(
        draft_id=draft.draft_id,
        teacher_user_id="teacher-b",
    )

    assert loaded is None


def test_same_draft_id_can_exist_for_different_teachers():
    service, _ = _service()

    first = _draft(
        teacher_user_id="teacher-a"
    )

    second = replace(
        first,
        teacher_user_id="teacher-b",
        objectives_text="Teacher B content",
    )

    service.save_draft(first)
    service.save_draft(second)

    loaded_a = service.get_draft(
        draft_id="draft-001",
        teacher_user_id="teacher-a",
    )

    loaded_b = service.get_draft(
        draft_id="draft-001",
        teacher_user_id="teacher-b",
    )

    assert loaded_a == first
    assert loaded_b == second


def test_service_rejects_empty_teacher_identity():
    service, _ = _service()

    draft = replace(
        _draft(),
        teacher_user_id="",
    )

    try:
        service.save_draft(draft)
    except ValueError as error:
        assert (
            "teacher_user_id"
            in str(error)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )
