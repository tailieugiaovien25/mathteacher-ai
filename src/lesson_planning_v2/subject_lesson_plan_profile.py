from __future__ import annotations

from dataclasses import dataclass

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.lesson_plan_template_profile import (
    LessonPlanTemplateProfile,
)


@dataclass(frozen=True)
class SubjectLessonPlanProfile:
    teacher_id: str
    subject_id: str

    templates: tuple[
        LessonPlanTemplateProfile,
        ...
    ]

    default_selection_mode: (
        LessonPlanSelectionMode
    ) = LessonPlanSelectionMode.LESSON

    allowed_selection_modes: tuple[
        LessonPlanSelectionMode,
        ...
    ] = (
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.TOPIC,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    )

    def __post_init__(self) -> None:
        if not self.teacher_id.strip():
            raise ValueError(
                "teacher_id must not be blank"
            )

        if not self.subject_id.strip():
            raise ValueError(
                "subject_id must not be blank"
            )

        if not self.templates:
            raise ValueError(
                "templates must not be empty"
            )

        if not self.allowed_selection_modes:
            raise ValueError(
                "allowed_selection_modes "
                "must not be empty"
            )

        if (
            len(self.allowed_selection_modes)
            != len(set(self.allowed_selection_modes))
        ):
            raise ValueError(
                "duplicate allowed selection mode"
            )

        if (
            self.default_selection_mode
            not in self.allowed_selection_modes
        ):
            raise ValueError(
                "default selection mode "
                "must be allowed"
            )

        names = tuple(
            template.profile_name
            for template in self.templates
        )

        if len(names) != len(set(names)):
            raise ValueError(
                "duplicate template profile name"
            )

        default_count = sum(
            1
            for template in self.templates
            if template.is_default
        )

        if default_count > 1:
            raise ValueError(
                "only one template may be default"
            )

    @property
    def default_template(
        self,
    ) -> LessonPlanTemplateProfile:
        for template in self.templates:
            if template.is_default:
                return template

        return self.templates[0]

    def supports(
        self,
        mode: LessonPlanSelectionMode,
    ) -> bool:
        return mode in self.allowed_selection_modes
