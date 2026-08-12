from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class LearningActivity:
    activity_id: str
    title: str
    activity_type: str
    order: int
    objective_refs: tuple[str, ...] = ()
    resource_refs: tuple[str, ...] = ()
    content: str | None = None
    organization: str | None = None
    expected_products: tuple[str, ...] = ()
    assessment: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
