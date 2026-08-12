from __future__ import annotations

from dataclasses import dataclass

from curriculum_v2.canonical_curriculum import (
    CanonicalCurriculumFacade,
    get_canonical_curriculum,
)
from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.models.curriculum_node import CurriculumNode
from educational_planning_v2.models import CurriculumScope


@dataclass(frozen=True)
class PlanningContext:
    """Resolved canonical curriculum data for one planning scope."""

    scope: CurriculumScope
    nodes: tuple[CurriculumNode, ...]
    requirements: tuple[CanonicalLearningRequirement, ...]


class PlanningContextService:
    """Resolve and validate planning references against canonical curriculum."""

    def __init__(
        self,
        curriculum: CanonicalCurriculumFacade | None = None,
    ) -> None:
        self._curriculum = curriculum or get_canonical_curriculum()

    def build(self, scope: CurriculumScope) -> PlanningContext:
        if scope.grade not in {6, 7, 8, 9}:
            raise ValueError("grade must be one of 6, 7, 8, 9")

        nodes = tuple(
            self._resolve_node(scope.grade, node_id)
            for node_id in scope.curriculum_node_ids
        )

        requirements = tuple(
            self._resolve_requirement(scope.grade, requirement_id)
            for requirement_id in scope.canonical_requirement_ids
        )

        selected_node_ids = {
            node.curriculum_node_id for node in nodes
        }

        if selected_node_ids:
            for requirement in requirements:
                if requirement.curriculum_node_ref not in selected_node_ids:
                    raise ValueError(
                        "canonical requirement is outside the selected "
                        "curriculum nodes"
                    )

        return PlanningContext(
            scope=scope,
            nodes=nodes,
            requirements=requirements,
        )

    def _resolve_node(
        self,
        grade: int,
        node_id: str,
    ) -> CurriculumNode:
        expected_prefix = f"CURR-NODE-MATH-G{grade}-"
        if not node_id.startswith(expected_prefix):
            raise ValueError(
                f"curriculum node {node_id} does not belong to grade {grade}"
            )

        node = self._curriculum.node_by_id(node_id)
        if node is None:
            raise LookupError(f"canonical curriculum node not found: {node_id}")
        return node

    def _resolve_requirement(
        self,
        grade: int,
        canonical_id: str,
    ) -> CanonicalLearningRequirement:
        expected_prefix = f"YCCD-MATH-{grade:02d}-"
        if not canonical_id.startswith(expected_prefix):
            raise ValueError(
                f"canonical requirement {canonical_id} "
                f"does not belong to grade {grade}"
            )

        requirement = self._curriculum.requirement_by_id(canonical_id)
        if requirement is None:
            raise LookupError(
                f"canonical requirement not found: {canonical_id}"
            )
        return requirement


def get_planning_context_service() -> PlanningContextService:
    return PlanningContextService()
