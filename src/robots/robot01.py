from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from excel_engine.excel_reader import ExcelReader
from excel_engine.report_writer import WorkbookReportWriter
from intelligence.excel_intelligence_engine import (
    ExcelIntelligenceEngine,
)
from robots.base_robot import BaseRobot


class Robot01(BaseRobot):
    """Đọc và phân tích thông minh cấu trúc Workbook Excel."""

    def __init__(
        self,
        excel_file: str,
        report_file: str,
        target_sheet: str = "LuuBG",
    ) -> None:
        super().__init__(
            name="Robot 01 - Excel Intelligence",
            version="0.2.0",
        )

        self.excel_file = excel_file
        self.report_file = report_file
        self.target_sheet = target_sheet

        self.excel_reader = ExcelReader()
        self.intelligence_engine = ExcelIntelligenceEngine()
        self.report_writer = WorkbookReportWriter()

    def run(self) -> None:
        """Chạy toàn bộ quy trình phân tích Excel."""
        self._print_progress(
            "Bước 1/4 - Đọc thông tin Workbook..."
        )
        start_time = perf_counter()

        workbook_info = self.excel_reader.read_workbook(
            self.excel_file
        )

        self._print_completed(start_time)

        self._print_progress(
            f"Bước 2/4 - Phân tích Worksheet "
            f"'{self.target_sheet}'..."
        )
        start_time = perf_counter()

        intelligence_result = self.intelligence_engine.analyze(
            self.excel_file,
            self.target_sheet,
        )

        self._print_completed(start_time)

        self._print_progress(
            "Bước 3/4 - Xây dựng dữ liệu báo cáo..."
        )
        start_time = perf_counter()

        report_data = self._build_report(
            workbook_info,
            intelligence_result,
        )

        self._print_completed(start_time)

        self._print_progress(
            "Bước 4/4 - Ghi báo cáo JSON..."
        )
        start_time = perf_counter()

        report_path = self.report_writer.write(
            report_data,
            self.report_file,
        )

        self._print_completed(start_time)

        self._print_result(
            workbook_info,
            intelligence_result,
            report_path,
        )

    def _build_report(
        self,
        workbook_info: dict[str, Any],
        intelligence_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Tạo cấu trúc báo cáo chuẩn của Robot 01."""
        return {
            "project": "MathTeacher AI",
            "robot": self.name,
            "version": self.version,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "workbook": workbook_info,
            "intelligence": intelligence_result,
        }

    @staticmethod
    def _print_progress(message: str) -> None:
        """Hiển thị bước Robot đang thực hiện."""
        print(f"\n{message}", flush=True)

    @staticmethod
    def _print_completed(start_time: float) -> None:
        """Hiển thị thời gian hoàn thành một bước."""
        elapsed_time = perf_counter() - start_time
        print(
            f"Đã hoàn thành trong {elapsed_time:.2f} giây.",
            flush=True,
        )

    def _print_result(
        self,
        workbook_info: dict[str, Any],
        intelligence_result: dict[str, Any],
        report_path: Path,
    ) -> None:
        """Hiển thị kết quả phân tích cuối cùng."""
        print(
            f"\nWorkbook: {workbook_info['file_name']}",
            flush=True,
        )
        print(
            f"Số worksheet: "
            f"{workbook_info['sheet_count']}",
            flush=True,
        )

        used_range = intelligence_result["used_range"]
        header = intelligence_result["header"]
        columns = intelligence_result["columns"]
        tables = intelligence_result["tables"]

        print(
            f"\nPhân tích Worksheet: "
            f"{self.target_sheet}",
            flush=True,
        )

        print(
            "Vùng dữ liệu: "
            f"dòng {used_range['first_row']}–"
            f"{used_range['last_row']}, "
            f"cột {used_range['first_column']}–"
            f"{used_range['last_column']}",
            flush=True,
        )

        print(
            "Hàng tiêu đề được phát hiện: "
            f"{header['row_index']}",
            flush=True,
        )

        print(
            f"Số cột được phân tích: {len(columns)}",
            flush=True,
        )
        print(
            f"Số bảng được phát hiện: {len(tables)}",
            flush=True,
        )

        print("\nDanh sách cột:", flush=True)

        if not columns:
            print(
                "- Chưa phát hiện được cột dữ liệu.",
                flush=True,
            )
        else:
            for column in columns:
                print(
                    f"- {column['column_letter']}: "
                    f"{column['header']} "
                    f"({column['data_type']})",
                    flush=True,
                )

        print("\nĐã tạo báo cáo:", flush=True)
        print(report_path, flush=True)