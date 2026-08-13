import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_WORKBOOK = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

CONTROL_DETAILS_REPORT = Path(
    "output/reports/workbook_control_details_audit.json"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_button_groups_audit.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Phân tích nhóm Button trong workbook."
        )
    )

    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help=(
            "Workbook cần audit. "
            "Nếu bỏ qua sẽ dùng workbook gốc."
        ),
    )

    return parser.parse_args()


def clean(value):
    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


def get_action(control: dict) -> str:
    macro = clean(
        control.get("macro")
    )

    formula_macro = clean(
        control.get(
            "formula_macro"
        )
    )

    if macro:
        return macro

    if formula_macro:
        return formula_macro

    return ""


def main() -> None:
    args = parse_args()

    workbook_path = args.workbook

    if not workbook_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: "
            f"{workbook_path}"
        )

    if not CONTROL_DETAILS_REPORT.exists():
        raise FileNotFoundError(
            "Không tìm thấy báo cáo "
            "workbook_control_details_audit.json.\n"
            "Hãy chạy "
            "audit_workbook_control_details.py "
            "trên đúng workbook trước."
        )

    audit = json.loads(
        CONTROL_DETAILS_REPORT.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    report_workbook = Path(
        audit.get(
            "workbook",
            "",
        )
    )

    # ---------------------------------------------------------
    # Fail closed:
    # report phải thuộc đúng workbook đang yêu cầu audit.
    # ---------------------------------------------------------

    try:
        requested_resolved = (
            workbook_path.resolve()
        )

        reported_resolved = (
            report_workbook.resolve()
        )

    except Exception:
        requested_resolved = (
            workbook_path
        )

        reported_resolved = (
            report_workbook
        )

    if (
        reported_resolved
        != requested_resolved
    ):
        raise RuntimeError(
            "\nBáo cáo Control Details "
            "không thuộc workbook đang yêu cầu.\n\n"
            f"Workbook yêu cầu:\n"
            f"{workbook_path}\n\n"
            f"Workbook trong report:\n"
            f"{report_workbook}\n\n"
            "Hãy chạy lại "
            "audit_workbook_control_details.py "
            "với cùng --workbook trước."
        )

    controls = []

    for sheet in audit.get(
        "sheets",
        [],
    ):
        sheet_name = sheet.get(
            "sheet_name"
        )

        for control in sheet.get(
            "controls",
            [],
        ):
            object_type = clean(
                control.get(
                    "object_type"
                )
            )

            if (
                object_type.lower()
                != "button"
            ):
                continue

            controls.append(
                {
                    "sheet": (
                        sheet_name
                    ),
                    "shape_id": clean(
                        control.get(
                            "shape_id"
                        )
                    ),
                    "caption": clean(
                        control.get(
                            "caption"
                        )
                    ),
                    "action": get_action(
                        control
                    ),
                    "row": clean(
                        control.get(
                            "row"
                        )
                    ),
                    "column": clean(
                        control.get(
                            "column"
                        )
                    ),
                    "anchor": clean(
                        control.get(
                            "anchor"
                        )
                    ),
                    "style": clean(
                        control.get(
                            "style"
                        )
                    ),
                }
            )

    # =========================================================
    # THỐNG KÊ CHUNG
    # =========================================================

    caption_counts = Counter(
        item["caption"]
        for item in controls
        if item["caption"]
    )

    action_counts = Counter(
        item["action"]
        for item in controls
        if item["action"]
    )

    # =========================================================
    # GROUP THEO CAPTION
    # =========================================================

    caption_groups = defaultdict(
        list
    )

    for item in controls:
        caption_groups[
            item["caption"]
        ].append(item)

    duplicate_caption_groups = {
        caption: items
        for caption, items
        in caption_groups.items()
        if (
            caption
            and len(items) > 1
        )
    }

    # =========================================================
    # GROUP THEO ACTION
    # =========================================================

    action_groups = defaultdict(
        list
    )

    for item in controls:
        action_groups[
            item["action"]
        ].append(item)

    duplicate_action_groups = {
        action: items
        for action, items
        in action_groups.items()
        if (
            action
            and len(items) > 1
        )
    }

    # =========================================================
    # GROUP SHEET + CAPTION + ACTION
    # =========================================================

    signature_groups = defaultdict(
        list
    )

    for item in controls:
        signature = (
            item["sheet"],
            item["caption"],
            item["action"],
        )

        signature_groups[
            signature
        ].append(item)

    exact_duplicate_groups = {
        signature: items
        for signature, items
        in signature_groups.items()
        if len(items) > 1
    }

    no_caption = [
        item
        for item in controls
        if not item["caption"]
    ]

    no_action = [
        item
        for item in controls
        if not item["action"]
    ]

    # =========================================================
    # MACRO10
    # =========================================================

    macro10_buttons = [
        item
        for item in controls
        if item["action"]
        == "[0]!Macro10"
    ]

    macro10_geometry_groups = (
        defaultdict(list)
    )

    for item in macro10_buttons:
        geometry = (
            item["anchor"],
            item["style"],
        )

        macro10_geometry_groups[
            geometry
        ].append(item)

    macro10_duplicate_geometry = {
        geometry: items
        for geometry, items
        in macro10_geometry_groups.items()
        if len(items) > 1
    }

    # =========================================================
    # REPORT
    # =========================================================

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-02C"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "workbook": str(
            workbook_path
        ),

        "summary": {
            "total_buttons": len(
                controls
            ),
            "unique_captions": len(
                caption_counts
            ),
            "unique_actions": len(
                action_counts
            ),
            "duplicate_caption_groups": (
                len(
                    duplicate_caption_groups
                )
            ),
            "duplicate_action_groups": (
                len(
                    duplicate_action_groups
                )
            ),
            "exact_duplicate_groups": (
                len(
                    exact_duplicate_groups
                )
            ),
            "buttons_without_caption": (
                len(
                    no_caption
                )
            ),
            "buttons_without_action": (
                len(
                    no_action
                )
            ),
            "macro10_buttons": (
                len(
                    macro10_buttons
                )
            ),
            "macro10_geometry_groups": (
                len(
                    macro10_geometry_groups
                )
            ),
            "macro10_duplicate_geometry_groups": (
                len(
                    macro10_duplicate_geometry
                )
            ),
        },

        "caption_counts": dict(
            caption_counts
        ),

        "action_counts": dict(
            action_counts
        ),

        "exact_duplicate_groups": [
            {
                "sheet": (
                    signature[0]
                ),
                "caption": (
                    signature[1]
                ),
                "action": (
                    signature[2]
                ),
                "count": (
                    len(items)
                ),
                "controls": (
                    items
                ),
            }
            for signature, items
            in exact_duplicate_groups.items()
        ],

        "macro10_duplicate_geometry_groups": [
            {
                "geometry": list(
                    geometry
                ),
                "count": len(
                    items
                ),
                "controls": items,
            }
            for geometry, items
            in (
                macro10_duplicate_geometry
                .items()
            )
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

    # =========================================================
    # TERMINAL
    # =========================================================

    print("=" * 72)

    print(
        "M5-XLS-AUDIT-02C - "
        "BUTTON GROUP ANALYSIS"
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
        f"{workbook_path}"
    )

    print(
        "\nKẾT QUẢ TỔNG HỢP"
    )

    print(
        f"Tổng Button: "
        f"{len(controls)}"
    )

    print(
        f"Số Caption khác nhau: "
        f"{len(caption_counts)}"
    )

    print(
        f"Số Action/Macro khác nhau: "
        f"{len(action_counts)}"
    )

    print(
        f"Nhóm Caption bị lặp: "
        f"{len(duplicate_caption_groups)}"
    )

    print(
        f"Nhóm Action bị lặp: "
        f"{len(duplicate_action_groups)}"
    )

    print(
        "Nhóm trùng chính xác "
        "(Sheet + Caption + Action): "
        f"{len(exact_duplicate_groups)}"
    )

    print(
        f"Button không có Caption: "
        f"{len(no_caption)}"
    )

    print(
        f"Button không có Action: "
        f"{len(no_action)}"
    )

    print(
        "\nMACRO10"
    )

    print(
        f"Button Macro10: "
        f"{len(macro10_buttons)}"
    )

    print(
        f"Nhóm hình học Macro10: "
        f"{len(macro10_geometry_groups)}"
    )

    print(
        "Nhóm Macro10 trùng hình học: "
        f"{len(macro10_duplicate_geometry)}"
    )

    print(
        "\n20 CAPTION XUẤT HIỆN "
        "NHIỀU NHẤT"
    )

    for caption, count in (
        caption_counts.most_common(
            20
        )
    ):
        print(
            f"- {count:3d} | "
            f"{caption}"
        )

    print(
        "\n20 ACTION/MACRO ĐƯỢC "
        "GỌI NHIỀU NHẤT"
    )

    for action, count in (
        action_counts.most_common(
            20
        )
    ):
        print(
            f"- {count:3d} | "
            f"{action}"
        )

    if exact_duplicate_groups:
        print(
            "\nNHÓM TRÙNG "
            "SHEET + CAPTION + ACTION"
        )

        for (
            signature,
            items,
        ) in list(
            exact_duplicate_groups.items()
        )[:20]:
            print(
                f"- {signature} | "
                f"Buttons={len(items)}"
            )

    if (
        macro10_duplicate_geometry
    ):
        print(
            "\nCẢNH BÁO: "
            "MACRO10 VẪN TRÙNG HÌNH HỌC"
        )

        for geometry, items in list(
            macro10_duplicate_geometry.items()
        )[:20]:
            print(
                f"- {geometry} | "
                f"Buttons={len(items)}"
            )

    else:
        print(
            "\nKhông phát hiện Macro10 "
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
        "BUTTON GROUP ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()