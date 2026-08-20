from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
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

    def process(
        self,
        *,
        row,
        drafting_date: date | None,
        content: bytes,
        original_name: str,
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
