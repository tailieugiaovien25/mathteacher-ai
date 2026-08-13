import json
from collections import defaultdict
from pathlib import Path


MANIFEST_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)

GEOMETRY_REPORT = Path(
    "output/reports/workbook_button_geometry_audit.json"
)

OUTPUT_FILE = Path(
    "output/reports/macro10_cleanup_manifest_validation.json"
)


def main() -> None:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy manifest: {MANIFEST_FILE}"
        )

    if not GEOMETRY_REPORT.exists():
        raise FileNotFoundError(
            f"Không tìm thấy geometry report: {GEOMETRY_REPORT}"
        )

    manifest = json.loads(
        MANIFEST_FILE.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    geometry = json.loads(
        GEOMETRY_REPORT.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    items = manifest.get(
        "items",
        [],
    )

    source_buttons = geometry.get(
        "macro10_buttons",
        [],
    )

    # =========================================================
    # INDEX SOURCE BUTTONS
    # =========================================================

    source_by_shape = {}

    for button in source_buttons:
        shape_id = button.get(
            "shape_id"
        )

        if shape_id:
            source_by_shape[
                shape_id
            ] = button

    # =========================================================
    # GROUP MANIFEST
    # =========================================================

    groups = defaultdict(list)

    for item in items:
        groups[
            item.get("group_id")
        ].append(item)

    invalid_groups = []

    action_mismatch = []

    caption_mismatch = []

    geometry_mismatch = []

    missing_source_shape = []

    keep_count = 0

    remove_count = 0

    seen_shapes = set()

    duplicate_shapes = []

    # =========================================================
    # VALIDATE EACH GROUP
    # =========================================================

    for group_id, group_items in (
        groups.items()
    ):
        keep_items = [
            item
            for item in group_items
            if item.get(
                "decision"
            ) == "KEEP"
        ]

        remove_items = [
            item
            for item in group_items
            if item.get(
                "decision"
            )
            == "REMOVE_CANDIDATE"
        ]

        keep_count += len(
            keep_items
        )

        remove_count += len(
            remove_items
        )

        # Mỗi group phải có đúng 1 KEEP.
        if len(keep_items) != 1:
            invalid_groups.append(
                {
                    "group_id": group_id,
                    "reason": (
                        "KEEP_COUNT_NOT_EQUAL_1"
                    ),
                    "keep_count": len(
                        keep_items
                    ),
                    "item_count": len(
                        group_items
                    ),
                }
            )

        # -----------------------------------------
        # Shape ID phải tồn tại và không bị lặp.
        # -----------------------------------------

        for item in group_items:
            shape_id = item.get(
                "shape_id"
            )

            if not shape_id:
                invalid_groups.append(
                    {
                        "group_id": (
                            group_id
                        ),
                        "reason": (
                            "MISSING_SHAPE_ID"
                        ),
                    }
                )

                continue

            if shape_id in seen_shapes:
                duplicate_shapes.append(
                    shape_id
                )

            seen_shapes.add(
                shape_id
            )

            if shape_id not in (
                source_by_shape
            ):
                missing_source_shape.append(
                    {
                        "group_id": (
                            group_id
                        ),
                        "shape_id": (
                            shape_id
                        ),
                    }
                )

        if not group_items:
            continue

        # -----------------------------------------
        # Trong cùng group:
        # Action phải giống nhau.
        # -----------------------------------------

        actions = {
            str(
                item.get(
                    "action"
                )
                or ""
            )
            for item in group_items
        }

        if len(actions) != 1:
            action_mismatch.append(
                {
                    "group_id": (
                        group_id
                    ),
                    "actions": sorted(
                        actions
                    ),
                }
            )

        # -----------------------------------------
        # Caption phải giống nhau.
        # -----------------------------------------

        captions = {
            str(
                item.get(
                    "caption"
                )
                or ""
            )
            for item in group_items
        }

        if len(captions) != 1:
            caption_mismatch.append(
                {
                    "group_id": (
                        group_id
                    ),
                    "captions": sorted(
                        captions
                    ),
                }
            )

        # -----------------------------------------
        # Geometry phải giống nhau.
        # -----------------------------------------

        geometries = {
            (
                item.get(
                    "anchor"
                )
                or "",
                item.get(
                    "left"
                )
                or "",
                item.get(
                    "top"
                )
                or "",
                item.get(
                    "width"
                )
                or "",
                item.get(
                    "height"
                )
                or "",
            )
            for item in group_items
        }

        if len(geometries) != 1:
            geometry_mismatch.append(
                {
                    "group_id": (
                        group_id
                    ),
                    "geometry_count": (
                        len(
                            geometries
                        )
                    ),
                }
            )

    # =========================================================
    # GLOBAL VALIDATION
    # =========================================================

    unexpected_decisions = [
        item
        for item in items
        if item.get(
            "decision"
        )
        not in {
            "KEEP",
            "REMOVE_CANDIDATE",
        }
    ]

    expected_final_button_count = (
        120 - remove_count
    )

    validation_pass = (
        len(items) == 70
        and len(groups) == 24
        and keep_count == 24
        and remove_count == 46
        and len(invalid_groups) == 0
        and len(action_mismatch) == 0
        and len(caption_mismatch) == 0
        and len(geometry_mismatch) == 0
        and len(missing_source_shape) == 0
        and len(duplicate_shapes) == 0
        and len(unexpected_decisions) == 0
        and len(seen_shapes) == 70
    )

    # =========================================================
    # REPORT
    # =========================================================

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01B2"
        ),
        "mode": (
            "VALIDATE_ONLY"
        ),
        "workbook_modified": False,

        "summary": {
            "manifest_items": len(
                items
            ),
            "groups": len(
                groups
            ),
            "keep_count": (
                keep_count
            ),
            "remove_candidate_count": (
                remove_count
            ),
            "invalid_groups": len(
                invalid_groups
            ),
            "action_mismatch": len(
                action_mismatch
            ),
            "caption_mismatch": len(
                caption_mismatch
            ),
            "geometry_mismatch": len(
                geometry_mismatch
            ),
            "missing_source_shape": len(
                missing_source_shape
            ),
            "duplicate_shape_id": len(
                duplicate_shapes
            ),
            "unexpected_decision": len(
                unexpected_decisions
            ),
            "expected_final_button_count": (
                expected_final_button_count
            ),
            "validation_pass": (
                validation_pass
            ),
        },

        "invalid_groups": (
            invalid_groups
        ),

        "action_mismatch": (
            action_mismatch
        ),

        "caption_mismatch": (
            caption_mismatch
        ),

        "geometry_mismatch": (
            geometry_mismatch
        ),

        "missing_source_shape": (
            missing_source_shape
        ),

        "duplicate_shape_ids": (
            duplicate_shapes
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
    # TERMINAL
    # =========================================================

    print("=" * 72)

    print(
        "M5-XLS-CLEANUP-01B2 - "
        "MACRO10 MANIFEST VALIDATION"
    )

    print("=" * 72)

    print(
        "Chế độ: VALIDATE ONLY"
    )

    print(
        "Workbook KHÔNG bị thay đổi."
    )

    print(
        "\nKẾT QUẢ TỔNG HỢP"
    )

    print(
        f"Manifest items: "
        f"{len(items)}"
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
        f"{remove_count}"
    )

    print(
        f"Invalid groups: "
        f"{len(invalid_groups)}"
    )

    print(
        f"Action mismatch: "
        f"{len(action_mismatch)}"
    )

    print(
        f"Caption mismatch: "
        f"{len(caption_mismatch)}"
    )

    print(
        f"Geometry mismatch: "
        f"{len(geometry_mismatch)}"
    )

    print(
        f"Missing source shape: "
        f"{len(missing_source_shape)}"
    )

    print(
        f"Duplicate Shape ID: "
        f"{len(duplicate_shapes)}"
    )

    print(
        f"Unexpected decision: "
        f"{len(unexpected_decisions)}"
    )

    print(
        "\nDỰ KIẾN SAU CLEANUP"
    )

    print(
        f"Button hiện tại: 120"
    )

    print(
        f"Button dự kiến loại: "
        f"{remove_count}"
    )

    print(
        f"Button dự kiến còn lại: "
        f"{expected_final_button_count}"
    )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    if validation_pass:
        print(
            "\nKẾT QUẢ: "
            "MANIFEST VALIDATED"
        )
    else:
        print(
            "\nKẾT QUẢ: "
            "MANIFEST VALIDATION FAILED"
        )

        raise RuntimeError(
            "Manifest chưa đủ an toàn "
            "để thực hiện cleanup."
        )


if __name__ == "__main__":
    main()