from __future__ import annotations

from src.multiai_v2.contracts import (
    CapabilityRequest,
    CollaborationExecutionPlan,
    CollaborationPlan,
    ProviderHealth,
)
from src.multiai_v2.execution_planner import (
    ExecutionPlanner,
)


class CollaborationPlanner:
    """
    Creates execution assignments for a Multi-AI collaboration.

    CollaborationPlanner maps each collaboration role to its
    CapabilityRequest and delegates provider planning to
    ExecutionPlanner.

    It MUST NOT:
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions;
    - register providers.
    """

    def __init__(
        self,
        execution_planner: ExecutionPlanner,
    ) -> None:
        self._execution_planner = execution_planner

    def plan(
        self,
        collaboration_plan: CollaborationPlan,
        role_requests: dict[str, CapabilityRequest],
        provider_health: dict[str, ProviderHealth],
    ) -> tuple[CollaborationExecutionPlan, ...] | None:
        assignments = []

        for role in collaboration_plan.roles:
            request = role_requests.get(role.role_id)

            if request is None:
                raise ValueError(
                    f"missing request for role: {role.role_id}"
                )

            if request.capability_id != role.capability_id:
                raise ValueError(
                    "request capability_id must match role"
                )

            if (
                request.capability_version
                != role.capability_version
            ):
                raise ValueError(
                    "request capability_version must match role"
                )

            execution_plan = self._execution_planner.plan(
                request=request,
                provider_health=provider_health,
            )

            if execution_plan is None:
                return None

            assignments.append(
                CollaborationExecutionPlan(
                    collaboration_id=(
                        collaboration_plan.collaboration_id
                    ),
                    role_id=role.role_id,
                    execution_plan=execution_plan,
                )
            )

        return tuple(assignments)