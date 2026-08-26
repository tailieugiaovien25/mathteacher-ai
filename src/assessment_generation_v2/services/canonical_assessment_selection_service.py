from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumSelection,
    AssessmentCurriculumTopic,
    AssessmentCurriculumTopicTreeNode,
    AssessmentLearningRequirement,
)


class CanonicalAssessmentSelectionError(ValueError):
    """Raised when canonical assessment selection is invalid."""


@dataclass(frozen=True, slots=True)
class CanonicalAssessmentSelection:
    subject_code: str
    grade_level: int
    program_code: str
    selected_topic_codes: tuple[str, ...]
    selected_requirement_codes: tuple[str, ...]
    selected_topics: tuple[AssessmentCurriculumTopic, ...] = ()
    selected_requirements: tuple[AssessmentLearningRequirement, ...] = ()
    finalized: bool = False

    def __post_init__(self) -> None:
        subject_code = _required_text(
            self.subject_code,
            "subject_code",
        )
        program_code = _required_text(
            self.program_code,
            "program_code",
        )

        grade_level = int(self.grade_level)

        if not 1 <= grade_level <= 12:
            raise CanonicalAssessmentSelectionError(
                "grade_level must be between 1 and 12"
            )

        topic_codes = _normalize_unique_codes(
            self.selected_topic_codes,
            field_name="selected_topic_codes",
        )

        requirement_codes = _normalize_unique_codes(
            self.selected_requirement_codes,
            field_name="selected_requirement_codes",
        )

        object.__setattr__(
            self,
            "subject_code",
            subject_code,
        )
        object.__setattr__(
            self,
            "grade_level",
            grade_level,
        )
        object.__setattr__(
            self,
            "program_code",
            program_code,
        )
        object.__setattr__(
            self,
            "selected_topic_codes",
            topic_codes,
        )
        object.__setattr__(
            self,
            "selected_requirement_codes",
            requirement_codes,
        )

        if self.finalized:
            if not topic_codes:
                raise CanonicalAssessmentSelectionError(
                    "finalized selection requires at least one topic"
                )

            if not requirement_codes:
                raise CanonicalAssessmentSelectionError(
                    "finalized selection requires at least one requirement"
                )


class CanonicalCurriculumReader(Protocol):
    def load_grade_curriculum(
        self,
        *,
        subject_code: str,
        grade_level: int,
    ) -> AssessmentCurriculumSelection:
        ...

    def build_topic_tree(
        self,
        topics: Sequence[AssessmentCurriculumTopic],
    ) -> tuple[AssessmentCurriculumTopicTreeNode, ...]:
        ...


