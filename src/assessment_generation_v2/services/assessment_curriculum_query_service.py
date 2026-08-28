"""Canonical assessment curriculum read-path service.

This module owns application-level curriculum queries.
It contains no database-adapter or UI dependency and performs no writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class AssessmentCurriculumQueryError(RuntimeError):
    """Raised when canonical curriculum data violates the read contract."""


def _required_text(
    value: object,
    field_name: str,
) -> str:
    text = str(value or "").strip()

    if not text:
        raise AssessmentCurriculumQueryError(
            f"{field_name} is required"
        )

    return text


@dataclass(frozen=True, slots=True)
class AssessmentCurriculumProgram:
    program_code: str
    program_name: str
    subject_code: str
    education_level: str
    grade_min: int
    grade_max: int
    version_label: str
    status: str

    def __post_init__(self) -> None:
        for field_name in (
            "program_code",
            "program_name",
            "subject_code",
            "education_level",
            "version_label",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not 1 <= int(self.grade_min) <= 12:
            raise AssessmentCurriculumQueryError(
                "grade_min must be between 1 and 12"
            )

        if not 1 <= int(self.grade_max) <= 12:
            raise AssessmentCurriculumQueryError(
                "grade_max must be between 1 and 12"
            )

        if int(self.grade_min) > int(self.grade_max):
            raise AssessmentCurriculumQueryError(
                "grade_min must not exceed grade_max"
            )


@dataclass(frozen=True, slots=True)
class AssessmentCurriculumTopic:
    topic_code: str
    program_code: str
    parent_topic_code: str | None
    grade_level: int
    domain_code: str
    topic_name: str
    sequence_number: int
    status: str
    canonical_node_type: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "topic_code",
            "program_code",
            "domain_code",
            "topic_name",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not 1 <= int(self.grade_level) <= 12:
            raise AssessmentCurriculumQueryError(
                "grade_level must be between 1 and 12"
            )

        if int(self.sequence_number) < 0:
            raise AssessmentCurriculumQueryError(
                "sequence_number must be non-negative"
            )


@dataclass(frozen=True, slots=True)
class AssessmentLearningRequirement:
    requirement_code: str
    program_code: str
    topic_code: str
    grade_level: int
    requirement_text: str
    source_locator: str | None
    version_number: int
    status: str
    canonical_status: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "requirement_code",
            "program_code",
            "topic_code",
            "requirement_text",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not 1 <= int(self.grade_level) <= 12:
            raise AssessmentCurriculumQueryError(
                "grade_level must be between 1 and 12"
            )

        if int(self.version_number) < 1:
            raise AssessmentCurriculumQueryError(
                "version_number must be positive"
            )


@dataclass(frozen=True, slots=True)
class AssessmentCurriculumTopicTreeNode:
    topic: AssessmentCurriculumTopic
    children: tuple["AssessmentCurriculumTopicTreeNode", ...]


@dataclass(frozen=True, slots=True)
class AssessmentCurriculumSelection:
    program: AssessmentCurriculumProgram
    topics: tuple[AssessmentCurriculumTopic, ...]
    requirements: tuple[AssessmentLearningRequirement, ...]
    topic_tree: tuple[AssessmentCurriculumTopicTreeNode, ...]


class AssessmentCurriculumCatalog(Protocol):
    """Port for governed canonical curriculum reads."""

    def find_active_program(
        self,
        *,
        subject_code: str,
        grade_level: int,
    ) -> AssessmentCurriculumProgram | None:
        ...

    def list_topics(
        self,
        *,
        program_code: str,
        grade_level: int,
    ) -> Sequence[AssessmentCurriculumTopic]:
        ...

    def list_requirements(
        self,
        *,
        program_code: str,
        grade_level: int,
        topic_codes: Sequence[str] | None = None,
    ) -> Sequence[AssessmentLearningRequirement]:
        ...


class AssessmentCurriculumQueryService:
    """Application service for governed canonical curriculum reads."""

    def __init__(
        self,
        *,
        catalog: AssessmentCurriculumCatalog,
    ) -> None:
        self._catalog = catalog

    @staticmethod
    def build_topic_tree(
        topics: Sequence[AssessmentCurriculumTopic],
    ) -> tuple[AssessmentCurriculumTopicTreeNode, ...]:
        topic_rows = tuple(topics)

        by_code: dict[str, AssessmentCurriculumTopic] = {}

        for topic in topic_rows:
            if topic.topic_code in by_code:
                raise AssessmentCurriculumQueryError(
                    "Duplicate topic code: "
                    + topic.topic_code
                )

            by_code[topic.topic_code] = topic

        children_by_parent: dict[
            str | None,
            list[AssessmentCurriculumTopic],
        ] = {}

        for topic in topic_rows:
            parent = topic.parent_topic_code

            if (
                parent is not None
                and parent not in by_code
            ):
                raise AssessmentCurriculumQueryError(
                    "Topic references parent outside "
                    "the selected grade: "
                    + topic.topic_code
                    + " -> "
                    + parent
                )

            if parent == topic.topic_code:
                raise AssessmentCurriculumQueryError(
                    "Topic cannot be its own parent: "
                    + topic.topic_code
                )

            children_by_parent.setdefault(
                parent,
                [],
            ).append(topic)

        def sort_key(
            topic: AssessmentCurriculumTopic,
        ) -> tuple[int, str]:
            return (
                int(topic.sequence_number),
                topic.topic_code,
            )

        for rows in children_by_parent.values():
            rows.sort(key=sort_key)

        visiting: set[str] = set()
        visited: set[str] = set()

        def build(
            topic: AssessmentCurriculumTopic,
        ) -> AssessmentCurriculumTopicTreeNode:
            code = topic.topic_code

            if code in visiting:
                raise AssessmentCurriculumQueryError(
                    "Topic hierarchy cycle detected at: "
                    + code
                )

            visiting.add(code)

            child_nodes = tuple(
                build(child)
                for child in children_by_parent.get(
                    code,
                    (),
                )
            )

            visiting.remove(code)
            visited.add(code)

            return AssessmentCurriculumTopicTreeNode(
                topic=topic,
                children=child_nodes,
            )

        roots = tuple(
            build(topic)
            for topic in children_by_parent.get(
                None,
                (),
            )
        )

        if len(visited) != len(topic_rows):
            unresolved = sorted(
                set(by_code) - visited
            )

            raise AssessmentCurriculumQueryError(
                "Topic hierarchy contains unreachable "
                "or cyclic nodes: "
                + ", ".join(unresolved)
            )

        return roots

    def load_grade_curriculum(
        self,
        *,
        subject_code: str,
        grade_level: int,
    ) -> AssessmentCurriculumSelection:

        normalized_subject = _required_text(
            subject_code,
            "subject_code",
        )

        if not 1 <= int(grade_level) <= 12:
            raise AssessmentCurriculumQueryError(
                "grade_level must be between 1 and 12"
            )

        program = self._catalog.find_active_program(
            subject_code=normalized_subject,
            grade_level=int(grade_level),
        )

        if program is None:
            raise AssessmentCurriculumQueryError(
                "No active curriculum program found"
            )

        topics = tuple(
            self._catalog.list_topics(
                program_code=program.program_code,
                grade_level=int(grade_level),
            )
        )

        requirements = tuple(
            self._catalog.list_requirements(
                program_code=program.program_code,
                grade_level=int(grade_level),
            )
        )

        topic_codes = {
            topic.topic_code
            for topic in topics
        }

        orphan_requirements = [
            requirement.requirement_code
            for requirement in requirements
            if requirement.topic_code not in topic_codes
        ]

        if orphan_requirements:
            raise AssessmentCurriculumQueryError(
                "Requirements reference topics "
                "outside the selected grade: "
                + ", ".join(orphan_requirements)
            )

        non_verified = [
            requirement.requirement_code
            for requirement in requirements
            if requirement.canonical_status != "VERIFIED"
        ]

        if non_verified:
            raise AssessmentCurriculumQueryError(
                "Non-verified canonical requirements returned: "
                + ", ".join(non_verified)
            )

        topic_tree = self.build_topic_tree(
            topics
        )

        return AssessmentCurriculumSelection(
            program=program,
            topics=topics,
            requirements=requirements,
            topic_tree=topic_tree,
        )

    def list_requirements_for_topics(
        self,
        *,
        subject_code: str,
        grade_level: int,
        topic_codes: Sequence[str],
    ) -> tuple[AssessmentLearningRequirement, ...]:

        selection = self.load_grade_curriculum(
            subject_code=subject_code,
            grade_level=grade_level,
        )

        requested = tuple(
            dict.fromkeys(
                _required_text(
                    code,
                    "topic_code",
                )
                for code in topic_codes
            )
        )

        available = {
            topic.topic_code
            for topic in selection.topics
        }

        unknown = [
            code
            for code in requested
            if code not in available
        ]

        if unknown:
            raise AssessmentCurriculumQueryError(
                "Unknown topic codes: "
                + ", ".join(unknown)
            )

        if not requested:
            return ()

        requirements = tuple(
            self._catalog.list_requirements(
                program_code=selection.program.program_code,
                grade_level=int(grade_level),
                topic_codes=requested,
            )
        )

        invalid = [
            requirement.requirement_code
            for requirement in requirements
            if requirement.canonical_status != "VERIFIED"
        ]

        if invalid:
            raise AssessmentCurriculumQueryError(
                "Non-verified canonical requirements returned: "
                + ", ".join(invalid)
            )

        return requirements
