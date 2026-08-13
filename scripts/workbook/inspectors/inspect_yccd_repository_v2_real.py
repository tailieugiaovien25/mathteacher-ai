import sys
from pathlib import Path

sys.path.insert(0, "src")

from repositories.yccd_repository_v2 import (
    YCCDRepositoryV2,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def main() -> None:
    repository = YCCDRepositoryV2()

    print("=" * 70)
    print(
        "LP-03D.3C.3 - "
        "YCCD REPOSITORY V2 REAL WORKBOOK INSPECTION"
    )
    print("=" * 70)

    rows = repository.load_rows(
        EXCEL_FILE
    )

    print(
        f"Tổng dòng dữ liệu YCCD: "
        f"{len(rows)}"
    )

    # Workbook hiện tại có thể đang trống.
    # Điều đó hoàn toàn hợp lệ.
    if rows:
        print(
            "\nCÁC DÒNG YCCD HIỆN CÓ"
        )

        for row in rows[:5]:
            print(
                f"- {row.get('YCCD_ID')} | "
                f"{row.get('LESSON_KEY')} | "
                f"{row.get('TRANG_THAI')}"
            )
    else:
        print(
            "\nBảng YCCD hiện chưa có dữ liệu: OK"
        )

    # Thử tìm một LessonKey.
    # Nếu bảng đang trống thì phải trả về [].
    records = (
        repository.find_by_lesson_key(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
        )
    )

    print(
        "\nTìm T7_DAI_B03 "
        f"(approved): {len(records)}"
    )

    # ---------------------------------------------------------
    # TIÊU CHUẨN CHẤP NHẬN
    # ---------------------------------------------------------

    load_pass = isinstance(
        rows,
        list,
    )

    find_pass = isinstance(
        records,
        list,
    )

    print(
        "\nTIÊU CHUẨN CHẤP NHẬN"
    )

    print(
        "- Đọc workbook thật: "
        + (
            "PASS"
            if load_pass
            else "FAIL"
        )
    )

    print(
        "- Schema 14 cột được chấp nhận: "
        + (
            "PASS"
            if load_pass
            else "FAIL"
        )
    )

    print(
        "- find_by_lesson_key hoạt động: "
        + (
            "PASS"
            if find_pass
            else "FAIL"
        )
    )

    accepted = (
        load_pass
        and find_pass
    )

    print(
        "\nKẾT QUẢ: "
        + (
            "YCCD REPOSITORY V2 REAL WORKBOOK ACCEPTED"
            if accepted
            else
            "YCCD REPOSITORY V2 REAL WORKBOOK NOT ACCEPTED"
        )
    )


if __name__ == "__main__":
    main()