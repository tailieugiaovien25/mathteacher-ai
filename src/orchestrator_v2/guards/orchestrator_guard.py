from src.orchestrator_v2.contracts import (
    DispatchResult,
    DispatchStatus,
    GuardIssue,
    GuardResult,
    GuardStatus,
    RecognitionResult,
    RecognitionStatus,
    ResolutionResult,
    ResolutionStatus,
    TaskPlan,
    TaskPlanStatus,
)


class OrchestratorGuard:

    def validate_recognition(
        self,
        result: RecognitionResult,
    ) -> GuardResult:

        issues = []

        if not (
            0.0 <= result.confidence <= 1.0
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_REC_INVALID_CONFIDENCE",
                    message=(
                        "Recognition confidence "
                        "phải thuộc khoảng [0, 1]."
                    ),
                    field="confidence",
                )
            )

        if (
            result.status
            == RecognitionStatus.RECOGNIZED
            and not result.data_type_id
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_REC_TYPE_REQUIRED",
                    message=(
                        "RecognitionResult ở trạng thái "
                        "RECOGNIZED phải có data_type_id."
                    ),
                    field="data_type_id",
                )
            )

        if (
            result.status
            == RecognitionStatus.AMBIGUOUS
            and not result.candidates
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_REC_CANDIDATE_REQUIRED",
                    message=(
                        "RecognitionResult ở trạng thái "
                        "AMBIGUOUS phải có ít nhất "
                        "một candidate."
                    ),
                    field="candidates",
                )
            )

        for candidate in result.candidates:
            if not (
                0.0 <= candidate.confidence <= 1.0
            ):
                issues.append(
                    GuardIssue(
                        code=(
                            "ORCH_REC_CANDIDATE_"
                            "INVALID_CONFIDENCE"
                        ),
                        message=(
                            "Candidate confidence "
                            "phải thuộc khoảng [0, 1]."
                        ),
                        field="candidates",
                    )
                )

        return self._build_result(
            issues
        )

    def validate_resolution(
        self,
        result: ResolutionResult,
    ) -> GuardResult:

        issues = []

        if not (
            0.0 <= result.confidence <= 1.0
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_RES_INVALID_CONFIDENCE",
                    message=(
                        "Resolution confidence "
                        "phải thuộc khoảng [0, 1]."
                    ),
                    field="confidence",
                )
            )

        if not result.data_type_id:
            issues.append(
                GuardIssue(
                    code="ORCH_RES_TYPE_REQUIRED",
                    message=(
                        "ResolutionResult phải có "
                        "data_type_id."
                    ),
                    field="data_type_id",
                )
            )

        if (
            result.status
            == ResolutionStatus.RESOLVED
            and not result.resolved_id
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_RES_ID_REQUIRED",
                    message=(
                        "ResolutionResult ở trạng thái "
                        "RESOLVED phải có resolved_id."
                    ),
                    field="resolved_id",
                )
            )

        if (
            result.status
            == ResolutionStatus.UNRESOLVED
            and result.resolved_id is not None
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_RES_ID_FORBIDDEN",
                    message=(
                        "ResolutionResult ở trạng thái "
                        "UNRESOLVED không được có "
                        "resolved_id."
                    ),
                    field="resolved_id",
                )
            )

        if (
            result.status
            == ResolutionStatus.AMBIGUOUS
            and not result.candidates
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_RES_CANDIDATE_REQUIRED",
                    message=(
                        "ResolutionResult ở trạng thái "
                        "AMBIGUOUS phải có ít nhất "
                        "một candidate."
                    ),
                    field="candidates",
                )
            )

        for candidate in result.candidates:
            if not (
                0.0 <= candidate.confidence <= 1.0
            ):
                issues.append(
                    GuardIssue(
                        code=(
                            "ORCH_RES_CANDIDATE_"
                            "INVALID_CONFIDENCE"
                        ),
                        message=(
                            "Resolution candidate confidence "
                            "phải thuộc khoảng [0, 1]."
                        ),
                        field="candidates",
                    )
                )

        return self._build_result(
            issues
        )

    def validate_task_plan(
        self,
        plan: TaskPlan,
    ) -> GuardResult:

        issues = []

        if (
            plan.status
            == TaskPlanStatus.READY
            and not plan.tasks
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_PLAN_TASK_REQUIRED",
                    message=(
                        "TaskPlan ở trạng thái READY "
                        "phải có ít nhất một task."
                    ),
                    field="tasks",
                )
            )

        task_ids = [
            task.task_id
            for task in plan.tasks
        ]

        if len(task_ids) != len(set(task_ids)):
            issues.append(
                GuardIssue(
                    code="ORCH_PLAN_DUPLICATE_TASK_ID",
                    message=(
                        "task_id trong cùng TaskPlan "
                        "phải là duy nhất."
                    ),
                    field="tasks",
                )
            )

        known_task_ids = set(task_ids)

        for task in plan.tasks:

            if not (
                isinstance(task.task_id, str)
                and task.task_id.strip()
            ):
                issues.append(
                    GuardIssue(
                        code="ORCH_TASK_ID_REQUIRED",
                        message=(
                            "Task phải có task_id hợp lệ."
                        ),
                        field="task_id",
                    )
                )

            if not (
                isinstance(task.capability, str)
                and task.capability.strip()
            ):
                issues.append(
                    GuardIssue(
                        code=(
                            "ORCH_TASK_CAPABILITY_REQUIRED"
                        ),
                        message=(
                            "Task phải có capability hợp lệ."
                        ),
                        field="capability",
                    )
                )

            if task.task_id in task.depends_on:
                issues.append(
                    GuardIssue(
                        code=(
                            "ORCH_TASK_SELF_DEPENDENCY"
                        ),
                        message=(
                            "Task không được phụ thuộc "
                            "vào chính nó."
                        ),
                        field="depends_on",
                    )
                )

            for dependency_id in task.depends_on:

                if dependency_id not in known_task_ids:
                    issues.append(
                        GuardIssue(
                            code=(
                                "ORCH_TASK_UNKNOWN_"
                                "DEPENDENCY"
                            ),
                            message=(
                                "depends_on phải tham chiếu "
                                "tới task tồn tại trong "
                                "cùng TaskPlan."
                            ),
                            field="depends_on",
                        )
                    )

        if self._has_dependency_cycle(
            plan
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_TASK_DEPENDENCY_CYCLE",
                    message=(
                        "Phát hiện vòng phụ thuộc "
                        "giữa các task."
                    ),
                    field="depends_on",
                )
            )

        return self._build_result(
            issues
        )

    def validate_dispatch(
        self,
        result: DispatchResult,
    ) -> GuardResult:

        issues = []

        # G12:
        # SUCCESS phải có processor_id
        if (
            result.status
            == DispatchStatus.SUCCESS
            and not result.processor_id
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_DISPATCH_PROCESSOR_REQUIRED",
                    message=(
                        "DispatchResult ở trạng thái "
                        "SUCCESS phải có processor_id."
                    ),
                    field="processor_id",
                )
            )

        # G13:
        # NO_PROCESSOR_AVAILABLE
        # không được có processor_id
        if (
            result.status
            == DispatchStatus.NO_PROCESSOR_AVAILABLE
            and result.processor_id is not None
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_DISPATCH_PROCESSOR_FORBIDDEN",
                    message=(
                        "NO_PROCESSOR_AVAILABLE "
                        "không được có processor_id."
                    ),
                    field="processor_id",
                )
            )

        # FAILED nên có thông tin lỗi rõ ràng
        if (
            result.status
            == DispatchStatus.FAILED
            and not result.error
        ):
            issues.append(
                GuardIssue(
                    code="ORCH_DISPATCH_ERROR_REQUIRED",
                    message=(
                        "DispatchResult ở trạng thái "
                        "FAILED phải có thông tin lỗi."
                    ),
                    field="error",
                )
            )

        return self._build_result(
            issues
        )

    @staticmethod
    def _has_dependency_cycle(
        plan: TaskPlan,
    ) -> bool:

        graph = {
            task.task_id: tuple(
                task.depends_on
            )
            for task in plan.tasks
        }

        visiting = set()
        visited = set()

        def visit(
            task_id: str,
        ) -> bool:

            if task_id in visiting:
                return True

            if task_id in visited:
                return False

            visiting.add(
                task_id
            )

            for dependency_id in graph.get(
                task_id,
                (),
            ):
                if dependency_id not in graph:
                    continue

                if visit(
                    dependency_id
                ):
                    return True

            visiting.remove(
                task_id
            )

            visited.add(
                task_id
            )

            return False

        for task_id in graph:
            if visit(
                task_id
            ):
                return True

        return False

    @staticmethod
    def _build_result(
        issues,
    ) -> GuardResult:

        if issues:
            return GuardResult(
                is_valid=False,
                status=GuardStatus.BLOCKED,
                issues=tuple(issues),
            )

        return GuardResult(
            is_valid=True,
            status=GuardStatus.PASS,
        )