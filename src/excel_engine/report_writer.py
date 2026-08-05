import json
from pathlib import Path
from typing import Any


class WorkbookReportWriter:
    """Xuất báo cáo cấu trúc Workbook ra tệp JSON."""

    def write(
        self,
        report_data: dict[str, Any],
        output_path: str,
    ) -> Path:
        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            mode="w",
            encoding="utf-8",
        ) as report_file:
            json.dump(
                report_data,
                report_file,
                ensure_ascii=False,
                indent=2,
            )

        return path