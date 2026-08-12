from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EducationalPlanAllocationConstraint:
    """
    Immutable allocation constraint for an educational plan.

    The contract describes one required allocation total.

    It MUST NOT:
    - allocate periods;
    - validate plans;
    - build plans;
    - execute providers;
    - route requests;
    - render or export products.
    """

    allocation_key: str
    total_periods: int

    def __post_init__(self) -> None:
        allocation_key = self.allocation_key.strip()

        if not allocation_key:
            raise ValueError(
                "allocation_key must not be empty"
            )

        if not isinstance(self.total_periods, int):
            raise TypeError(
                "total_periods must be int"
            )

        if self.total_periods <= 0:
            raise ValueError(
                "total_periods must be positive"
            )

        object.__setattr__(
            self,
            "allocation_key",
            allocation_key,
        )