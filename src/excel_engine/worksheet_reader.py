from openpyxl.worksheet.worksheet import Worksheet


class WorksheetReader:
    """Đọc thông tin của một Worksheet."""

    def get_info(self, worksheet: Worksheet) -> dict:
        return {
            "name": worksheet.title,
            "row_count": worksheet.max_row,
            "column_count": worksheet.max_column,
        }

    def get_cell_value(
        self,
        worksheet: Worksheet,
        cell: str,
    ):
        """Đọc giá trị của một ô."""
        return worksheet[cell].value

    def get_row_values(
        self,
        worksheet: Worksheet,
        row: int,
    ) -> list:
        """Đọc toàn bộ giá trị của một dòng."""
        return [cell.value for cell in worksheet[row]]