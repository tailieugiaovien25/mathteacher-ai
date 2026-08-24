"""Teacher-owned editable lesson-plan workspace draft."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LessonPlanWorkspaceDraft:
    """
    Editable lesson-plan content owned by one teacher.

    This model represents workspace state before conversion
    into the canonical LessonPlanDraft / LessonPlan model.
    """

    draft_id: str
    teacher_user_id: str
    academic_year: str
    week_number: int
    subject_ref: str
    selection_mode: str
    selection_unit_id: str

    objectives_text: str = ""
    materials_text: str = ""
    teaching_process_text: str = ""

    class_or_grade_ref: str | None = None
    lesson_id: str | None = None
    title: str = ""

    status: str = "DRAFT"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
