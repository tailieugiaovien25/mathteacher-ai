from __future__ import annotations

from dataclasses import dataclass

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.models.curriculum_node import CurriculumNode
from curriculum_v2.processors.canonical_curriculum_query import (
    CanonicalCurriculumQuery,
)
from curriculum_v2.processors.curriculum_node_query import CurriculumNodeQuery


@dataclass(frozen=True)
class CanonicalCurriculumContext:
    grade: int
    selected_node: CurriculumNode
    ancestors: tuple[CurriculumNode, ...]
    descendants: tuple[CurriculumNode, ...]
    requirements: tuple[CanonicalLearningRequirement, ...]


class CanonicalCurriculumContextService:
    """Compose canonical node hierarchy and YCCĐ into one read-only context."""

    def __init__(
        self,
        node_query: CurriculumNodeQuery | None = None,
        requirement_query: CanonicalCurriculumQuery | None = None,
    ) -> None:
        self.node_query = node_query or CurriculumNodeQuery()
        self.requirement_query = requirement_query or CanonicalCurriculumQuery()

    @staticmethod
    def _grade_prefix(grade: int) -> str:
        if grade not in {6, 7, 8, 9}:
            raise ValueError("grade must be one of 6, 7, 8, 9")
        return f"CURR-NODE-MATH-G{grade}-"

    def build(
        self,
        grade: int,
        curriculum_node_id: str,
        *,
        include_descendants: bool = True,
    ) -> CanonicalCurriculumContext:
        prefix = self._grade_prefix(grade)
        if not curriculum_node_id.startswith(prefix):
            raise ValueError(
                "curriculum_node_id does not belong to the requested grade"
            )

        selected_node = self.node_query.by_id(curriculum_node_id)
        if selected_node is None:
            raise LookupError(
                f"canonical curriculum node not found: {curriculum_node_id}"
            )

        ancestors = tuple(
            self.node_query.ancestors(grade, curriculum_node_id)
        )
        descendants = (
            tuple(self.node_query.descendants(grade, curriculum_node_id))
            if include_descendants
            else ()
        )

        scoped_node_ids = {curriculum_node_id}
        scoped_node_ids.update(
            node.curriculum_node_id for node in descendants
        )

        requirements = tuple(
            requirement
            for requirement in self.requirement_query.by_grade(grade)
            if requirement.curriculum_node_ref in scoped_node_ids
        )

        return CanonicalCurriculumContext(
            grade=grade,
            selected_node=selected_node,
            ancestors=ancestors,
            descendants=descendants,
            requirements=requirements,
        )


def get_canonical_curriculum_context_service(
) -> CanonicalCurriculumContextService:
    return CanonicalCurriculumContextService()
