from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class LessonObjective:
    objective_id: str
    objective_type: str
    statement: str
    source_requirement_refs: tuple[str, ...] = ()
    competency_refs: tuple[str, ...] = ()
    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
