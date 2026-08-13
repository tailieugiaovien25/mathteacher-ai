import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_controls_audit.json"
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
            "Audit Control/VML trong workbook."
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
        name = sheet.attrib.get("name")
        rel_id = sheet.attrib.get(
            REL_ID
        )

        if not name or not rel_id:
            continue

        target = relationships.get(
            rel_id
        )

        if target:
            result[target] = name

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


def extract_tag_text(
    block: str,
    tag_name: str,
) -> str | None:
    pattern = (
        rf"<(?:\w+:)?{re.escape(tag_name)}"
        rf"[^>]*>(.*?)"
        rf"</(?:\w+:)?{re.escape(tag_name)}>"
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

    value = re.sub(
        r"<[^>]+>",
        "",
        match.group(1),
    ).strip()

    return value or None


def inspect_vml_tolerant(
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

    controls = []

    for match in shape_pattern.finditer(
        text
    ):
        attrs = match.group(
            "attrs"
        )

        body = match.group(
            "body"
        )

        shape_id_match = re.search(
            r'\bid\s*=\s*"([^"]+)"',
            attrs,
            flags=re.IGNORECASE,
        )

        type_match = re.search(
            r'\btype\s*=\s*"([^"]+)"',
            attrs,
            flags=re.IGNORECASE,
        )

        client_match = re.search(
            r"<(?:\w+:)?ClientData\b"
            r"([^>]*)>"
            r"(.*?)"
            r"</(?:\w+:)?ClientData>",
            body,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        object_type = None
        client_body = ""

        if client_match:
            client_attrs = (
                client_match.group(1)
            )

            client_body = (
                client_match.group(2)
            )

            object_match = re.search(
                r'ObjectType\s*=\s*"([^"]+)"',
                client_attrs,
                flags=re.IGNORECASE,
            )

            if object_match:
                object_type = (
                    object_match.group(1)
                )

        controls.append(
            {
                "shape_id": (
                    shape_id_match.group(1)
                    if shape_id_match
                    else None
                ),
                "shape_type": (
                    type_match.group(1)
                    if type_match
                    else None
                ),
                "object_type": (
                    object_type
                ),
                "row": extract_tag_text(
                    client_body,
                    "Row",
                ),
                "column": extract_tag_text(
                    client_body,
                    "Column",
                ),
                "macro": extract_tag_text(
                    client_body,
                    "Macro",
                ),
                "vml_path": vml_path,
            }
        )

    return controls


def inspect_control_parts(
    archive: zipfile.ZipFile,
) -> list[dict]:
    result = []

    paths = sorted(
        name
        for name in archive.namelist()
        if (
            name.startswith(
                "xl/controls/"
            )
            or name.startswith(
                "xl/ctrlProps/"
            )
        )
    )

    for path in paths:
        content = read_text_safe(
            archive,
            path,
        )

        result.append(
            {
                "path": path,
                "size": len(
                    content.encode(
                        "utf-8"
                    )
                ),
                "preview": content[:500],
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
        "M5-XLS-AUDIT-02 - "
        "WORKBOOK CONTROLS AUDIT"
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

        sheet_reports = []

        total_vml_controls = 0

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

            sheet_controls = []

            for vml_path in vml_paths:
                controls = (
                    inspect_vml_tolerant(
                        archive,
                        vml_path,
                    )
                )

                total_vml_controls += (
                    len(controls)
                )

                sheet_controls.extend(
                    controls
                )

            if (
                vml_paths
                or sheet_controls
            ):
                sheet_reports.append(
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
                            len(
                                sheet_controls
                            )
                        ),
                        "controls": (
                            sheet_controls
                        ),
                    }
                )

        control_parts = (
            inspect_control_parts(
                archive
            )
        )

        macro_refs = []

        for sheet in sheet_reports:
            for control in sheet[
                "controls"
            ]:
                macro = control.get(
                    "macro"
                )

                if macro:
                    macro_refs.append(
                        {
                            "sheet": (
                                sheet[
                                    "sheet_name"
                                ]
                            ),
                            "shape_id": (
                                control.get(
                                    "shape_id"
                                )
                            ),
                            "object_type": (
                                control.get(
                                    "object_type"
                                )
                            ),
                            "macro": macro,
                        }
                    )

        unique_macros = sorted(
            {
                item["macro"]
                for item in macro_refs
            }
        )

        report = {
            "audit_id": (
                "M5-XLS-AUDIT-02"
            ),
            "mode": (
                "READ_ONLY_AUDIT"
            ),
            "workbook_modified": (
                False
            ),
            "workbook": str(
                excel_file
            ),
            "sheet_control_reports": (
                sheet_reports
            ),
            "vml_control_count": (
                total_vml_controls
            ),
            "control_part_count": (
                len(control_parts)
            ),
            "control_parts": (
                control_parts
            ),
            "macro_reference_count": (
                len(macro_refs)
            ),
            "unique_macro_count": (
                len(unique_macros)
            ),
            "unique_macros": (
                unique_macros
            ),
            "macro_references": (
                macro_refs
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

    print("\n" + "=" * 72)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        "Số sheet có VML/control: "
        f"{len(sheet_reports)}"
    )

    print(
        "Tổng VML shape/control: "
        f"{total_vml_controls}"
    )

    print(
        "Control XML/Prop parts: "
        f"{len(control_parts)}"
    )

    print(
        "Macro references từ VML: "
        f"{len(macro_refs)}"
    )

    print(
        "Số macro duy nhất được tham chiếu: "
        f"{len(unique_macros)}"
    )

    if unique_macros:
        print(
            "\nDANH SÁCH MACRO "
            "ĐƯỢC VML CONTROL GỌI"
        )

        for macro in unique_macros:
            print(
                f"- {macro}"
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
        "WORKBOOK CONTROLS AUDIT COMPLETE"
    )


if __name__ == "__main__":
    main()