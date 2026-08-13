import re
from pathlib import Path


VBA_SOURCE = Path(
    r"output\reports\vba\workbook_vba_source_utf8.txt"
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

SAVE_PATTERN = re.compile(
    r"\.Save\b",
    flags=re.IGNORECASE,
)


def extract_procedures(lines):
    procedures = []

    current_module = None
    current_proc = None

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

        if current_proc is None:
            proc_match = PROC_START.match(
                line
            )

            if proc_match:
                current_proc = {
                    "module": current_module,
                    "kind": (
                        proc_match.group(1)
                        .upper()
                    ),
                    "name": (
                        proc_match.group(2)
                    ),
                    "start_line": (
                        line_number
                    ),
                    "end_line": None,
                    "lines": [],
                }

        if current_proc is not None:
            current_proc[
                "lines"
            ].append(
                {
                    "line_number": (
                        line_number
                    ),
                    "text": line,
                }
            )

            if PROC_END.match(
                line
            ):
                current_proc[
                    "end_line"
                ] = (
                    line_number
                )

                procedures.append(
                    current_proc
                )

                current_proc = None

    return procedures


def main():
    print("=" * 76)
    print(
        "M5-XLS-VBA-DIAG-02 - "
        "VBA SAVE CALL INVENTORY"
    )
    print("=" * 76)

    print("Chế độ: READ ONLY")
    print("Workbook KHÔNG bị mở hoặc thay đổi.")
    print()

    if not VBA_SOURCE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy VBA source: "
            f"{VBA_SOURCE}"
        )

    text = VBA_SOURCE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = text.splitlines()

    procedures = extract_procedures(
        lines
    )

    save_hits = []

    for proc in procedures:
        for item in proc[
            "lines"
        ]:
            line = item[
                "text"
            ]

            if not SAVE_PATTERN.search(
                line
            ):
                continue

            save_hits.append(
                {
                    "module": (
                        proc[
                            "module"
                        ]
                    ),
                    "procedure": (
                        proc[
                            "name"
                        ]
                    ),
                    "proc_start": (
                        proc[
                            "start_line"
                        ]
                    ),
                    "proc_end": (
                        proc[
                            "end_line"
                        ]
                    ),
                    "line_number": (
                        item[
                            "line_number"
                        ]
                    ),
                    "line": line,
                    "procedure_lines": (
                        proc[
                            "lines"
                        ]
                    ),
                }
            )

    print(
        "Tổng procedure:",
        len(procedures),
    )

    print(
        "Tổng .Save phát hiện:",
        len(save_hits),
    )

    print()

    for index, hit in enumerate(
        save_hits,
        start=1,
    ):
        print("=" * 76)
        print(
            f"SAVE CALL #{index}"
        )
        print("=" * 76)

        print(
            "Module:",
            hit[
                "module"
            ],
        )

        print(
            "Procedure:",
            hit[
                "procedure"
            ],
        )

        print(
            "Procedure lines:",
            f"{hit['proc_start']}-"
            f"{hit['proc_end']}",
        )

        print(
            "Save line:",
            hit[
                "line_number"
            ],
        )

        print(
            "Statement:",
            hit[
                "line"
            ].strip(),
        )

        print()
        print(
            "CONTEXT:"
        )
        print("-" * 76)

        proc_lines = hit[
            "procedure_lines"
        ]

        save_index = None

        for i, item in enumerate(
            proc_lines
        ):
            if (
                item[
                    "line_number"
                ]
                == hit[
                    "line_number"
                ]
            ):
                save_index = i
                break

        if save_index is None:
            continue

        context_start = max(
            0,
            save_index - 8,
        )

        context_end = min(
            len(proc_lines),
            save_index + 9,
        )

        for item in proc_lines[
            context_start:
            context_end
        ]:
            marker = (
                ">>>"
                if (
                    item[
                        "line_number"
                    ]
                    == hit[
                        "line_number"
                    ]
                )
                else "   "
            )

            print(
                marker,
                f"{item['line_number']:5d}:",
                item[
                    "text"
                ],
            )

        print()

    print("=" * 76)

    if len(save_hits) == 6:
        print(
            "RESULT: PASS - "
            "FOUND EXACTLY 6 SAVE CALLS"
        )
    else:
        print(
            "RESULT: REVIEW REQUIRED - "
            f"FOUND {len(save_hits)} SAVE CALLS"
        )

    print("=" * 76)

    print()
    print(
        "Workbook KHÔNG bị mở hoặc thay đổi."
    )


if __name__ == "__main__":
    main()
