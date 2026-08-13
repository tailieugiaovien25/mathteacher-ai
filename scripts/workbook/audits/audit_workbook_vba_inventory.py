import json
import re
from collections import Counter
from pathlib import Path


SOURCE_FILE = Path(
    "output/reports/vba/workbook_vba_source_utf8.txt"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_vba_inventory_audit.json"
)


PROC_START_PATTERN = re.compile(
    r"^\s*(Public\s+|Private\s+|Friend\s+)?"
    r"(Sub|Function)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\(",
    flags=re.IGNORECASE,
)

PROC_END_PATTERN = re.compile(
    r"^\s*End\s+(Sub|Function)\s*$",
    flags=re.IGNORECASE,
)

MODULE_PATTERN = re.compile(
    r"^VBA MACRO (.+?)\s*$"
)

RANGE_PATTERN = re.compile(
    r'Range\("([^"]+)"\)',
    flags=re.IGNORECASE,
)


def extract_procedures(
    lines: list[str],
) -> list[dict]:
    procedures = []

    current_module = None
    current_proc = None

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        module_match = MODULE_PATTERN.match(
            line.strip()
        )

        if module_match:
            current_module = (
                module_match.group(1)
            )
            continue

        if current_proc is None:
            proc_match = (
                PROC_START_PATTERN.match(
                    line
                )
            )

            if proc_match:
                current_proc = {
                    "module": current_module,
                    "kind": (
                        proc_match.group(2)
                        .upper()
                    ),
                    "name": proc_match.group(3),
                    "start_line": line_number,
                    "end_line": None,
                    "lines": [line],
                }

            continue

        current_proc["lines"].append(
            line
        )

        if PROC_END_PATTERN.match(
            line
        ):
            current_proc[
                "end_line"
            ] = line_number

            procedures.append(
                current_proc
            )

            current_proc = None

    return procedures


def analyze_procedure(
    procedure: dict,
) -> dict:
    lines = procedure["lines"]

    source = "\n".join(
        lines
    )

    source_lower = (
        source.lower()
    )

    select_count = sum(
        1
        for line in lines
        if ".select" in line.lower()
    )

    paste_count = sum(
        1
        for line in lines
        if (
            ".paste" in line.lower()
            or "pastespecial"
            in line.lower()
        )
    )

    scroll_count = sum(
        1
        for line in lines
        if (
            "scrollrow" in line.lower()
            or "smallscroll"
            in line.lower()
        )
    )

    save_count = sum(
        1
        for line in lines
        if (
            ".save" in line.lower()
            or "saveas" in line.lower()
        )
    )

    caller_count = sum(
        1
        for line in lines
        if (
            "application.caller"
            in line.lower()
        )
    )

    onaction_count = sum(
        1
        for line in lines
        if "onaction" in line.lower()
    )

    active_sheet_count = sum(
        1
        for line in lines
        if "activesheet" in line.lower()
    )

    active_workbook_count = sum(
        1
        for line in lines
        if "activeworkbook" in line.lower()
    )

    range_refs = []

    suspicious_ranges = []

    for line_number, line in enumerate(
        lines,
        start=procedure["start_line"],
    ):
        for match in RANGE_PATTERN.finditer(
            line
        ):
            ref = match.group(1)

            range_refs.append(
                {
                    "line": line_number,
                    "reference": ref,
                }
            )

            two_cell_match = re.fullmatch(
                r"([A-Z]+)(\d+):"
                r"([A-Z]+)(\d+)",
                ref,
                flags=re.IGNORECASE,
            )

            if two_cell_match:
                row1 = int(
                    two_cell_match.group(2)
                )

                row2 = int(
                    two_cell_match.group(4)
                )

                if row1 > row2:
                    suspicious_ranges.append(
                        {
                            "line": (
                                line_number
                            ),
                            "reference": (
                                ref
                            ),
                            "reason": (
                                "START_ROW_GREATER_THAN_END_ROW"
                            ),
                        }
                    )

    macro_recorder_score = (
        select_count
        + paste_count
        + scroll_count
    )

    flags = []

    if caller_count:
        flags.append(
            "USES_APPLICATION_CALLER"
        )

    if save_count:
        flags.append(
            "SAVES_WORKBOOK"
        )

    if suspicious_ranges:
        flags.append(
            "SUSPICIOUS_RANGE"
        )

    if scroll_count >= 10:
        flags.append(
            "HEAVY_UI_SCROLLING"
        )

    if select_count >= 10:
        flags.append(
            "HEAVY_SELECT_USAGE"
        )

    if macro_recorder_score >= 20:
        flags.append(
            "LIKELY_MACRO_RECORDER_CODE"
        )

    return {
        "module": procedure["module"],
        "kind": procedure["kind"],
        "name": procedure["name"],
        "start_line": (
            procedure["start_line"]
        ),
        "end_line": (
            procedure["end_line"]
        ),
        "line_count": len(lines),
        "select_count": select_count,
        "paste_count": paste_count,
        "scroll_count": scroll_count,
        "save_count": save_count,
        "application_caller_count": (
            caller_count
        ),
        "onaction_count": (
            onaction_count
        ),
        "active_sheet_count": (
            active_sheet_count
        ),
        "active_workbook_count": (
            active_workbook_count
        ),
        "range_reference_count": (
            len(range_refs)
        ),
        "range_references": (
            range_refs
        ),
        "suspicious_ranges": (
            suspicious_ranges
        ),
        "flags": flags,
    }


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy VBA source: "
            f"{SOURCE_FILE}"
        )

    print("=" * 72)
    print(
        "M5-XLS-AUDIT-03C - "
        "VBA PROCEDURE INVENTORY"
    )
    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook gốc KHÔNG được truy cập "
        "hoặc thay đổi."
    )

    source = SOURCE_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = source.splitlines()

    procedures = extract_procedures(
        lines
    )

    analyses = [
        analyze_procedure(
            procedure
        )
        for procedure in procedures
    ]

    module_counts = Counter(
        item["module"]
        for item in analyses
    )

    flagged = [
        item
        for item in analyses
        if item["flags"]
    ]

    suspicious_range_procs = [
        item
        for item in analyses
        if item["suspicious_ranges"]
    ]

    save_procs = [
        item
        for item in analyses
        if item["save_count"] > 0
    ]

    caller_procs = [
        item
        for item in analyses
        if (
            item[
                "application_caller_count"
            ]
            > 0
        )
    ]

    macro_recorder_procs = [
        item
        for item in analyses
        if (
            "LIKELY_MACRO_RECORDER_CODE"
            in item["flags"]
        )
    ]

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-03C"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "source_file": str(
            SOURCE_FILE
        ),
        "summary": {
            "procedure_count": len(
                analyses
            ),
            "module_count": len(
                module_counts
            ),
            "flagged_procedure_count": (
                len(flagged)
            ),
            "save_procedure_count": (
                len(save_procs)
            ),
            "application_caller_procedure_count": (
                len(caller_procs)
            ),
            "suspicious_range_procedure_count": (
                len(
                    suspicious_range_procs
                )
            ),
            "likely_macro_recorder_count": (
                len(
                    macro_recorder_procs
                )
            ),
        },
        "module_counts": dict(
            module_counts
        ),
        "procedures": analyses,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 72)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        f"Tổng Sub/Function: "
        f"{len(analyses)}"
    )

    print(
        f"Số module có procedure: "
        f"{len(module_counts)}"
    )

    print(
        f"Procedure có cảnh báo: "
        f"{len(flagged)}"
    )

    print(
        f"Procedure có Save/SaveAs: "
        f"{len(save_procs)}"
    )

    print(
        "Procedure dùng "
        "Application.Caller: "
        f"{len(caller_procs)}"
    )

    print(
        "Procedure có Range đáng ngờ: "
        f"{len(suspicious_range_procs)}"
    )

    print(
        "Procedure có dấu hiệu "
        "Macro Recorder: "
        f"{len(macro_recorder_procs)}"
    )

    print(
        "\nPHÂN BỔ PROCEDURE THEO MODULE"
    )

    for module, count in (
        module_counts.items()
    ):
        print(
            f"- {module}: {count}"
        )

    if suspicious_range_procs:
        print(
            "\nRANGE ĐÁNG NGỜ"
        )

        for item in (
            suspicious_range_procs
        ):
            print(
                f"\n- {item['module']}."
                f"{item['name']}"
            )

            for problem in (
                item[
                    "suspicious_ranges"
                ]
            ):
                print(
                    f"    Line "
                    f"{problem['line']} | "
                    f"{problem['reference']} | "
                    f"{problem['reason']}"
                )

    if save_procs:
        print(
            "\nPROCEDURE CÓ LỆNH SAVE"
        )

        for item in save_procs:
            print(
                f"- {item['module']}."
                f"{item['name']} | "
                f"Save={item['save_count']}"
            )

    print(
        "\n20 PROCEDURE CÓ NHIỀU "
        "SELECT/SCROLL/PASTE NHẤT"
    )

    ranked = sorted(
        analyses,
        key=lambda item: (
            item["select_count"]
            + item["scroll_count"]
            + item["paste_count"]
        ),
        reverse=True,
    )

    for item in ranked[:20]:
        score = (
            item["select_count"]
            + item["scroll_count"]
            + item["paste_count"]
        )

        print(
            f"- {item['module']}."
            f"{item['name']} | "
            f"Lines={item['line_count']} | "
            f"Select={item['select_count']} | "
            f"Paste={item['paste_count']} | "
            f"Scroll={item['scroll_count']} | "
            f"Score={score}"
        )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nKẾT QUẢ: "
        "VBA PROCEDURE INVENTORY COMPLETE"
    )


if __name__ == "__main__":
    main()