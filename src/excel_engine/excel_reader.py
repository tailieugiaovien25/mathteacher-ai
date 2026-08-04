from pathlib import Path
from typing import Any

from excel_engine.range_detector import RangeDetector
from excel_engine.workbook_reader import WorkbookReader
from excel_engine.worksheet_reader import WorksheetReader


class ExcelReader:
    """Điều phối việc đọc và phân tích Workbook Excel."""

    def __init__(self) -> None:
        self.workbook_reader = WorkbookReader()
        self.worksheet_reader = WorksheetReader()
        self.range_detector = RangeDetector()

    def read_workbook(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)
        workbook = self.workbook_reader.load(file_path)

        try:
            worksheets: list[dict[str, Any]] = []

            for worksheet in workbook.worksheets:
                worksheets.append(
                    self.worksheet_reader.get_info(worksheet)
                )

            return {
                "file_name": path.name,
                "sheet_count": len(worksheets),
                "worksheets": worksheets,
            }
        finally:
            self.workbook_reader.close(workbook)

    def get_used_range(
        self,
        file_path: str,
        sheet_name: str,
        key_columns: tuple[str, ...] = ("F", "G", "H", "I", "L"),
    ) -> dict[str, int | str]:
        workbook = self.workbook_reader.load(file_path)

        try:
            if sheet_name not in workbook.sheetnames:
                raise ValueError(
                    f"Không tìm thấy worksheet: {sheet_name}"
                )

            worksheet = workbook[sheet_name]
            used_range = self.range_detector.detect(
                worksheet,
                key_columns,
            )

            return {
                "sheet_name": sheet_name,
                "first_data_row": used_range.first_row,
                "last_data_row": used_range.last_row,
                "first_column": used_range.first_column,
                "last_column": used_range.last_column,
                "column_count": worksheet.max_column,
            }
        finally:
            self.workbook_reader.close(workbook)