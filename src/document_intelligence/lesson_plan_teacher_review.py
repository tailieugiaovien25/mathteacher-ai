from dataclasses import dataclass
from enum import Enum

from document_intelligence.contracts import (
    DocumentField,
)


class TeacherReviewAction(str, Enum):
    CONFIRM = "confirm"
    OVERRIDE = "override"
    REJECT = "reject"


@dataclass(frozen=True)
class TeacherFieldDecision:
    field: DocumentField
    action: TeacherReviewAction
    detected_value: str | None = None
    canonical_value: str | None = None
    override_value: str | None = None

    def __post_init__(self) -> None:
        if (
            self.action
            is TeacherReviewAction.OVERRIDE
        ):
            value = (
                self.override_value.strip()
                if self.override_value
                else ""
            )

            if not value:
                raise ValueError(
                    "override_value is required "
                    "for OVERRIDE"
                )

            object.__setattr__(
                self,
                "override_value",
                value,
            )

        elif self.override_value is not None:
            raise ValueError(
                "override_value is only valid "
                "for OVERRIDE"
            )

    @property
    def is_accepted(self) -> bool:
        return self.action in {
            TeacherReviewAction.CONFIRM,
            TeacherReviewAction.OVERRIDE,
        }

    @property
    def resolved_value(self) -> str | None:
        if (
            self.action
            is TeacherReviewAction.REJECT
        ):
            return None

        if (
            self.action
            is TeacherReviewAction.OVERRIDE
        ):
            return self.override_value

        if self.canonical_value is not None:
            return self.canonical_value

        return self.detected_value


@dataclass(frozen=True)
class LessonPlanTeacherReview:
    decisions: tuple[
        TeacherFieldDecision,
        ...,
    ]

    def __post_init__(self) -> None:
        fields = tuple(
            item.field
            for item in self.decisions
        )

        if len(fields) != len(set(fields)):
            raise ValueError(
                "duplicate teacher review field"
            )

    @property
    def is_accepted(self) -> bool:
        return all(
            item.is_accepted
            for item in self.decisions
        )

    def decision_for(
        self,
        field: DocumentField,
    ) -> TeacherFieldDecision | None:
        for item in self.decisions:
            if item.field is field:
                return item

        return None
