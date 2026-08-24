from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any

from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


def _required_text(
    value: str,
    *,
    field_name: str,
) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be blank"
        )

    return normalized


def _positive_integer(
    value: int,
    *,
    field_name: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{field_name} must be positive"
        )

    return value


@dataclass(frozen=True)
class WeeklyLessonPlanWordHeader:
    teacher_id: str
    academic_year: str
    week_number: int
    subject_ref: str
    scope_label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "teacher_id",
            _required_text(
                self.teacher_id,
                field_name="teacher_id",
            ),
        )

        object.__setattr__(
            self,
            "academic_year",
            _required_text(
                self.academic_year,
                field_name="academic_year",
            ),
        )

        object.__setattr__(
            self,
            "week_number",
            _positive_integer(
                self.week_number,
                field_name="week_number",
            ),
        )

        object.__setattr__(
            self,
            "subject_ref",
            _required_text(
                self.subject_ref,
                field_name="subject_ref",
            ),
        )

        object.__setattr__(
            self,
            "scope_label",
            _required_text(
                self.scope_label,
                field_name="scope_label",
            ),
        )


@dataclass(frozen=True)
class WeeklyLessonPlanWordSection:
    period_number: int
    curriculum_period: int
    preparation_date: date
    teaching_date: date
    title: str
    class_id: str
    content: Mapping[str, Any]
    component_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "period_number",
            _positive_integer(
                self.period_number,
                field_name="period_number",
            ),
        )

        object.__setattr__(
            self,
            "curriculum_period",
            _positive_integer(
                self.curriculum_period,
                field_name="curriculum_period",
            ),
        )

        object.__setattr__(
            self,
            "title",
            _required_text(
                self.title,
                field_name="title",
            ),
        )

        object.__setattr__(
            self,
            "class_id",
            _required_text(
                self.class_id,
                field_name="class_id",
            ),
        )

        if self.component_ref is not None:
            object.__setattr__(
                self,
                "component_ref",
                _required_text(
                    self.component_ref,
                    field_name="component_ref",
                ),
            )

        if (
            not isinstance(self.content, Mapping)
            or not self.content
        ):
            raise ValueError(
                "content must be a non-empty mapping"
            )

        object.__setattr__(
            self,
            "content",
            MappingProxyType(
                dict(self.content)
            ),
        )


@dataclass(frozen=True)
class WeeklyLessonPlanWordApproval:
    approver_role: str
    placement: str = "end_of_document"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "approver_role",
            _required_text(
                self.approver_role,
                field_name="approver_role",
            ),
        )

        normalized_placement = (
            _required_text(
                self.placement,
                field_name="placement",
            )
        )

        if normalized_placement != "end_of_document":
            raise ValueError(
                "approval placement must be "
                "end_of_document"
            )

        object.__setattr__(
            self,
            "placement",
            normalized_placement,
        )


@dataclass(frozen=True)
class WeeklyLessonPlanWordDocument:
    identity: WeeklyLessonPlanIdentity
    header: WeeklyLessonPlanWordHeader
    sections: tuple[
        WeeklyLessonPlanWordSection,
        ...,
    ]
    approval: (
        WeeklyLessonPlanWordApproval
        | None
    ) = None

    def __post_init__(self) -> None:
        normalized_sections = tuple(
            self.sections
        )

        if not normalized_sections:
            raise ValueError(
                "sections must not be empty"
            )

        normalized_sections = tuple(
            sorted(
                normalized_sections,
                key=lambda value: (
                    value.period_number,
                    value.curriculum_period,
                ),
            )
        )

        object.__setattr__(
            self,
            "sections",
            normalized_sections,
        )
