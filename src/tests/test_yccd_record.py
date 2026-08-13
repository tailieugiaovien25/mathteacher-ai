import sys
from datetime import date

sys.path.insert(0, "src")

from models.yccd_record import YCCDRecord


def expect_value_error(
    record: YCCDRecord,
) -> None:
    try:
        record.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. BẢN GHI HỢP LỆ
    # =========================================================

    record = YCCDRecord(
        yccd_id="T7_DAI_B03_Y01",
        lesson_key="T7_DAI_B03",
        subject="Toán",
        grade=7,
        lesson_id="B03",
        lesson_name=(
            "Bài 3. Lũy thừa với số mũ tự nhiên "
            "của một số hữu tỉ"
        ),
        order=1,
        requirement=(
            "Nhận biết được lũy thừa với số mũ "
            "tự nhiên của một số hữu tỉ."
        ),
        source="CTGDPT/SGK",
        reference="Bài 3",
        version="1.0",
        status="approved",
        updated_at=date(
            2026,
            8,
            8,
        ),
        note="Dữ liệu kiểm thử.",
    )

    record.validate()

    row = record.to_excel_row()

    assert (
        row["YCCD_ID"]
        == "T7_DAI_B03_Y01"
    )

    assert (
        row["LESSON_KEY"]
        == "T7_DAI_B03"
    )

    assert row["MON"] == "Toán"
    assert row["KHOI"] == 7
    assert row["BAI_ID"] == "B03"
    assert row["YCCD_ORDER"] == 1

    assert (
        row["TRANG_THAI"]
        == "approved"
    )

    # =========================================================
    # 2. THIẾU YCCD_ID
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 3. THIẾU LESSON_KEY
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 4. THIẾU MÔN
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 5. THIẾU TÊN BÀI
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="",
            order=1,
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 6. YCCĐ RỖNG
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="",
        )
    )

    # =========================================================
    # 7. ORDER = 0
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=0,
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 8. ORDER KHÔNG PHẢI SỐ
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order="abc",
            requirement="YCCĐ mẫu",
        )
    )

    # =========================================================
    # 9. TRẠNG THÁI KHÔNG HỢP LỆ
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_Y01",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
            status="active",
        )
    )

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 70)
    print("LP-03D.3B - YCCD RECORD TEST")
    print("=" * 70)

    print("- Bản ghi hợp lệ: PASS")
    print("- Chuyển sang Excel row: PASS")
    print("- Thiếu YCCD_ID: PASS")
    print("- Thiếu LESSON_KEY: PASS")
    print("- Thiếu MON: PASS")
    print("- Thiếu TEN_BAI: PASS")
    print("- YEU_CAU_CAN_DAT rỗng: PASS")
    print("- YCCD_ORDER = 0: PASS")
    print("- YCCD_ORDER không phải số: PASS")
    print("- TRANG_THAI không hợp lệ: PASS")

    print("\nKẾT QUẢ: 10/10 TEST PASS")


if __name__ == "__main__":
    main()