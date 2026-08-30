# V57-B PHASE 1
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import ContextFieldKind


@dataclass(frozen=True, slots=True)
class ContextFieldSpec:
    name: str
    kind: ContextFieldKind
    authority: str
    depends_on: tuple[str, ...] = ()
    invalidates: tuple[str, ...] = ()
    description: str = ""


class ContextRegistry:
    def __init__(self, specs: Iterable[ContextFieldSpec]) -> None:
        ordered = tuple(specs)
        names = [item.name for item in ordered]
        if len(names) != len(set(names)):
            raise ValueError("DUPLICATE_CONTEXT_FIELD")

        self._specs = {item.name: item for item in ordered}
        self._validate_references()

    def _validate_references(self) -> None:
        known = set(self._specs)
        for spec in self._specs.values():
            unknown = set(spec.depends_on + spec.invalidates) - known
            if unknown:
                raise ValueError(
                    f"UNKNOWN_CONTEXT_FIELD_REFERENCE:{spec.name}:"
                    + ",".join(sorted(unknown))
                )

    def get(self, name: str) -> ContextFieldSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"UNREGISTERED_CONTEXT_FIELD:{name}") from exc

    def contains(self, name: str) -> bool:
        return name in self._specs

    def all(self) -> tuple[ContextFieldSpec, ...]:
        return tuple(self._specs.values())

    def downstream_of(self, field: str) -> tuple[str, ...]:
        self.get(field)
        seen: set[str] = set()
        stack = list(self.get(field).invalidates)

        while stack:
            current = stack.pop(0)
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.get(current).invalidates)

        return tuple(
            item.name
            for item in self._specs.values()
            if item.name in seen
        )


def build_default_context_registry() -> ContextRegistry:
    specs = [
        ContextFieldSpec("user_id", ContextFieldKind.GLOBAL, "IDENTITY",
                         invalidates=("teacher_id","academic_year","week_number","subject_ref","component_ref","grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("teacher_id", ContextFieldKind.GLOBAL, "TEACHING_ASSIGNMENT",
                         depends_on=("user_id",),
                         invalidates=("subject_ref","component_ref","grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("academic_year", ContextFieldKind.GLOBAL, "ACADEMIC_CALENDAR",
                         depends_on=("user_id",),
                         invalidates=("week_number","subject_ref","component_ref","grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("week_number", ContextFieldKind.GLOBAL, "ACADEMIC_CALENDAR",
                         depends_on=("academic_year",),
                         invalidates=("subject_ref","component_ref","grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("subject_ref", ContextFieldKind.GLOBAL, "TEACHING_ASSIGNMENT",
                         depends_on=("teacher_id","academic_year"),
                         invalidates=("component_ref","grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("component_ref", ContextFieldKind.GLOBAL, "TEACHING_ASSIGNMENT",
                         depends_on=("subject_ref",),
                         invalidates=("grade","class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("grade", ContextFieldKind.GLOBAL, "ACTIVE_TEACHER_TIMETABLE",
                         depends_on=("week_number","subject_ref"),
                         invalidates=("class_id","timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("class_id", ContextFieldKind.GLOBAL, "ACTIVE_TEACHER_TIMETABLE",
                         depends_on=("week_number","subject_ref"),
                         invalidates=("timetable_slot_id","teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("timetable_slot_id", ContextFieldKind.DERIVED, "ACTIVE_TEACHER_TIMETABLE",
                         depends_on=("teacher_id","academic_year","week_number","subject_ref","component_ref","class_id"),
                         invalidates=("teaching_date","timetable_period","curriculum_period","lesson_id")),
        ContextFieldSpec("teaching_date", ContextFieldKind.DERIVED, "ACTIVE_TEACHER_TIMETABLE",
                         depends_on=("timetable_slot_id",)),
        ContextFieldSpec("timetable_period", ContextFieldKind.DERIVED, "ACTIVE_TEACHER_TIMETABLE",
                         depends_on=("timetable_slot_id",)),
        ContextFieldSpec("curriculum_period", ContextFieldKind.GLOBAL, "PPCT_CURRICULUM",
                         depends_on=("subject_ref","component_ref","grade"),
                         invalidates=("lesson_id",)),
        ContextFieldSpec("lesson_id", ContextFieldKind.DERIVED, "PPCT_CURRICULUM",
                         depends_on=("curriculum_period",)),
        ContextFieldSpec("source_page", ContextFieldKind.LOCAL, "UI"),
        ContextFieldSpec("source_control", ContextFieldKind.LOCAL, "UI"),
        ContextFieldSpec("context_version", ContextFieldKind.DERIVED, "SYSTEM_CONTEXT"),
    ]
    return ContextRegistry(specs)
