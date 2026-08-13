import sys

sys.path.insert(0, "src")

from utils.lesson_key import build_lesson_key


def main() -> None:
    # =========================================================
    # 1. BÀI CÓ SỐ
    # =========================================================

    assert build_lesson_key(
        7,
        "Đại7",
        "Bài 3. Lũy thừa với số mũ tự nhiên của một số hữu tỉ",
        7,
    ) == "T7_DAI_B03"

    assert build_lesson_key(
        7,
        "Hình7",
        "Bài 12. Tổng các góc trong một tam giác",
        12,
    ) == "T7_HINH_B12"

    assert build_lesson_key(
        7,
        "CN7",
        "Bài 12. Chăn nuôi gà thịt trong nông hộ",
        25,
    ) == "T7_CN_B12"

    # =========================================================
    # 2. KIỂM TRA KHÔNG XUNG ĐỘT GIỮA CÁC STREAM
    # =========================================================

    hinh_key = build_lesson_key(
        7,
        "Hình7",
        "Bài 12. Tổng các góc trong một tam giác",
        12,
    )

    cn_key = build_lesson_key(
        7,
        "CN7",
        "Bài 12. Chăn nuôi gà thịt trong nông hộ",
        25,
    )

    assert hinh_key != cn_key

    # =========================================================
    # 3. NỘI DUNG KHÔNG CÓ SỐ BÀI
    # =========================================================

    assert build_lesson_key(
        7,
        "Đại7",
        "Luyện tập chung",
        5,
    ) == "T7_DAI_P005"

    assert build_lesson_key(
        8,
        "Hình8",
        "Ôn tập học kì II",
        54,
    ) == "T8_HINH_P054"

    assert build_lesson_key(
        6,
        "Nhạc6",
        "Chủ đề 1: Tuổi học trò (T1)",
        1,
    ) == "T6_NHAC_P001"

    # =========================================================
    # 4. DỮ LIỆU KHÔNG HỢP LỆ
    # =========================================================

    assert build_lesson_key(
        8,
        "",
        "Luyện tập chung",
        5,
    ) is None

    assert build_lesson_key(
        8,
        "Đại8",
        "Luyện tập chung",
        0,
    ) is None

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 70)
    print("LP-03C.6A - BUILD LESSON KEY TEST")
    print("=" * 70)

    print("- Đại7 Bài 3 -> Lesson V2: PASS")
    print("- Hình7 Bài 12 -> Lesson V2: PASS")
    print("- CN7 Bài 12 -> Lesson V2: PASS")
    print("- Hình/CN cùng Bài 12 không xung đột: PASS")

    print("- Đại7 luyện tập -> fallback: PASS")
    print("- Hình8 ôn tập -> fallback: PASS")
    print("- Nhạc6 chủ đề -> fallback: PASS")

    print("- Thiếu Môn-lớp -> None: PASS")
    print("- Tiết không hợp lệ -> None: PASS")

    print("\nKẾT QUẢ: 9/9 TEST PASS")


if __name__ == "__main__":
    main()