"""Application service for editable lesson-plan workspace drafts."""

from __future__ import annotations

from lesson_planning_v2.repositories.lesson_plan_workspace_draft_repository import (
    LessonPlanWorkspaceDraftRepository,
)
from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


class LessonPlanDraftWorkspaceService:
    """
    Application boundary for saving and retrieving drafts.

    The service depends only on the repository contract and
    therefore owns no physical persistence responsibility.
    """

    def __init__(
        self,
        repository: LessonPlanWorkspaceDraftRepository,
    ) -> None:
        if repository is None:
            raise ValueError(
                "repository must not be None"
            )

        self._repository = repository

    def save_draft(
        self,
        draft: LessonPlanWorkspaceDraft,
    ) -> LessonPlanWorkspaceDraft:
        if not draft.draft_id.strip():
            raise ValueError(
                "draft_id must not be empty"
            )

        if not draft.teacher_user_id.strip():
            raise ValueError(
                "teacher_user_id must not be empty"
            )

        return self._repository.save(
            draft
        )

    def get_draft(
        self,
        *,
        draft_id: str,
        teacher_user_id: str,
    ) -> LessonPlanWorkspaceDraft | None:
        if not draft_id.strip():
            raise ValueError(
                "draft_id must not be empty"
            )

        if not teacher_user_id.strip():
            raise ValueError(
                "teacher_user_id must not be empty"
            )

        return self._repository.get(
            draft_id=draft_id,
            teacher_user_id=teacher_user_id,
        )
