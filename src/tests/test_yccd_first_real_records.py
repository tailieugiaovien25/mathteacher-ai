import sys
from datetime import date

sys.path.insert(0, "src")

from models.yccd_record import YCCDRecord


def build_records() -> list[YCCDRecord]:
    """Tạo bộ 4 YCCĐ thử nghiệm đầu tiên."""

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
        "updated_at": date(2026, 8, 8),
    }

    official = YCCDRecord(
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
    )

    derived_1 = YCCDRecord(
        **common,
        yccd_id="T7_DAI_B03_Y01",
        order=2,
        requirement=(
            "Mô tả được phép tính lũy thừa với số mũ "
            "tự nhiên của một số hữu tỉ."
        ),
        yccd_type="TRIEN_KHAI",
        source_yccd_id="T7_DAI_B03_Y00",
        source="TONG_HOP",
        reference=(
            "CTGDPT_2018 + nội dung triển khai Bài 3"
        ),
        note="YCCĐ triển khai từ Y00.",
    )

    derived_2 = YCCDRecord(
        **common,
        yccd_id="T7_DAI_B03_Y02",
        order=3,
        requirement=(
            "Mô tả và thực hiện được phép tính tích, "
            "thương của hai lũy thừa cùng cơ số."
        ),
        yccd_type="TRIEN_KHAI",
        source_yccd_id="T7_DAI_B03_Y00",
        source="TONG_HOP",
        reference=(
            "CTGDPT_2018 + nội dung triển khai Bài 3"
        ),
        note="YCCĐ triển khai từ Y00.",
    )

    derived_3 = YCCDRecord(
        **common,
        yccd_id="T7_DAI_B03_Y03",
        order=4,
        requirement=(
            "Mô tả và thực hiện được phép tính "
            "lũy thừa của lũy thừa."
        ),
        yccd_type="TRIEN_KHAI",
        source_yccd_id="T7_DAI_B03_Y00",
        source="TONG_HOP",
        reference=(
            "CTGDPT_2018 + nội dung triển khai Bài 3"
        ),
        note="YCCĐ triển khai từ Y00.",
    )

    return [
        official,
        derived_1,
        derived_2,
        derived_3,
    ]


def main() -> None:
    records = build_records()

    # 1. Phải có đúng 4 record.
    assert len(records) == 4

    # 2. Validate từng record.
    for record in records:
        record.validate()

    # 3. Y00 phải là CHINH_THUC.
    assert (
        records[0].yccd_type
        == "CHINH_THUC"
    )

    assert (
        records[0].source_yccd_id
        is None
    )

    # 4. Y01-Y03 phải là TRIEN_KHAI.
    for record in records[1:]:
        assert (
            record.yccd_type
            == "TRIEN_KHAI"
        )

        assert (
            record.source_yccd_id
            == "T7_DAI_B03_Y00"
        )

    # 5. Tất cả cùng LESSON_KEY.
    assert all(
        record.lesson_key
        == "T7_DAI_B03"
        for record in records
    )

    # 6. ID không được trùng.
    ids = [
        record.yccd_id
        for record in records
    ]

    assert (
        len(ids)
        == len(set(ids))
    )

    # 7. Thứ tự phải là 1, 2, 3, 4.
    assert [
        record.order
        for record in records
    ] == [1, 2, 3, 4]

    # 8. Chưa được approved.
    assert all(
        record.status == "draft"
        for record in records
    )

    # 9. Xuất được schema Excel 16 cột.
    excel_rows = [
        record.to_excel_row()
        for record in records
    ]

    assert all(
        len(row) == 16
        for row in excel_rows
    )

    print("=" * 70)
    print(
        "LP-03D.3D.4 - "
        "FIRST REAL YCCD RECORDS TEST"
    )
    print("=" * 70)

    print("- Tạo đủ 4 YCCDRecord: PASS")
    print("- Validate 4 record: PASS")
    print("- Y00 là CHINH_THUC: PASS")
    print("- Y00 không có YCCD_GOC_ID: PASS")
    print("- Y01-Y03 là TRIEN_KHAI: PASS")
    print("- Y01-Y03 truy vết về Y00: PASS")
    print("- Không trùng YCCD_ID: PASS")
    print("- YCCD_ORDER hợp lệ: PASS")
    print("- Tất cả đang ở trạng thái draft: PASS")
    print("- Xuất schema Excel 16 cột: PASS")

    print(
        "\nKẾT QUẢ: 10/10 TEST PASS"
    )


if __name__ == "__main__":
    main()