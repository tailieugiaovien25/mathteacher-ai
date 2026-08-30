# V57-B PHASE 1
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping


class ContextFieldKind(str, Enum):
    GLOBAL = "GLOBAL"
    DERIVED = "DERIVED"
    LOCAL = "LOCAL"


@dataclass(frozen=True, slots=True)
class SystemContext:
    user_id: str | None = None
    teacher_id: str | None = None
    academic_year: str | None = None
    week_number: int | None = None
    subject_ref: str | None = None
    component_ref: str | None = None
    grade: int | None = None
    class_id: str | None = None
    timetable_slot_id: str | None = None
    teaching_date: date | None = None
    timetable_period: int | None = None
    curriculum_period: int | None = None
    lesson_id: str | None = None
    source_page: str | None = None
    source_control: str | None = None
    context_version: int = 0

    def with_values(self, **changes: Any) -> "SystemContext":
        return replace(self, **changes)

    def as_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(frozen=True, slots=True)
class ContextChange:
    field: str
    value: Any
    source_page: str
    source_control: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ContextEvent:
    field: str
    old_value: Any
    new_value: Any
    source_page: str
    source_control: str
    invalidated_fields: tuple[str, ...]
    context_version: int
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class SynchronizationResult:
    context: SystemContext
    events: tuple[ContextEvent, ...]
    invalidated_fields: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] | None = None
