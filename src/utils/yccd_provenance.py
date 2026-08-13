from models.yccd_record import YCCDRecord


def validate_provenance(
    records: list[YCCDRecord],
) -> None:
    """Kiểm tra tính toàn vẹn quan hệ YCCĐ gốc - triển khai."""

    # Kiểm tra từng record trước.
    for record in records:
        record.validate()

    # Không được trùng YCCD_ID.
    record_index: dict[
        str,
        YCCDRecord,
    ] = {}

    for record in records:
        if record.yccd_id in record_index:
            raise ValueError(
                "Trùng YCCD_ID: "
                f"{record.yccd_id}"
            )

        record_index[
            record.yccd_id
        ] = record

    # Kiểm tra quan hệ provenance.
    for record in records:
        yccd_type = (
            record.yccd_type
            .strip()
            .upper()
        )

        if yccd_type == "CHINH_THUC":
            continue

        if yccd_type != "TRIEN_KHAI":
            continue

        source_id = record.source_yccd_id

        if not source_id:
            raise ValueError(
                "YCCĐ TRIEN_KHAI thiếu YCCD_GOC_ID: "
                f"{record.yccd_id}"
            )

        source_record = record_index.get(
            source_id
        )

        if source_record is None:
            raise ValueError(
                "Không tìm thấy YCCD_GOC_ID "
                f"{source_id} của {record.yccd_id}"
            )

        if (
            source_record.yccd_type
            .strip()
            .upper()
            != "CHINH_THUC"
        ):
            raise ValueError(
                "YCCD_GOC_ID phải trỏ tới "
                "YCCĐ CHINH_THUC: "
                f"{record.yccd_id}"
            )

        if (
            source_record.lesson_key
            != record.lesson_key
        ):
            raise ValueError(
                "YCCĐ gốc và YCCĐ triển khai "
                "không cùng LESSON_KEY: "
                f"{record.yccd_id}"
            )

        if (
            source_record.yccd_id
            == record.yccd_id
        ):
            raise ValueError(
                "YCCĐ không được tự trỏ "
                "về chính nó: "
                f"{record.yccd_id}"
            )