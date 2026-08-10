from src.orchestrator_v2.contracts import (
    Task,
    TaskPlan,
    TaskPlanStatus,
)

from src.orchestrator_v2.guards import (
    OrchestratorGuard,
)


def main():

    print("=" * 72)
    print(
        "V2-ORCH-003B-4B - "
        "TASK DEPENDENCY CYCLE TEST"
    )
    print("=" * 72)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # 1. Chuỗi hợp lệ:
    # A <- B <- C
    # --------------------------------------------------------

    valid_plan = TaskPlan(
        plan_id="PLAN-VALID",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-A",
                capability="CAP-A",
            ),
            Task(
                task_id="TASK-B",
                capability="CAP-B",
                depends_on=("TASK-A",),
            ),
            Task(
                task_id="TASK-C",
                capability="CAP-C",
                depends_on=("TASK-B",),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        valid_plan
    )

    assert result.is_valid

    print(
        "Valid dependency chain: PASS"
    )

    # --------------------------------------------------------
    # 2. Cycle:
    # A -> B -> C -> A
    # --------------------------------------------------------

    cycle_plan = TaskPlan(
        plan_id="PLAN-CYCLE",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-A",
                capability="CAP-A",
                depends_on=("TASK-B",),
            ),
            Task(
                task_id="TASK-B",
                capability="CAP-B",
                depends_on=("TASK-C",),
            ),
            Task(
                task_id="TASK-C",
                capability="CAP-C",
                depends_on=("TASK-A",),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        cycle_plan
    )

    assert not result.is_valid

    assert any(
        issue.code
        == "ORCH_TASK_DEPENDENCY_CYCLE"
        for issue in result.issues
    )

    print(
        "G11 three-task cycle blocked: PASS"
    )

    # --------------------------------------------------------
    # 3. Cycle hai task:
    # A <-> B
    # --------------------------------------------------------

    two_task_cycle = TaskPlan(
        plan_id="PLAN-CYCLE-2",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-A",
                capability="CAP-A",
                depends_on=("TASK-B",),
            ),
            Task(
                task_id="TASK-B",
                capability="CAP-B",
                depends_on=("TASK-A",),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        two_task_cycle
    )

    assert not result.is_valid

    print(
        "G11 two-task cycle blocked: PASS"
    )

    # --------------------------------------------------------
    # 4. Nhiều nhánh nhưng không cycle
    # --------------------------------------------------------

    branching_plan = TaskPlan(
        plan_id="PLAN-BRANCH",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-A",
                capability="CAP-A",
            ),
            Task(
                task_id="TASK-B",
                capability="CAP-B",
                depends_on=("TASK-A",),
            ),
            Task(
                task_id="TASK-C",
                capability="CAP-C",
                depends_on=("TASK-A",),
            ),
            Task(
                task_id="TASK-D",
                capability="CAP-D",
                depends_on=(
                    "TASK-B",
                    "TASK-C",
                ),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        branching_plan
    )

    assert result.is_valid

    print(
        "Valid branching dependencies: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - TASK DEPENDENCY CYCLE VERIFIED"
    )


if __name__ == "__main__":
    main()