from openpyxl.worksheet.worksheet import Worksheet

from models.used_range import UsedRange


class RangeDetector:
    """Xác định vùng dữ liệu thực của Worksheet."""

    def detect(
        self,
        worksheet: Worksheet,
        key_columns: tuple[str, ...] = ("F", "G", "H", "I", "L"),
    ) -> UsedRange:
        last_data_row = 0

        for row_number in range(worksheet.max_row, 0, -1):
            has_data = any(
                worksheet[f"{column}{row_number}"].value not in (None, "")
                for column in key_columns
            )

            if has_data:
                last_data_row = row_number
                break

        if last_data_row == 0:
            return UsedRange(
                first_row=0,
                last_row=0,
                first_column=0,
                last_column=0,
            )

        first_data_row = 1

        for row_number in range(1, last_data_row + 1):
            has_data = any(
                worksheet[f"{column}{row_number}"].value not in (None, "")
                for column in key_columns
            )

            if has_data:
                first_data_row = row_number
                break

        return UsedRange(
            first_row=first_data_row,
            last_row=last_data_row,
            first_column=1,
            last_column=worksheet.max_column,
        )