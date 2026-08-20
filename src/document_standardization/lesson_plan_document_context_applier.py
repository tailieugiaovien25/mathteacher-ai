from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from docx import Document

from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)


@dataclass(frozen=True)
class ContextApplicationResult:
    applied_fields: tuple[str, ...]
    unresolved_fields: tuple[str, ...]


class LessonPlanDocumentContextApplier:
    """
    Apply scheduled teaching metadata to an existing
    lesson-plan DOCX without owning formatting rules.
    """

    _FIELD_PATTERNS = {
        "drafting_date": (
            r"^\s*ngày\s+soạn\s*:",
        ),
        "teaching_date": (
            r"^\s*ngày\s+(?:dạy|giảng)\s*:",
        ),
        "class_id": (
            r"^\s*lớp\s*:",
        ),
        "curriculum_period": (
            r"^\s*(?:tiết|ppct|tiết\s+ppct)\s*:",
        ),
        "lesson_title": (
            r"^\s*(?:tên\s+bài|bài)\s*:",
        ),
    }

    def apply(
        self,
        source: Path,
        output: Path,
        context: ScheduledLessonContext,
    ) -> ContextApplicationResult:
        source = source.resolve()
        output = output.resolve()

        if source == output:
            raise ValueError(
                "Không được ghi đè tệp Word gốc."
            )

        if (
            source.suffix.lower() != ".docx"
            or output.suffix.lower() != ".docx"
        ):
            raise ValueError(
                "Context applier chỉ xử lý tệp .docx."
            )

        if not isinstance(
            context,
            ScheduledLessonContext,
        ):
            raise TypeError(
                "context must be ScheduledLessonContext"
            )

        document = Document(source)

        values = self._context_values(
            context
        )

        applied: list[str] = []

        for field_name, value in values.items():
            if self._apply_field(
                document,
                field_name,
                value,
            ):
                applied.append(
                    field_name
                )

        unresolved = [
            field_name
            for field_name in values
            if field_name not in applied
        ]

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        document.save(output)

        return ContextApplicationResult(
            applied_fields=tuple(applied),
            unresolved_fields=tuple(unresolved),
        )

    @staticmethod
    def _context_values(
        context: ScheduledLessonContext,
    ) -> dict[str, str]:
        drafting_date = (
            context.drafting_date.strftime(
                "%d/%m/%Y"
            )
            if context.drafting_date
            else ""
        )

        return {
            "drafting_date": drafting_date,
            "teaching_date": (
                context.teaching_date.strftime(
                    "%d/%m/%Y"
                )
            ),
            "class_id": context.class_id,
            "curriculum_period": str(
                context.curriculum_period
            ),
            "lesson_title": context.lesson_title,
        }

    def _apply_field(
        self,
        document,
        field_name: str,
        value: str,
    ) -> bool:
        if not value:
            return False

        patterns = self._FIELD_PATTERNS[
            field_name
        ]

        for paragraph in self._all_paragraphs(
            document
        ):
            text = paragraph.text

            for pattern in patterns:
                match = re.match(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match is None:
                    continue

                prefix = text[
                    : match.end()
                ]

                self._replace_paragraph_text(
                    paragraph,
                    f"{prefix} {value}",
                )

                return True

        return False

    @staticmethod
    def _all_paragraphs(document):
        yield from document.paragraphs

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from cell.paragraphs

    @staticmethod
    def _replace_paragraph_text(
        paragraph,
        value: str,
    ) -> None:
        if paragraph.runs:
            paragraph.runs[0].text = value

            for run in paragraph.runs[1:]:
                run.text = ""

            return

        paragraph.add_run(value)
