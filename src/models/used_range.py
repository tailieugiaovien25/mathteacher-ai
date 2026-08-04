from dataclasses import dataclass


@dataclass
class UsedRange:
    """Vùng dữ liệu thực của Worksheet."""

    first_row: int
    last_row: int
    first_column: int
    last_column: int