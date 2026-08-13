from models.yccd_record import YCCDRecord
from models.yccd_period_map_record import (
    YCCDPeriodMapRecord,
)


def validate_period_map_integrity(
    yccd_records: list[YCCDRecord],
    map_records: list[YCCDPeriodMapRecord],
) -> None:
    """Kiểm tra tính toàn vẹn giữa YCCD và YCCD_PERIOD_MAP."""

    # Validate từng record trước.
    for record in yccd_records:
        record.validate()

    for map_record in map_records:
        map_record.validate()

    # ---------------------------------------------------------
    # 1. Không được trùng YCCD_ID
    # ---------------------------------------------------------

    yccd_index: dict[str, YCCDRecord] = {}

    for record in yccd_records:
        if record.yccd_id in yccd_index:
            raise ValueError(
                "Trùng YCCD_ID trong dữ liệu YCCD: "
                f"{record.yccd_id}"
            )

        yccd_index[
            record.yccd_id
        ] = record

    # ---------------------------------------------------------
    # 2. Không được trùng MAP_ID
    # ---------------------------------------------------------

    map_ids: set[str] = set()

    for map_record in map_records:
        if map_record.map_id in map_ids:
            raise ValueError(
                "Trùng MAP_ID: "
                f"{map_record.map_id}"
            )

        map_ids.add(
            map_record.map_id
        )

    # ---------------------------------------------------------
    # 3. Kiểm tra từng mapping
    # ---------------------------------------------------------

    for map_record in map_records:
        yccd_record = yccd_index.get(
            map_record.yccd_id
        )

        if yccd_record is None:
            raise ValueError(
                "YCCD_ID trong mapping không tồn tại: "
                f"{map_record.yccd_id}"
            )

        if (
            yccd_record.lesson_key
            != map_record.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY của mapping không khớp YCCD: "
                f"{map_record.map_id}"
            )

        if (
            yccd_record.yccd_type
            .strip()
            .upper()
            != "TRIEN_KHAI"
        ):
            raise ValueError(
                "Chỉ YCCĐ TRIEN_KHAI mới được "
                "mapping xuống tiết: "
                f"{map_record.yccd_id}"
            )