from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Protocol

from .canonical_code_catalog import (
    CanonicalCodeDefinition,
    CanonicalEducationalInputIdentity,
)


class CanonicalCodeRepository(Protocol):
    def list_codes(self, *, namespace: str | None = None, include_inactive: bool = False) -> tuple[CanonicalCodeDefinition, ...]: ...
    def get_code(self, *, namespace: str, code: str) -> CanonicalCodeDefinition | None: ...
    def save_code(self, definition: CanonicalCodeDefinition) -> CanonicalCodeDefinition: ...


class InMemoryCanonicalCodeRepository:
    def __init__(self, definitions: Iterable[CanonicalCodeDefinition] = ()) -> None:
        self._items={(x.namespace, x.code): x for x in definitions}

    def list_codes(self, *, namespace=None, include_inactive=False):
        values=tuple(self._items.values())
        if namespace is not None:
            values=tuple(x for x in values if x.namespace == namespace)
        if not include_inactive:
            values=tuple(x for x in values if x.active)
        return tuple(sorted(values, key=lambda x:(x.namespace,x.code)))

    def get_code(self, *, namespace, code):
        return self._items.get((namespace, code))

    def save_code(self, definition):
        self._items[(definition.namespace, definition.code)] = definition
        return definition


@dataclass(frozen=True)
class CanonicalResolvedLessonPlan:
    curriculum_business_id: str
    lesson_plan_business_id: str
    exact_filename: str


class CanonicalCodeService:
    def __init__(self, repository: CanonicalCodeRepository) -> None:
        self.repository=repository

    def upsert_code(self, *, namespace: str, code: str, label: str, active: bool=True):
        namespace=namespace.strip()
        code=code.strip().upper()
        label=label.strip()
        if not namespace or not code or not label:
            raise ValueError("namespace, code and label are required")
        return self.repository.save_code(CanonicalCodeDefinition(namespace,code,label,active))

    def set_active(self, *, namespace: str, code: str, active: bool):
        current=self.repository.get_code(namespace=namespace,code=code)
        if current is None:
            raise KeyError(f"Unknown canonical code: {namespace}/{code}")
        return self.repository.save_code(replace(current,active=active))

    def require_active_code(self, *, namespace: str, code: str):
        item=self.repository.get_code(namespace=namespace,code=code)
        if item is None or not item.active:
            raise KeyError(f"Inactive or unknown canonical code: {namespace}/{code}")
        return item

    def resolve_lesson_plan(self, *, grade: int, ppct_position: int,
                            subject_code: str, component_code: str | None,
                            lesson_plan_code: str) -> CanonicalResolvedLessonPlan:
        self.require_active_code(namespace="subject",code=subject_code)
        if component_code:
            self.require_active_code(namespace="component",code=component_code)
        self.require_active_code(namespace="lesson_plan",code=lesson_plan_code)
        identity=CanonicalEducationalInputIdentity(
            grade=grade, ppct_position=ppct_position,
            subject_code=subject_code, component_code=component_code,
            lesson_plan_code=lesson_plan_code,
        )
        return CanonicalResolvedLessonPlan(
            curriculum_business_id=identity.curriculum_business_id,
            lesson_plan_business_id=identity.lesson_plan_business_id,
            exact_filename=identity.lesson_plan_filename,
        )


@dataclass(frozen=True)
class CanonicalDocumentRecord:
    document_id: str
    canonical_business_id: str
    filename: str
    storage_location: str


class CanonicalLessonPlanFileResolver:
    def resolve_exact(self, *, expected_business_id: str,
                      expected_filename: str,
                      records: Iterable[CanonicalDocumentRecord]) -> CanonicalDocumentRecord | None:
        matches=tuple(
            r for r in records
            if r.filename == expected_filename
            and r.canonical_business_id == expected_business_id
        )
        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(f"Duplicate canonical lesson-plan file: {expected_filename}")
        return matches[0]
