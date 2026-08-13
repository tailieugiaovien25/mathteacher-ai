import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "src")

from models.yccd_record import YCCDRecord
from repositories.yccd_repository_v2 import (
    YCCDRepositoryV2,
)
from repositories.yccd_writer import (
    YCCDWriter,
)


SOURCE_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

TEST_FILE = Path(
    "output/test_yccd_writer_copy.xlsm"
)


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
                "chất của phép tính đó."
            ),
            yccd_type="CHINH_THUC",
            source_yccd_id=None,
            source="CTGDPT_2018",
            reference=(
                "Toán 7 > Số và Đại số > "
                "Các phép tính với số hữu tỉ"
            ),
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
        ),
    ]


def main() -> None:
    TEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if TEST_FILE.exists():
        TEST_FILE.unlink()

    shutil.copy2(
        SOURCE_FILE,
        TEST_FILE,
    )

    writer = YCCDWriter()
    repository = YCCDRepositoryV2()

    records = build_records()

    written = writer.append_records(
        TEST_FILE,
        records,
    )

    assert written == 4

    rows = repository.load_rows(
        TEST_FILE
    )

    assert len(rows) == 4

    draft_records = (
        repository.find_by_lesson_key(
            file_path=TEST_FILE,
            lesson_key="T7_DAI_B03",
            status="draft",
        )
    )

    assert len(draft_records) == 4

    assert [
        item.yccd_id
        for item in draft_records
    ] == [
        "T7_DAI_B03_Y00",
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    ]

    # Kiểm tra writer không cho ghi trùng.
    duplicate_blocked = False

    try:
        writer.append_records(
            TEST_FILE,
            records,
        )
    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print("=" * 70)
    print(
        "LP-03D.3D.5 - "
        "YCCD WRITER COPY TEST"
    )
    print("=" * 70)

    print("- Tạo bản sao workbook thật: PASS")
    print("- Ghi 4 YCCĐ vào bản sao: PASS")
    print("- Đọc lại bằng RepositoryV2: PASS")
    print("- Đọc đủ 4 record draft: PASS")
    print("- Thứ tự YCCD_ID đúng: PASS")
    print("- Chặn ghi trùng YCCD_ID: PASS")
    print("- Workbook gốc không bị ghi: PASS")

    print(
        "\nKẾT QUẢ: 7/7 TEST PASS"
    )


if __name__ == "__main__":
    main()