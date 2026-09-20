"""Fail-closed canonical scope orchestration for the Math 6-9 assessment builder.

This service composes existing canonical infrastructure only:
- source items are resolved through exact VERIFIED source bindings,
- textbook lesson-to-requirement mappings must be VERIFIED,
- canonical curriculum requirements must be ACTIVE and VERIFIED,
- CanonicalAssessmentSelectionService remains the final validator.

It does not read PPCT rows, candidate JSON files, Supabase, or use fuzzy/AI
fallbacks. Blocked results are explicit and never auto-fill the builder.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, Sequence

from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelectionError,
    CanonicalAssessmentSelectionService,
    CanonicalCurriculumReader,
)
from curriculum_v2.source_binding.models import CurriculumSourceItem
from curriculum_v2.source_binding.registry import (
    SourceCanonicalBindingRegistry,
    SourceCanonicalBindingResolutionError,
)
from curriculum_v2.textbooks.models.textbook_requirement_mapping import (
    TextbookRequirementMapping,
)


READY = "READY"
BLOCKED_UNAVAILABLE = "BLOCKED_UNAVAILABLE"
BLOCKED_AMBIGUOUS = "BLOCKED_AMBIGUOUS"
BLOCKED_UNVERIFIED = "BLOCKED_UNVERIFIED"

_ALLOWED_STATUSES = frozenset(
    {
        READY,
        BLOCKED_UNAVAILABLE,
        BLOCKED_AMBIGUOUS,
        BLOCKED_UNVERIFIED,
    }
)


class TextbookRequirementMappingProvider(Protocol):
    def get_textbook_requirement_mappings(
        self,
        *,
        textbook_ref: str,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ) -> tuple[object, ...]:
        ...


@dataclass(frozen=True, slots=True)
class AssessmentBuilderCanonicalScopeResult:
    status: str
    source_item_refs: tuple[str, ...] = ()
    lesson_ids: tuple[str, ...] = ()
    topic_codes: tuple[str, ...] = ()
    requirement_codes: tuple[str, ...] = ()
    blocking_reasons: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_status = str(self.status or "").strip().upper()
        if normalized_status not in _ALLOWED_STATUSES:
            raise ValueError("unsupported canonical scope status")
        object.__setattr__(self, "status", normalized_status)

        for field_name in (
            "source_item_refs",
            "lesson_ids",
            "topic_codes",
            "requirement_codes",
            "blocking_reasons",
            "provenance_refs",
        ):
            values = tuple(
                str(value).strip()
                for value in getattr(self, field_name)
                if str(value).strip()
            )
            object.__setattr__(self, field_name, values)

        if self.status == READY:
            if not self.lesson_ids:
                raise ValueError("READY canonical scope requires lesson_ids")
            if not self.topic_codes:
                raise ValueError("READY canonical scope requires topic_codes")
            if not self.requirement_codes:
                raise ValueError(
                    "READY canonical scope requires requirement_codes"
                )
            if self.blocking_reasons:
                raise ValueError(
                    "READY canonical scope must not contain blocking reasons"
                )
        elif not self.blocking_reasons:
            raise ValueError(
                "blocked canonical scope requires blocking reasons"
            )

    @property
    def ready(self) -> bool:
        return self.status == READY


class AssessmentBuilderCanonicalScopeService:
    """Compose existing canonical services without creating new authority."""

    def __init__(
        self,
        *,
        binding_registry: SourceCanonicalBindingRegistry,
        mapping_provider: TextbookRequirementMappingProvider,
        curriculum_reader: CanonicalCurriculumReader,
    ) -> None:
        self._binding_registry = binding_registry
        self._mapping_provider = mapping_provider
        self._curriculum_reader = curriculum_reader
        self._selection_service = CanonicalAssessmentSelectionService(
            curriculum_reader=curriculum_reader
        )

    def resolve(
        self,
        *,
        source_items: Sequence[CurriculumSourceItem],
        textbook_ref: str,
        curriculum_ref: str,
        subject_code: str,
        grade_level: int,
        program_code: str,
    ) -> AssessmentBuilderCanonicalScopeResult:
        items = tuple(source_items)
        source_refs = tuple(
            self._source_item_ref(item)
            for item in items
            if isinstance(item, CurriculumSourceItem)
        )

        if not items:
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=(),
                reason="canonical scope has no source items",
            )

        if any(
            not isinstance(item, CurriculumSourceItem)
            for item in items
        ):
            raise TypeError(
                "source_items must contain CurriculumSourceItem values"
            )

        normalized_subject = str(subject_code or "").strip().upper()
        normalized_grade = int(grade_level)
        normalized_program = str(program_code or "").strip()
        normalized_textbook = str(textbook_ref or "").strip()
        normalized_curriculum = str(curriculum_ref or "").strip()

        if not all(
            (
                normalized_subject,
                normalized_program,
                normalized_textbook,
                normalized_curriculum,
            )
        ):
            raise ValueError(
                "subject_code, program_code, textbook_ref and "
                "curriculum_ref are required"
            )

        if any(
            item.subject_code != normalized_subject
            or item.grade_level != normalized_grade
            for item in items
        ):
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                reason=(
                    "source item subject/grade does not match "
                    "the requested builder scope"
                ),
            )

        try:
            bindings = self._binding_registry.resolve_many_verified(
                items
            )
        except SourceCanonicalBindingResolutionError as error:
            message = str(error)
            status = (
                BLOCKED_AMBIGUOUS
                if "ambiguous" in message.lower()
                else BLOCKED_UNAVAILABLE
            )
            return self._blocked(
                status,
                source_item_refs=source_refs,
                reason=message,
            )

        if not bindings:
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                reason="no VERIFIED source bindings were resolved",
            )

        lesson_ids = tuple(
            binding.canonical_lesson_id
            for binding in bindings
        )

        try:
            mappings = tuple(
                self._mapping_provider.get_textbook_requirement_mappings(
                    textbook_ref=normalized_textbook,
                    curriculum_ref=normalized_curriculum,
                    subject=normalized_subject,
                    grade=normalized_grade,
                )
            )
        except (RuntimeError, ValueError, NotImplementedError) as error:
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "textbook requirement mapping provider unavailable: "
                    + str(error)
                ),
            )

        if any(
            not isinstance(mapping, TextbookRequirementMapping)
            for mapping in mappings
        ):
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "mapping provider returned a non-canonical "
                    "TextbookRequirementMapping value"
                ),
            )

        relevant: list[TextbookRequirementMapping] = []
        for lesson_id in lesson_ids:
            lesson_rows = tuple(
                mapping
                for mapping in mappings
                if mapping.lesson_id == lesson_id
            )
            if not lesson_rows:
                return self._blocked(
                    BLOCKED_UNAVAILABLE,
                    source_item_refs=source_refs,
                    lesson_ids=lesson_ids,
                    reason=(
                        "no lesson-to-requirement mapping exists for "
                        + lesson_id
                    ),
                )
            relevant.extend(lesson_rows)

        if any(
            mapping.status != "VERIFIED"
            for mapping in relevant
        ):
            return self._blocked(
                BLOCKED_UNVERIFIED,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "one or more relevant lesson-to-requirement "
                    "mappings are not VERIFIED"
                ),
            )

        requirement_codes = self._stable_unique(
            mapping.canonical_requirement_id
            for mapping in relevant
        )

        curriculum = self._curriculum_reader.load_grade_curriculum(
            subject_code=normalized_subject,
            grade_level=normalized_grade,
        )

        if curriculum.program.program_code != normalized_program:
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "program_code does not match active "
                    "canonical curriculum"
                ),
            )

        requirements_by_code = {
            requirement.requirement_code: requirement
            for requirement in curriculum.requirements
        }

        missing_requirements = tuple(
            code
            for code in requirement_codes
            if code not in requirements_by_code
        )
        if missing_requirements:
            return self._blocked(
                BLOCKED_UNAVAILABLE,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "canonical requirement is unavailable: "
                    + ", ".join(missing_requirements)
                ),
            )

        selected_requirement_rows = tuple(
            requirements_by_code[code]
            for code in requirement_codes
        )

        if any(
            requirement.status != "ACTIVE"
            or requirement.canonical_status != "VERIFIED"
            for requirement in selected_requirement_rows
        ):
            return self._blocked(
                BLOCKED_UNVERIFIED,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=(
                    "one or more canonical requirements are not "
                    "ACTIVE and VERIFIED"
                ),
            )

        topic_codes = self._stable_unique(
            requirement.topic_code
            for requirement in selected_requirement_rows
        )

        try:
            selection = (
                self._selection_service.build_editing_selection(
                    subject_code=normalized_subject,
                    grade_level=normalized_grade,
                    program_code=normalized_program,
                    selected_topic_codes=topic_codes,
                    selected_requirement_codes=requirement_codes,
                )
            )
        except CanonicalAssessmentSelectionError as error:
            message = str(error)
            status = (
                BLOCKED_UNVERIFIED
                if (
                    "not VERIFIED" in message
                    or "not ACTIVE" in message
                )
                else BLOCKED_UNAVAILABLE
            )
            return self._blocked(
                status,
                source_item_refs=source_refs,
                lesson_ids=lesson_ids,
                reason=message,
            )

        provenance_refs = tuple(
            [f"binding:{binding.binding_id}" for binding in bindings]
            + [f"mapping:{mapping.mapping_id}" for mapping in relevant]
        )

        return AssessmentBuilderCanonicalScopeResult(
            status=READY,
            source_item_refs=source_refs,
            lesson_ids=lesson_ids,
            topic_codes=selection.selected_topic_codes,
            requirement_codes=selection.selected_requirement_codes,
            provenance_refs=provenance_refs,
        )

    @staticmethod
    def _source_item_ref(item: CurriculumSourceItem) -> str:
        identity = item.identity
        return "|".join(
            (
                identity.source_type,
                identity.source_id,
                identity.source_version,
                identity.academic_year,
                identity.subject_code,
                str(identity.grade_level),
                identity.external_item_key,
            )
        )

    @staticmethod
    def _stable_unique(values: Iterable[str]) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = str(value or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return tuple(result)

    @staticmethod
    def _blocked(
        status: str,
        *,
        source_item_refs: tuple[str, ...],
        reason: str,
        lesson_ids: tuple[str, ...] = (),
    ) -> AssessmentBuilderCanonicalScopeResult:
        return AssessmentBuilderCanonicalScopeResult(
            status=status,
            source_item_refs=source_item_refs,
            lesson_ids=lesson_ids,
            blocking_reasons=(reason,),
        )
