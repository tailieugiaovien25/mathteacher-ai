from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecognitionEvidence:
    provider_id: str
    candidate_data_type_id: str

    confidence: float
    authority: float

    evidence: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )