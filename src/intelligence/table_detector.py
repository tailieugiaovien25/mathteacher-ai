from typing import Any

from models.header_info import HeaderInfo
from models.table_info import TableInfo
from models.used_range import UsedRange


class TableDetector:
    """Phát hiện các khối dữ liệu liên tục trong Worksheet."""

    @staticmethod
    def _is_meaningful(value: Any) -> bool:
        if value is None:
            return False

        if isinstance(value, str):
            cleaned = value.strip()

            if not cleaned:
                return False

            if cleaned.startswith("#"):
                return False

            return True

        if isinstance(value, (int, float)) and value == 0:
            return False

        return True

    def detect(
        self,
        worksheet,
        used_range: UsedRange,
        header_info: HeaderInfo,
    ) -> list[TableInfo]:
        if header_info.row_index == 0:
            return []

        tables: list[TableInfo] = []
        current_start_row: int | None = None
        last_meaningful_row = 0

        for row_number in range(
            header_info.row_index + 1,
            used_range.last_row + 1,
        ):
            row_has_data = any(
                self._is_meaningful(
                    worksheet.cell(
                        row=row_number,
                        column=column_number,
                    ).value
                )
                for column_number in range(
                    used_range.first_column,
                    used_range.last_column + 1,
                )
            )

            if row_has_data:
                if current_start_row is None:
                    current_start_row = row_number

                last_meaningful_row = row_number

            elif current_start_row is not None:
                tables.append(
                    TableInfo(
                        first_row=current_start_row,
                        last_row=last_meaningful_row,
                        first_column=used_range.first_column,
                        last_column=used_range.last_column,
                    )
                )

                current_start_row = None

        if current_start_row is not None:
            tables.append(
                TableInfo(
                    first_row=current_start_row,
                    last_row=last_meaningful_row,
                    first_column=used_range.first_column,
                    last_column=used_range.last_column,
                )
            )

        return tables