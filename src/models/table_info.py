from dataclasses import dataclass


@dataclass
class TableInfo:
    """Phạm vi của một bảng dữ liệu."""

    first_row: int
    last_row: int
    first_column: int
    last_column: int