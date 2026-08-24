from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    SubjectLessonPlanProfile,
)


@dataclass(frozen=True)
class LessonPlanSubjectSelectionPolicy:
    """
    Effective lesson-plan selection policy for one subject.

    The workspace consumes this object instead of knowing
    where or how the subject profile is stored.
    """

    subject_id: str
    default_selection_mode: LessonPlanSelectionMode
    allowed_selection_modes: tuple[
        LessonPlanSelectionMode,
        ...,
    ]


class LessonPlanSubjectProfileResolver:
    """
    Resolve the effective lesson-plan selection policy
    for a scheduled subject.

    Storage is deliberately outside this service.
    The caller supplies canonical subject profiles.

    This keeps the lesson-plan workspace independent from:
    - Streamlit session-state key structure;
    - Supabase table structure;
    - physical persistence implementation.
    """

    DEFAULT_ALLOWED_MODES = (
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.TOPIC,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    )

    DEFAULT_MODE = LessonPlanSelectionMode.LESSON

    def resolve(
        self,
        *,
        subject_id: str,
        profiles: Mapping[
            str,
            SubjectLessonPlanProfile,
        ],
    ) -> LessonPlanSubjectSelectionPolicy:
        normalized_subject_id = str(
            subject_id or ""
        ).strip()

        if not normalized_subject_id:
            raise ValueError(
                "subject_id must not be blank"
            )

        profile = profiles.get(
            normalized_subject_id
        )

        if profile is None:
            return LessonPlanSubjectSelectionPolicy(
                subject_id=normalized_subject_id,
                default_selection_mode=(
                    self.DEFAULT_MODE
                ),
                allowed_selection_modes=(
                    self.DEFAULT_ALLOWED_MODES
                ),
            )

        allowed = tuple(
            profile.allowed_selection_modes
        )

        if not allowed:
            allowed = self.DEFAULT_ALLOWED_MODES

        default_mode = (
            profile.default_selection_mode
        )

        if default_mode not in allowed:
            default_mode = allowed[0]

        return LessonPlanSubjectSelectionPolicy(
            subject_id=normalized_subject_id,
            default_selection_mode=default_mode,
            allowed_selection_modes=allowed,
        )
