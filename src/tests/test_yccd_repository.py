import sys
from pathlib import Path

sys.path.insert(0, "src")

from repositories.yccd_repository import YCCDRepository


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def main() -> None:
    repository = YCCDRepository()

    # Đọc toàn bộ dữ liệu trong sheet YCCD.
    rows = repository.load_rows(
        EXCEL_FILE
    )

    # Phải đọc được ít nhất một dòng dữ liệu.
    assert len(rows) >= 1

    # Tìm dòng kiểm thử TEST_001.
    test_row = next(
        (
            row
            for row in rows
            if row.get("YCCD_ID") == "TEST_001"
        ),
        None,
    )

    assert test_row is not None

    # Kiểm tra dữ liệu cơ bản.
    assert test_row["MON"] == "Toán"
    assert str(test_row["KHOI"]) == "8"
    assert test_row["BAI_ID"] == "B02"
    assert test_row["YCCD_ORDER"] == 1

    # Excel có thể trả 1.0 dưới dạng số hoặc chuỗi.
    assert test_row["PHIEN_BAN"] in (
        "1.0",
        1.0,
    )

    print("=" * 70)
    print("LP-03B - YCCD REPOSITORY TEST")
    print("=" * 70)

    print(f"Tổng số dòng YCCD: {len(rows)}")
    print(f"YCCD_ID: {test_row['YCCD_ID']}")
    print(f"Môn: {test_row['MON']}")
    print(f"Khối: {test_row['KHOI']}")
    print(f"Bài: {test_row['TEN_BAI']}")
    print(f"Tiết: {test_row['TIET']}")
    print(f"Trạng thái: {test_row['TRANG_THAI']}")

    print("\nKẾT QUẢ KIỂM TRA")
    print("- Đọc sheet YCCD: PASS")
    print("- Nhận diện headers: PASS")
    print("- Đọc tblYCCD: PASS")
    print("- Tìm TEST_001: PASS")
    print("- Đọc metadata: PASS")

    print("\nKẾT QUẢ: 5/5 TEST PASS")


if __name__ == "__main__":
    main()