from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class LessonPlanWorkflowIdentity:
    week_number: int
    row_index: int
    source_name: str
    source_digest: str

    @classmethod
    def from_upload(
        cls,
        *,
        week_number: int,
        row_index: int,
        source_name: str,
        content: bytes,
    ) -> "LessonPlanWorkflowIdentity":
        if week_number < 1:
            raise ValueError(
                "week_number must be positive"
            )

        if row_index < 0:
            raise ValueError(
                "row_index must not be negative"
            )

        source_name = str(
            source_name
        ).strip()

        if not source_name:
            raise ValueError(
                "source_name must not be empty"
            )

        if not isinstance(content, bytes):
            raise TypeError(
                "content must be bytes"
            )

        if not content:
            raise ValueError(
                "content must not be empty"
            )

        return cls(
            week_number=week_number,
            row_index=row_index,
            source_name=source_name,
            source_digest=sha256(
                content
            ).hexdigest(),
        )

    @property
    def state_key(self) -> str:
        return (
            "lbg_lesson_plan_workflow_"
            f"{self.week_number}_"
            f"{self.row_index}"
        )

    @property
    def widget_key_prefix(self) -> str:
        return (
            "lbg_lesson_plan_review_"
            f"{self.week_number}_"
            f"{self.row_index}_"
            f"{self.source_digest[:12]}"
        )


@dataclass(frozen=True)
class LessonPlanWorkflowState:
    identity: LessonPlanWorkflowIdentity
    preview: Any | None = None
    review: Any | None = None
    resolution: Any | None = None
    result: Any | None = None

    def matches(
        self,
        identity: LessonPlanWorkflowIdentity,
    ) -> bool:
        return self.identity == identity

    def with_preview(
        self,
        preview: Any,
    ) -> "LessonPlanWorkflowState":
        return replace(
            self,
            preview=preview,
            review=None,
            resolution=None,
            result=None,
        )

    def with_review(
        self,
        *,
        review: Any,
        resolution: Any,
    ) -> "LessonPlanWorkflowState":
        if (
            self.review == review
            and self.resolution == resolution
        ):
            return self

        return replace(
            self,
            review=review,
            resolution=resolution,
            result=None,
        )

    def with_result(
        self,
        result: Any,
    ) -> "LessonPlanWorkflowState":
        if self.resolution is None:
            raise ValueError(
                "review resolution is required "
                "before processing result"
            )

        return replace(
            self,
            result=result,
        )
