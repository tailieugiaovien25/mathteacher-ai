import sys

sys.path.insert(0, "src")

from utils.period_mapping import (
    build_period_mapping,
    is_fallback_key,
)


def main() -> None:
    records = [
        {
            "lesson_key": "T7_DAI_B03",
            "period": 9,
            "lesson_name": "Bài 3. Tiết 3",
        },
        {
            "lesson_key": "T7_DAI_B03",
            "period": 7,
            "lesson_name": "Bài 3. Tiết 1",
        },
        {
            "lesson_key": "T7_DAI_B03",
            "period": 8,
            "lesson_name": "Bài 3. Tiết 2",
        },
        {
            "lesson_key": "T7_DAI_P005",
            "period": 5,
            "lesson_name": "Luyện tập chung",
        },
        {
            "lesson_key": "T8_HINH_P052",
            "period": 52,
            "lesson_name": "HĐTN.TH.",
        },
    ]

    mapped = build_period_mapping(
        records
    )

    # =========================================================
    # 1. FALLBACK KEY
    # =========================================================

    assert is_fallback_key(
        "T7_DAI_P005"
    )

    assert is_fallback_key(
        "T8_HINH_P052"
    )

    assert not is_fallback_key(
        "T7_DAI_B03"
    )

    # =========================================================
    # 2. BÀI NHIỀU TIẾT
    # =========================================================

    lesson_rows = [
        item
        for item in mapped
        if item["lesson_key"]
        == "T7_DAI_B03"
    ]

    lesson_rows = sorted(
        lesson_rows,
        key=lambda item: (
            item["period_in_lesson"]
        ),
    )

    assert len(lesson_rows) == 3

    assert (
        lesson_rows[0]["period"]
        == 7
    )

    assert (
        lesson_rows[0][
            "period_in_lesson"
        ]
        == 1
    )

    assert (
        lesson_rows[1]["period"]
        == 8
    )

    assert (
        lesson_rows[1][
            "period_in_lesson"
        ]
        == 2
    )

    assert (
        lesson_rows[2]["period"]
        == 9
    )

    assert (
        lesson_rows[2][
            "period_in_lesson"
        ]
        == 3
    )

    # =========================================================
    # 3. FALLBACK LUÔN = TIẾT 1 TRONG BÀI
    # =========================================================

    fallback_rows = [
        item
        for item in mapped
        if is_fallback_key(
            item["lesson_key"]
        )
    ]

    assert len(
        fallback_rows
    ) == 2

    assert all(
        item["period_in_lesson"]
        == 1
        for item in fallback_rows
    )

    # =========================================================
    # 4. KHÔNG LÀM THAY ĐỔI RECORD GỐC
    # =========================================================

    assert all(
        "period_in_lesson"
        not in item
        for item in records
    )

    print("=" * 70)
    print("LP-03D.2D - PERIOD MAPPING TEST")
    print("=" * 70)

    print("- Nhận diện fallback key: PASS")
    print("- Nhận diện lesson key thường: PASS")
    print("- Sắp xếp bài nhiều tiết: PASS")
    print("- Tiết PPCT 7 -> tiết trong bài 1: PASS")
    print("- Tiết PPCT 8 -> tiết trong bài 2: PASS")
    print("- Tiết PPCT 9 -> tiết trong bài 3: PASS")
    print("- Fallback luôn là tiết trong bài 1: PASS")
    print("- Không làm thay đổi dữ liệu gốc: PASS")

    print("\nKẾT QUẢ: 8/8 TEST PASS")


if __name__ == "__main__":
    main()