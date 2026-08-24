from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


class PPCTTemplateWorkbookAdapter:
    """
    Generate the standard MathTeacher-AI PPCT Template V1.

    Columns:
    - subject/grade
    - optional sub-subject
    - period
    - lesson name
    """

    def build(self) -> bytes:
        workbook = Workbook()

        worksheet = workbook.active
        worksheet.title = "PPCT"

        headers = (
            "M\u00f4n/L\u1edbp",
            "Ph\u00e2n m\u00f4n",
            "Ti\u1ebft",
            "T\u00ean b\u00e0i h\u1ecdc",
        )

        worksheet.append(headers)

        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = "A1:D1"

        worksheet.column_dimensions["A"].width = 20
        worksheet.column_dimensions["B"].width = 24
        worksheet.column_dimensions["C"].width = 12
        worksheet.column_dimensions["D"].width = 55

        guide = workbook.create_sheet(
            "Huong_dan"
        )

        guide_rows = (
            (
                "Cot",
                "Y nghia",
                "Bat buoc",
            ),
            (
                "Mon/Lop",
                "Mon hoc va khoi/lop",
                "Co",
            ),
            (
                "Phan mon",
                "Phan mon, mach noi dung hoac thanh phan mon hoc",
                "Khong",
            ),
            (
                "Tiet",
                "So tiet PPCT",
                "Co",
            ),
            (
                "Ten bai hoc",
                "Ten bai/bai hoc/noi dung day hoc",
                "Co",
            ),
        )

        for row in guide_rows:
            guide.append(row)

        for cell in guide[1]:
            cell.font = Font(bold=True)

        guide.column_dimensions["A"].width = 22
        guide.column_dimensions["B"].width = 55
        guide.column_dimensions["C"].width = 15

        buffer = BytesIO()

        workbook.save(buffer)
        workbook.close()

        return buffer.getvalue()
