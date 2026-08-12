from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    rule_type: str
    applies_to_data_type: str
    context: str
    priority: int = 100
    status: RuleStatus = RuleStatus.ACTIVE

    condition: dict[str, Any] = field(
        default_factory=dict
    )

    action: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )