from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from typing import Any


class GuardStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class GuardIssue:
    code: str
    message: str

    field: str | None = None

    metadata: dict[str, Any] = dataclass_field(
        default_factory=dict
    )


@dataclass(frozen=True)
class GuardResult:
    is_valid: bool
    status: GuardStatus

    issues: tuple[
        GuardIssue,
        ...
    ] = ()

    metadata: dict[str, Any] = dataclass_field(
        default_factory=dict
    )