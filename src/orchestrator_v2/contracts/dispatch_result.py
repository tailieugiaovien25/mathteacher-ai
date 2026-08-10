from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DispatchStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NO_PROCESSOR_AVAILABLE = (
        "NO_PROCESSOR_AVAILABLE"
    )
    VALIDATION_FAILED = (
        "VALIDATION_FAILED"
    )


@dataclass(frozen=True)
class DispatchResult:
    task_id: str
    processor_id: str | None
    status: DispatchStatus

    result: Any = None
    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )