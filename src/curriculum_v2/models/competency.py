from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Competency:
    competency_id: str
    name: str
    competency_type: str

    description: str | None = None

    status: str = "ACTIVE"

    effective_from: str | None = None
    effective_to: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )