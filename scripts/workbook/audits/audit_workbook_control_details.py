import argparse
import html
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_control_details_audit.json"
)


WORKBOOK_NS = {
    "main": (
        "http://schemas.openxmlformats.org/"
        "spreadsheetml/2006/main"
    ),
}

REL_ID = (
    "{http://schemas.openxmlformats.org/"
    "officeDocument/2006/relationships}id"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Audit chi tiết Control/VML trong workbook."
        )
    )

    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_EXCEL_FILE,
        help=(
            "Đường dẫn workbook cần audit. "
            "Nếu bỏ qua sẽ dùng workbook gốc."
        ),
    )

    return parser.parse_args()


def normalize_target(
    base_path: str,
    target: str,
) -> str:
    if target.startswith("/"):
        return target.lstrip("/")

    parts = base_path.split("/")[:-1]

    for segment in target.split("/"):
        if segment == "..":
            if parts:
                parts.pop()

        elif segment == ".":
            continue

        elif segment:
            parts.append(segment)

    return "/".join(parts)


def read_xml_safe(
    archive: zipfile.ZipFile,
    path: str,
):
    try:
        content = archive.read(path)
    except KeyError:
        return None

    try:
        return ET.fromstring(content)
    except ET.ParseError:
        return None


def read_text_safe(
    archive: zipfile.ZipFile,
    path: str,
) -> str:
    try:
        content = archive.read(path)
    except KeyError:
        return ""

    return content.decode(
        "utf-8",
        errors="replace",
    )


def get_relationships(
    archive: zipfile.ZipFile,
    rels_path: str,
    base_path: str,
) -> dict[str, str]:
    root = read_xml_safe(
        archive,
        rels_path,
    )

    if root is None:
        return {}

    result = {}

    for rel in root:
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")

        if rel_id and target:
            result[rel_id] = normalize_target(
                base_path,
                target,
            )

    return result


def get_sheet_mapping(
    archive: zipfile.ZipFile,
) -> dict[str, str]:
    workbook_root = read_xml_safe(
        archive,
        "xl/workbook.xml",
    )

    if workbook_root is None:
        return {}

    relationships = get_relationships(
        archive,
        "xl/_rels/workbook.xml.rels",
        "xl/workbook.xml",
    )

    result = {}

    sheets = workbook_root.find(
        "main:sheets",
        WORKBOOK_NS,
    )

    if sheets is None:
        return result

    for sheet in sheets:
        sheet_name = sheet.attrib.get(
            "name"
        )

        rel_id = sheet.attrib.get(
            REL_ID
        )

        if not sheet_name or not rel_id:
            continue

        target = relationships.get(
            rel_id
        )

        if target:
            result[target] = (
                sheet_name
            )

    return result


def get_sheet_relationships(
    archive: zipfile.ZipFile,
    sheet_path: str,
) -> dict[str, str]:
    folder, filename = (
        sheet_path.rsplit("/", 1)
    )

    rels_path = (
        f"{folder}/_rels/"
        f"{filename}.rels"
    )

    return get_relationships(
        archive,
        rels_path,
        sheet_path,
    )


def clean_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    value = html.unescape(
        value
    )

    value = re.sub(
        r"<[^>]+>",
        "",
        value,
    )

    value = " ".join(
        value.split()
    )

    return value or None


