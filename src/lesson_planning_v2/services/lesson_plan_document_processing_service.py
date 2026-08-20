from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from dataclasses import replace
from datetime import datetime

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_modification_plan import (
    LessonPlanModificationPlan,
)
import tempfile

from document_standardization import (
    LessonPlanDocumentPipeline,
    LessonPlanWordStandardizer,
)
from lesson_planning_v2.services.scheduled_lesson_context_service import (
    ScheduledLessonContextService,
)


@dataclass(frozen=True)
class LessonPlanDocumentProcessingResult:
    output_name: str
    output_bytes: bytes
    unresolved_fields: tuple[str, ...]


class LessonPlanDocumentProcessingService:
    """
    Application boundary between weekly-schedule UI
    and lesson-plan document processing.

    The renderer supplies schedule metadata and DOCX
    bytes. Physical workspace handling and document
    pipeline execution belong here.
    """

    def __init__(
        self,
        *,
        profile_path: Path,
    ) -> None:
        self._profile_path = Path(
            profile_path
        )

    @staticmethod
    def apply_modification_plan(
        *,
        context,
        modification_plan,
    ):
        from lesson_planning_v2.contexts import (
            ScheduledLessonContext,
        )

        if not isinstance(
            context,
            ScheduledLessonContext,
        ):
            raise TypeError(
                "context must be ScheduledLessonContext"
            )

        if not isinstance(
            modification_plan,
            LessonPlanModificationPlan,
        ):
            raise TypeError(
                "modification_plan must be "
                "LessonPlanModificationPlan"
            )

        if modification_plan.is_empty:
            return context

        changes = {}

        class_name = modification_plan.value_for(
            DocumentField.CLASS_NAME
        )
        if class_name is not None:
            changes["class_id"] = class_name

        curriculum_period = (
            modification_plan.value_for(
                DocumentField.CURRICULUM_PERIOD
            )
        )
        if curriculum_period is not None:
            try:
                parsed_period = int(
                    curriculum_period
                )
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "curriculum_period must be "
                    "a positive integer"
                ) from error

            if parsed_period <= 0:
                raise ValueError(
                    "curriculum_period must be "
                    "a positive integer"
                )

            changes[
                "curriculum_period"
            ] = parsed_period

        lesson_title = modification_plan.value_for(
            DocumentField.LESSON_TITLE
        )
        if lesson_title is not None:
            changes["lesson_title"] = lesson_title

        drafting_date = modification_plan.value_for(
            DocumentField.DRAFTING_DATE
        )
        if drafting_date is not None:
            changes["drafting_date"] = (
                LessonPlanDocumentProcessingService
                ._parse_review_date(
                    drafting_date
                )
            )

        teaching_date = modification_plan.value_for(
            DocumentField.TEACHING_DATE
        )
        if teaching_date is not None:
            changes["teaching_date"] = (
                LessonPlanDocumentProcessingService
                ._parse_review_date(
                    teaching_date
                )
            )

        return replace(
            context,
            **changes,
        )

    @staticmethod
    def _parse_review_date(value):
        try:
            return datetime.strptime(
                value,
                "%d/%m/%Y",
            ).date()
        except (TypeError, ValueError) as error:
            raise ValueError(
                "date must use DD/MM/YYYY format"
            ) from error

    def process(
        self,
        *,
        row,
        drafting_date: date | None,
        content: bytes,
        original_name: str,
        modification_plan: LessonPlanModificationPlan | None = None,
    ) -> LessonPlanDocumentProcessingResult:
        safe_name = Path(
            original_name
        ).name

        if not safe_name.lower().endswith(
            ".docx"
        ):
            raise ValueError(
                "Only .docx lesson-plan files "
                "are accepted."
            )

        if not content:
            raise ValueError(
                "Lesson-plan file must not be empty."
            )

        context = (
            ScheduledLessonContextService()
            .build_from_weekly_schedule_row(
                row,
                drafting_date=drafting_date,
            )
        )

        if modification_plan is not None:
            context = self.apply_modification_plan(
                context=context,
                modification_plan=modification_plan,
            )

        output_name = (
            f"{Path(safe_name).stem}"
            ".lbg-standardized.docx"
        )

        with tempfile.TemporaryDirectory(
            prefix="lbg-lesson-plan-"
        ) as workspace_name:
            workspace = Path(
                workspace_name
            )

            source = workspace / safe_name
            output = workspace / output_name

            report_path = (
                workspace
                / (
                    f"{Path(safe_name).stem}"
                    ".lbg-standardization-report.json"
                )
            )

            source.write_bytes(
                content
            )

            pipeline = (
                LessonPlanDocumentPipeline(
                    standardizer=(
                        LessonPlanWordStandardizer
                        .from_json(
                            self._profile_path
                        )
                    )
                )
            )

            result = pipeline.process(
                source=source,
                output=output,
                report_path=report_path,
                context=context,
            )

            output_bytes = (
                output.read_bytes()
            )

        return (
            LessonPlanDocumentProcessingResult(
                output_name=output_name,
                output_bytes=output_bytes,
                unresolved_fields=(
                    result
                    .context_result
                    .unresolved_fields
                ),
            )
        )


def get_lesson_plan_document_processing_service(
    *,
    profile_path: Path,
) -> LessonPlanDocumentProcessingService:
    return LessonPlanDocumentProcessingService(
        profile_path=profile_path
    )