class CanonicalAssessmentSelectionService:
    def __init__(
        self,
        *,
        curriculum_reader: CanonicalCurriculumReader,
    ) -> None:
        self._curriculum_reader = curriculum_reader

    def build_editing_selection(
        self,
        *,
        subject_code: str,
        grade_level: int,
        program_code: str,
        selected_topic_codes: Sequence[str] = (),
        selected_requirement_codes: Sequence[str] = (),
    ) -> CanonicalAssessmentSelection:
        selection = CanonicalAssessmentSelection(
            subject_code=subject_code,
            grade_level=grade_level,
            program_code=program_code,
            selected_topic_codes=tuple(
                selected_topic_codes
            ),
            selected_requirement_codes=tuple(
                selected_requirement_codes
            ),
            finalized=False,
        )

        return self.validate_selection(
            selection
        )

    def validate_selection(
        self,
        selection: CanonicalAssessmentSelection,
    ) -> CanonicalAssessmentSelection:
        curriculum = (
            self._curriculum_reader.load_grade_curriculum(
                subject_code=selection.subject_code,
                grade_level=selection.grade_level,
            )
        )

        if (
            curriculum.program.program_code
            != selection.program_code
        ):
            raise CanonicalAssessmentSelectionError(
                "program_code does not match active "
                "canonical curriculum"
            )

        topics_by_code = {
            topic.topic_code: topic
            for topic in curriculum.topics
        }

        requirements_by_code = {
            requirement.requirement_code:
            requirement
            for requirement in curriculum.requirements
        }

        missing_topics = [
            code
            for code in selection.selected_topic_codes
            if code not in topics_by_code
        ]

        if missing_topics:
            raise CanonicalAssessmentSelectionError(
                "unknown canonical topic codes: "
                + ", ".join(
                    missing_topics
                )
            )

        missing_requirements = [
            code
            for code
            in selection.selected_requirement_codes
            if code not in requirements_by_code
        ]

        if missing_requirements:
            raise CanonicalAssessmentSelectionError(
                "unknown canonical requirement codes: "
                + ", ".join(
                    missing_requirements
                )
            )

        selected_topics = tuple(
            topics_by_code[code]
            for code in selection.selected_topic_codes
        )

        selected_topic_set = set(
            selection.selected_topic_codes
        )

        selected_requirements = tuple(
            requirements_by_code[code]
            for code
            in selection.selected_requirement_codes
        )

        for requirement in selected_requirements:
            if requirement.topic_code not in selected_topic_set:
                raise CanonicalAssessmentSelectionError(
                    "requirement is outside selected "
                    "topic scope: "
                    + requirement.requirement_code
                )

            if requirement.status != "ACTIVE":
                raise CanonicalAssessmentSelectionError(
                    "requirement is not ACTIVE: "
                    + requirement.requirement_code
                )

            if (
                requirement.canonical_status
                != "VERIFIED"
            ):
                raise CanonicalAssessmentSelectionError(
                    "requirement is not VERIFIED: "
                    + requirement.requirement_code
                )

        return CanonicalAssessmentSelection(
            subject_code=selection.subject_code,
            grade_level=selection.grade_level,
            program_code=selection.program_code,
            selected_topic_codes=selection.selected_topic_codes,
            selected_requirement_codes=selection.selected_requirement_codes,
            selected_topics=selected_topics,
            selected_requirements=selected_requirements,
            finalized=selection.finalized,
        )

    def finalize_selection(
        self,
        selection: CanonicalAssessmentSelection,
    ) -> CanonicalAssessmentSelection:
        if not selection.selected_topic_codes:
            raise CanonicalAssessmentSelectionError(
                "finalization requires at least one "
                "canonical topic"
            )

        if not selection.selected_requirement_codes:
            raise CanonicalAssessmentSelectionError(
                "finalization requires at least one "
                "canonical requirement"
            )

        candidate = CanonicalAssessmentSelection(
            subject_code=selection.subject_code,
            grade_level=selection.grade_level,
            program_code=selection.program_code,
            selected_topic_codes=selection.selected_topic_codes,
            selected_requirement_codes=(
                selection.selected_requirement_codes
            ),
            finalized=True,
        )

        return self.validate_selection(
            candidate
        )

    def expand_topic_descendants_explicitly(
        self,
        *,
        subject_code: str,
        grade_level: int,
        topic_codes: Sequence[str],
    ) -> tuple[str, ...]:
        requested = _normalize_unique_codes(
            topic_codes,
            field_name="topic_codes",
        )

        if not requested:
            return ()

        curriculum = (
            self._curriculum_reader.load_grade_curriculum(
                subject_code=subject_code,
                grade_level=grade_level,
            )
        )

        topics_by_code = {
            topic.topic_code: topic
            for topic in curriculum.topics
        }

        for code in requested:
            if code not in topics_by_code:
                raise CanonicalAssessmentSelectionError(
                    "unknown canonical topic code: "
                    + code
                )

        children_by_parent: dict[
            str,
            list[AssessmentCurriculumTopic],
        ] = {}

        for topic in curriculum.topics:
            parent = topic.parent_topic_code

            if parent is None:
                continue

            children_by_parent.setdefault(
                parent,
                [],
            ).append(
                topic
            )

        for children in children_by_parent.values():
            children.sort(
                key=lambda topic: (
                    topic.sequence_number,
                    topic.topic_code,
                )
            )

        expanded: list[str] = []
        seen: set[str] = set()

        def visit(code: str) -> None:
            if code in seen:
                return

            seen.add(code)
            expanded.append(code)

            for child in children_by_parent.get(
                code,
                (),
            ):
                visit(
                    child.topic_code
                )

        for code in requested:
            visit(code)

        canonical_order = {
            topic.topic_code: index
            for index, topic
            in enumerate(curriculum.topics)
        }

        expanded.sort(
            key=lambda code: (
                canonical_order.get(
                    code,
                    10**9,
                ),
                code,
            )
        )

        return tuple(
            expanded
        )


def _required_text(
    value: object,
    field_name: str,
) -> str:
    normalized = str(
        value or ""
    ).strip()

    if not normalized:
        raise CanonicalAssessmentSelectionError(
            field_name + " is required"
        )

    return normalized


def _normalize_unique_codes(
    values: Sequence[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(
        _required_text(
            value,
            field_name,
        )
        for value in values
    )

    if len(set(normalized)) != len(normalized):
        raise CanonicalAssessmentSelectionError(
            field_name
            + " contains duplicate canonical IDs"
        )

    return normalized
