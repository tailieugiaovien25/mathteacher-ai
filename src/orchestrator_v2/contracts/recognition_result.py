from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RecognitionStatus(str, Enum):
    RECOGNIZED = "RECOGNIZED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class RecognitionCandidate:
    data_type_id: str
    confidence: float


@dataclass(frozen=True)
class RecognitionResult:
    data_type_id: str | None
    confidence: float
    status: RecognitionStatus

    candidates: tuple[
        RecognitionCandidate,
        ...
    ] = ()

    metadata: dict[str, Any] = field(
        default_factory=dict
    )