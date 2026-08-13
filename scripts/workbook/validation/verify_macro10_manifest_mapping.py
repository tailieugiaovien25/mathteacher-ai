import json
import re
import zipfile
from pathlib import Path


WORKBOOK = Path(
    r"data\input\LBG-TUYEN_chuan_VBA_macro.xlsm"
)

MANIFEST_FILE = Path(
    r"output\reports\macro10_button_cleanup_manifest.json"
)

SHEET_XML = "xl/worksheets/sheet5.xml"
VML_XML = "xl/drawings/vmlDrawing1.vml"


def numeric_shape_id(
    shape_id: str,
) -> str:
    match = re.search(
        r"(\d+)$",
        shape_id or "",
    )

    if not match:
        raise RuntimeError(
            f"Không lấy được numeric ID: {shape_id}"
        )

    return match.group(1)


print("=" * 72)
print(
    "M5-XLS-DIAG - "
    "MACRO10 MANIFEST / VML / WORKSHEET MAPPING"
)
print("=" * 72)


# ============================================================
# KIỂM TRA FILE
# ============================================================

if not WORKBOOK.exists():
    raise FileNotFoundError(
        f"Không tìm thấy workbook: {WORKBOOK}"
    )

if not MANIFEST_FILE.exists():
    raise FileNotFoundError(
        f"Không tìm thấy manifest: {MANIFEST_FILE}"
    )


# ============================================================
# ĐỌC MANIFEST
# ============================================================

manifest = json.loads(
    MANIFEST_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )
)

items = manifest.get(
    "items",
    [],
)

keep_items = [
    item
    for item in items
    if item.get("decision") == "KEEP"
]

remove_items = [
    item
    for item in items
    if (
        item.get("decision")
        == "REMOVE_CANDIDATE"
    )
]

keep_shape_ids = {
    item.get("shape_id")
    for item in keep_items
    if item.get("shape_id")
}

remove_shape_ids = {
    item.get("shape_id")
    for item in remove_items
    if item.get("shape_id")
}

all_manifest_shape_ids = (
    keep_shape_ids
    | remove_shape_ids
)

keep_numeric_ids = {
    numeric_shape_id(shape_id)
    for shape_id in keep_shape_ids
}

remove_numeric_ids = {
    numeric_shape_id(shape_id)
    for shape_id in remove_shape_ids
}

all_manifest_numeric_ids = (
    keep_numeric_ids
    | remove_numeric_ids
)


# ============================================================
# ĐỌC WORKBOOK
# ============================================================

with zipfile.ZipFile(
    WORKBOOK,
    "r",
) as archive:

    sheet_text = archive.read(
        SHEET_XML
    ).decode(
        "utf-8",
        errors="replace",
    )

    vml_text = archive.read(
        VML_XML
    ).decode(
        "utf-8",
        errors="replace",
    )


# ============================================================
# WORKSHEET CONTROL IDS
# ============================================================

worksheet_control_ids = set(
    re.findall(
        r'<control\b'
        r'[^>]*\bshapeId="([^"]+)"',
        sheet_text,
        flags=re.IGNORECASE,
    )
)


# ============================================================
# VML SHAPE BLOCKS
# ============================================================

shape_blocks = re.findall(
    r"<v:shape\b.*?</v:shape>",
    vml_text,
    flags=(
        re.IGNORECASE
        | re.DOTALL
    ),
)

vml_macro10_shape_ids = set()

