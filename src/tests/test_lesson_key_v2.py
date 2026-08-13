import sys

sys.path.insert(0, "src")

from utils.lesson_key import (
    build_lesson_id_v2,
)


def main() -> None:
    hinh_b12 = build_lesson_id_v2(
        7,
        "Hình7",
        "Bài 12. Tổng các góc trong một tam giác",
    )

    cn_b12 = build_lesson_id_v2(
        7,
        "CN7",
        "Bài 12. Chăn nuôi gà thịt trong nông hộ",
    )

    assert hinh_b12 == "T7_HINH_B12"
    assert cn_b12 == "T7_CN_B12"

    assert hinh_b12 != cn_b12

    assert build_lesson_id_v2(
        7,
        "Đại7",
        "Bài 3. Lũy thừa với số mũ tự nhiên của một số hữu tỉ",
    ) == "T7_DAI_B03"

    assert build_lesson_id_v2(
        8,
        "Hình8",
        "Bài 24. Phép nhân và phép chia PTĐS",
    ) == "T8_HINH_B24"

    assert build_lesson_id_v2(
        6,
        "Nhạc6",
        "Chủ đề 1: Tuổi học trò",
    ) is None

    print("=" * 70)
    print("LP-03C.5J - LESSON KEY V2 TEST")
    print("=" * 70)

    print("- Hình7 Bài 12 -> T7_HINH_B12: PASS")
    print("- CN7 Bài 12 -> T7_CN_B12: PASS")
    print("- Hình/CN cùng số bài không trùng: PASS")
    print("- Đại7 Bài 3: PASS")
    print("- Hình8 Bài 24: PASS")
    print("- Nội dung không có số bài -> None: PASS")

    print("\nKẾT QUẢ: 6/6 TEST PASS")


if __name__ == "__main__":
    main()