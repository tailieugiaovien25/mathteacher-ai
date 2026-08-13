from pathlib import Path

from openpyxl import load_workbook


WORKBOOK = Path(
    r"data\input\LBG-TUYEN_chuan_VBA_macro.xlsm"
)

SHEET_NAME = "TKB-Q"


print("=" * 72)
print("M5-XLS-DIAG - TKB-Q DATA VALIDATION MAP")
print("=" * 72)
print("Chế độ: READ ONLY")
print()

wb = load_workbook(
    WORKBOOK,
    data_only=False,
    read_only=False,
    keep_vba=True,
    keep_links=True,
)

try:
    ws = wb[SHEET_NAME]

    dvs = ws.data_validations.dataValidation

    print(
        "Data Validation records:",
        len(dvs),
    )

    print()

    for index, dv in enumerate(
        dvs,
        start=1,
    ):
        print("-" * 72)
        print(f"DV #{index}")
        print("Type      :", dv.type)
        print("Formula1  :", dv.formula1)
        print("Formula2  :", dv.formula2)
        print("AllowBlank:", dv.allow_blank)
        print("Ranges    :")

        for cell_range in dv.ranges.ranges:
            print(
                "   ",
                str(cell_range),
            )

    print()
    print("=" * 72)
    print("KẾT QUẢ: DATA VALIDATION MAP COMPLETE")
    print("=" * 72)
    print("Workbook KHÔNG bị thay đổi.")

finally:
    wb.close()