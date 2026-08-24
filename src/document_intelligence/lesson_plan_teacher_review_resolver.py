from __future__ import annotations

from dataclasses import dataclass

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewViewModel,
)
from document_intelligence.lesson_plan_teacher_review import (
    LessonPlanTeacherReview,
)


@dataclass(frozen=True)
class ResolvedLessonPlanMetadata:
    values: tuple[
        tuple[DocumentField, str],
        ...
    ]

    def value_for(
        self,
        field: DocumentField,
    ) -> str | None:
        for item_field, value in self.values:
            if item_field is field:
                return value

        return None


@dataclass(frozen=True)
class LessonPlanTeacherReviewResolution:
    accepted: bool
    metadata: ResolvedLessonPlanMetadata
    rejected_fields: tuple[
        DocumentField,
        ...
    ]


class LessonPlanTeacherReviewResolver:
    def resolve(
        self,
        *,
        preview: LessonPlanPreviewViewModel,
        review: LessonPlanTeacherReview,
    ) -> LessonPlanTeacherReviewResolution:
        if not isinstance(
            preview,
            LessonPlanPreviewViewModel,
        ):
            raise TypeError(
                "preview must be LessonPlanPreviewViewModel"
            )

        if not isinstance(
            review,
            LessonPlanTeacherReview,
        ):
            raise TypeError(
                "review must be LessonPlanTeacherReview"
            )

        preview_fields = tuple(
            item.field
            for item in preview.items
        )

        missing = tuple(
            field
            for field in preview_fields
            if review.decision_for(field) is None
        )

        if missing:
            raise ValueError(
                "teacher review is incomplete"
            )

        resolved_values = []
        rejected_fields = []

        for item in preview.items:
            decision = review.decision_for(
                item.field
            )

            if decision is None:
                raise RuntimeError(
                    "review decision unexpectedly missing"
                )

            value = decision.resolved_value

            if value is None:
                rejected_fields.append(
                    item.field
                )
                continue

            resolved_values.append(
                (
                    item.field,
                    value,
                )
            )

        rejected_fields_tuple = tuple(
            rejected_fields
        )

        return LessonPlanTeacherReviewResolution(
            accepted=(
                review.is_accepted
                and not rejected_fields_tuple
            ),
            metadata=ResolvedLessonPlanMetadata(
                values=tuple(
                    resolved_values
                )
            ),
            rejected_fields=(
                rejected_fields_tuple
            ),
        )
