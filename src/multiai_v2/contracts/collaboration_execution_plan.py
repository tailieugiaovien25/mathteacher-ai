from __future__ import annotations

from dataclasses import dataclass

from src.multiai_v2.contracts.execution_plan import (
    ExecutionPlan,
)


@dataclass(frozen=True)
class CollaborationExecutionPlan:
    """
    Provider-neutral execution assignment for one collaboration role.

    CollaborationExecutionPlan links one collaboration role to the
    ExecutionPlan produced for that role.

    It MUST NOT:
    - select or route providers;
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions;
    - register providers.
    """

    collaboration_id: str
    role_id: str
    execution_plan: ExecutionPlan

    def __post_init__(self) -> None:
        collaboration_id = self.collaboration_id.strip()
        role_id = self.role_id.strip()

        if not collaboration_id:
            raise ValueError(
                "collaboration_id must not be empty"
            )

        if not role_id:
            raise ValueError(
                "role_id must not be empty"
            )

        if not isinstance(
            self.execution_plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "execution_plan must be ExecutionPlan"
            )

        object.__setattr__(
            self,
            "collaboration_id",
            collaboration_id,
        )
        object.__setattr__(
            self,
            "role_id",
            role_id,
        )