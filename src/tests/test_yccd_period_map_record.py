import sys
from datetime import date

sys.path.insert(0, "src")

from models.yccd_period_map_record import (
    YCCDPeriodMapRecord,
)


def expect_value_error(
    record: YCCDPeriodMapRecord,
) -> None:
    try:
        record.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    records = [
        YCCDPeriodMapRecord(
            map_id="T7_DAI_B03_P01_Y01",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            yccd_id="T7_DAI_B03_Y01",
            role="CHINH",
            status="draft",
            updated_at=date(2026, 8, 8),
        ),
        YCCDPeriodMapRecord(
            map_id="T7_DAI_B03_P02_Y01",
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            yccd_id="T7_DAI_B03_Y01",
            role="CUNG_CO",
            status="draft",
            updated_at=date(2026, 8, 8),
        ),
        YCCDPeriodMapRecord(
            map_id="T7_DAI_B03_P02_Y02",
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            yccd_id="T7_DAI_B03_Y02",
            role="CHINH",
            status="draft",
            updated_at=date(2026, 8, 8),
        ),
        YCCDPeriodMapRecord(
            map_id="T7_DAI_B03_P03_Y02",
            lesson_key="T7_DAI_B03",
            period_in_lesson=3,
            yccd_id="T7_DAI_B03_Y02",
            role="CUNG_CO",
            status="draft",
            updated_at=date(2026, 8, 8),
        ),
        YCCDPeriodMapRecord(
            map_id="T7_DAI_B03_P03_Y03",
            lesson_key="T7_DAI_B03",
            period_in_lesson=3,
            yccd_id="T7_DAI_B03_Y03",
            role="CHINH",
            status="draft",
            updated_at=date(2026, 8, 8),
        ),
    ]

    for record in records:
        record.validate()

    assert len(records) == 5

    assert all(
        record.lesson_key
        == "T7_DAI_B03"
        for record in records
    )

    assert [
        record.period_in_lesson
        for record in records
    ] == [1, 2, 2, 3, 3]

    assert [
        record.role
        for record in records
    ] == [
        "CHINH",
        "CUNG_CO",
        "CHINH",
        "CUNG_CO",
        "CHINH",
    ]

    map_ids = [
        record.map_id
        for record in records
    ]

    assert (
        len(map_ids)
        == len(set(map_ids))
    )

    assert all(
        len(record.to_excel_row()) == 9
        for record in records
    )

    expect_value_error(
        YCCDPeriodMapRecord(
            map_id="TEST",
            lesson_key="T7_DAI_B03",
            period_in_lesson=0,
            yccd_id="T7_DAI_B03_Y01",
            role="CHINH",
        )
    )

    expect_value_error(
        YCCDPeriodMapRecord(
            map_id="TEST",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            yccd_id="T7_DAI_B03_Y01",
            role="SAI",
        )
    )

    print("=" * 70)
    print(
        "LP-03D.3D.7 - "
        "YCCD PERIOD MAP RECORD TEST"
    )
    print("=" * 70)

    print("- Tạo đủ 5 mapping: PASS")
    print("- Validate 5 mapping: PASS")
    print("- LessonKey thống nhất: PASS")
    print("- Tiết trong bài đúng: PASS")
    print("- Vai trò đúng: PASS")
    print("- MAP_ID không trùng: PASS")
    print("- Xuất schema 9 cột: PASS")
    print("- Tiết = 0 bị từ chối: PASS")
    print("- Vai trò sai bị từ chối: PASS")

    print(
        "\nKẾT QUẢ: 9/9 TEST PASS"
    )


if __name__ == "__main__":
    main()