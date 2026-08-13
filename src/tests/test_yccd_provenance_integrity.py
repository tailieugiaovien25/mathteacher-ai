import sys

sys.path.insert(0, "src")

from models.yccd_record import YCCDRecord
from utils.yccd_provenance import (
    validate_provenance,
)


def expect_value_error(
    records: list[YCCDRecord],
) -> None:
    try:
        validate_provenance(
            records
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def make_official(
    yccd_id: str = "T7_DAI_B03_Y00",
    lesson_key: str = "T7_DAI_B03",
) -> YCCDRecord:
    return YCCDRecord(
        yccd_id=yccd_id,
        lesson_key=lesson_key,
        subject="Toán",
        grade=7,
        lesson_id="B03",
        lesson_name="Bài 3",
        order=1,
        requirement="YCCĐ chính thức.",
        yccd_type="CHINH_THUC",
        source_yccd_id=None,
        status="draft",
    )


def make_derived(
    yccd_id: str = "T7_DAI_B03_Y01",
    lesson_key: str = "T7_DAI_B03",
    source_yccd_id: str = "T7_DAI_B03_Y00",
) -> YCCDRecord:
    return YCCDRecord(
        yccd_id=yccd_id,
        lesson_key=lesson_key,
        subject="Toán",
        grade=7,
        lesson_id="B03",
        lesson_name="Bài 3",
        order=2,
        requirement="YCCĐ triển khai.",
        yccd_type="TRIEN_KHAI",
        source_yccd_id=source_yccd_id,
        status="draft",
    )


def main() -> None:
    # 1. Quan hệ hợp lệ.
    valid_records = [
        make_official(),
        make_derived(),
    ]

    validate_provenance(
        valid_records
    )

    # 2. YCCD_GOC_ID không tồn tại.
    expect_value_error(
        [
            make_official(),
            make_derived(
                source_yccd_id="NOT_FOUND"
            ),
        ]
    )

    # 3. YCCĐ triển khai trỏ tới một YCCĐ triển khai khác.
    derived_parent = make_derived(
        yccd_id="T7_DAI_B03_Y01"
    )

    derived_child = make_derived(
        yccd_id="T7_DAI_B03_Y02",
        source_yccd_id="T7_DAI_B03_Y01",
    )

    expect_value_error(
        [
            make_official(),
            derived_parent,
            derived_child,
        ]
    )

    # 4. Không cùng LESSON_KEY.
    expect_value_error(
        [
            make_official(),
            make_derived(
                lesson_key="T7_DAI_B04"
            ),
        ]
    )

    # 5. Trùng YCCD_ID.
    expect_value_error(
        [
            make_official(),
            make_official(),
        ]
    )

    # 6. Bộ 4 YCCĐ thực tế thử nghiệm.
    real_records = [
        make_official(),
        make_derived(
            yccd_id="T7_DAI_B03_Y01"
        ),
        make_derived(
            yccd_id="T7_DAI_B03_Y02"
        ),
        make_derived(
            yccd_id="T7_DAI_B03_Y03"
        ),
    ]

    validate_provenance(
        real_records
    )

    print("=" * 70)
    print(
        "LP-03D.3D.4 - "
        "YCCD PROVENANCE INTEGRITY TEST"
    )
    print("=" * 70)

    print("- Quan hệ CHINH_THUC -> TRIEN_KHAI hợp lệ: PASS")
    print("- YCCD_GOC_ID không tồn tại bị từ chối: PASS")
    print("- TRIEN_KHAI không được làm YCCĐ gốc: PASS")
    print("- Khác LESSON_KEY bị từ chối: PASS")
    print("- Trùng YCCD_ID bị từ chối: PASS")
    print("- Bộ 4 YCCĐ thử nghiệm hợp lệ: PASS")

    print(
        "\nKẾT QUẢ: 6/6 TEST PASS"
    )


if __name__ == "__main__":
    main()