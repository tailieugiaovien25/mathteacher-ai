from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class TeachingResource:
    resource_id: str
    name: str
    resource_type: str
    description: str | None = None
    source_ref: str | None = None
    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
