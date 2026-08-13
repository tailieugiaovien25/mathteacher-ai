import json
import re
from collections import Counter, defaultdict
from pathlib import Path


SOURCE_FILE = Path(
    "output/reports/vba/workbook_vba_source_utf8.txt"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_vba_function_map_audit.json"
)


MODULE_PATTERN = re.compile(
    r"^VBA MACRO (.+?)\s*$"
)

PROC_START_PATTERN = re.compile(
    r"^\s*(?:Public\s+|Private\s+|Friend\s+)?"
    r"(Sub|Function)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\(",
    flags=re.IGNORECASE,
)

PROC_END_PATTERN = re.compile(
    r"^\s*End\s+(Sub|Function)\s*$",
    flags=re.IGNORECASE,
)

RANGE_PATTERN = re.compile(
    r'Range\("([^"]+)"\)',
    flags=re.IGNORECASE,
)

CELLS_PATTERN = re.compile(
    r"Cells\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)",
    flags=re.IGNORECASE,
)

MACRO_NAME_PATTERN = re.compile(
    r"^Macro\d+$",
    flags=re.IGNORECASE,
)


def extract_procedures(lines):
    procedures = []

    current_module = None
    current = None

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        module_match = MODULE_PATTERN.match(
            line.strip()
        )

        if module_match:
            current_module = module_match.group(1)
            continue

        if current is None:
            proc_match = PROC_START_PATTERN.match(
                line
            )

            if proc_match:
                current = {
                    "module": current_module,
                    "kind": proc_match.group(1).upper(),
                    "name": proc_match.group(2),
                    "start_line": line_number,
                    "lines": [line],
                }

            continue

        current["lines"].append(line)

        if PROC_END_PATTERN.match(line):
            current["end_line"] = line_number

            procedures.append(current)

            current = None

    return procedures


