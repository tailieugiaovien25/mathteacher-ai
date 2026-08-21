from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


NameResolver = Callable[
    [str],
    str,
]


@dataclass(frozen=True)
class WeeklyLessonPlanDisplay:
    teacher_id: str
    subject_ref: str
    class_id: str
    component_ref: str | None

    teacher_name: str
    subject_name: str
    class_name: str
    component_name: str | None


class WeeklyLessonPlanDisplayResolver:
    def resolve(
        self,
        *,
        teacher_id: str,
        subject_ref: str,
        class_id: str,
        component_ref: str | None,
        teacher_name_resolver: NameResolver,
        subject_name_resolver: NameResolver,
        class_name_resolver: NameResolver,
        component_name_resolver: NameResolver,
    ) -> WeeklyLessonPlanDisplay:
        teacher_id = self._required(
            teacher_id,
            "teacher_id",
        )

        subject_ref = self._required(
            subject_ref,
            "subject_ref",
        )

        class_id = self._required(
            class_id,
            "class_id",
        )

        teacher_name = self._required(
            teacher_name_resolver(
                teacher_id
            ),
            "teacher_name",
        )

        subject_name = self._required(
            subject_name_resolver(
                subject_ref
            ),
            "subject_name",
        )

        class_name = self._required(
            class_name_resolver(
                class_id
            ),
            "class_name",
        )

        normalized_component_ref = (
            None
            if component_ref is None
            else self._required(
                component_ref,
                "component_ref",
            )
        )

        component_name = None

        if normalized_component_ref is not None:
            component_name = self._required(
                component_name_resolver(
                    normalized_component_ref
                ),
                "component_name",
            )

        return WeeklyLessonPlanDisplay(
            teacher_id=teacher_id,
            subject_ref=subject_ref,
            class_id=class_id,
            component_ref=(
                normalized_component_ref
            ),
            teacher_name=teacher_name,
            subject_name=subject_name,
            class_name=class_name,
            component_name=component_name,
        )

    @staticmethod
    def _required(
        value: str,
        field_name: str,
    ) -> str:
        normalized = str(
            value or ""
        ).strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be blank"
            )

        return normalized
