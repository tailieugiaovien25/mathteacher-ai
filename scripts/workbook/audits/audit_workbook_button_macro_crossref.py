import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BUTTON_REPORT = Path(
    "output/reports/workbook_button_groups_audit.json"
)

VBA_REPORT = Path(
    "output/reports/workbook_vba_function_map_audit.json"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_button_macro_crossref_audit.json"
)


MACRO_PATTERN = re.compile(
    r"Macro\d+",
    flags=re.IGNORECASE,
)


def normalize_macro_name(value: str) -> str:
    if not value:
        return ""

    match = MACRO_PATTERN.search(
        str(value)
    )

    if not match:
        return ""

    return match.group(0)


def main() -> None:
    if not BUTTON_REPORT.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {BUTTON_REPORT}"
        )

    if not VBA_REPORT.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {VBA_REPORT}"
        )

    print("=" * 72)
    print(
        "M5-XLS-AUDIT-03E - "
        "BUTTON / MACRO CROSS REFERENCE"
    )
    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook gốc KHÔNG bị thay đổi."
    )

    button_data = json.loads(
        BUTTON_REPORT.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    vba_data = json.loads(
        VBA_REPORT.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    # =========================================================
    # BUTTON -> MACRO
    # =========================================================

    action_counts = button_data.get(
        "action_counts",
        {},
    )

    button_macro_counts = Counter()

    raw_actions = defaultdict(list)

    for action, count in (
        action_counts.items()
    ):
        macro_name = normalize_macro_name(
            action
        )

        if not macro_name:
            continue

        button_macro_counts[
            macro_name.lower()
        ] += int(count)

        raw_actions[
            macro_name.lower()
        ].append(
            {
                "action": action,
                "count": int(count),
            }
        )

    # =========================================================
    # VBA PROCEDURES
    # =========================================================

    procedures = vba_data.get(
        "procedures",
        [],
    )

    proc_index = {}

    for proc in procedures:
        name = str(
            proc.get(
                "name",
                "",
            )
        )

        if not name:
            continue

        proc_index[
            name.lower()
        ] = proc

    all_macro_names = set(
        proc_index.keys()
    )

    called_macro_names = set(
        button_macro_counts.keys()
    )

    # =========================================================
    # ORPHAN / UNKNOWN
    # =========================================================

    orphan_candidates = sorted(
        all_macro_names
        - called_macro_names
    )

    unknown_button_macros = sorted(
        called_macro_names
        - all_macro_names
    )

    # =========================================================
    # CROSS REFERENCE
    # =========================================================

    crossref = []

    for macro_key in sorted(
        all_macro_names
        | called_macro_names
    ):
        proc = proc_index.get(
            macro_key
        )

        button_count = (
            button_macro_counts.get(
                macro_key,
                0,
            )
        )

        if proc is None:
            status = "UNKNOWN_MACRO"
            recommendation = (
                "REVIEW"
            )
            module = None
            features = []
            reasons = [
                "Button gọi macro nhưng không tìm thấy procedure trong VBA report"
            ]

        else:
            module = proc.get(
                "module"
            )

            recommendation = proc.get(
                "recommendation",
                "REVIEW",
            )

            features = proc.get(
                "features",
                [],
            )

            reasons = proc.get(
                "reasons",
                [],
            )

            if button_count == 0:
                status = (
                    "ORPHAN_CANDIDATE"
                )
            elif recommendation == "REWRITE":
                status = (
                    "USED_REWRITE"
                )
            elif recommendation == "KEEP_CANDIDATE":
                status = (
                    "USED_KEEP_CANDIDATE"
                )
            else:
                status = (
                    "USED_REVIEW"
                )

        crossref.append(
            {
                "macro": (
                    proc.get(
                        "name"
                    )
                    if proc
                    else macro_key
                ),
                "module": module,
                "button_count": (
                    button_count
                ),
                "status": status,
                "recommendation": (
                    recommendation
                ),
                "features": features,
                "reasons": reasons,
                "raw_actions": (
                    raw_actions.get(
                        macro_key,
                        [],
                    )
                ),
            }
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    status_counts = Counter(
        item["status"]
        for item in crossref
    )

    used_macros = [
        item
        for item in crossref
        if item["button_count"] > 0
    ]

    used_rewrite = [
        item
        for item in crossref
        if item["status"]
        == "USED_REWRITE"
    ]

    used_keep = [
        item
        for item in crossref
        if item["status"]
        == "USED_KEEP_CANDIDATE"
    ]

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-03E"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,

        "summary": {
            "vba_procedure_count": len(
                procedures
            ),
            "button_macro_count": len(
                called_macro_names
            ),
            "used_macro_count": len(
                used_macros
            ),
            "orphan_candidate_count": len(
                orphan_candidates
            ),
            "unknown_button_macro_count": len(
                unknown_button_macros
            ),
            "status_counts": dict(
                status_counts
            ),
        },

        "cross_reference": (
            crossref
        ),

        "orphan_candidates": (
            orphan_candidates
        ),

        "unknown_button_macros": (
            unknown_button_macros
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
        f"VBA procedure: "
        f"{len(procedures)}"
    )

    print(
        f"Macro được Button gọi: "
        f"{len(called_macro_names)}"
    )

    print(
        f"Macro thực sự đang được dùng: "
        f"{len(used_macros)}"
    )

    print(
        f"Macro không có Button gọi "
        f"(ORPHAN candidate): "
        f"{len(orphan_candidates)}"
    )

    print(
        f"Button gọi macro không tồn tại: "
        f"{len(unknown_button_macros)}"
    )

    print(
        "\nPHÂN LOẠI CROSS-REFERENCE"
    )

    for status, count in (
        status_counts.most_common()
    ):
        print(
            f"- {status}: "
            f"{count}"
        )

    print(
        "\nMACRO ĐƯỢC BUTTON GỌI NHIỀU NHẤT"
    )

    ranked_used = sorted(
        used_macros,
        key=lambda item: (
            item["button_count"]
        ),
        reverse=True,
    )

    for item in ranked_used[:30]:
        print(
            f"- {item['module']}."
            f"{item['macro']} | "
            f"Buttons="
            f"{item['button_count']} | "
            f"{item['status']} | "
            f"{item['recommendation']}"
        )

    if orphan_candidates:
        print(
            "\nMACRO MỒ CÔI CẦN KIỂM TRA"
        )

        for name in (
            orphan_candidates[:30]
        ):
            proc = proc_index.get(
                name
            )

            if proc:
                print(
                    f"- {proc.get('module')}."
                    f"{proc.get('name')} | "
                    f"{proc.get('recommendation')}"
                )

    if unknown_button_macros:
        print(
            "\nBUTTON GỌI MACRO "
            "KHÔNG TÌM THẤY TRONG VBA"
        )

        for name in (
            unknown_button_macros
        ):
            print(
                f"- {name}"
            )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nKẾT QUẢ: "
        "BUTTON / MACRO CROSS REFERENCE COMPLETE"
    )


if __name__ == "__main__":
    main()