from __future__ import annotations

from collections.abc import Mapping

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.services.lesson_plan_subject_profile_resolver import (
    LessonPlanSubjectProfileResolver,
)
from lesson_planning_v2.services.weekly_lesson_plan_content_assembler_service import (
    WeeklyLessonPlanContentAssemblerService,
)
from lesson_planning_v2.services.weekly_lesson_plan_selection_content_resolver import (
    WeeklyLessonPlanSelectionContentResolver,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    SubjectLessonPlanProfile,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
)
from lesson_planning_v2.weekly_lesson_plan_content import (
    WeeklyLessonPlanContent,
)


class SubjectAwareWeeklyLessonPlanContentPipeline:
    def __init__(
        self,
        *,
        subject_profile_resolver: (
            LessonPlanSubjectProfileResolver
            | None
        ) = None,
        content_assembler: (
            WeeklyLessonPlanContentAssemblerService
            | None
        ) = None,
    ) -> None:
        self._subject_profile_resolver = (
            subject_profile_resolver
            or LessonPlanSubjectProfileResolver()
        )

        self._content_assembler = (
            content_assembler
            or WeeklyLessonPlanContentAssemblerService()
        )

    def build(
        self,
        *,
        weekly_plan: WeeklyLessonPlan,
        subject_profiles: Mapping[
            str,
            SubjectLessonPlanProfile,
        ],
        content_resolver: (
            WeeklyLessonPlanSelectionContentResolver
        ),
        selection_mode: (
            LessonPlanSelectionMode
            | None
        ) = None,
    ) -> WeeklyLessonPlanContent:
        subject_ref = (
            weekly_plan.identity.subject_ref
        )

        policy = (
            self._subject_profile_resolver.resolve(
                subject_id=subject_ref,
                profiles=subject_profiles,
            )
        )

        effective_mode = (
            policy.default_selection_mode
            if selection_mode is None
            else selection_mode
        )

        self._validate_content_mode(
            effective_mode
        )

        if (
            effective_mode
            not in policy.allowed_selection_modes
        ):
            raise ValueError(
                "selection mode is not allowed "
                "for this subject"
            )

        return self._content_assembler.assemble(
            weekly_plan=weekly_plan,
            content_resolver=(
                lambda session: (
                    content_resolver.resolve(
                        session=session,
                        mode=effective_mode,
                    )
                )
            ),
        )

    @staticmethod
    def _validate_content_mode(
        mode: LessonPlanSelectionMode,
    ) -> None:
        valid_modes = (
            LessonPlanSelectionMode.LESSON,
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.TOPIC,
        )

        if mode not in valid_modes:
            raise ValueError(
                "unsupported content selection mode"
            )
