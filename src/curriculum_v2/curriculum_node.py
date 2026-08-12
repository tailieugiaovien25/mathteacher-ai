from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CurriculumNode:
    curriculum_node_id: str
    curriculum_ref: str

    code: str
    name: str
    node_type: str

    parent_id: str | None = None
    sequence: int = 0

    status: str = "ACTIVE"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )