import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "src")

from models.yccd_period_map_record import (
    YCCDPeriodMapRecord,
)
from repositories.yccd_repository_v2 import (
    YCCDRepositoryV2,
)
from utils.yccd_period_map_integrity import (
    validate_period_map_integrity,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def build_map_records() -> list[
    YCCDPeriodMapRecord
]:
    return [
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


def main() -> None:
    repository = YCCDRepositoryV2()

    yccd_records = (
        repository.find_by_lesson_key(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
            status="draft",
        )
    )

    assert len(yccd_records) == 4

    map_records = build_map_records()

    validate_period_map_integrity(
        yccd_records,
        map_records,
    )

    # ---------------------------------------------------------
    # 1. Mapping hợp lệ
    # ---------------------------------------------------------

    assert len(map_records) == 5

    # ---------------------------------------------------------
    # 2. Không được mapping Y00 CHINH_THUC
    # ---------------------------------------------------------

    invalid_official = (
        map_records.copy()
    )

    invalid_official.append(
        YCCDPeriodMapRecord(
            map_id="TEST_OFFICIAL",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            yccd_id="T7_DAI_B03_Y00",
            role="CHINH",
        )
    )

    official_blocked = False

    try:
        validate_period_map_integrity(
            yccd_records,
            invalid_official,
        )
    except ValueError:
        official_blocked = True

    assert official_blocked

    # ---------------------------------------------------------
    # 3. YCCD_ID không tồn tại phải bị chặn
    # ---------------------------------------------------------

    invalid_missing = [
        YCCDPeriodMapRecord(
            map_id="TEST_MISSING",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            yccd_id="NOT_FOUND",
            role="CHINH",
        )
    ]

    missing_blocked = False

    try:
        validate_period_map_integrity(
            yccd_records,
            invalid_missing,
        )
    except ValueError:
        missing_blocked = True

    assert missing_blocked

    # ---------------------------------------------------------
    # 4. Sai LESSON_KEY phải bị chặn
    # ---------------------------------------------------------

    invalid_key = [
        YCCDPeriodMapRecord(
            map_id="TEST_KEY",
            lesson_key="T7_DAI_B04",
            period_in_lesson=1,
            yccd_id="T7_DAI_B03_Y01",
            role="CHINH",
        )
    ]

    key_blocked = False

    try:
        validate_period_map_integrity(
            yccd_records,
            invalid_key,
        )
    except ValueError:
        key_blocked = True

    assert key_blocked

    # ---------------------------------------------------------
    # KẾT QUẢ
    # ---------------------------------------------------------

    print("=" * 70)
    print(
        "LP-03D.3D.8 - "
        "YCCD PERIOD MAP INTEGRITY REAL TEST"
    )
    print("=" * 70)

    print("- Đọc đủ 4 YCCĐ thật: PASS")
    print("- 5 mapping hợp lệ: PASS")
    print("- Y00 CHINH_THUC không được mapping: PASS")
    print("- YCCD_ID không tồn tại bị chặn: PASS")
    print("- Sai LESSON_KEY bị chặn: PASS")

    print(
        "\nKẾT QUẢ: 5/5 TEST PASS"
    )


if __name__ == "__main__":
    main()