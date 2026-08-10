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
        "V2-ORCH-003B-4A - "
        "TASK PLAN GUARD TEST"
    )
    print("=" * 72)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # Valid plan
    # --------------------------------------------------------

    task_1 = Task(
        task_id="TASK-001",
        capability="RESOLVE_MAPPING",
    )

    task_2 = Task(
        task_id="TASK-002",
        capability="ASSESSMENT_GENERATE",
        depends_on=("TASK-001",),
    )

    valid_plan = TaskPlan(
        plan_id="PLAN-001",
        context="ASSESSMENT",
        tasks=(task_1, task_2),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        valid_plan
    )

    assert result.is_valid

    print(
        "Valid task plan: PASS"
    )

    # --------------------------------------------------------
    # G6 - task_id rỗng
    # --------------------------------------------------------

    bad_task_id = TaskPlan(
        plan_id="PLAN-002",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="",
                capability="MAP",
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        bad_task_id
    ).is_valid

    print(
        "G6 empty task_id blocked: PASS"
    )

    # --------------------------------------------------------
    # G6 - capability rỗng
    # --------------------------------------------------------

    bad_capability = TaskPlan(
        plan_id="PLAN-003",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-001",
                capability="",
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        bad_capability
    ).is_valid

    print(
        "G6 empty capability blocked: PASS"
    )

    # --------------------------------------------------------
    # G7 - tự phụ thuộc
    # --------------------------------------------------------

    self_dependency = TaskPlan(
        plan_id="PLAN-004",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-001",
                capability="MAP",
                depends_on=("TASK-001",),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        self_dependency
    ).is_valid

    print(
        "G7 self dependency blocked: PASS"
    )

    # --------------------------------------------------------
    # G8 - dependency không tồn tại
    # --------------------------------------------------------

    unknown_dependency = TaskPlan(
        plan_id="PLAN-005",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-001",
                capability="GENERATE",
                depends_on=("TASK-999",),
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        unknown_dependency
    ).is_valid

    print(
        "G8 unknown dependency blocked: PASS"
    )

    # --------------------------------------------------------
    # G9 - READY nhưng không có task
    # --------------------------------------------------------

    empty_ready_plan = TaskPlan(
        plan_id="PLAN-006",
        context="ASSESSMENT",
        tasks=(),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        empty_ready_plan
    ).is_valid

    print(
        "G9 empty READY plan blocked: PASS"
    )

    # --------------------------------------------------------
    # G10 - task_id trùng nhau
    # --------------------------------------------------------

    duplicate_ids = TaskPlan(
        plan_id="PLAN-007",
        context="ASSESSMENT",
        tasks=(
            Task(
                task_id="TASK-001",
                capability="MAP",
            ),
            Task(
                task_id="TASK-001",
                capability="GENERATE",
            ),
        ),
        status=TaskPlanStatus.READY,
    )

    assert not guard.validate_task_plan(
        duplicate_ids
    ).is_valid

    print(
        "G10 duplicate task_id blocked: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - TASK PLAN GUARD G6-G10 VERIFIED"
    )


if __name__ == "__main__":
    main()