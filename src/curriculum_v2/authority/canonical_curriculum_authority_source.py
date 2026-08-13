from curriculum_v2.authority.authority_data_source import (
    AuthorityDataSource,
)
from curriculum_v2.canonical_curriculum import (
    CanonicalCurriculumFacade,
)
from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
)
from curriculum_v2.models.canonical_time_allocation import (
    CanonicalTimeAllocation,
)
from curriculum_v2.models.curriculum_node import (
    CurriculumNode,
)


class CanonicalCurriculumAuthoritySource(
    AuthorityDataSource
):
    """
    AuthorityDataSource backed by injected canonical-domain services
    and canonical authority records.

    Physical storage and dataset location remain outside this boundary.
    """

    def __init__(
        self,
        *,
        facade: CanonicalCurriculumFacade,
        curriculum_refs: tuple[str, ...],
        subject_refs: tuple[str, ...],
        time_allocations: tuple[
            CanonicalTimeAllocation,
            ...,
        ] = (),
    ) -> None:
        if not isinstance(
            facade,
            CanonicalCurriculumFacade,
        ):
            raise TypeError(
                "facade must be CanonicalCurriculumFacade"
            )

        self._facade = facade

        self._curriculum_refs = (
            self._normalize_refs(
                curriculum_refs,
                "curriculum_refs",
            )
        )

        self._subject_refs = (
            self._normalize_refs(
                subject_refs,
                "subject_refs",
            )
        )

        if not isinstance(
            time_allocations,
            tuple,
        ):
            raise TypeError(
                "time_allocations must be a tuple"
            )

        for allocation in time_allocations:
            if not isinstance(
                allocation,
                CanonicalTimeAllocation,
            ):
                raise TypeError(
                    "time_allocations must contain "
                    "CanonicalTimeAllocation objects"
                )

        self._time_allocations = tuple(
            time_allocations
        )

    def requirements_for_grade(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> tuple[
        CanonicalLearningRequirement,
        ...,
    ]:
        self._validate_scope(
            curriculum_ref=curriculum_ref,
            subject_ref=subject_ref,
        )

        grade = self._validate_grade(
            grade
        )

        requirements = tuple(
            self._facade.requirements_for_grade(
                grade
            )
        )

        return tuple(
            requirement
            for requirement in requirements
            if requirement.curriculum_ref
            == curriculum_ref
        )

    def requirement_by_id(
        self,
        *,
        curriculum_ref: str,
        canonical_id: str,
    ) -> CanonicalLearningRequirement | None:
        curriculum_ref = (
            self._require_supported_curriculum(
                curriculum_ref
            )
        )

        canonical_id = self._required_text(
            canonical_id,
            "canonical_id",
        )

        requirement = (
            self._facade.requirement_by_id(
                canonical_id
            )
        )

        if requirement is None:
            return None

        if (
            requirement.curriculum_ref
            != curriculum_ref
        ):
            return None

        return requirement

    def nodes_for_grade(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> tuple[
        CurriculumNode,
        ...,
    ]:
        self._validate_scope(
            curriculum_ref=curriculum_ref,
            subject_ref=subject_ref,
        )

        grade = self._validate_grade(
            grade
        )

        nodes = tuple(
            self._facade.nodes_for_grade(
                grade
            )
        )

        return tuple(
            node
            for node in nodes
            if node.curriculum_ref
            == curriculum_ref
        )

    def node_by_id(
        self,
        *,
        curriculum_ref: str,
        curriculum_node_id: str,
    ) -> CurriculumNode | None:
        curriculum_ref = (
            self._require_supported_curriculum(
                curriculum_ref
            )
        )

        curriculum_node_id = (
            self._required_text(
                curriculum_node_id,
                "curriculum_node_id",
            )
        )

        node = self._facade.node_by_id(
            curriculum_node_id
        )

        if node is None:
            return None

        if (
            node.curriculum_ref
            != curriculum_ref
        ):
            return None

        return node

    def time_allocation(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
        grade: int,
    ) -> CanonicalTimeAllocation | None:
        self._validate_scope(
            curriculum_ref=curriculum_ref,
            subject_ref=subject_ref,
        )

        grade = self._validate_grade(
            grade
        )

        matches = tuple(
            allocation
            for allocation in self._time_allocations
            if (
                allocation.curriculum_ref
                == curriculum_ref
                and allocation.subject_ref
                == subject_ref
                and allocation.grade
                == grade
                and allocation.status
                == "VERIFIED"
            )
        )

        if not matches:
            return None

        if len(matches) > 1:
            raise ValueError(
                "multiple VERIFIED time allocations "
                "for the same curriculum/subject/grade"
            )

        return matches[0]

    def _validate_scope(
        self,
        *,
        curriculum_ref: str,
        subject_ref: str,
    ) -> None:
        self._require_supported_curriculum(
            curriculum_ref
        )

        subject_ref = self._required_text(
            subject_ref,
            "subject_ref",
        )

        if (
            subject_ref
            not in self._subject_refs
        ):
            raise LookupError(
                "unsupported subject_ref: "
                f"{subject_ref}"
            )

    def _require_supported_curriculum(
        self,
        curriculum_ref: str,
    ) -> str:
        curriculum_ref = self._required_text(
            curriculum_ref,
            "curriculum_ref",
        )

        if (
            curriculum_ref
            not in self._curriculum_refs
        ):
            raise LookupError(
                "unsupported curriculum_ref: "
                f"{curriculum_ref}"
            )

        return curriculum_ref

    @staticmethod
    def _validate_grade(
        grade: int,
    ) -> int:
        if (
            isinstance(grade, bool)
            or not isinstance(grade, int)
        ):
            raise TypeError(
                "grade must be an integer"
            )

        if grade <= 0:
            raise ValueError(
                "grade must be greater than 0"
            )

        return grade

    @classmethod
    def _normalize_refs(
        cls,
        values: tuple[str, ...],
        field_name: str,
    ) -> tuple[str, ...]:
        if not isinstance(
            values,
            tuple,
        ):
            raise TypeError(
                f"{field_name} must be a tuple"
            )

        normalized = []

        for value in values:
            value = cls._required_text(
                value,
                field_name,
            )

            if value not in normalized:
                normalized.append(
                    value
                )

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return tuple(
            normalized
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
