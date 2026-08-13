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
    # 1. YCCĐ CHÍNH THỨC HỢP LỆ
    # =========================================================

    official = YCCDRecord(
        yccd_id="T7_DAI_B03_Y00",
        lesson_key="T7_DAI_B03",
        subject="Toán",
        grade=7,
        lesson_id="B03",
        lesson_name="Bài 3. Lũy thừa",
        order=1,
        requirement="YCCĐ chính thức của chương trình.",
        yccd_type="CHINH_THUC",
        source_yccd_id=None,
        source="CTGDPT_2018",
        reference="Nội dung yêu cầu cần đạt tương ứng",
        version="1.0",
        status="approved",
        updated_at=date(
            2026,
            8,
            8,
        ),
        note="Dữ liệu kiểm thử.",
    )

    official.validate()

    official_row = (
        official.to_excel_row()
    )

    assert (
        official_row["LOAI_YCCD"]
        == "CHINH_THUC"
    )

    assert (
        official_row["YCCD_GOC_ID"]
        is None
    )

    # =========================================================
    # 2. YCCĐ TRIỂN KHAI HỢP LỆ
    # =========================================================

    derived = YCCDRecord(
        yccd_id="T7_DAI_B03_Y01",
        lesson_key="T7_DAI_B03",
        subject="Toán",
        grade=7,
        lesson_id="B03",
        lesson_name="Bài 3. Lũy thừa",
        order=2,
        requirement=(
            "Mô tả được phép tính lũy thừa "
            "với số mũ tự nhiên của số hữu tỉ."
        ),
        yccd_type="TRIEN_KHAI",
        source_yccd_id=(
            "T7_DAI_B03_Y00"
        ),
        source="TONG_HOP",
        reference=(
            "CTGDPT_2018 + SGK Kết nối tri thức"
        ),
        version="1.0",
        status="draft",
        updated_at=date(
            2026,
            8,
            8,
        ),
    )

    derived.validate()

    derived_row = (
        derived.to_excel_row()
    )

    assert (
        derived_row["LOAI_YCCD"]
        == "TRIEN_KHAI"
    )

    assert (
        derived_row["YCCD_GOC_ID"]
        == "T7_DAI_B03_Y00"
    )

    # =========================================================
    # 3. CHÍNH THỨC KHÔNG ĐƯỢC CÓ YCCD_GOC_ID
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_OFFICIAL",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
            yccd_type="CHINH_THUC",
            source_yccd_id="ABC",
        )
    )

    # =========================================================
    # 4. TRIỂN KHAI BẮT BUỘC CÓ YCCD_GOC_ID
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_DERIVED",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
            yccd_type="TRIEN_KHAI",
            source_yccd_id=None,
        )
    )

    # =========================================================
    # 5. LOẠI YCCĐ KHÔNG HỢP LỆ
    # =========================================================

    expect_value_error(
        YCCDRecord(
            yccd_id="TEST_TYPE",
            lesson_key="T7_DAI_B03",
            subject="Toán",
            grade=7,
            lesson_id="B03",
            lesson_name="Bài 3",
            order=1,
            requirement="YCCĐ mẫu",
            yccd_type="AI_GENERATED",
            source_yccd_id=None,
        )
    )

    # =========================================================
    # 6. SCHEMA EXCEL 16 CỘT
    # =========================================================

    expected_headers = {
        "YCCD_ID",
        "LESSON_KEY",
        "MON",
        "KHOI",
        "BAI_ID",
        "TEN_BAI",
        "YCCD_ORDER",
        "YEU_CAU_CAN_DAT",
        "LOAI_YCCD",
        "YCCD_GOC_ID",
        "NGUON",
        "THAM_CHIEU",
        "PHIEN_BAN",
        "TRANG_THAI",
        "NGAY_CAP_NHAT",
        "GHI_CHU",
    }

    assert (
        set(
            derived_row.keys()
        )
        == expected_headers
    )

    assert (
        len(derived_row)
        == 16
    )

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 70)
    print(
        "LP-03D.3D.3A - "
        "YCCD PROVENANCE TEST"
    )
    print("=" * 70)

    print("- CHINH_THUC hợp lệ: PASS")
    print("- TRIEN_KHAI hợp lệ: PASS")
    print(
        "- CHINH_THUC không có YCCD_GOC_ID: PASS"
    )
    print(
        "- TRIEN_KHAI bắt buộc có YCCD_GOC_ID: PASS"
    )
    print("- LOAI_YCCD sai bị từ chối: PASS")
    print("- to_excel_row có đủ 16 cột: PASS")

    print(
        "\nKẾT QUẢ: 6/6 TEST PASS"
    )


if __name__ == "__main__":
    main()