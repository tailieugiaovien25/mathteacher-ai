"""Supabase persistence for teacher lesson-plan workspace drafts."""

from __future__ import annotations

from typing import Any

from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


class SupabaseLessonPlanWorkspaceDraftRepository:
    """Persist teacher-owned workspace drafts in Supabase."""

    TABLE_NAME = "lesson_plan_workspace_drafts"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def save(
        self,
        draft: LessonPlanWorkspaceDraft,
    ) -> LessonPlanWorkspaceDraft:
        if not isinstance(
            draft,
            LessonPlanWorkspaceDraft,
        ):
            raise TypeError(
                "draft must be "
                "LessonPlanWorkspaceDraft"
            )

        row = self._to_row(
            draft
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                row,
                on_conflict=(
                    "teacher_user_id,draft_id"
                ),
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if rows:
            return self._from_row(
                rows[0]
            )

        verified = self.get(
            draft_id=draft.draft_id,
            teacher_user_id=(
                draft.teacher_user_id
            ),
        )

        if verified is None:
            raise RuntimeError(
                "Supabase did not persist lesson-plan "
                f"workspace draft {draft.draft_id!r}. "
                "Check authenticated teacher session, "
                "RLS policies and table privileges."
            )

        return verified

    def get(
        self,
        *,
        draft_id: str,
        teacher_user_id: str,
    ) -> LessonPlanWorkspaceDraft | None:
        normalized_draft_id = (
            self._required_text(
                draft_id,
                "draft_id",
            )
        )

        normalized_teacher_user_id = (
            self._required_text(
                teacher_user_id,
                "teacher_user_id",
            )
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "teacher_user_id",
                normalized_teacher_user_id,
            )
            .eq(
                "draft_id",
                normalized_draft_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    @staticmethod
    def _to_row(
        draft: LessonPlanWorkspaceDraft,
    ) -> dict[str, Any]:
        return {
            "draft_id": draft.draft_id,
            "teacher_user_id": (
                draft.teacher_user_id
            ),
            "academic_year": (
                draft.academic_year
            ),
            "week_number": (
                draft.week_number
            ),
            "subject_ref": (
                draft.subject_ref
            ),
            "selection_mode": (
                draft.selection_mode
            ),
            "selection_unit_id": (
                draft.selection_unit_id
            ),
            "objectives_text": (
                draft.objectives_text
            ),
            "materials_text": (
                draft.materials_text
            ),
            "teaching_process_text": (
                draft.teaching_process_text
            ),
            "class_or_grade_ref": (
                draft.class_or_grade_ref
            ),
            "lesson_id": (
                draft.lesson_id
            ),
            "title": draft.title,
            "status": draft.status,
            "metadata": dict(
                draft.metadata
            ),
        }

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> LessonPlanWorkspaceDraft:
        metadata = row.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        return LessonPlanWorkspaceDraft(
            draft_id=str(
                row["draft_id"]
            ),
            teacher_user_id=str(
                row["teacher_user_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            week_number=int(
                row["week_number"]
            ),
            subject_ref=str(
                row["subject_ref"]
            ),
            selection_mode=str(
                row["selection_mode"]
            ),
            selection_unit_id=str(
                row["selection_unit_id"]
            ),
            objectives_text=str(
                row.get(
                    "objectives_text",
                    "",
                )
                or ""
            ),
            materials_text=str(
                row.get(
                    "materials_text",
                    "",
                )
                or ""
            ),
            teaching_process_text=str(
                row.get(
                    "teaching_process_text",
                    "",
                )
                or ""
            ),
            class_or_grade_ref=(
                str(
                    row["class_or_grade_ref"]
                )
                if row.get(
                    "class_or_grade_ref"
                )
                is not None
                else None
            ),
            lesson_id=(
                str(
                    row["lesson_id"]
                )
                if row.get(
                    "lesson_id"
                )
                is not None
                else None
            ),
            title=str(
                row.get(
                    "title",
                    "",
                )
                or ""
            ),
            status=str(
                row.get(
                    "status",
                    "DRAFT",
                )
                or "DRAFT"
            ),
            metadata=metadata,
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if not isinstance(
            data,
            list,
        ):
            return []

        return [
            row
            for row in data
            if isinstance(
                row,
                dict,
            )
        ]

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        normalized = str(
            value
        ).strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
