from __future__ import annotations

from collections.abc import Callable

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.weekly_lesson_plan_content import (
    WeeklyLessonPlanContent,
    WeeklyLessonPlanContentSession,
)
from lesson_planning_v2.weekly_lesson_plan_word_document import (
    WeeklyLessonPlanWordApproval,
    WeeklyLessonPlanWordDocument,
    WeeklyLessonPlanWordHeader,
    WeeklyLessonPlanWordSection,
)


ScopeLabelResolver = Callable[
    [LessonPlanTeachingScope],
    str,
]


class WeeklyLessonPlanWordDocumentMapper:
    def map(
        self,
        *,
        weekly_content: WeeklyLessonPlanContent,
        scope_label_resolver: ScopeLabelResolver,
    ) -> WeeklyLessonPlanWordDocument:
        identity = weekly_content.identity

        scope_label = str(
            scope_label_resolver(
                identity.teaching_scope
            )
            or ""
        ).strip()

        if not scope_label:
            raise ValueError(
                "scope_label must not be blank"
            )

        header = WeeklyLessonPlanWordHeader(
            teacher_id=identity.teacher_id,
            academic_year=identity.academic_year,
            week_number=identity.week_number,
            subject_ref=identity.subject_ref,
            scope_label=scope_label,
        )

        sections = tuple(
            self._map_section(
                session
            )
            for session in weekly_content.sessions
        )

        approval = self._map_approval(
            weekly_content
        )

        return WeeklyLessonPlanWordDocument(
            identity=identity,
            header=header,
            sections=sections,
            approval=approval,
        )

    def map_with_display(
        self,
        *,
        weekly_content,
        display,
        scope_label_resolver=None,
    ):
        """
        Build a Word document using externally resolved
        display names while preserving canonical identity.
        """
        if weekly_content.identity.teacher_id != display.teacher_id:
            raise ValueError(
                "display teacher_id does not match identity"
            )

        if weekly_content.identity.subject_ref != display.subject_ref:
            raise ValueError(
                "display subject_ref does not match identity"
            )

        if not weekly_content.sessions:
            raise ValueError(
                "weekly_content must contain sessions"
            )

        class_ids = {
            session.class_id
            for session in weekly_content.sessions
        }

        if display.class_id not in class_ids:
            raise ValueError(
                "display class_id does not match sessions"
            )

        identity = weekly_content.identity

        header = WeeklyLessonPlanWordHeader(
            teacher_id=display.teacher_name,
            academic_year=identity.academic_year,
            week_number=identity.week_number,
            subject_ref=display.subject_name,
            scope_label=display.class_name,
        )

        sections = tuple(
            WeeklyLessonPlanWordSection(
                period_number=session.period_number,
                curriculum_period=session.curriculum_period,
                preparation_date=session.preparation_date,
                teaching_date=session.teaching_date,
                title=session.lesson_title,
                class_id=display.class_name,
                component_ref=(
                    display.component_name
                    if session.component_ref is not None
                    else None
                ),
                content=session.content,
            )
            for session in weekly_content.sessions
        )

        approval = self._map_approval(
            weekly_content
        )

        return WeeklyLessonPlanWordDocument(
            identity=identity,
            header=header,
            sections=sections,
            approval=approval,
        )

    @staticmethod
    def _map_section(
        session: WeeklyLessonPlanContentSession,
    ) -> WeeklyLessonPlanWordSection:
        return WeeklyLessonPlanWordSection(
            period_number=session.period_number,
            curriculum_period=(
                session.curriculum_period
            ),
            preparation_date=(
                session.preparation_date
            ),
            teaching_date=session.teaching_date,
            title=session.lesson_title,
            class_id=session.class_id,
            component_ref=session.component_ref,
            content=session.content,
        )

    @staticmethod
    def _map_approval(
        weekly_content: WeeklyLessonPlanContent,
    ) -> WeeklyLessonPlanWordApproval | None:
        if weekly_content.approval is None:
            return None

        return WeeklyLessonPlanWordApproval(
            approver_role=(
                weekly_content.approval
                .approver_role
            ),
            placement="end_of_document",
        )