for block in shape_blocks:

    macro_match = re.search(
        r"<x:FmlaMacro>"
        r"\s*(.*?)\s*"
        r"</x:FmlaMacro>",
        block,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    if not macro_match:
        continue

    macro = (
        macro_match
        .group(1)
        .strip()
    )

    if (
        macro.lower()
        != "[0]!macro10"
    ):
        continue

    id_match = re.search(
        r'\bid="([^"]+)"',
        block,
        flags=re.IGNORECASE,
    )

    if not id_match:
        continue

    vml_macro10_shape_ids.add(
        id_match.group(1)
    )


# ============================================================
# SO SÁNH MANIFEST ↔ VML
# ============================================================

manifest_missing_in_vml = (
    all_manifest_shape_ids
    - vml_macro10_shape_ids
)

vml_missing_in_manifest = (
    vml_macro10_shape_ids
    - all_manifest_shape_ids
)

remove_missing_in_vml = (
    remove_shape_ids
    - vml_macro10_shape_ids
)

keep_missing_in_vml = (
    keep_shape_ids
    - vml_macro10_shape_ids
)


# ============================================================
# SO SÁNH MANIFEST ↔ WORKSHEET
# ============================================================

remove_missing_in_sheet = (
    remove_numeric_ids
    - worksheet_control_ids
)

keep_missing_in_sheet = (
    keep_numeric_ids
    - worksheet_control_ids
)

manifest_missing_in_sheet = (
    all_manifest_numeric_ids
    - worksheet_control_ids
)


# ============================================================
# KIỂM TRA GIAO NHAU KEEP / REMOVE
# ============================================================

keep_remove_overlap = (
    keep_shape_ids
    & remove_shape_ids
)

keep_remove_numeric_overlap = (
    keep_numeric_ids
    & remove_numeric_ids
)


# ============================================================
# KIỂM TRA ACTION
# ============================================================

unexpected_actions = [
    {
        "shape_id": item.get(
            "shape_id"
        ),
        "action": item.get(
            "action"
        ),
    }
    for item in items
    if (
        item.get("action")
        != "[0]!Macro10"
    )
]


# ============================================================
# KẾT QUẢ
# ============================================================

manifest_count_ok = (
    len(items) == 70
)

keep_count_ok = (
    len(keep_shape_ids) == 24
)

remove_count_ok = (
    len(remove_shape_ids) == 46
)

vml_count_ok = (
    len(vml_macro10_shape_ids) == 70
)

manifest_vml_exact = (
    len(manifest_missing_in_vml) == 0
    and len(vml_missing_in_manifest) == 0
)

remove_vml_ok = (
    len(remove_missing_in_vml) == 0
)

keep_vml_ok = (
    len(keep_missing_in_vml) == 0
)

remove_sheet_ok = (
    len(remove_missing_in_sheet) == 0
)

keep_sheet_ok = (
    len(keep_missing_in_sheet) == 0
)

no_overlap = (
    len(keep_remove_overlap) == 0
    and len(
        keep_remove_numeric_overlap
    ) == 0
)

actions_ok = (
    len(unexpected_actions) == 0
)


final_pass = (
    manifest_count_ok
    and keep_count_ok
    and remove_count_ok
    and vml_count_ok
    and manifest_vml_exact
    and remove_vml_ok
    and keep_vml_ok
    and remove_sheet_ok
    and keep_sheet_ok
    and no_overlap
    and actions_ok
)


# ============================================================
# TERMINAL
# ============================================================

print()
print("MANIFEST")
print("-" * 72)

print(
    f"Manifest items:       "
    f"{len(items)}"
)

print(
    f"KEEP:                 "
    f"{len(keep_shape_ids)}"
)

print(
    f"REMOVE_CANDIDATE:     "
    f"{len(remove_shape_ids)}"
)

print()
print("VML")
print("-" * 72)

print(
    f"VML Macro10 IDs:      "
    f"{len(vml_macro10_shape_ids)}"
)

print(
    "Manifest missing VML: "
    f"{len(manifest_missing_in_vml)}"
)

print(
    "VML missing manifest: "
    f"{len(vml_missing_in_manifest)}"
)

print()
print("REMOVE MAPPING")
print("-" * 72)

print(
    f"REMOVE -> VML:        "
    f"{46 - len(remove_missing_in_vml)}/46"
)

print(
    f"REMOVE -> Worksheet:  "
    f"{46 - len(remove_missing_in_sheet)}/46"
)

print()
print("KEEP MAPPING")
print("-" * 72)

print(
    f"KEEP -> VML:          "
    f"{24 - len(keep_missing_in_vml)}/24"
)

print(
    f"KEEP -> Worksheet:    "
    f"{24 - len(keep_missing_in_sheet)}/24"
)

print()
print("SAFETY CHECK")
print("-" * 72)

print(
    "KEEP/REMOVE overlap: "
    f"{len(keep_remove_overlap)}"
)

print(
    "Unexpected actions:  "
    f"{len(unexpected_actions)}"
)

print(
    "Worksheet controls:  "
    f"{len(worksheet_control_ids)}"
)


# ============================================================
# CHỈ IN CHI TIẾT NẾU CÓ LỖI
# ============================================================

if remove_missing_in_vml:
    print()
    print(
        "REMOVE MISSING IN VML:"
    )

    print(
        sorted(
            remove_missing_in_vml
        )
    )

if remove_missing_in_sheet:
    print()
    print(
        "REMOVE MISSING IN WORKSHEET:"
    )

    print(
        sorted(
            remove_missing_in_sheet
        )
    )

if keep_missing_in_vml:
    print()
    print(
        "KEEP MISSING IN VML:"
    )

    print(
        sorted(
            keep_missing_in_vml
        )
    )

if keep_missing_in_sheet:
    print()
    print(
        "KEEP MISSING IN WORKSHEET:"
    )

    print(
        sorted(
            keep_missing_in_sheet
        )
    )

if manifest_missing_in_vml:
    print()
    print(
        "MANIFEST MISSING IN VML:"
    )

    print(
        sorted(
            manifest_missing_in_vml
        )
    )

if vml_missing_in_manifest:
    print()
    print(
        "VML MISSING IN MANIFEST:"
    )

    print(
        sorted(
            vml_missing_in_manifest
        )
    )


print()
print("=" * 72)

if final_pass:
    print(
        "MAPPING RESULT: "
        "PASS - MANIFEST EXACTLY VERIFIED"
    )

    print(
        "REMOVE mapping: 46/46"
    )

    print(
        "KEEP mapping:   24/24"
    )

else:
    print(
        "MAPPING RESULT: "
        "FAIL - DO NOT CLEANUP"
    )

print("=" * 72)

print()
print(
    "Workbook KHÔNG bị thay đổi."
)