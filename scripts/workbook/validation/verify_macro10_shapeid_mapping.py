import re
import zipfile
from pathlib import Path


WORKBOOK = Path(r"data\input\LBG-TUYEN_chuan_VBA_macro.xlsm")

SHEET_XML = "xl/worksheets/sheet5.xml"
VML_XML = "xl/drawings/vmlDrawing1.vml"


print("=" * 70)
print("M5-XLS-DIAG - MACRO10 SHAPEID MAPPING")
print("=" * 70)

if not WORKBOOK.exists():
    raise FileNotFoundError(
        f"Không tìm thấy workbook: {WORKBOOK}"
    )

with zipfile.ZipFile(WORKBOOK, "r") as z:
    sheet_text = z.read(SHEET_XML).decode(
        "utf-8",
        errors="replace",
    )

    vml_text = z.read(VML_XML).decode(
        "utf-8",
        errors="replace",
    )


# ------------------------------------------------------------
# 1. Lấy toàn bộ shapeId của worksheet
# ------------------------------------------------------------

worksheet_ids = set(
    re.findall(
        r'<control\b[^>]*\bshapeId="([^"]+)"',
        sheet_text,
        flags=re.IGNORECASE,
    )
)


# ------------------------------------------------------------
# 2. Tìm từng VML shape
# ------------------------------------------------------------

shape_blocks = re.findall(
    r'<v:shape\b.*?</v:shape>',
    vml_text,
    flags=re.IGNORECASE | re.DOTALL,
)

macro10_ids = []

for block in shape_blocks:

    macro_match = re.search(
        r'<x:FmlaMacro>\s*(.*?)\s*</x:FmlaMacro>',
        block,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not macro_match:
        continue

    macro = macro_match.group(1).strip()

    if macro.lower() != "[0]!macro10":
        continue

    id_match = re.search(
        r'\bid="(?:_x0000_s)?(\d+)"',
        block,
        flags=re.IGNORECASE,
    )

    if not id_match:
        continue

    macro10_ids.append(
        id_match.group(1)
    )


# ------------------------------------------------------------
# 3. So sánh
# ------------------------------------------------------------

matched = [
    shape_id
    for shape_id in macro10_ids
    if shape_id in worksheet_ids
]

missing = [
    shape_id
    for shape_id in macro10_ids
    if shape_id not in worksheet_ids
]


print()
print("Worksheet control IDs =", len(worksheet_ids))
print("VML Macro10 targets   =", len(macro10_ids))
print("Matched               =", len(matched))
print("Missing               =", len(missing))

print()
print("MACRO10 IDs:")
print(macro10_ids)

print()
print("MISSING IDs:")
print(missing)

print()

if (
    len(macro10_ids) == 46
    and len(matched) == 46
    and len(missing) == 0
):
    print("MAPPING RESULT: PASS - EXACT 46/46")
else:
    print("MAPPING RESULT: FAIL - DO NOT CLEANUP")

print()
print("Workbook KHÔNG bị thay đổi.")