from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskPlanStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Task:
    task_id: str
    capability: str

    input_refs: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class TaskPlan:
    plan_id: str
    context: str
    tasks: tuple[Task, ...]

    status: TaskPlanStatus = TaskPlanStatus.DRAFT

    metadata: dict[str, Any] = field(
        default_factory=dict
    )