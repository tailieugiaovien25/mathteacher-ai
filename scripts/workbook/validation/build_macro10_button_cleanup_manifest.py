import json
from collections import defaultdict
from pathlib import Path


GEOMETRY_REPORT = Path(
    "output/reports/workbook_button_geometry_audit.json"
)

OUTPUT_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)


def main() -> None:
    if not GEOMETRY_REPORT.exists():
        raise FileNotFoundError(
            f"Không tìm thấy báo cáo geometry: "
            f"{GEOMETRY_REPORT}"
        )

    data = json.loads(
        GEOMETRY_REPORT.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    buttons = data.get(
        "macro10_buttons",
        [],
    )

    groups = defaultdict(list)

    for button in buttons:
        anchor = button.get("anchor") or ""

        geometry_key = (
            anchor,
            button.get("left") or "",
            button.get("top") or "",
            button.get("width") or "",
            button.get("height") or "",
        )

        groups[geometry_key].append(
            button
        )

    manifest_items = []

    keep_count = 0
    remove_candidate_count = 0

    for group_index, (
        geometry,
        items,
    ) in enumerate(
        sorted(
            groups.items(),
            key=lambda x: str(x[0]),
        ),
        start=1,
    ):
        # Chọn button đầu tiên trong nhóm làm KEEP.
        # Hiện tại chỉ là manifest, chưa xóa gì.
        sorted_items = sorted(
            items,
            key=lambda item: (
                item.get("shape_id") or ""
            ),
        )

        for index, item in enumerate(
            sorted_items
        ):
            if index == 0:
                decision = "KEEP"
                reason = (
                    "Đại diện duy nhất cần giữ "
                    "cho vị trí hình học này."
                )
                keep_count += 1
            else:
                decision = (
                    "REMOVE_CANDIDATE"
                )
                reason = (
                    "Cùng Action + Caption + "
                    "Geometry với Button KEEP."
                )
                remove_candidate_count += 1

            manifest_items.append(
                {
                    "group_id": (
                        f"MACRO10_G{group_index:03d}"
                    ),
                    "shape_id": (
                        item.get("shape_id")
                    ),
                    "caption": (
                        item.get("caption")
                    ),
                    "action": (
                        item.get("action")
                    ),
                    "anchor": (
                        item.get("anchor")
                    ),
                    "left": (
                        item.get("left")
                    ),
                    "top": (
                        item.get("top")
                    ),
                    "width": (
                        item.get("width")
                    ),
                    "height": (
                        item.get("height")
                    ),
                    "decision": decision,
                    "reason": reason,
                }
            )

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01B"
        ),
        "mode": (
            "PLAN_ONLY"
        ),
        "workbook_modified": False,
        "source_report": str(
            GEOMETRY_REPORT
        ),
        "summary": {
            "macro10_button_count": len(
                buttons
            ),
            "geometry_group_count": len(
                groups
            ),
            "keep_count": keep_count,
            "remove_candidate_count": (
                remove_candidate_count
            ),
        },
        "items": manifest_items,
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

    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01B - "
        "MACRO10 BUTTON CLEANUP MANIFEST"
    )
    print("=" * 72)

    print(
        "Chế độ: PLAN ONLY"
    )

    print(
        "Workbook KHÔNG bị thay đổi."
    )

    print("\nKẾT QUẢ TỔNG HỢP")

    print(
        f"Button Macro10: "
        f"{len(buttons)}"
    )

    print(
        f"Nhóm hình học: "
        f"{len(groups)}"
    )

    print(
        f"KEEP: "
        f"{keep_count}"
    )

    print(
        f"REMOVE_CANDIDATE: "
        f"{remove_candidate_count}"
    )

    print(
        "\n20 NHÓM ĐẦU TIÊN"
    )

    shown_groups = set()

    for item in manifest_items:
        group_id = item["group_id"]

        if group_id in shown_groups:
            continue

        shown_groups.add(
            group_id
        )

        group_items = [
            x
            for x in manifest_items
            if x["group_id"]
            == group_id
        ]

        print(
            f"\n- {group_id}"
        )

        print(
            f"  Anchor: "
            f"{group_items[0]['anchor']}"
        )

        for group_item in (
            group_items
        ):
            print(
                f"    "
                f"{group_item['shape_id']} | "
                f"{group_item['decision']}"
            )

        if len(shown_groups) >= 20:
            break

    print(
        "\nĐã tạo manifest:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nKẾT QUẢ: "
        "MACRO10 CLEANUP MANIFEST COMPLETE"
    )


if __name__ == "__main__":
    main()