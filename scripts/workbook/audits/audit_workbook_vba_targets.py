import json
import re
import zipfile
from pathlib import Path


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_vba_targets_audit.json"
)

TARGET_TERMS = [
    "Macro7",
    "Macro07",
    "Macro8",
    "Macro08",
    "Macro9",
    "Macro09",
    "Macro10",
    "Macro11",
    "Application.Caller",
    "Caller",
    "Shapes",
    "Buttons",
    "OnAction",
    "TKB-Q",
]


def read_vba_binary(
    file_path: Path,
) -> bytes:
    with zipfile.ZipFile(
        file_path,
        "r",
    ) as archive:
        try:
            return archive.read(
                "xl/vbaProject.bin"
            )
        except KeyError as exc:
            raise RuntimeError(
                "Workbook không có vbaProject.bin"
            ) from exc


def extract_ascii_strings(
    data: bytes,
    min_length: int = 4,
) -> list[str]:
    pattern = re.compile(
        rb"[\x20-\x7E]{"
        + str(min_length).encode()
        + rb",}"
    )

    return [
        item.decode(
            "latin-1",
            errors="replace",
        )
        for item in pattern.findall(
            data
        )
    ]


def extract_utf16le_strings(
    data: bytes,
    min_length: int = 4,
) -> list[str]:
    pattern = re.compile(
        rb"(?:[\x20-\x7E]\x00){"
        + str(min_length).encode()
        + rb",}"
    )

    result = []

    for item in pattern.findall(
        data
    ):
        try:
            result.append(
                item.decode(
                    "utf-16le",
                    errors="replace",
                )
            )
        except UnicodeDecodeError:
            pass

    return result


def find_hits(
    strings: list[str],
    term: str,
) -> list[dict]:
    hits = []

    term_lower = term.lower()

    for index, value in enumerate(
        strings
    ):
        if term_lower in value.lower():
            start = max(
                0,
                index - 3,
            )

            end = min(
                len(strings),
                index + 4,
            )

            hits.append(
                {
                    "index": index,
                    "value": value,
                    "context": strings[
                        start:end
                    ],
                }
            )

    return hits


def main() -> None:
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: "
            f"{EXCEL_FILE}"
        )

    print("=" * 72)
    print(
        "M5-XLS-AUDIT-03A - "
        "TARGETED VBA AUDIT"
    )
    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook và VBA sẽ KHÔNG bị thay đổi."
    )

    vba_data = read_vba_binary(
        EXCEL_FILE
    )

    ascii_strings = (
        extract_ascii_strings(
            vba_data
        )
    )

    utf16_strings = (
        extract_utf16le_strings(
            vba_data
        )
    )

    combined_strings = (
        ascii_strings
        + utf16_strings
    )

    term_results = {}

    for term in TARGET_TERMS:
        hits = find_hits(
            combined_strings,
            term,
        )

        term_results[
            term
        ] = hits

    macro_names = sorted(
        {
            match.group(0)
            for value in combined_strings
            for match in re.finditer(
                r"\bMacro\d+\b",
                value,
                flags=re.IGNORECASE,
            )
        },
        key=lambda value: (
            len(value),
            value.lower(),
        ),
    )

    report = {
        "audit_id": (
            "M5-XLS-AUDIT-03A"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "workbook": str(
            EXCEL_FILE
        ),
        "vba_project_size_bytes": len(
            vba_data
        ),
        "ascii_string_count": len(
            ascii_strings
        ),
        "utf16_string_count": len(
            utf16_strings
        ),
        "detected_macro_names": (
            macro_names
        ),
        "target_terms": (
            term_results
        ),
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
        "Kích thước vbaProject.bin: "
        f"{len(vba_data)} bytes"
    )

    print(
        "ASCII strings đọc được: "
        f"{len(ascii_strings)}"
    )

    print(
        "UTF-16 strings đọc được: "
        f"{len(utf16_strings)}"
    )

    print(
        "Số tên MacroN phát hiện: "
        f"{len(macro_names)}"
    )

    print(
        "\nCÁC TỪ KHÓA MỤC TIÊU"
    )

    for term in TARGET_TERMS:
        hits = term_results[
            term
        ]

        print(
            f"- {term}: "
            f"{len(hits)}"
        )

    print(
        "\n30 TÊN MACRO ĐẦU TIÊN"
    )

    for macro_name in macro_names[:30]:
        print(
            f"- {macro_name}"
        )

    important_terms = [
        "Macro10",
        "Application.Caller",
        "Caller",
        "Shapes",
        "Buttons",
        "OnAction",
        "TKB-Q",
    ]

    print(
        "\nCHI TIẾT TỪ KHÓA QUAN TRỌNG"
    )

    for term in important_terms:
        hits = term_results.get(
            term,
            [],
        )

        if not hits:
            continue

        print(
            f"\n[{term}]"
        )

        for hit in hits[:10]:
            print(
                f"- {hit['value']!r}"
            )

            for context_item in (
                hit["context"]
            ):
                print(
                    f"    {context_item!r}"
                )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nWorkbook/VBA gốc "
        "KHÔNG bị thay đổi."
    )

    print(
        "\nKẾT QUẢ: "
        "TARGETED VBA AUDIT COMPLETE"
    )


if __name__ == "__main__":
    main()