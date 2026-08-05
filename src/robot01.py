from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from excel_engine.excel_reader import ExcelReader
from excel_engine.report_writer import WorkbookReportWriter
from robots.base_robot import BaseRobot


class Robot01(BaseRobot):
    """Điều phối quy trình đọc và phân tích Workbook Excel."""

    def __init__(
        self,
        excel_file: str,
        report_file: str,
        target_sheet: str = "LuuBG",
    ) -> None:
        super().__init__(
            name="Robot 01 - Excel Reader",
            version="0.1.4",
        )

        self.excel_file = excel_file
        self.report_file = report_file
        self.target_sheet = target_sheet

        self.excel_reader = ExcelReader()
        self.report_writer = WorkbookReportWriter()

    def run(self) -> None:
        workbook_info = self.excel_reader.read_workbook(
            self.excel_file
        )

        used_range = self.excel_reader.get_used_range(
            self.excel_file,
            self.target_sheet,
        )

        report_data = self._build_report(
            workbook_info,
            used_range,
        )

        report_path = self.report_writer.write(
            report_data,
            self.report_file,
        )

        self._print_result(
            workbook_info,
            used_range,
            report_path,
        )

    def _build_report(
        self,
        workbook_info: dict[str, Any],
        used_range: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "project": "MathTeacher AI",
            "robot": self.name,
            "version": self.version,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "workbook": {
                **workbook_info,
                "luubg_used_range": used_range,
            },
        }

    def _print_result(
        self,
        workbook_info: dict[str, Any],
        used_range: dict[str, Any],
        report_path: Path,
    ) -> None:
        print(f"\nWorkbook: {workbook_info['file_name']}")
        print(f"Số worksheet: {workbook_info['sheet_count']}")

        print("\nCấu trúc worksheet:")

        for index, worksheet in enumerate(
            workbook_info["worksheets"],
            start=1,
        ):
            print(
                f"{index:>2}. {worksheet['name']} "
                f"- Rows: {worksheet['row_count']} "
                f"- Columns: {worksheet['column_count']}"
            )

        print(f"\nVùng dữ liệu thật của {self.target_sheet}:")
        print(
            f"Dòng đầu có dữ liệu: "
            f"{used_range['first_data_row']}"
        )
        print(
            f"Dòng cuối có dữ liệu: "
            f"{used_range['last_data_row']}"
        )
        print(
            f"Cột đầu: "
            f"{used_range['first_column']}"
        )
        print(
            f"Cột cuối: "
            f"{used_range['last_column']}"
        )

        print("\nĐã tạo báo cáo:")
        print(report_path)