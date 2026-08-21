"""In-memory implementation of lesson-plan workspace persistence."""

from __future__ import annotations

from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


class InMemoryLessonPlanWorkspaceDraftRepository:
    """
    In-memory repository used for application tests.

    Ownership is part of the lookup key so one teacher
    cannot retrieve another teacher's workspace draft.
    """

    def __init__(self) -> None:
        self._drafts: dict[
            tuple[str, str],
            LessonPlanWorkspaceDraft,
        ] = {}

    def save(
        self,
        draft: LessonPlanWorkspaceDraft,
    ) -> LessonPlanWorkspaceDraft:
        key = (
            draft.teacher_user_id,
            draft.draft_id,
        )

        self._drafts[key] = draft
        return draft

    def get(
        self,
        *,
        draft_id: str,
        teacher_user_id: str,
    ) -> LessonPlanWorkspaceDraft | None:
        return self._drafts.get(
            (
                teacher_user_id,
                draft_id,
            )
        )
