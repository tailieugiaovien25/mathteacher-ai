from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
)


@dataclass(frozen=True)
class PPCTScopeMappingRule:
    class_id: str
    subject_ref: str
    subject_grade: str
    component_ref: str | None = None
    sub_subject: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "class_id",
            self._required_text(
                self.class_id,
                "class_id",
            ),
        )

        object.__setattr__(
            self,
            "subject_ref",
            self._required_text(
                self.subject_ref,
                "subject_ref",
            ),
        )

        object.__setattr__(
            self,
            "subject_grade",
            self._required_text(
                self.subject_grade,
                "subject_grade",
            ),
        )

        object.__setattr__(
            self,
            "component_ref",
            self._optional_text(
                self.component_ref,
                "component_ref",
            ),
        )

        object.__setattr__(
            self,
            "sub_subject",
            self._optional_text(
                self.sub_subject,
                "sub_subject",
            ),
        )

    @property
    def assignment_key(
        self,
    ) -> tuple[str, str, str | None]:
        return (
            self.class_id,
            self.subject_ref,
            self.component_ref,
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str or None"
            )

        normalized = value.strip()

        return normalized or None


class PPCTScopeResolver:
    """
    Resolve PPCT source rows for one teaching assignment
    through explicit data-driven mapping rules.

    The resolver contains no subject, grade, textbook,
    school, or storage-specific constants.
    """

    def __init__(
        self,
        *,
        rules: tuple[
            PPCTScopeMappingRule,
            ...,
        ],
    ) -> None:
        if not isinstance(
            rules,
            tuple,
        ):
            raise TypeError(
                "rules must be a tuple"
            )

        if not all(
            isinstance(
                rule,
                PPCTScopeMappingRule,
            )
            for rule in rules
        ):
            raise TypeError(
                "rules contain invalid value"
            )

        self._rules = rules

        self._validate_unique_rules()

    def resolve(
        self,
        assignment: TeachingAssignment,
        rows: tuple[PPCTRow, ...],
    ) -> tuple[PPCTRow, ...]:
        if not isinstance(
            assignment,
            TeachingAssignment,
        ):
            raise TypeError(
                "assignment must be TeachingAssignment"
            )

        if not isinstance(
            rows,
            tuple,
        ):
            raise TypeError(
                "rows must be a tuple"
            )

        if not all(
            isinstance(
                row,
                PPCTRow,
            )
            for row in rows
        ):
            raise TypeError(
                "rows contain invalid value"
            )

        key = (
            assignment.class_id,
            assignment.subject_ref,
            assignment.component_ref,
        )

        matches = tuple(
            rule
            for rule in self._rules
            if rule.assignment_key == key
        )

        if not matches:
            raise LookupError(
                "PPCT scope mapping not found for "
                f"{key}"
            )

        if len(matches) > 1:
            raise ValueError(
                "multiple PPCT scope mappings found for "
                f"{key}"
            )

        rule = matches[0]

        return tuple(
            row
            for row in rows
            if (
                self._normalized_text(
                    row.subject_grade
                )
                == rule.subject_grade
                and self._normalized_optional_text(
                    row.sub_subject
                )
                == rule.sub_subject
            )
        )

    def _validate_unique_rules(
        self,
    ) -> None:
        seen = set()

        for rule in self._rules:
            key = rule.assignment_key

            if key in seen:
                raise ValueError(
                    "duplicate PPCT scope mapping for "
                    f"{key}"
                )

            seen.add(key)

    @staticmethod
    def _normalized_text(
        value: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "PPCT source text must be str"
            )

        return value.strip()

    @staticmethod
    def _normalized_optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "PPCT source optional text "
                "must be str or None"
            )

        normalized = value.strip()

        return normalized or None
