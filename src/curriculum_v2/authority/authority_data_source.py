from abc import ABC, abstractmethod

from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
)
from curriculum_v2.models.canonical_time_allocation import (
    CanonicalTimeAllocation,
)
from curriculum_v2.models.curriculum_node import (
    CurriculumNode,
)


class AuthorityDataSource(ABC):
    """
    Stable read boundary for authoritative educational data.

    The contract knows canonical educational domain objects and
    logical references only.

    It MUST NOT know JSON, Excel, databases, APIs, folders,
    file paths, or any concrete storage implementation.
    """

    @abstractmethod
    def requirements_for_grade(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> tuple[CanonicalLearningRequirement, ...]:
        raise NotImplementedError

    @abstractmethod
    def requirement_by_id(
        self,
        *,
        curriculum_ref: str,
        canonical_id: str,
    ) -> CanonicalLearningRequirement | None:
        raise NotImplementedError

    @abstractmethod
    def nodes_for_grade(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> tuple[CurriculumNode, ...]:
        raise NotImplementedError

    @abstractmethod
    def node_by_id(
        self,
        *,
        curriculum_ref: str,
        curriculum_node_id: str,
    ) -> CurriculumNode | None:
        raise NotImplementedError

    @abstractmethod
    def time_allocation(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> CanonicalTimeAllocation | None:
        raise NotImplementedError
