from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataTypeStatus(str, Enum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    ACCEPTED = "ACCEPTED"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class DataTypePassport:
    data_type_id: str
    name: str
    family: str
    description: str

    status: DataTypeStatus = DataTypeStatus.DRAFT

    required_fields: tuple[str, ...] = ()
    extensible_fields: tuple[str, ...] = ()

    supported_capabilities: tuple[str, ...] = ()
    applicable_rules: tuple[str, ...] = ()
    allowed_outputs: tuple[str, ...] = ()

    version_policy: str = "SIMPLE"
    update_policy: str = "CONTROLLED"
    retention_policy: str = "ACTIVE_FIRST"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )