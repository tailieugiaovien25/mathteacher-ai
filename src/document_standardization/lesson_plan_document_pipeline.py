from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any, Callable

from document_standardization.lesson_plan_document_context_applier import (
    ContextApplicationResult,
    LessonPlanDocumentContextApplier,
)
from document_standardization.lesson_plan_standardizer import (
    LessonPlanStandardizationOptions,
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
        options: LessonPlanStandardizationOptions | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
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

            resolved_options = (
                options
                or LessonPlanStandardizationOptions()
            )

            if resolved_options.sync_context:
                context_result = (
                    self.context_applier.apply(
                        source,
                        context_applied,
                        context,
                    )
                )
            else:
                from shutil import copyfile

                copyfile(source, context_applied)
                context_result = ContextApplicationResult(
                    applied_fields=(),
                    unresolved_fields=(),
                )

            if options is None:
                standardization_report = (
                    self.standardizer.standardize(
                        context_applied,
                        output,
                        report_path,
                        progress_callback=progress_callback,
                    )
                )
            else:
                standardization_report = (
                    self.standardizer.standardize(
                        context_applied,
                        output,
                        report_path,
                        options=resolved_options,
                        progress_callback=progress_callback,
                    )
                )

        return LessonPlanDocumentPipelineResult(
            context_result=context_result,
            standardization_report=standardization_report,
        )
