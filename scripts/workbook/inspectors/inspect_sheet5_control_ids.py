import re
import zipfile
from pathlib import Path


WORKBOOK = Path(r"data\input\LBG-TUYEN_chuan_VBA_macro.xlsm")
SHEET_XML = "xl/worksheets/sheet5.xml"


print("=" * 70)
print("M5-XLS-DIAG - SHEET5 CONTROL ID INSPECTION")
print("=" * 70)

if not WORKBOOK.exists():
    raise FileNotFoundError(f"Không tìm thấy workbook: {WORKBOOK}")

with zipfile.ZipFile(WORKBOOK, "r") as z:
    text = z.read(SHEET_XML).decode("utf-8")

ids = re.findall(
    r'<control\b[^>]*\bshapeId="([^"]+)"',
    text,
    flags=re.IGNORECASE,
)

print()
print("Workbook:", WORKBOOK)
print("Worksheet:", SHEET_XML)
print()

print("TOTAL CONTROL IDs =", len(ids))

if ids:
    numeric_ids = [int(x) for x in ids]

    print("MIN/MAX =", min(numeric_ids), max(numeric_ids))
    print("3931233 EXISTS =", "3931233" in ids)
    print("FIRST 20 =", ids[:20])
    print("LAST 20 =", ids[-20:])
else:
    print("Không tìm thấy control shapeId.")

print()
print("KẾT QUẢ: INSPECTION COMPLETE")