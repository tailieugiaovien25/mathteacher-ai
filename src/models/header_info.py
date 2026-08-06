from dataclasses import dataclass


@dataclass
class HeaderInfo:
    """Thông tin hàng tiêu đề của Worksheet."""

    row_index: int
    headers: list[str]