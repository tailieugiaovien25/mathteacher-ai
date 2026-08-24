import pytest

from document_intelligence.lesson_plan_workflow_state import (
    LessonPlanWorkflowIdentity,
    LessonPlanWorkflowState,
)


def make_identity(
    *,
    content=b"first-document",
    source_name="lesson.docx",
):
    return (
        LessonPlanWorkflowIdentity
        .from_upload(
            week_number=5,
            row_index=2,
            source_name=source_name,
            content=content,
        )
    )


def test_identity_is_stable_for_same_upload():
    first = make_identity()
    second = make_identity()

    assert first == second
    assert (
        first.source_digest
        == second.source_digest
    )


def test_same_filename_different_content_has_new_identity():
    first = make_identity(
        content=b"document-one",
    )

    second = make_identity(
        content=b"document-two",
    )

    assert (
        first.source_name
        == second.source_name
    )

    assert (
        first.source_digest
        != second.source_digest
    )

    assert first != second


def test_widget_prefix_changes_with_source_content():
    first = make_identity(
        content=b"document-one",
    )

    second = make_identity(
        content=b"document-two",
    )

    assert (
        first.widget_key_prefix
        != second.widget_key_prefix
    )


def test_state_key_is_scoped_to_week_and_row():
    identity = make_identity()

    assert (
        identity.state_key
        == "lbg_lesson_plan_workflow_5_2"
    )


def test_state_matches_only_same_identity():
    state = LessonPlanWorkflowState(
        identity=make_identity()
    )

    assert state.matches(
        make_identity()
    )

    assert not state.matches(
        make_identity(
            content=b"other-document"
        )
    )


def test_new_preview_invalidates_downstream_state():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="old-preview",
        review="old-review",
        resolution="old-resolution",
        result="old-result",
    )

    changed = state.with_preview(
        "new-preview"
    )

    assert changed.preview == "new-preview"
    assert changed.review is None
    assert changed.resolution is None
    assert changed.result is None


def test_review_invalidates_old_result():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="preview",
        result="old-result",
    )

    changed = state.with_review(
        review="review",
        resolution="resolution",
    )

    assert changed.review == "review"
    assert changed.resolution == "resolution"
    assert changed.result is None


def test_result_requires_resolution():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="preview",
    )

    with pytest.raises(
        ValueError,
        match="resolution",
    ):
        state.with_result(
            "result"
        )


def test_result_is_preserved_for_resolved_workflow():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="preview",
        review="review",
        resolution="resolution",
    )

    changed = state.with_result(
        "result"
    )

    assert changed.result == "result"
    assert changed.preview == "preview"
    assert changed.review == "review"
    assert (
        changed.resolution
        == "resolution"
    )


def test_identity_validates_inputs():
    with pytest.raises(ValueError):
        LessonPlanWorkflowIdentity.from_upload(
            week_number=0,
            row_index=0,
            source_name="lesson.docx",
            content=b"x",
        )

    with pytest.raises(ValueError):
        LessonPlanWorkflowIdentity.from_upload(
            week_number=1,
            row_index=-1,
            source_name="lesson.docx",
            content=b"x",
        )

    with pytest.raises(ValueError):
        LessonPlanWorkflowIdentity.from_upload(
            week_number=1,
            row_index=0,
            source_name="",
            content=b"x",
        )

    with pytest.raises(ValueError):
        LessonPlanWorkflowIdentity.from_upload(
            week_number=1,
            row_index=0,
            source_name="lesson.docx",
            content=b"",
        )

def test_same_review_preserves_existing_result():
    identity = make_identity()

    state = LessonPlanWorkflowState(
        identity=identity,
        preview="preview",
        review="review",
        resolution="resolution",
        result="existing-result",
    )

    changed = state.with_review(
        review="review",
        resolution="resolution",
    )

    assert changed is state
    assert (
        changed.result
        == "existing-result"
    )


def test_changed_review_invalidates_existing_result():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="preview",
        review="old-review",
        resolution="old-resolution",
        result="existing-result",
    )

    changed = state.with_review(
        review="new-review",
        resolution="new-resolution",
    )

    assert (
        changed.review
        == "new-review"
    )
    assert (
        changed.resolution
        == "new-resolution"
    )
    assert changed.result is None


def test_changed_resolution_invalidates_existing_result():
    state = LessonPlanWorkflowState(
        identity=make_identity(),
        preview="preview",
        review="review",
        resolution="old-resolution",
        result="existing-result",
    )

    changed = state.with_review(
        review="review",
        resolution="new-resolution",
    )

    assert changed.result is None
