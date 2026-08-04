from dataclasses import dataclass
from typing import Any


@dataclass
class CellInfo:
    """Thông tin của một ô Excel."""

    address: str
    value: Any