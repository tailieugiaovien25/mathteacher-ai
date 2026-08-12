from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CurriculumScope:
    """Canonical curriculum references selected for a planning scope."""

    curriculum_ref: str
    grade: int

    curriculum_node_ids: tuple[str, ...] = ()
    canonical_requirement_ids: tuple[str, ...] = ()

    metadata: dict[str, Any] = field(default_factory=dict)
