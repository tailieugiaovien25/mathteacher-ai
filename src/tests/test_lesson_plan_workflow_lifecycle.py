from document_intelligence.lesson_plan_workflow_state import (
    LessonPlanWorkflowIdentity,
    LessonPlanWorkflowState,
)


def identity(
    *,
    content: bytes,
):
    return (
        LessonPlanWorkflowIdentity
        .from_upload(
            week_number=5,
            row_index=2,
            source_name="lesson.docx",
            content=content,
        )
    )


def test_same_upload_and_same_review_preserves_result_across_rerun():
    workflow_identity = identity(
        content=b"same-document"
    )

    state = LessonPlanWorkflowState(
        identity=workflow_identity,
        preview="preview",
        review="review",
        resolution="resolution",
    )

    processed = state.with_result(
        "standardized-docx"
    )

    rerun_state = processed.with_review(
        review="review",
        resolution="resolution",
    )

    assert rerun_state is processed
    assert (
        rerun_state.result
        == "standardized-docx"
    )


def test_same_filename_different_bytes_rejects_old_workflow_state():
    first_identity = identity(
        content=b"first-document"
    )

    second_identity = identity(
        content=b"second-document"
    )

    first_state = LessonPlanWorkflowState(
        identity=first_identity,
        preview="preview-one",
        review="review-one",
        resolution="resolution-one",
        result="result-one",
    )

    assert (
        first_identity.source_name
        == second_identity.source_name
    )

    assert (
        first_identity.source_digest
        != second_identity.source_digest
    )

    assert not first_state.matches(
        second_identity
    )


def test_different_content_uses_different_review_widget_prefix():
    first_identity = identity(
        content=b"first-document"
    )

    second_identity = identity(
        content=b"second-document"
    )

    assert (
        first_identity.widget_key_prefix
        != second_identity.widget_key_prefix
    )


def test_changed_teacher_decision_invalidates_existing_result():
    workflow_identity = identity(
        content=b"same-document"
    )

    state = LessonPlanWorkflowState(
        identity=workflow_identity,
        preview="preview",
        review="old-review",
        resolution="old-resolution",
        result="old-result",
    )

    changed = state.with_review(
        review="new-review",
        resolution="new-resolution",
    )

    assert changed.result is None


def test_changed_preview_invalidates_review_resolution_and_result():
    workflow_identity = identity(
        content=b"same-document"
    )

    state = LessonPlanWorkflowState(
        identity=workflow_identity,
        preview="old-preview",
        review="review",
        resolution="resolution",
        result="result",
    )

    changed = state.with_preview(
        "new-preview"
    )

    assert changed.preview == "new-preview"
    assert changed.review is None
    assert changed.resolution is None
    assert changed.result is None
