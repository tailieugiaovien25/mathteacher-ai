import sys
from pathlib import Path

sys.path.insert(0, "src")

from repositories.yccd_period_map_repository import (
    YCCDPeriodMapRepository,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def main() -> None:
    repository = YCCDPeriodMapRepository()

    # =========================================================
    # 1. ĐỌC TOÀN BỘ 5 MAPPING CỦA BÀI 3
    # =========================================================

    all_records = (
        repository.find_by_lesson_key(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
            status="draft",
        )
    )

    assert len(all_records) == 5

    # =========================================================
    # 2. TIẾT 1
    # =========================================================

    period_1 = repository.find_by_period(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        period_in_lesson=1,
        status="draft",
    )

    assert len(period_1) == 1

    assert (
        period_1[0].yccd_id
        == "T7_DAI_B03_Y01"
    )

    assert (
        period_1[0].role
        == "CHINH"
    )

    # =========================================================
    # 3. TIẾT 2
    # =========================================================

    period_2 = repository.find_by_period(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        status="draft",
    )

    assert len(period_2) == 2

    assert [
        item.yccd_id
        for item in period_2
    ] == [
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
    ]

    assert [
        item.role
        for item in period_2
    ] == [
        "CUNG_CO",
        "CHINH",
    ]

    # =========================================================
    # 4. TIẾT 3
    # =========================================================

    period_3 = repository.find_by_period(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        period_in_lesson=3,
        status="draft",
    )

    assert len(period_3) == 2

    assert [
        item.yccd_id
        for item in period_3
    ] == [
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    ]

    assert [
        item.role
        for item in period_3
    ] == [
        "CUNG_CO",
        "CHINH",
    ]

    # =========================================================
    # 5. TIẾT KHÔNG TỒN TẠI
    # =========================================================

    period_4 = repository.find_by_period(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        period_in_lesson=4,
        status="draft",
    )

    assert period_4 == []

    print("=" * 70)
    print(
        "LP-03E.2A - "
        "YCCD PERIOD MAP REPOSITORY REAL TEST"
    )
    print("=" * 70)

    print("- Đọc toàn bộ 5 mapping: PASS")
    print("- Tiết 1 -> Y01 CHINH: PASS")
    print("- Tiết 2 -> Y01 + Y02: PASS")
    print("- Vai trò tiết 2 đúng: PASS")
    print("- Tiết 3 -> Y02 + Y03: PASS")
    print("- Vai trò tiết 3 đúng: PASS")
    print("- Tiết 4 không tồn tại -> []: PASS")

    print(
        "\nKẾT QUẢ: 7/7 TEST PASS"
    )

if __name__ == "__main__":
    main()