def extract_tag_text(
    block: str,
    tag_name: str,
) -> str | None:
    pattern = (
        rf"<(?:\w+:)?"
        rf"{re.escape(tag_name)}"
        rf"[^>]*>"
        rf"(.*?)"
        rf"</(?:\w+:)?"
        rf"{re.escape(tag_name)}>"
    )

    match = re.search(
        pattern,
        block,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    if not match:
        return None

    return clean_text(
        match.group(1)
    )


def extract_attribute(
    text: str,
    attribute: str,
) -> str | None:
    pattern = (
        rf"\b{re.escape(attribute)}"
        rf'\s*=\s*"([^"]*)"'
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return clean_text(
        match.group(1)
    )


def inspect_vml_shapes(
    archive: zipfile.ZipFile,
    vml_path: str,
) -> list[dict]:
    text = read_text_safe(
        archive,
        vml_path,
    )

    if not text:
        return []

    shape_pattern = re.compile(
        r"<(?:\w+:)?shape\b"
        r"(?P<attrs>[^>]*)>"
        r"(?P<body>.*?)"
        r"</(?:\w+:)?shape>",
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    results = []

    for match in shape_pattern.finditer(
        text
    ):
        attrs = match.group(
            "attrs"
        )

        body = match.group(
            "body"
        )

        client_match = re.search(
            r"<(?:\w+:)?ClientData\b"
            r"(?P<attrs>[^>]*)>"
            r"(?P<body>.*?)"
            r"</(?:\w+:)?ClientData>",
            body,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        client_attrs = ""
        client_body = ""

        if client_match:
            client_attrs = (
                client_match.group(
                    "attrs"
                )
            )

            client_body = (
                client_match.group(
                    "body"
                )
            )

        textbox_match = re.search(
            r"<(?:\w+:)?textbox\b"
            r"[^>]*>"
            r"(.*?)"
            r"</(?:\w+:)?textbox>",
            body,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        caption = None

        if textbox_match:
            caption = clean_text(
                textbox_match.group(1)
            )

        if caption is None:
            caption = extract_tag_text(
                client_body,
                "Text",
            )

        result = {
            "vml_path": vml_path,

            "shape_id": extract_attribute(
                attrs,
                "id",
            ),

            "shape_type": (
                extract_attribute(
                    attrs,
                    "type",
                )
            ),

            "style": extract_attribute(
                attrs,
                "style",
            ),

            "object_type": (
                extract_attribute(
                    client_attrs,
                    "ObjectType",
                )
            ),

            "caption": caption,

            "row": extract_tag_text(
                client_body,
                "Row",
            ),

            "column": extract_tag_text(
                client_body,
                "Column",
            ),

            "anchor": extract_tag_text(
                client_body,
                "Anchor",
            ),

            "macro": extract_tag_text(
                client_body,
                "Macro",
            ),

            "linked_cell": (
                extract_tag_text(
                    client_body,
                    "FmlaLink",
                )
            ),

            "range_source": (
                extract_tag_text(
                    client_body,
                    "FmlaRange",
                )
            ),

            "formula_macro": (
                extract_tag_text(
                    client_body,
                    "FmlaMacro",
                )
            ),

            "checked": extract_tag_text(
                client_body,
                "Checked",
            ),

            "visible": (
                extract_tag_text(
                    client_body,
                    "Visible",
                )
            ),

            "print_object": (
                extract_tag_text(
                    client_body,
                    "PrintObject",
                )
            ),
        }

        results.append(
            result
        )

    return results


def inspect_control_property_parts(
    archive: zipfile.ZipFile,
) -> list[dict]:
    result = []

    paths = sorted(
        path
        for path in archive.namelist()
        if (
            path.startswith(
                "xl/controls/"
            )
            or path.startswith(
                "xl/ctrlProps/"
            )
        )
    )

    for path in paths:
        text = read_text_safe(
            archive,
            path,
        )

        if not text:
            continue

        result.append(
            {
                "path": path,
                "name": extract_attribute(
                    text,
                    "name",
                ),
                "shape_id": (
                    extract_attribute(
                        text,
                        "shapeId",
                    )
                ),
                "object_type": (
                    extract_attribute(
                        text,
                        "objectType",
                    )
                ),
                "linked_cell": (
                    extract_attribute(
                        text,
                        "fmlaLink",
                    )
                ),
                "range_source": (
                    extract_attribute(
                        text,
                        "fmlaRange",
                    )
                ),
                "macro": extract_attribute(
                    text,
                    "macro",
                ),
                "raw_preview": (
                    clean_text(
                        text[:800]
                    )
                ),
            }
        )

    return result


def main() -> None:
    args = parse_args()

    excel_file = args.workbook

    if not excel_file.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: "
            f"{excel_file}"
        )

    print("=" * 72)
    print(
        "M5-XLS-AUDIT-02B - "
        "CONTROL DETAILS AUDIT"
    )
    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook sẽ KHÔNG bị thay đổi."
    )

    print(
        f"Workbook đang audit: "
        f"{excel_file}"
    )

    with zipfile.ZipFile(
        excel_file,
        "r",
    ) as archive:
        sheet_mapping = (
            get_sheet_mapping(
                archive
            )
        )

        sheet_details = []

        all_controls = []

        for sheet_path, sheet_name in (
            sheet_mapping.items()
        ):
            relationships = (
                get_sheet_relationships(
                    archive,
                    sheet_path,
                )
            )

            vml_paths = sorted(
                {
                    target
                    for target
                    in relationships.values()
                    if "vmlDrawing"
                    in target
                }
            )

            controls = []

            for vml_path in vml_paths:
                controls.extend(
                    inspect_vml_shapes(
                        archive,
                        vml_path,
                    )
                )

            for control in controls:
                control["sheet_name"] = (
                    sheet_name
                )

                all_controls.append(
                    control
                )

            if controls:
                sheet_details.append(
                    {
                        "sheet_name": (
                            sheet_name
                        ),
                        "sheet_path": (
                            sheet_path
                        ),
                        "vml_paths": (
                            vml_paths
                        ),
                        "control_count": (
                            len(controls)
                        ),
                        "controls": (
                            controls
                        ),
                    }
                )

        property_parts = (
            inspect_control_property_parts(
                archive
            )
        )

    # =========================================================
    # THỐNG KÊ
    # =========================================================

    sheet_counts = Counter(
        control["sheet_name"]
        for control in all_controls
    )

    type_counts = Counter(
        (
            control.get(
                "object_type"
            )
            or "UNKNOWN"
        )
        for control in all_controls
    )

    sheet_type_counts = defaultdict(
        Counter
    )

    for control in all_controls:
        sheet_type_counts[
            control["sheet_name"]
        ][
            control.get(
                "object_type"
            )
            or "UNKNOWN"
        ] += 1

    captioned = [
        control
        for control in all_controls
        if control.get(
            "caption"
        )
    ]

    macro_controls = [
        control
        for control in all_controls
        if (
            control.get("macro")
            or control.get(
                "formula_macro"
            )
        )
    ]

    linked_controls = [
        control
        for control in all_controls
        if control.get(
            "linked_cell"
        )
    ]

    range_controls = [
        control
        for control in all_controls
        if control.get(
            "range_source"
        )
    ]

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-02B"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "workbook": str(
            excel_file
        ),
        "summary": {
            "sheet_count_with_controls": (
                len(sheet_counts)
            ),
            "total_controls": len(
                all_controls
            ),
            "captioned_controls": len(
                captioned
            ),
            "macro_controls": len(
                macro_controls
            ),
            "linked_cell_controls": len(
                linked_controls
            ),
            "range_source_controls": len(
                range_controls
            ),
            "control_property_parts": len(
                property_parts
            ),
        },
        "sheet_counts": dict(
            sheet_counts
        ),
        "type_counts": dict(
            type_counts
        ),
        "sheet_type_counts": {
            sheet: dict(counts)
            for sheet, counts
            in sheet_type_counts.items()
        },
        "sheets": sheet_details,
        "property_parts": (
            property_parts
        ),
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # =========================================================
    # TERMINAL REPORT
    # =========================================================

    print("\n" + "=" * 72)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        "Tổng control/shape: "
        f"{len(all_controls)}"
    )

    print(
        "Control có caption: "
        f"{len(captioned)}"
    )

    print(
        "Control có macro/action: "
        f"{len(macro_controls)}"
    )

    print(
        "Control có linked cell: "
        f"{len(linked_controls)}"
    )

    print(
        "Control có range source: "
        f"{len(range_controls)}"
    )

    print(
        "Control/Prop XML parts: "
        f"{len(property_parts)}"
    )

    print(
        "\nPHÂN BỔ THEO SHEET"
    )

    for sheet, count in (
        sheet_counts.items()
    ):
        print(
            f"- {sheet}: {count}"
        )

        for control_type, number in (
            sheet_type_counts[
                sheet
            ].items()
        ):
            print(
                f"    {control_type}: "
                f"{number}"
            )

    print(
        "\nPHÂN BỔ THEO LOẠI CONTROL"
    )

    for control_type, count in (
        type_counts.most_common()
    ):
        print(
            f"- {control_type}: "
            f"{count}"
        )

    if captioned:
        print(
            "\n20 CONTROL CÓ CAPTION ĐẦU TIÊN"
        )

        for control in captioned[:20]:
            print(
                f"- {control['sheet_name']} | "
                f"{control.get('object_type')} | "
                f"Row={control.get('row')} | "
                f"Col={control.get('column')} | "
                f"{control.get('caption')!r}"
            )

    if macro_controls:
        print(
            "\nCONTROL CÓ MACRO/ACTION"
        )

        for control in macro_controls[:30]:
            print(
                f"- {control['sheet_name']} | "
                f"{control.get('shape_id')} | "
                f"macro={control.get('macro')} | "
                f"fmlaMacro="
                f"{control.get('formula_macro')}"
            )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nWorkbook KHÔNG bị thay đổi."
    )

    print(
        "\nKẾT QUẢ: "
        "CONTROL DETAILS AUDIT COMPLETE"
    )


if __name__ == "__main__":
    main()