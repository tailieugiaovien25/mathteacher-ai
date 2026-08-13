import argparse
import hashlib
import json
from pathlib import Path

from oletools.olevba import VBA_Parser


DEFAULT_WORKBOOK = Path(
    "data/working/LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

DEFAULT_OUTPUT = Path(
    "output/reports/vba/cleanup_working_vba_source_utf8.txt"
)

DEFAULT_REPORT = Path(
    "output/reports/vba/cleanup_working_vba_extraction.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Trích VBA source trực tiếp từ workbook XLSM."
        )
    )

    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook XLSM cần trích VBA.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="File TXT chứa VBA source.",
    )

    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    args = parse_args()

    workbook = args.workbook
    output = args.output

    if not workbook.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: {workbook}"
        )

    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01D2 - VBA SOURCE EXTRACTION"
    )
    print("=" * 72)

    print("Chế độ: READ ONLY")
    print("Workbook sẽ KHÔNG bị thay đổi.")
    print(f"Workbook: {workbook}")

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    parser = VBA_Parser(
        str(workbook)
    )

    modules = []
    source_blocks = []

    try:
        if not parser.detect_vba_macros():
            raise RuntimeError(
                "Workbook không phát hiện VBA macro."
            )

        for (
            filename,
            stream_path,
            vba_filename,
            vba_code,
        ) in parser.extract_macros():

            if isinstance(
                vba_code,
                bytes,
            ):
                source = vba_code.decode(
                    "utf-8",
                    errors="replace",
                )
            else:
                source = str(
                    vba_code
                )

            module_name = (
                vba_filename
                or stream_path
                or "UNKNOWN"
            )

            modules.append(
                {
                    "module": module_name,
                    "stream_path": stream_path,
                    "source_length": len(
                        source
                    ),
                }
            )

            source_blocks.append(
                "\n".join(
                    [
                        "",
                        "=" * 72,
                        f"VBA MACRO ({module_name})",
                        "=" * 72,
                        source.rstrip(),
                        "",
                    ]
                )
            )

    finally:
        parser.close()

    full_source = "\n".join(
        source_blocks
    )

    output.write_text(
        full_source,
        encoding="utf-8",
        newline="\n",
    )

    report = {
        "audit_id": (
            "M5-XLS-CLEANUP-01D2"
        ),
        "mode": "READ_ONLY",
        "workbook_modified": False,
        "workbook": str(
            workbook
        ),
        "workbook_sha256": sha256_file(
            workbook
        ),
        "output": str(
            output
        ),
        "module_count": len(
            modules
        ),
        "source_character_count": len(
            full_source
        ),
        "modules": modules,
    }

    DEFAULT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    DEFAULT_REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("KẾT QUẢ")
    print("=" * 72)

    print(
        f"Số VBA module trích được: "
        f"{len(modules)}"
    )

    print(
        f"Số ký tự VBA source: "
        f"{len(full_source)}"
    )

    print()
    print("VBA source:")
    print(output)

    print()
    print("Extraction report:")
    print(DEFAULT_REPORT)

    print()
    print(
        f"Workbook SHA256: "
        f"{report['workbook_sha256']}"
    )

    print()
    print(
        "Workbook KHÔNG bị thay đổi."
    )

    print()
    print(
        "KẾT QUẢ: VBA SOURCE EXTRACTION COMPLETE"
    )


if __name__ == "__main__":
    main()