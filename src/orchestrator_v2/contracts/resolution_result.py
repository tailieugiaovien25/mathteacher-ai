from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ResolutionCandidate:
    data_type_id: str
    resolved_id: str
    confidence: float


@dataclass(frozen=True)
class ResolutionResult:
    data_type_id: str
    resolved_id: str | None
    confidence: float
    status: ResolutionStatus

    candidates: tuple[
        ResolutionCandidate,
        ...
    ] = ()

    metadata: dict[str, Any] = field(
        default_factory=dict
    )