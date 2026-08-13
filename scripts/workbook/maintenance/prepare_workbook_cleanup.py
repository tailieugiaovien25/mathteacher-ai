import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


SOURCE_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

WORKING_DIR = Path(
    "data/working"
)

BACKUP_DIR = Path(
    "data/backups"
)

REPORT_FILE = Path(
    "output/reports/workbook_cleanup_baseline.json"
)

WORKING_FILE = WORKING_DIR / (
    "LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

CREATE_COPIES = False


def sha256_file(path: Path) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def main() -> None:
    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01A - "
        "PREPARE CLEANUP WORKING COPY"
    )
    print("=" * 72)

    if not CREATE_COPIES:
        print(
            "CREATE_COPIES = False; "
            "không tạo backup hoặc working copy."
        )
        return

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook gốc: "
            f"{SOURCE_FILE}"
        )

    WORKING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Baseline file gốc
    # ---------------------------------------------------------

    source_hash_before = sha256_file(
        SOURCE_FILE
    )

    source_size = SOURCE_FILE.stat().st_size

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = BACKUP_DIR / (
        f"LBG-TUYEN_BASELINE_{timestamp}.xlsm"
    )

    # ---------------------------------------------------------
    # Không ghi đè working copy cũ
    # ---------------------------------------------------------

    if WORKING_FILE.exists():
        raise FileExistsError(
            "\nĐã tồn tại working copy:\n"
            f"{WORKING_FILE}\n\n"
            "Script dừng để tránh ghi đè "
            "một bản cleanup đang làm việc."
        )

    # ---------------------------------------------------------
    # Tạo backup + working copy
    # ---------------------------------------------------------

    shutil.copy2(
        SOURCE_FILE,
        backup_file,
    )

    shutil.copy2(
        SOURCE_FILE,
        WORKING_FILE,
    )

    # ---------------------------------------------------------
    # Kiểm tra checksum
    # ---------------------------------------------------------

    backup_hash = sha256_file(
        backup_file
    )

    working_hash = sha256_file(
        WORKING_FILE
    )

    source_hash_after = sha256_file(
        SOURCE_FILE
    )

    backup_match = (
        backup_hash == source_hash_before
    )

    working_match = (
        working_hash == source_hash_before
    )

    source_unchanged = (
        source_hash_after
        == source_hash_before
    )

    all_pass = (
        backup_match
        and working_match
        and source_unchanged
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01A"
        ),
        "created_at": (
            datetime.now().isoformat(
                timespec="seconds"
            )
        ),
        "source": {
            "path": str(
                SOURCE_FILE
            ),
            "size_bytes": (
                source_size
            ),
            "sha256_before": (
                source_hash_before
            ),
            "sha256_after": (
                source_hash_after
            ),
            "unchanged": (
                source_unchanged
            ),
        },
        "backup": {
            "path": str(
                backup_file
            ),
            "sha256": (
                backup_hash
            ),
            "matches_source": (
                backup_match
            ),
        },
        "working_copy": {
            "path": str(
                WORKING_FILE
            ),
            "sha256": (
                working_hash
            ),
            "matches_source": (
                working_match
            ),
        },
        "baseline_pass": (
            all_pass
        ),
    }

    REPORT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Terminal
    # ---------------------------------------------------------

    print(
        f"\nWorkbook gốc:\n"
        f"{SOURCE_FILE}"
    )

    print(
        f"\nBackup:\n"
        f"{backup_file}"
    )

    print(
        f"\nWorking copy:\n"
        f"{WORKING_FILE}"
    )

    print(
        "\nKIỂM TRA CHECKSUM"
    )

    print(
        "- Backup giống file gốc: "
        f"{'PASS' if backup_match else 'FAIL'}"
    )

    print(
        "- Working copy giống file gốc: "
        f"{'PASS' if working_match else 'FAIL'}"
    )

    print(
        "- File gốc không bị thay đổi: "
        f"{'PASS' if source_unchanged else 'FAIL'}"
    )

    print(
        "\nSHA256 BASELINE:"
    )

    print(
        source_hash_before
    )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        REPORT_FILE
    )

    if not all_pass:
        raise RuntimeError(
            "BASELINE CHECK FAILED - "
            "KHÔNG ĐƯỢC TIẾP TỤC CLEANUP."
        )

    print(
        "\nKẾT QUẢ: "
        "CLEANUP BASELINE ACCEPTED"
    )

    print(
        "\nTừ bước tiếp theo, CHỈ được sửa:"
    )

    print(
        WORKING_FILE
    )

    print(
        "\nKHÔNG sửa workbook gốc."
    )


if __name__ == "__main__":
    main()
