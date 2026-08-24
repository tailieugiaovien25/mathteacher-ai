from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
)
from educational_planning_v2.models.subject_catalog import (
    Subject,
    SubjectComponent,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
)
from educational_planning_v2.services.ppct_scope_catalog import (
    PPCTScopeOption,
)
from educational_planning_v2.services.ppct_scope_resolver import (
    PPCTScopeMappingRule,
)


@dataclass(frozen=True)
class AutoPPCTScopeMappingResult:
    rule: PPCTScopeMappingRule
    matched_option: PPCTScopeOption


class AutoPPCTScopeMappingService:
    """
    Resolve one canonical teaching assignment
    to one PPCT scope.

    This service owns no persistence and no UI.
    """

    def resolve(
        self,
        *,
        assignment: TeachingAssignment,
        class_item: ClassCatalog,
        subject: Subject,
        component: SubjectComponent | None,
        options: tuple[PPCTScopeOption, ...],
    ) -> AutoPPCTScopeMappingResult:
        if not isinstance(
            assignment,
            TeachingAssignment,
        ):
            raise TypeError(
                "assignment must be TeachingAssignment"
            )

        if not isinstance(
            class_item,
            ClassCatalog,
        ):
            raise TypeError(
                "class_item must be ClassCatalog"
            )

        if not isinstance(
            subject,
            Subject,
        ):
            raise TypeError(
                "subject must be Subject"
            )

        if (
            component is not None
            and not isinstance(
                component,
                SubjectComponent,
            )
        ):
            raise TypeError(
                "component must be "
                "SubjectComponent or None"
            )

        if not isinstance(
            options,
            tuple,
        ):
            raise TypeError(
                "options must be a tuple"
            )

        if (
            assignment.class_id
            != class_item.class_id
        ):
            raise ValueError(
                "assignment class does not match "
                "class catalog"
            )

        if (
            assignment.subject_ref
            != subject.subject_id
        ):
            raise ValueError(
                "assignment subject does not match "
                "subject catalog"
            )

        if assignment.component_ref is None:
            if component is not None:
                raise ValueError(
                    "component must be None when "
                    "assignment has no component"
                )
        else:
            if component is None:
                raise ValueError(
                    "component is required for "
                    "component assignment"
                )

            if (
                component.component_id
                != assignment.component_ref
            ):
                raise ValueError(
                    "assignment component does not "
                    "match component catalog"
                )

            if (
                component.subject_id
                != subject.subject_id
            ):
                raise ValueError(
                    "component does not belong to "
                    "assignment subject"
                )

        expected_subject_grade = (
            f"{subject.name.strip()} "
            f"{class_item.grade_level.strip()}"
        ).strip()

        expected_sub_subject = (
            component.name.strip()
            if component is not None
            else None
        )

        matches = tuple(
            option
            for option in options
            if (
                self._normalized(
                    option.subject_grade
                )
                == self._normalized(
                    expected_subject_grade
                )
                and self._normalized_optional(
                    option.sub_subject
                )
                == self._normalized_optional(
                    expected_sub_subject
                )
            )
        )

        if not matches:
            raise LookupError(
                "no PPCT scope matches "
                f"{expected_subject_grade!r}"
                + (
                    ""
                    if expected_sub_subject is None
                    else (
                        " / "
                        + repr(
                            expected_sub_subject
                        )
                    )
                )
            )

        if len(matches) != 1:
            raise ValueError(
                "PPCT scope mapping is ambiguous"
            )

        matched = matches[0]

        rule = PPCTScopeMappingRule(
            class_id=assignment.class_id,
            subject_ref=(
                assignment.subject_ref
                or ""
            ),
            component_ref=(
                assignment.component_ref
            ),
            subject_grade=(
                matched.subject_grade
            ),
            sub_subject=(
                matched.sub_subject
            ),
        )

        return AutoPPCTScopeMappingResult(
            rule=rule,
            matched_option=matched,
        )

    @staticmethod
    def _normalized(
        value: str,
    ) -> str:
        return (
            " ".join(
                value.strip().split()
            )
            .casefold()
        )

    @classmethod
    def _normalized_optional(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = cls._normalized(
            value
        )

        return normalized or None
