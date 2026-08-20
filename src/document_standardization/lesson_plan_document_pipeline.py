from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from document_standardization.lesson_plan_document_context_applier import (
    ContextApplicationResult,
    LessonPlanDocumentContextApplier,
)
from document_standardization.lesson_plan_standardizer import (
    LessonPlanWordStandardizer,
)
from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)


@dataclass(frozen=True)
class LessonPlanDocumentPipelineResult:
    context_result: ContextApplicationResult
    standardization_report: dict[str, object]


class LessonPlanDocumentPipeline:
    """
    Apply scheduled lesson metadata first, then run
    deterministic lesson-plan formatting standardization.
    """

    def __init__(
        self,
        *,
        standardizer: LessonPlanWordStandardizer,
        context_applier: LessonPlanDocumentContextApplier | None = None,
    ):
        self.standardizer = standardizer
        self.context_applier = (
            context_applier
            or LessonPlanDocumentContextApplier()
        )

    def process(
        self,
        *,
        source: Path,
        output: Path,
        report_path: Path,
        context: ScheduledLessonContext,
    ) -> LessonPlanDocumentPipelineResult:
        source = source.resolve()
        output = output.resolve()
        report_path = report_path.resolve()

        if source == output:
            raise ValueError(
                "Không được ghi đè tệp Word gốc."
            )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.TemporaryDirectory(
            prefix="lesson-plan-context-"
        ) as temporary_directory:
            context_applied = (
                Path(temporary_directory)
                / "context-applied.docx"
            )

            context_result = (
                self.context_applier.apply(
                    source,
                    context_applied,
                    context,
                )
            )

            standardization_report = (
                self.standardizer.standardize(
                    context_applied,
                    output,
                    report_path,
                )
            )

        return LessonPlanDocumentPipelineResult(
            context_result=context_result,
            standardization_report=standardization_report,
        )
