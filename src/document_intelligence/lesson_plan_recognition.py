from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RecognizedDocumentField:
    field_name: str
    value: str
    evidence: str


class LessonPlanRecognitionEngine:
    """
    Pure deterministic recognition for lesson-plan text.

    This engine only recognizes metadata.
    It never modifies a DOCX document.
    """

    _SIMPLE_PATTERNS = {
        "drafting_date": (
            r"ngày\s+soạn\s*:\s*"
            r"(?P<value>\d{1,2}/\d{1,2}/\d{4})"
        ),
        "teaching_date": (
            r"ngày\s+(?:dạy|giảng)\s*:\s*"
            r"(?P<value>\d{1,2}/\d{1,2}/\d{4})"
        ),
        "class_name": (
            r"lớp\s*:?\s*"
            r"(?P<value>[A-Za-z0-9._-]+)"
        ),
        "curriculum_period": (
            r"(?:tiết\s+ppct|ppct|tiết)"
            r"\s*:\s*"
            r"(?P<value>\d+)"
        ),
        "lesson_title": (
            r"(?:tên\s+bài|bài)"
            r"\s*:\s*"
            r"(?P<value>.+?)\s*$"
        ),
    }

    _HEADING_PATTERNS = (
        (
            r"^\s*tiết\s+"
            r"(?P<periods>\d+(?:\s*,\s*\d+)*)"
            r"\s*[.\-:]\s*"
            r"bài\s+\d+"
            r"\s*[.\-:]\s*"
            r"(?P<title>.*?)"
            r"(?:\s*\(\s*\d+\s+tiết\s*\))?\s*$"
        ),
        (
            r"^\s*tiết\s+"
            r"(?P<periods>\d+(?:\s*,\s*\d+)*)"
            r"\s*[.\-:]\s*"
            r"§\s*\d+"
            r"\s*:\s*"
            r"(?P<title>.*?)"
            r"(?:\s*\(\s*\d+\s+tiết\s*\))?\s*$"
        ),
    )

    def recognize_text(
        self,
        text: str,
    ) -> tuple[RecognizedDocumentField, ...]:
        stripped = text.strip()

        if not stripped:
            return ()

        results: list[RecognizedDocumentField] = []

        for field_name, pattern in (
            self._SIMPLE_PATTERNS.items()
        ):
            match = re.search(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            )

            if match is None:
                continue

            results.append(
                RecognizedDocumentField(
                    field_name=field_name,
                    value=match.group("value").strip(),
                    evidence=stripped,
                )
            )

        for pattern in self._HEADING_PATTERNS:
            match = re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            )

            if match is None:
                continue

            periods = re.findall(
                r"\d+",
                match.group("periods"),
            )

            if periods:
                results.append(
                    RecognizedDocumentField(
                        field_name="curriculum_period",
                        value=periods[-1],
                        evidence=stripped,
                    )
                )

            title = match.group("title").strip()

            if title:
                results.append(
                    RecognizedDocumentField(
                        field_name="lesson_title",
                        value=title,
                        evidence=stripped,
                    )
                )

            break

        return tuple(results)
