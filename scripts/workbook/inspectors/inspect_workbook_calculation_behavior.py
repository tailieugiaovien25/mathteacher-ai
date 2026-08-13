import re
import zipfile
from pathlib import Path

from openpyxl import load_workbook


WORKBOOK = Path(
    r"data\working\LBG-TUYEN_CLEANUP_SAFE_WORKING.xlsm"
)

VBA_SOURCE = Path(
    r"output\reports\vba\workbook_vba_source_utf8.txt"
)


print("=" * 76)
print(
    "M5-XLS-DIAG - "
    "WORKBOOK CALCULATION / RECALC INVENTORY"
)
print("=" * 76)

print("Chế độ: READ ONLY")
print("Workbook KHÔNG bị thay đổi.")
print()


# ============================================================
# 1. OPENPYXL CALCULATION SETTINGS
# ============================================================

wb = load_workbook(
    WORKBOOK,
    data_only=False,
    read_only=False,
    keep_vba=True,
    keep_links=True,
)

try:
    calc = wb.calculation

    print("CALCULATION SETTINGS")
    print("-" * 76)

    print(
        "calcMode:",
        getattr(
            calc,
            "calcMode",
            None,
        ),
    )

    print(
        "fullCalcOnLoad:",
        getattr(
            calc,
            "fullCalcOnLoad",
            None,
        ),
    )

    print(
        "forceFullCalc:",
        getattr(
            calc,
            "forceFullCalc",
            None,
        ),
    )

    print(
        "calcOnSave:",
        getattr(
            calc,
            "calcOnSave",
            None,
        ),
    )

    print(
        "calcId:",
        getattr(
            calc,
            "calcId",
            None,
        ),
    )

finally:
    wb.close()


# ============================================================
# 2. RAW WORKBOOK XML
# ============================================================

print()
print("RAW workbook.xml calcPr")
print("-" * 76)

with zipfile.ZipFile(
    WORKBOOK,
    "r",
) as z:
    text = z.read(
        "xl/workbook.xml"
    ).decode(
        "utf-8",
        errors="replace",
    )

    match = re.search(
        r"<calcPr\b[^>]*/?>",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        print(
            match.group(0)
        )
    else:
        print(
            "Không tìm thấy calcPr."
        )


# ============================================================
# 3. VBA RECALC / SAVE / SCREEN ACTIVITY
# ============================================================

print()
print("VBA KEYWORD INVENTORY")
print("-" * 76)

if not VBA_SOURCE.exists():
    raise FileNotFoundError(
        f"Không tìm thấy VBA source: "
        f"{VBA_SOURCE}"
    )

vba = VBA_SOURCE.read_text(
    encoding="utf-8",
    errors="replace",
)

keywords = [
    "Calculate",
    "CalculateFull",
    "CalculateFullRebuild",
    "Application.Calculation",
    "ScreenUpdating",
    "EnableEvents",
    "DisplayAlerts",
    "DoEvents",
    ".Save",
    "SaveAs",
]

for keyword in keywords:
    count = len(
        re.findall(
            re.escape(keyword),
            vba,
            flags=re.IGNORECASE,
        )
    )

    print(
        f"{keyword}: {count}"
    )


print()
print("=" * 76)
print(
    "KẾT QUẢ: "
    "CALCULATION INVENTORY COMPLETE"
)
print("=" * 76)

print()
print(
    "Workbook KHÔNG bị thay đổi."
)