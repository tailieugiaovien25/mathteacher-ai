from __future__ import annotations

from dataclasses import dataclass

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewViewModel,
    PreviewReviewState,
)
from document_intelligence.lesson_plan_teacher_review import (
    TeacherReviewAction,
)


@dataclass(frozen=True)
class TeacherReviewItemView:
    field: DocumentField
    field_label: str
    detected_value: str
    canonical_value: str | None
    review_state: PreviewReviewState
    requires_review: bool
    default_action: TeacherReviewAction


@dataclass(frozen=True)
class LessonPlanTeacherReviewViewModel:
    items: tuple[
        TeacherReviewItemView,
        ...
    ]
    requires_review: bool


class LessonPlanTeacherReviewPresenter:
    def present(
        self,
        *,
        preview: LessonPlanPreviewViewModel,
        canonical_values: dict[
            DocumentField,
            str | None,
        ],
    ) -> LessonPlanTeacherReviewViewModel:
        if not isinstance(
            preview,
            LessonPlanPreviewViewModel,
        ):
            raise TypeError(
                "preview must be LessonPlanPreviewViewModel"
            )

        if not isinstance(
            canonical_values,
            dict,
        ):
            raise TypeError(
                "canonical_values must be dict"
            )

        items = tuple(
            self._present_item(
                item=item,
                canonical_value=(
                    canonical_values.get(
                        item.field
                    )
                ),
            )
            for item in preview.items
        )

        return LessonPlanTeacherReviewViewModel(
            items=items,
            requires_review=any(
                item.requires_review
                for item in items
            ),
        )

    @staticmethod
    def _present_item(
        *,
        item,
        canonical_value: str | None,
    ) -> TeacherReviewItemView:
        if (
            item.review_state
            is PreviewReviewState.ACCEPTED
        ):
            default_action = (
                TeacherReviewAction.CONFIRM
            )
        else:
            default_action = (
                TeacherReviewAction.REJECT
            )

        return TeacherReviewItemView(
            field=item.field,
            field_label=item.field_label,
            detected_value=item.value,
            canonical_value=canonical_value,
            review_state=item.review_state,
            requires_review=item.requires_review,
            default_action=default_action,
        )
