from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.allocation_constraint import (
    EducationalPlanAllocationConstraint,
)


@dataclass(frozen=True)
class EducationalPlanAllocationProfile:
    """
    Immutable collection of allocation constraints for an educational plan.

    The profile groups allocation constraints under one stable identity.

    It MUST NOT:
    - allocate periods;
    - validate plans;
    - build plans;
    - execute providers;
    - route requests;
    - render or export products.
    """

    profile_id: str
    constraints: tuple[
        EducationalPlanAllocationConstraint,
        ...,
    ]

    def __post_init__(self) -> None:
        profile_id = self.profile_id.strip()

        if not profile_id:
            raise ValueError(
                "profile_id must not be empty"
            )

        if not isinstance(self.constraints, tuple):
            raise TypeError(
                "constraints must be tuple"
            )

        if not self.constraints:
            raise ValueError(
                "constraints must not be empty"
            )

        if not all(
            isinstance(
                constraint,
                EducationalPlanAllocationConstraint,
            )
            for constraint in self.constraints
        ):
            raise TypeError(
                "every constraint must be "
                "EducationalPlanAllocationConstraint"
            )

        allocation_keys = tuple(
            constraint.allocation_key
            for constraint in self.constraints
        )

        if len(allocation_keys) != len(set(allocation_keys)):
            raise ValueError(
                "allocation_key must be unique within profile"
            )

        object.__setattr__(
            self,
            "profile_id",
            profile_id,
        )