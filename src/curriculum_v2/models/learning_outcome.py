from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LearningOutcome:
    learning_outcome_id: str
    curriculum_ref: str

    code: str
    statement: str
    outcome_type: str

    status: str = "ACTIVE"

    effective_from: str | None = None
    effective_to: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )