import re
from pathlib import Path


SOURCE_FILE = Path(
    r"output\reports\vba\workbook_vba_source_utf8.txt"
)

EVENT_NAMES = (
    "Workbook_Open",
    "Workbook_BeforeSave",
    "Workbook_AfterSave",
    "Workbook_BeforeClose",
    "Workbook_SheetChange",
    "Workbook_SheetCalculate",
    "Workbook_SheetSelectionChange",
    "Workbook_SheetActivate",
    "Worksheet_Change",
    "Worksheet_Calculate",
    "Worksheet_SelectionChange",
    "Worksheet_Activate",
    "Worksheet_Deactivate",
)


PROC_START = re.compile(
    r"^\s*"
    r"(?:Public\s+|Private\s+|Friend\s+)?"
    r"(Sub|Function)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\(",
    flags=re.IGNORECASE,
)

PROC_END = re.compile(
    r"^\s*End\s+(Sub|Function)\s*$",
    flags=re.IGNORECASE,
)

MODULE_HEADER = re.compile(
    r"^===\s*VBA MACRO\s+\((.+?)\)\s*===\s*$"
)


def extract_procedures(lines):
    procedures = []

    current_module = None
    current = None

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        module_match = MODULE_HEADER.match(
            line.strip()
        )

        if module_match:
            current_module = (
                module_match.group(1)
            )

        if current is None:
            match = PROC_START.match(line)

            if match:
                current = {
                    "module": current_module,
                    "kind": (
                        match.group(1)
                        .upper()
                    ),
                    "name": (
                        match.group(2)
                    ),
                    "start_line": (
                        line_number
                    ),
                    "end_line": None,
                    "lines": [line],
                }

            continue

        current["lines"].append(
            line
        )

        if PROC_END.match(line):
            current["end_line"] = (
                line_number
            )

            procedures.append(
                current
            )

            current = None

    return procedures


def is_event_procedure(name):
    lower_name = name.lower()

    for event_name in EVENT_NAMES:
        if (
            lower_name
            == event_name.lower()
        ):
            return True

    return False


def main():
    print("=" * 76)
    print(
        "M5-XLS-VBA-DIAG - "
        "WORKBOOK EVENT INVENTORY"
    )
    print("=" * 76)

    print(
        "Chế độ: READ ONLY"
    )

    print(
        "Workbook KHÔNG bị mở hoặc thay đổi."
    )

    print()

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy VBA source: "
            f"{SOURCE_FILE}"
        )

    text = SOURCE_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = text.splitlines()

    procedures = extract_procedures(
        lines
    )

    events = [
        proc
        for proc in procedures
        if is_event_procedure(
            proc["name"]
        )
    ]

    print(
        "Tổng procedure đọc được:",
        len(procedures),
    )

    print(
        "Event procedure phát hiện:",
        len(events),
    )

    print()

    if not events:
        print(
            "Không phát hiện event procedure "
            "trong VBA source."
        )

    for index, proc in enumerate(
        events,
        start=1,
    ):
        print("=" * 76)

        print(
            f"EVENT #{index}"
        )

        print(
            "Module:",
            proc["module"],
        )

        print(
            "Procedure:",
            proc["name"],
        )

        print(
            "Lines:",
            f"{proc['start_line']}-"
            f"{proc['end_line']}",
        )

        print("-" * 76)

        for line in proc["lines"]:
            print(line)

        print()

    print("=" * 76)
    print(
        "KẾT QUẢ: "
        "WORKBOOK EVENT INVENTORY COMPLETE"
    )
    print("=" * 76)

    print()

    print(
        "Workbook KHÔNG bị mở hoặc thay đổi."
    )


if __name__ == "__main__":
    main()