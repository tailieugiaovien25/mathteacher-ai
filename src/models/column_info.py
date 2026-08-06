from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """Thông tin một cột dữ liệu."""

    column_letter: str
    column_index: int
    header: str
    data_type: str