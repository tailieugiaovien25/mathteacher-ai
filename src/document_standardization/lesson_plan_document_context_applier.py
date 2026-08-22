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
            """
            Compatibility entry point.

            Public API remains unchanged, but canonical
            metadata mutation is delegated to the
            preservation-first metadata overlay engine.
            """
            source = source.resolve()
            output = output.resolve()

            if source == output:
                raise ValueError(
                    "Kh\u00f4ng \u0111\u01b0\u1ee3c ghi \u0111\u00e8 t\u1ec7p Word g\u1ed1c."
                )

            if (
                source.suffix.lower() != ".docx"
                or output.suffix.lower() != ".docx"
            ):
                raise ValueError(
                    "Context applier ch\u1ec9 x\u1eed l\u00fd t\u1ec7p .docx."
                )

            if not isinstance(
                context,
                ScheduledLessonContext,
            ):
                raise TypeError(
                    "context must be ScheduledLessonContext"
                )

            from document_standardization.lesson_plan_metadata import (
                LessonPlanMetadata,
            )
            from document_standardization.lesson_plan_metadata_overlay import (
                LessonPlanMetadataOverlay,
            )

            document = Document(source)

            metadata = LessonPlanMetadata(
                drafting_date=context.drafting_date,
                teaching_date=context.teaching_date,
                class_name=context.class_id,
                curriculum_period=(
                    context.curriculum_period
                ),
                lesson_title=context.lesson_title,
            )

            overlay_result = (
                LessonPlanMetadataOverlay()
                .apply(
                    document=document,
                    metadata=metadata,
                )
            )

            output.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            document.save(output)

            field_name_map = {
                "drafting_date": "drafting_date",
                "teaching_date": "teaching_date",
                "class_name": "class_id",
                "curriculum_period": (
                    "curriculum_period"
                ),
                "lesson_title": "lesson_title",
            }

            unresolved_metadata = {
                field.value
                for field
                in overlay_result.unresolved_fields
            }

            requested = (
                metadata.overlay_values()
            )

            applied = []

            unresolved = []

            for metadata_name in requested:
                public_name = field_name_map.get(
                    metadata_name,
                    metadata_name,
                )

                if (
                    metadata_name
                    in unresolved_metadata
                ):
                    unresolved.append(
                        public_name
                    )
                else:
                    applied.append(
                        public_name
                    )

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
        *,
        context: ScheduledLessonContext,
    ) -> bool:
        if not value:
            return False

        for paragraph in self._all_paragraphs(
            document
        ):
            original_text = paragraph.text

            updated_text = (
                self._replace_field_in_text(
                    original_text,
                    field_name=field_name,
                    value=value,
                    context=context,
                )
            )

            if updated_text is None:
                continue

            if updated_text != original_text:
                self._replace_paragraph_text(
                    paragraph,
                    updated_text,
                )

            return True

        if self._apply_table_label_value(
            document,
            field_name=field_name,
            value=value,
        ):
            return True

        return False

    @classmethod
    def _apply_table_label_value(
        cls,
        document,
        *,
        field_name: str,
        value: str,
    ) -> bool:
        """
        Support common lesson-plan tables where
        the metadata label and value occupy
        separate cells in the same row.

        Example:
            | Lớp       | 8A1        |
            | Tiết PPCT | 1          |
            | Tên bài   | Bài cũ     |
        """
        patterns = cls._FIELD_PATTERNS.get(
            field_name,
            (),
        )

        for table in document.tables:
            for row in table.rows:
                if len(row.cells) < 2:
                    continue

                label = row.cells[0].text.strip()

                if not cls._matches_table_label(
                    label,
                    patterns,
                ):
                    continue

                value_cell = row.cells[1]

                if value_cell.paragraphs:
                    paragraph = (
                        value_cell.paragraphs[0]
                    )
                    cls._replace_paragraph_text(
                        paragraph,
                        value,
                    )

                    for extra_paragraph in (
                        value_cell.paragraphs[1:]
                    ):
                        cls._replace_paragraph_text(
                            extra_paragraph,
                            "",
                        )
                else:
                    value_cell.text = value

                return True

        return False

    @staticmethod
    def _matches_table_label(
        label: str,
        patterns,
    ) -> bool:
        normalized = label.strip()

        for pattern in patterns:
            table_pattern = pattern

            if table_pattern.endswith(
                r"\s*:"
            ):
                table_pattern = (
                    table_pattern[:-4]
                )
            elif table_pattern.endswith(":"):
                table_pattern = (
                    table_pattern[:-1]
                )

            if re.match(
                table_pattern + r"\s*$",
                normalized,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    @classmethod
    def _replace_field_in_text(
        cls,
        text: str,
        *,
        field_name: str,
        value: str,
        context: ScheduledLessonContext,
    ) -> str | None:
        if field_name == "drafting_date":
            return cls._replace_simple_value(
                text,
                pattern=(
                    r"(?P<prefix>"
                    r"ng\u00e0y\s+so\u1ea1n"
                    r"\s*:\s*)"
                    r"\d{1,2}/\d{1,2}/\d{2,4}"
                ),
                value=value,
            )

        if field_name == "teaching_date":
            return cls._replace_simple_value(
                text,
                pattern=(
                    r"(?P<prefix>"
                    r"ng\u00e0y\s+"
                    r"(?:d\u1ea1y|gi\u1ea3ng)"
                    r"\s*:\s*)"
                    r"\d{1,2}/\d{1,2}/\d{2,4}"
                ),
                value=value,
            )

        if field_name == "class_id":
            return cls._replace_simple_value(
                text,
                pattern=(
                    r"(?P<prefix>"
                    r"l\u1edbp\s*:?\s*)"
                    r"[A-Za-z0-9._-]+"
                ),
                value=value,
            )

        if field_name == "curriculum_period":
            explicit = (
                cls._replace_simple_value(
                    text,
                    pattern=(
                        r"(?P<prefix>"
                        r"ti\u1ebft\s+ppct"
                        r"\s*:\s*)"
                        r"\d+"
                    ),
                    value=value,
                )
            )

            if explicit is not None:
                return explicit

            explicit = (
                cls._replace_simple_value(
                    text,
                    pattern=(
                        r"(?P<prefix>"
                        r"ppct\s*:\s*)"
                        r"\d+"
                    ),
                    value=value,
                )
            )

            if explicit is not None:
                return explicit

            explicit = (
                cls._replace_simple_value(
                    text,
                    pattern=(
                        r"(?P<prefix>"
                        r"^\s*ti\u1ebft"
                        r"\s*:\s*)"
                        r"\d+"
                    ),
                    value=value,
                )
            )

            if explicit is not None:
                return explicit

            return cls._replace_period_heading(
                text,
                curriculum_period=(
                    context.curriculum_period
                ),
                period_in_lesson=(
                    context.period_in_lesson
                ),
            )

        if field_name == "lesson_title":
            explicit = re.match(
                (
                    r"(?P<prefix>"
                    r"^\s*(?:"
                    r"t\u00ean\s+b\u00e0i"
                    r"|b\u00e0i"
                    r")\s*:\s*)"
                    r"(?P<old>.*)$"
                ),
                text,
                flags=re.IGNORECASE,
            )

            if explicit is not None:
                return (
                    explicit.group("prefix")
                    + value
                )

            return cls._replace_lesson_heading(
                text,
                lesson_title=value,
            )

        return None

    @staticmethod
    def _replace_simple_value(
        text: str,
        *,
        pattern: str,
        value: str,
    ) -> str | None:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            return None

        return (
            text[:match.start()]
            + match.group("prefix")
            + value
            + text[match.end():]
        )

    @staticmethod
    def _replace_period_heading(
        text: str,
        *,
        curriculum_period: int,
        period_in_lesson: int,
    ) -> str | None:
        match = re.match(
            (
                r"(?P<prefix>"
                r"^\s*ti\u1ebft\s+)"
                r"(?P<periods>"
                r"\d+(?:\s*(?:,|\+)\s*\d+)*"
                r")"
                r"(?P<separator>"
                r"\s*[.\-:]?)"
            ),
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            return None

        existing_periods = re.findall(
            r"\d+",
            match.group("periods"),
        )

        count = max(
            1,
            len(existing_periods),
        )

        start_period = (
            curriculum_period
            - period_in_lesson
            + 1
        )

        if start_period <= 0:
            start_period = (
                curriculum_period
            )

        original_periods = (
            match.group("periods")
        )

        period_joiner = (
            " + "
            if "+" in original_periods
            else ","
        )

        replacement_periods = (
            period_joiner.join(
                str(
                    start_period + offset
                )
                for offset in range(count)
            )
        )

        return (
            text[:match.start()]
            + match.group("prefix")
            + replacement_periods
            + match.group("separator")
            + text[match.end():]
        )

    @staticmethod
    def _replace_lesson_heading(
        text: str,
        *,
        lesson_title: str,
    ) -> str | None:
        patterns = (
            # Standalone section heading:
            # ?7: Ten bai
            (
                r"(?P<prefix>"
                r"^\s*\u00a7\s*\d+"
                r"\s*:\s*)"
                r"(?P<title>.*?)"
                r"(?P<suffix>"
                r"\s*\(\s*\d+\s+"
                r"ti\u1ebft\s*\)\s*"
                r")?$"
            ),

            # Tiet 1. BAI 1. Ten bai
            (
                r"(?P<prefix>"
                r"^\s*ti\u1ebft\s+"
                r"\d+(?:\s*,\s*\d+)*"
                r"\s*[.\-:]\s*"
                r"b\u00e0i\s+\d+"
                r"\s*[.\-:]\s*)"
                r"(?P<title>.*?)"
                r"(?P<suffix>"
                r"\s*\(\s*\d+\s+"
                r"ti\u1ebft\s*\)\s*"
                r")?$"
            ),

            # TIET 4 - ?4: Ten bai
            (
                r"(?P<prefix>"
                r"^\s*ti\u1ebft\s+"
                r"\d+(?:\s*,\s*\d+)*"
                r"\s*[.\-:]\s*"
                r"\u00a7\s*\d+"
                r"\s*:\s*)"
                r"(?P<title>.*?)"
                r"(?P<suffix>"
                r"\s*\(\s*\d+\s+"
                r"ti\u1ebft\s*\)\s*"
                r")?$"
            ),
        )

        for pattern in patterns:
            match = re.match(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match is None:
                continue

            suffix = (
                match.group("suffix")
                or ""
            )

            return (
                match.group("prefix")
                + lesson_title
                + suffix
            )

        return None

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