def analyze(proc):
    source = "\n".join(
        proc["lines"]
    )

    lower = source.lower()

    ranges = RANGE_PATTERN.findall(
        source
    )

    cells = CELLS_PATTERN.findall(
        source
    )

    select_count = lower.count(
        ".select"
    )

    paste_count = (
        lower.count(".paste")
        + lower.count("pastespecial")
    )

    copy_count = lower.count(
        ".copy"
    )

    scroll_count = (
        lower.count("scrollrow")
        + lower.count("smallscroll")
    )

    save_count = (
        lower.count(".save")
        + lower.count("saveas")
    )

    activate_count = lower.count(
        ".activate"
    )

    active_sheet_count = lower.count(
        "activesheet"
    )

    active_workbook_count = lower.count(
        "activeworkbook"
    )

    caller_count = lower.count(
        "application.caller"
    )

    delete_count = lower.count(
        ".delete"
    )

    clear_count = (
        lower.count(".clear")
        + lower.count("clearcontents")
    )

    print_count = (
        lower.count("printout")
        + lower.count("printpreview")
    )

    # -----------------------------------------
    # RANGE đáng ngờ
    # -----------------------------------------

    suspicious_ranges = []

    for ref in ranges:
        match = re.fullmatch(
            r"([A-Z]+)(\d+):([A-Z]+)(\d+)",
            ref,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        row1 = int(match.group(2))
        row2 = int(match.group(4))

        if row1 > row2:
            suspicious_ranges.append(
                ref
            )

    # -----------------------------------------
    # PHÂN LOẠI CHỨC NĂNG SƠ BỘ
    # -----------------------------------------

    features = []

    if copy_count or paste_count:
        features.append(
            "COPY_PASTE"
        )

    if scroll_count:
        features.append(
            "UI_SCROLL"
        )

    if select_count:
        features.append(
            "SELECT_BASED"
        )

    if save_count:
        features.append(
            "SAVE_WORKBOOK"
        )

    if print_count:
        features.append(
            "PRINT"
        )

    if delete_count:
        features.append(
            "DELETE"
        )

    if clear_count:
        features.append(
            "CLEAR"
        )

    if caller_count:
        features.append(
            "APPLICATION_CALLER"
        )

    if active_sheet_count:
        features.append(
            "ACTIVE_SHEET"
        )

    if active_workbook_count:
        features.append(
            "ACTIVE_WORKBOOK"
        )

    if suspicious_ranges:
        features.append(
            "SUSPICIOUS_RANGE"
        )

    # -----------------------------------------
    # ĐỀ XUẤT PHÂN LOẠI
    # -----------------------------------------

    recommendation = "REVIEW"

    reasons = []

    recorder_score = (
        select_count
        + paste_count
        + scroll_count
    )

    if suspicious_ranges:
        recommendation = "REWRITE"

        reasons.append(
            "Có Range đảo hàng"
        )

    elif (
        recorder_score >= 20
        or scroll_count >= 10
        or select_count >= 10
    ):
        recommendation = "REWRITE"

        reasons.append(
            "Mã Macro Recorder dài/phụ thuộc giao diện"
        )

    elif (
        len(proc["lines"]) <= 20
        and recorder_score < 5
        and not suspicious_ranges
    ):
        recommendation = "KEEP_CANDIDATE"

        reasons.append(
            "Procedure ngắn và ít phụ thuộc UI"
        )

    else:
        reasons.append(
            "Cần kiểm tra thêm chức năng nghiệp vụ"
        )

    if save_count:
        reasons.append(
            "Có lệnh Save/SaveAs cần chuẩn hóa"
        )

    if caller_count:
        reasons.append(
            "Phụ thuộc Application.Caller"
        )

    # -----------------------------------------
    # Chữ ký logic sơ bộ
    # -----------------------------------------

    logic_signature = {
        "copy": bool(copy_count),
        "paste": bool(paste_count),
        "scroll": bool(scroll_count),
        "save": bool(save_count),
        "print": bool(print_count),
        "delete": bool(delete_count),
        "clear": bool(clear_count),
        "caller": bool(caller_count),
    }

    return {
        "module": proc["module"],
        "kind": proc["kind"],
        "name": proc["name"],
        "start_line": proc["start_line"],
        "end_line": proc.get(
            "end_line"
        ),
        "line_count": len(
            proc["lines"]
        ),

        "range_count": len(ranges),
        "ranges": ranges,

        "cells_count": len(cells),
        "cells": [
            {
                "row": int(row),
                "column": int(column),
            }
            for row, column in cells
        ],

        "copy_count": copy_count,
        "paste_count": paste_count,
        "select_count": select_count,
        "scroll_count": scroll_count,
        "save_count": save_count,
        "activate_count": activate_count,
        "active_sheet_count": (
            active_sheet_count
        ),
        "active_workbook_count": (
            active_workbook_count
        ),
        "application_caller_count": (
            caller_count
        ),
        "delete_count": delete_count,
        "clear_count": clear_count,
        "print_count": print_count,

        "features": features,
        "logic_signature": (
            logic_signature
        ),

        "suspicious_ranges": (
            suspicious_ranges
        ),

        "recommendation": (
            recommendation
        ),

        "reasons": reasons,
    }


def signature_key(item):
    signature = item[
        "logic_signature"
    ]

    return tuple(
        sorted(
            signature.items()
        )
    )


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {SOURCE_FILE}"
        )

    print("=" * 72)
    print(
        "M5-XLS-AUDIT-03D - "
        "VBA FUNCTION MAP"
    )
    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook gốc KHÔNG bị thay đổi."
    )

    source = SOURCE_FILE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    lines = source.splitlines()

    procedures = extract_procedures(
        lines
    )

    analyses = [
        analyze(proc)
        for proc in procedures
    ]

    # -----------------------------------------
    # Recommendation
    # -----------------------------------------

    recommendation_counts = Counter(
        item["recommendation"]
        for item in analyses
    )

    # -----------------------------------------
    # Feature
    # -----------------------------------------

    feature_counts = Counter()

    for item in analyses:
        feature_counts.update(
            item["features"]
        )

    # -----------------------------------------
    # Nhóm theo chữ ký logic
    # -----------------------------------------

    signature_groups = defaultdict(
        list
    )

    for item in analyses:
        signature_groups[
            signature_key(item)
        ].append(item)

    repeated_logic_groups = [
        items
        for items in signature_groups.values()
        if len(items) > 1
    ]

    repeated_logic_groups.sort(
        key=len,
        reverse=True,
    )

    # -----------------------------------------
    # MacroN
    # -----------------------------------------

    numbered_macros = [
        item
        for item in analyses
        if MACRO_NAME_PATTERN.match(
            item["name"]
        )
    ]

    # -----------------------------------------
    # Report
    # -----------------------------------------

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-03D"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,

        "summary": {
            "procedure_count": len(
                analyses
            ),
            "numbered_macro_count": len(
                numbered_macros
            ),
            "recommendation_counts": dict(
                recommendation_counts
            ),
            "feature_counts": dict(
                feature_counts
            ),
            "repeated_logic_group_count": len(
                repeated_logic_groups
            ),
        },

        "procedures": analyses,

        "repeated_logic_groups": [
            {
                "count": len(items),
                "procedures": [
                    {
                        "module": item[
                            "module"
                        ],
                        "name": item[
                            "name"
                        ],
                        "line_count": item[
                            "line_count"
                        ],
                        "ranges": item[
                            "ranges"
                        ][:10],
                        "recommendation": item[
                            "recommendation"
                        ],
                    }
                    for item in items
                ],
            }
            for items in repeated_logic_groups
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

    # -----------------------------------------
    # Terminal
    # -----------------------------------------

    print("\n" + "=" * 72)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        f"Tổng procedure: "
        f"{len(analyses)}"
    )

    print(
        f"MacroN phát hiện: "
        f"{len(numbered_macros)}"
    )

    print(
        "\nPHÂN LOẠI SƠ BỘ"
    )

    for key in [
        "KEEP_CANDIDATE",
        "REWRITE",
        "REVIEW",
    ]:
        print(
            f"- {key}: "
            f"{recommendation_counts.get(key, 0)}"
        )

    print(
        "\nĐẶC ĐIỂM VBA"
    )

    for feature, count in (
        feature_counts.most_common()
    ):
        print(
            f"- {feature}: {count}"
        )

    print(
        "\nSỐ NHÓM CÓ CHỮ KÝ LOGIC LẶP: "
        f"{len(repeated_logic_groups)}"
    )

    print(
        "\n10 NHÓM LOGIC LẶP LỚN NHẤT"
    )

    for index, items in enumerate(
        repeated_logic_groups[:10],
        start=1,
    ):
        print(
            f"\nNhóm {index}: "
            f"{len(items)} procedure"
        )

        for item in items[:20]:
            first_range = (
                item["ranges"][0]
                if item["ranges"]
                else "-"
            )

            print(
                f"  - "
                f"{item['module']}."
                f"{item['name']} | "
                f"Lines={item['line_count']} | "
                f"Range đầu={first_range} | "
                f"{item['recommendation']}"
            )

    print(
        "\nCÁC PROCEDURE CẦN VIẾT LẠI"
    )

    rewrite_items = [
        item
        for item in analyses
        if item[
            "recommendation"
        ] == "REWRITE"
    ]

    for item in rewrite_items[:30]:
        print(
            f"- {item['module']}."
            f"{item['name']} | "
            f"Lines={item['line_count']} | "
            f"Select={item['select_count']} | "
            f"Paste={item['paste_count']} | "
            f"Scroll={item['scroll_count']} | "
            f"Save={item['save_count']}"
        )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nKẾT QUẢ: "
        "VBA FUNCTION MAP COMPLETE"
    )


if __name__ == "__main__":
    main()