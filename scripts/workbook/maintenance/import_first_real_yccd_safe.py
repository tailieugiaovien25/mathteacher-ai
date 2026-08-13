import shutil
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, "src")

from models.yccd_record import YCCDRecord
from repositories.yccd_repository_v2 import (
    YCCDRepositoryV2,
)
from repositories.yccd_writer import (
    YCCDWriter,
)
from utils.yccd_provenance import (
    validate_provenance,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

BACKUP_DIR = Path(
    "output/backups"
)

# ============================================================
# AN TOÀN:
# True  = chỉ kiểm tra, KHÔNG ghi workbook thật.
# False = cho phép ghi.
# ============================================================

DRY_RUN = True


def build_records() -> list[YCCDRecord]:
    common = {
        "lesson_key": "T7_DAI_B03",
        "subject": "Toán",
        "grade": 7,
        "lesson_id": "B03",
        "lesson_name": (
            "Bài 3. Lũy thừa với số mũ tự nhiên "
            "của một số hữu tỉ"
        ),
        "version": "1.0",
        "status": "draft",
        "updated_at": date(
            2026,
            8,
            8,
        ),
    }

    return [
        YCCDRecord(
            **common,
            yccd_id="T7_DAI_B03_Y00",
            order=1,
            requirement=(
                "Mô tả được phép tính lũy thừa với số mũ "
                "tự nhiên của một số hữu tỉ và một số tính "
                "chất của phép tính đó, gồm tích và thương "
                "hai lũy thừa cùng cơ số, lũy thừa của "
                "lũy thừa."
            ),
            yccd_type="CHINH_THUC",
            source_yccd_id=None,
            source="CTGDPT_2018",
            reference=(
                "Toán 7 > Số và Đại số > "
                "Các phép tính với số hữu tỉ"
            ),
            note="YCCĐ cấp chương trình.",
        ),
        YCCDRecord(
            **common,
            yccd_id="T7_DAI_B03_Y01",
            order=2,
            requirement=(
                "Mô tả được phép tính lũy thừa với số mũ "
                "tự nhiên của một số hữu tỉ."
            ),
            yccd_type="TRIEN_KHAI",
            source_yccd_id=(
                "T7_DAI_B03_Y00"
            ),
            source="TONG_HOP",
            reference=(
                "CTGDPT_2018 + nội dung triển khai Bài 3"
            ),
            note="YCCĐ triển khai từ Y00.",
        ),
        YCCDRecord(
            **common,
            yccd_id="T7_DAI_B03_Y02",
            order=3,
            requirement=(
                "Mô tả và thực hiện được phép tính tích, "
                "thương của hai lũy thừa cùng cơ số."
            ),
            yccd_type="TRIEN_KHAI",
            source_yccd_id=(
                "T7_DAI_B03_Y00"
            ),
            source="TONG_HOP",
            reference=(
                "CTGDPT_2018 + nội dung triển khai Bài 3"
            ),
            note="YCCĐ triển khai từ Y00.",
        ),
        YCCDRecord(
            **common,
            yccd_id="T7_DAI_B03_Y03",
            order=4,
            requirement=(
                "Mô tả và thực hiện được phép tính "
                "lũy thừa của lũy thừa."
            ),
            yccd_type="TRIEN_KHAI",
            source_yccd_id=(
                "T7_DAI_B03_Y00"
            ),
            source="TONG_HOP",
            reference=(
                "CTGDPT_2018 + nội dung triển khai Bài 3"
            ),
            note="YCCĐ triển khai từ Y00.",
        ),
    ]


def make_backup() -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = (
        BACKUP_DIR
        / f"LBG-TUYEN_chuan_VBA_macro_BEFORE_YCCD_{timestamp}.xlsm"
    )

    shutil.copy2(
        EXCEL_FILE,
        backup_file,
    )

    return backup_file


def main() -> None:
    print("=" * 72)
    print(
        "LP-03D.3D.6 - "
        "SAFE FIRST REAL YCCD IMPORT"
    )
    print("=" * 72)

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: {EXCEL_FILE}"
        )

    records = build_records()

    # --------------------------------------------------------
    # 1. Validate model + provenance
    # --------------------------------------------------------

    validate_provenance(
        records
    )

    print(
        "- Validate 4 YCCDRecord: PASS"
    )

    print(
        "- Validate provenance: PASS"
    )

    # --------------------------------------------------------
    # 2. Kiểm tra workbook thật hiện tại
    # --------------------------------------------------------

    repository = YCCDRepositoryV2()

    existing_rows = repository.load_rows(
        EXCEL_FILE
    )

    print(
        f"- Số dòng YCCD hiện có: "
        f"{len(existing_rows)}"
    )

    existing_ids = {
        str(row.get("YCCD_ID")).strip()
        for row in existing_rows
        if row.get("YCCD_ID")
    }

    new_ids = {
        record.yccd_id
        for record in records
    }

    duplicated_ids = (
        existing_ids
        & new_ids
    )

    if duplicated_ids:
        raise ValueError(
            "Workbook đã có các YCCD_ID: "
            + ", ".join(
                sorted(
                    duplicated_ids
                )
            )
        )

    print(
        "- Không trùng YCCD_ID với workbook: PASS"
    )

    # --------------------------------------------------------
    # 3. DRY RUN
    # --------------------------------------------------------

    if DRY_RUN:
        print(
            "\nDRY_RUN = True"
        )

        print(
            "KHÔNG ghi bất kỳ dữ liệu nào "
            "vào workbook thật."
        )

        print(
            "\n4 RECORD SẼ ĐƯỢC GHI KHI "
            "DRY_RUN = False"
        )

        for record in records:
            print(
                f"- {record.yccd_id} | "
                f"{record.yccd_type} | "
                f"{record.status}"
            )

        print(
            "\nKẾT QUẢ: DRY RUN ACCEPTED"
        )

        return

    # --------------------------------------------------------
    # 4. BACKUP
    # --------------------------------------------------------

    backup_file = make_backup()

    print(
        f"- Backup: {backup_file}"
    )

    # --------------------------------------------------------
    # 5. GHI DỮ LIỆU
    # --------------------------------------------------------

    writer = YCCDWriter()

    written = writer.append_records(
        EXCEL_FILE,
        records,
    )

    if written != 4:
        raise RuntimeError(
            f"Số record ghi không đúng: {written}"
        )

    # --------------------------------------------------------
    # 6. ĐỌC LẠI VÀ XÁC MINH
    # --------------------------------------------------------

    saved_records = (
        repository.find_by_lesson_key(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
            status="draft",
        )
    )

    if len(saved_records) != 4:
        raise RuntimeError(
            "Đọc lại không đủ 4 YCCĐ draft."
        )

    saved_ids = [
        record.yccd_id
        for record in saved_records
    ]

    expected_ids = [
        "T7_DAI_B03_Y00",
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    ]

    if saved_ids != expected_ids:
        raise RuntimeError(
            "Thứ tự hoặc YCCD_ID đọc lại không đúng."
        )

    print(
        "- Ghi 4 YCCĐ thật: PASS"
    )

    print(
        "- Đọc lại 4 YCCĐ: PASS"
    )

    print(
        "\nKẾT QUẢ: REAL YCCD IMPORT ACCEPTED"
    )


if __name__ == "__main__":
    main()
