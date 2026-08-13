import argparse
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path


DEFAULT_EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_button_geometry_audit.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Audit geometry của Button "
            "trong workbook."
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


def clean(value: str | None) -> str:
    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


def extract_attribute(
    text: str,
    name: str,
) -> str:
    match = re.search(
        rf'\b{re.escape(name)}\s*=\s*"([^"]*)"',
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return clean(
        match.group(1)
    )


def parse_style(
    style: str,
) -> dict[str, str]:
    result = {}

    for part in style.split(";"):
        if ":" not in part:
            continue

        key, value = part.split(
            ":",
            1,
        )

        key = key.strip().lower()
        value = value.strip()

        if key:
            result[key] = value

    return result


def extract_tag_text(
    block: str,
    tag_name: str,
) -> str:
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
        return ""

    value = re.sub(
        r"<[^>]+>",
        "",
        match.group(1),
    )

    return clean(value)


def inspect_vml(
    archive: zipfile.ZipFile,
    path: str,
) -> list[dict]:
    text = read_text_safe(
        archive,
        path,
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

    result = []

    for match in shape_pattern.finditer(
        text
    ):
        attrs = match.group(
            "attrs"
        )

        body = match.group(
            "body"
        )

        style_text = extract_attribute(
            attrs,
            "style",
        )

        style = parse_style(
            style_text
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

        object_type = extract_attribute(
            client_attrs,
            "ObjectType",
        )

        if object_type.lower() != "button":
            continue

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

        caption = ""

        if textbox_match:
            caption = re.sub(
                r"<[^>]+>",
                "",
                textbox_match.group(1),
            )

            caption = clean(
                caption
            )

        action = (
            extract_tag_text(
                client_body,
                "FmlaMacro",
            )
            or extract_tag_text(
                client_body,
                "Macro",
            )
        )

        anchor = extract_tag_text(
            client_body,
            "Anchor",
        )

        result.append(
            {
                "vml_path": path,
                "shape_id": extract_attribute(
                    attrs,
                    "id",
                ),
                "caption": caption,
                "action": action,
                "style_raw": style_text,
                "left": style.get(
                    "margin-left",
                    "",
                ),
                "top": style.get(
                    "margin-top",
                    "",
                ),
                "width": style.get(
                    "width",
                    "",
                ),
                "height": style.get(
                    "height",
                    "",
                ),
                "visibility": style.get(
                    "visibility",
                    "",
                ),
                "anchor": anchor,
                "row": extract_tag_text(
                    client_body,
                    "Row",
                ),
                "column": extract_tag_text(
                    client_body,
                    "Column",
                ),
            }
        )

    return result


def geometry_signature(
    item: dict,
) -> tuple:
    if item["anchor"]:
        return (
            "ANCHOR",
            item["anchor"],
        )

    return (
        "STYLE",
        item["left"],
        item["top"],
        item["width"],
        item["height"],
    )


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
        "M5-XLS-AUDIT-02D - "
        "BUTTON GEOMETRY AUDIT"
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

    all_buttons = []

    with zipfile.ZipFile(
        excel_file,
        "r",
    ) as archive:
        vml_paths = sorted(
            path
            for path in archive.namelist()
            if "vmlDrawing" in path
        )

        for path in vml_paths:
            all_buttons.extend(
                inspect_vml(
                    archive,
                    path,
                )
            )

    macro10_buttons = [
        item
        for item in all_buttons
        if item["action"]
        == "[0]!Macro10"
    ]

    geometry_groups = defaultdict(
        list
    )

    for item in macro10_buttons:
        geometry_groups[
            geometry_signature(
                item
            )
        ].append(item)

    duplicate_geometry = {
        signature: items
        for signature, items
        in geometry_groups.items()
        if len(items) > 1
    }

    all_geometry_groups = defaultdict(
        list
    )

    for item in all_buttons:
        signature = (
            item["action"],
            item["caption"],
            geometry_signature(
                item
            ),
        )

        all_geometry_groups[
            signature
        ].append(item)

    exact_geometry_duplicates = {
        signature: items
        for signature, items
        in all_geometry_groups.items()
        if len(items) > 1
    }

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-02D"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "workbook": str(
            excel_file
        ),

        "summary": {
            "total_buttons": len(
                all_buttons
            ),
            "macro10_buttons": len(
                macro10_buttons
            ),
            "macro10_unique_geometry": len(
                geometry_groups
            ),
            "macro10_duplicate_geometry_groups": len(
                duplicate_geometry
            ),
            "exact_geometry_duplicate_groups": len(
                exact_geometry_duplicates
            ),
        },

        "macro10_buttons": (
            macro10_buttons
        ),

        "macro10_duplicate_geometry_groups": [
            {
                "geometry": list(
                    signature
                ),
                "count": len(items),
                "buttons": items,
            }
            for signature, items
            in duplicate_geometry.items()
        ],

        "exact_geometry_duplicate_groups": [
            {
                "action": signature[0],
                "caption": signature[1],
                "geometry": list(
                    signature[2]
                ),
                "count": len(items),
                "buttons": items,
            }
            for signature, items
            in exact_geometry_duplicates.items()
        ],
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
        f"Tổng Button đọc được: "
        f"{len(all_buttons)}"
    )

    print(
        f"Button gọi [0]!Macro10: "
        f"{len(macro10_buttons)}"
    )

    print(
        "Số vị trí/hình học khác nhau "
        "của Macro10: "
        f"{len(geometry_groups)}"
    )

    print(
        "Nhóm Macro10 trùng hình học: "
        f"{len(duplicate_geometry)}"
    )

    print(
        "Nhóm trùng hoàn toàn "
        "(Action + Caption + Geometry): "
        f"{len(exact_geometry_duplicates)}"
    )

    if duplicate_geometry:
        print(
            "\nCÁC NHÓM MACRO10 "
            "TRÙNG HÌNH HỌC"
        )

        for signature, items in list(
            duplicate_geometry.items()
        )[:20]:
            print(
                f"\n- Geometry: "
                f"{signature}"
            )

            print(
                f"  Số Button: "
                f"{len(items)}"
            )

    else:
        print(
            "\nKhông phát hiện Button Macro10 "
            "trùng hình học."
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
        "BUTTON GEOMETRY AUDIT COMPLETE"
    )


if __name__ == "__main__":
    main()