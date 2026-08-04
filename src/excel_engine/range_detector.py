from typing import Any

from openpyxl.worksheet.worksheet import Worksheet

from models.used_range import UsedRange


class RangeDetector:
    """Xác định vùng dữ liệu có ý nghĩa của Worksheet."""

    KEY_COLUMN_OFFSETS = {
        "F": 0,
        "G": 1,
        "H": 2,
        "I": 3,
        "L": 6,
    }

    @staticmethod
    def _is_meaningful(value: Any) -> bool:
        """Loại bỏ ô trống, số 0 và lỗi công thức Excel."""
        if value is None:
            return False

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return False

            if cleaned_value.startswith("#"):
                return False

            return True

        if isinstance(value, (int, float)) and value == 0:
            return False

        return True

    def detect(
        self,
        worksheet: Worksheet,
        key_columns: tuple[str, ...] = ("F", "G", "H", "I", "L"),
    ) -> UsedRange:
        selected_offsets = [
            self.KEY_COLUMN_OFFSETS[column]
            for column in key_columns
            if column in self.KEY_COLUMN_OFFSETS
        ]

        first_data_row = 0
        last_data_row = 0

        # Đọc tuần tự một lần để tránh truy cập ngẫu nhiên 65.536 dòng.
        for row_number, row_values in enumerate(
            worksheet.iter_rows(
                min_row=1,
                max_row=worksheet.max_row,
                min_col=6,   # Cột F
                max_col=12,  # Cột L
                values_only=True,
            ),
            start=1,
        ):
            has_meaningful_data = any(
                self._is_meaningful(row_values[offset])
                for offset in selected_offsets
            )

            if has_meaningful_data:
                if first_data_row == 0:
                    first_data_row = row_number

                last_data_row = row_number

        if last_data_row == 0:
            return UsedRange(
                first_row=0,
                last_row=0,
                first_column=0,
                last_column=0,
            )

        return UsedRange(
            first_row=first_data_row,
            last_row=last_data_row,
            first_column=6,
            last_column=12,
        )