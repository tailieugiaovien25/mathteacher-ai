from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from educational_planning_v2.models import TeachingSession
from lesson_planning_v2.contexts import ScheduledLessonContext

from document_standardization.lesson_plan_document_context_applier import (
    repair_lesson_plan_canonical_field,
)


_FIELD_NAME_MAP = {
    "class_name": "class_id",
    "curriculum_period": "curriculum_period",
    "lesson_title": "lesson_title",
    "drafting_date": "drafting_date",
    "teaching_date": "teaching_date",
}


@dataclass(frozen=True)
class CanonicalFieldRepairBytesResult:
    changed: bool
    content: bytes
    repair_field_name: str


def _positive_int(value: Any, *, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(name + " must be a positive integer") from error
    if isinstance(value, bool) or result <= 0:
        raise ValueError(name + " must be a positive integer")
    return result


def _date_value(value: Any, *, name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for format_text in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, format_text).date()
        except ValueError:
            pass
    raise ValueError(name + " must be a supported date")


def _teaching_session(value: Any) -> TeachingSession:
    if isinstance(value, TeachingSession):
        return value
    normalized = str(
        getattr(value, "value", getattr(value, "name", value)) or ""
    ).strip().upper().removeprefix("TEACHINGSESSION.")
    aliases = {
        "SANG": TeachingSession.MORNING,
        "BUOI_SANG": TeachingSession.MORNING,
        "MORNING": TeachingSession.MORNING,
        "CHIEU": TeachingSession.AFTERNOON,
        "BUOI_CHIEU": TeachingSession.AFTERNOON,
        "AFTERNOON": TeachingSession.AFTERNOON,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return TeachingSession(normalized)
    except (TypeError, ValueError) as error:
        raise ValueError("session must be a supported TeachingSession") from error


def build_repair_scheduled_context(
    group_context: Mapping[str, Any],
    *,
    field_key: str,
    teacher_value: str,
) -> ScheduledLessonContext:
    context = dict(group_context or {})
    occurrence = next(
        (
            dict(item)
            for item in tuple(context.get("occurrences", ()) or ())
            if isinstance(item, Mapping)
        ),
        None,
    )
    if occurrence is None:
        raise ValueError("group context has no valid occurrence")

    field_key = str(field_key or "").strip()
    teacher_value = str(teacher_value or "").strip()
    if field_key not in _FIELD_NAME_MAP:
        raise ValueError("unsupported canonical field: " + field_key)
    if not teacher_value:
        raise ValueError("teacher value must not be empty")

    teaching_date_value = occurrence.get("teaching_date")
    if field_key == "teaching_date":
        teaching_date_value = teacher_value

    return ScheduledLessonContext(
        teaching_date=_date_value(teaching_date_value, name="teaching_date"),
        drafting_date=None,
        class_id=str(occurrence.get("class_id") or "").strip(),
        subject_ref=str(context.get("subject_ref") or "").strip(),
        component_ref=(str(context.get("component_ref") or "").strip() or None),
        curriculum_period=_positive_int(
            occurrence.get("curriculum_period"),
            name="curriculum_period",
        ),
        lesson_id=str(context.get("lesson_id") or "").strip(),
        lesson_title=str(context.get("lesson_title") or "").strip(),
        session=_teaching_session(occurrence.get("session")),
        timetable_period=_positive_int(
            occurrence.get("timetable_period"),
            name="timetable_period",
        ),
        period_in_lesson=_positive_int(
            occurrence.get("period_in_lesson"),
            name="period_in_lesson",
        ),
    )


def repair_canonical_field_bytes(
    standardized_content: bytes,
    *,
    group_context: Mapping[str, Any],
    field_key: str,
    teacher_value: str,
) -> CanonicalFieldRepairBytesResult:
    content = bytes(standardized_content or b"")
    if not content:
        raise ValueError("standardized content must not be empty")

    normalized_field_key = str(field_key or "").strip()
    repair_field_name = _FIELD_NAME_MAP.get(normalized_field_key)
    if repair_field_name is None:
        raise ValueError("unsupported canonical field: " + normalized_field_key)

    repair_context = build_repair_scheduled_context(
        group_context,
        field_key=normalized_field_key,
        teacher_value=teacher_value,
    )

    with TemporaryDirectory(prefix="g1b-canonical-repair-") as directory:
        source_path = Path(directory) / "standardized-source.docx"
        output_path = Path(directory) / "standardized-repaired.docx"
        source_path.write_bytes(content)
        changed = bool(
            repair_lesson_plan_canonical_field(
                source_path,
                output_path,
                field_name=repair_field_name,
                value=str(teacher_value or "").strip(),
                context=repair_context,
            )
        )
        if not changed:
            return CanonicalFieldRepairBytesResult(
                changed=False,
                content=content,
                repair_field_name=repair_field_name,
            )
        if not output_path.is_file():
            raise RuntimeError("canonical repair returned no output DOCX")
        repaired_content = output_path.read_bytes()
        if not repaired_content:
            raise RuntimeError("canonical repair returned empty output DOCX")

    return CanonicalFieldRepairBytesResult(
        changed=True,
        content=repaired_content,
        repair_field_name=repair_field_name,
    )
