"""Persistence contract for teacher lesson-plan workspace drafts."""

from __future__ import annotations

from typing import Protocol

from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


class LessonPlanWorkspaceDraftRepository(Protocol):
    """Storage-neutral persistence boundary for workspace drafts."""

    def save(
        self,
        draft: LessonPlanWorkspaceDraft,
    ) -> LessonPlanWorkspaceDraft:
        """Create or replace one teacher-owned draft."""
        ...

    def get(
        self,
        *,
        draft_id: str,
        teacher_user_id: str,
    ) -> LessonPlanWorkspaceDraft | None:
        """Return one draft only for its owning teacher."""
        ...
