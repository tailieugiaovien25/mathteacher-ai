from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MappingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class Mapping:
    mapping_id: str

    source_data_type: str
    source_id: str

    target_data_type: str
    target_id: str

    mapping_type: str

    status: MappingStatus = MappingStatus.ACTIVE
    priority: int = 100

    metadata: dict[str, Any] = field(
        default_factory=dict
    )