from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
    WeeklyLessonPlanSession,
)
from lesson_planning_v2.weekly_lesson_plan_content import (
    WeeklyLessonPlanContent,
    WeeklyLessonPlanContentSession,
)


ContentResolver = Callable[
    [WeeklyLessonPlanSession],
    Mapping[str, Any],
]


class WeeklyLessonPlanContentAssemblerService:
    def assemble(
        self,
        *,
        weekly_plan: WeeklyLessonPlan,
        content_resolver: ContentResolver,
    ) -> WeeklyLessonPlanContent:
        sessions = tuple(
            self._build_content_session(
                session=session,
                content_resolver=content_resolver,
            )
            for session in weekly_plan.sessions
        )

        return WeeklyLessonPlanContent(
            identity=weekly_plan.identity,
            sessions=sessions,
            approval=weekly_plan.approval,
        )

    def _build_content_session(
        self,
        *,
        session: WeeklyLessonPlanSession,
        content_resolver: ContentResolver,
    ) -> WeeklyLessonPlanContentSession:
        content = content_resolver(
            session
        )

        if (
            not isinstance(content, Mapping)
            or not content
        ):
            raise ValueError(
                "content must be a non-empty mapping"
            )

        return WeeklyLessonPlanContentSession(
            period_number=(
                session.period_number
            ),
            curriculum_period=(
                session.curriculum_period
            ),
            lesson_title=(
                session.lesson_title
            ),
            preparation_date=(
                session.preparation_date
            ),
            teaching_date=(
                session.teaching_date
            ),
            class_id=(
                session.class_id
            ),
            component_ref=(
                session.component_ref
            ),
            content=content,
        )
