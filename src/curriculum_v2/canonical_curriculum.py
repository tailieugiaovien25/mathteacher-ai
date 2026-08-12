from __future__ import annotations

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.models.curriculum_node import CurriculumNode
from curriculum_v2.processors.canonical_curriculum_context import (
    CanonicalCurriculumContext,
    CanonicalCurriculumContextService,
)
from curriculum_v2.processors.canonical_curriculum_query import (
    CanonicalCurriculumQuery,
)
from curriculum_v2.processors.curriculum_node_query import CurriculumNodeQuery


class CanonicalCurriculumFacade:
    """Stable read-only public API for canonical Mathematics curriculum data."""

    def __init__(
        self,
        requirement_query: CanonicalCurriculumQuery | None = None,
        node_query: CurriculumNodeQuery | None = None,
        context_service: CanonicalCurriculumContextService | None = None,
    ) -> None:
        self._requirements = requirement_query or CanonicalCurriculumQuery()
        self._nodes = node_query or CurriculumNodeQuery()
        self._contexts = context_service or CanonicalCurriculumContextService(
            node_query=self._nodes,
            requirement_query=self._requirements,
        )

    def requirements_for_grade(
        self,
        grade: int,
    ) -> tuple[CanonicalLearningRequirement, ...]:
        return tuple(self._requirements.by_grade(grade))

    def requirement_by_id(
        self,
        canonical_id: str,
    ) -> CanonicalLearningRequirement | None:
        return self._requirements.by_id(canonical_id)

    def search_requirements(
        self,
        keyword: str,
        *,
        grade: int | None = None,
    ) -> tuple[CanonicalLearningRequirement, ...]:
        return tuple(self._requirements.search(keyword, grade=grade))

    def nodes_for_grade(
        self,
        grade: int,
    ) -> tuple[CurriculumNode, ...]:
        return tuple(self._nodes.by_grade(grade))

    def node_by_id(
        self,
        curriculum_node_id: str,
    ) -> CurriculumNode | None:
        return self._nodes.by_id(curriculum_node_id)

    def root_nodes(
        self,
        grade: int,
    ) -> tuple[CurriculumNode, ...]:
        return tuple(self._nodes.roots(grade))

    def child_nodes(
        self,
        grade: int,
        parent_id: str,
    ) -> tuple[CurriculumNode, ...]:
        return tuple(self._nodes.children(grade, parent_id))

    def curriculum_context(
        self,
        grade: int,
        curriculum_node_id: str,
        *,
        include_descendants: bool = True,
    ) -> CanonicalCurriculumContext:
        return self._contexts.build(
            grade,
            curriculum_node_id,
            include_descendants=include_descendants,
        )


_default_facade: CanonicalCurriculumFacade | None = None


def get_canonical_curriculum() -> CanonicalCurriculumFacade:
    """Return the shared public canonical curriculum facade."""
    global _default_facade
    if _default_facade is None:
        _default_facade = CanonicalCurriculumFacade()
    return _default_facade
