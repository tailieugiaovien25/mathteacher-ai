import sys

sys.path.insert(0, "src")

from utils.lesson_key import (
    build_fallback_lesson_id,
    build_lesson_id,
    extract_lesson_number,
    extract_stream,
    normalize_lesson_name,
)


def main() -> None:
    # =========================================================
    # 1. TEST TRÍCH SỐ BÀI
    # =========================================================

    assert extract_lesson_number(
        "Bài 2. Đa thức"
    ) == 2

    assert extract_lesson_number(
        "Bài 12. Hình bình hành"
    ) == 12

    assert extract_lesson_number(
        "bài 7. Số thực"
    ) == 7

    assert extract_lesson_number(
        "Luyện tập chung"
    ) is None

    # =========================================================
    # 2. TEST TẠO BAI_ID CHO BÀI CÓ SỐ
    # =========================================================

    assert build_lesson_id(
        7,
        "Bài 2. Cộng, trừ, nhân, chia số hữu tỉ",
    ) == "T7_B02"

    assert build_lesson_id(
        8,
        "Bài 12. Hình bình hành",
    ) == "T8_B12"

    assert build_lesson_id(
        "9",
        "Bài 3. Căn thức",
    ) == "T9_B03"

    assert build_lesson_id(
        7,
        "Luyện tập chung",
    ) is None

    # =========================================================
    # 3. TEST UNICODE DECOMPOSED
    # =========================================================

    decomposed_name = (
        "Ba\u0300i 3. "
        "Lu\u0303y thu\u0300a vo\u0301i "
        "so\u0302\u0301 mu\u0303 tu\u031b\u0323 nhie\u0302n"
    )

    normalized_name = normalize_lesson_name(
        decomposed_name
    )

    assert normalized_name.startswith(
        "Bài 3."
    )

    assert extract_lesson_number(
        decomposed_name
    ) == 3

    assert build_lesson_id(
        7,
        decomposed_name,
    ) == "T7_B03"

    # =========================================================
    # 4. TEST STREAM
    # =========================================================

    assert extract_stream("Đại7") == "DAI"
    assert extract_stream("Đại8") == "DAI"

    assert extract_stream("Hình7") == "HINH"
    assert extract_stream("Hình8") == "HINH"

    assert extract_stream("Toán8") is None

    # =========================================================
    # 5. TEST FALLBACK ID
    # =========================================================

    dai_52 = build_fallback_lesson_id(
        8,
        "Đại8",
        52,
    )

    hinh_52 = build_fallback_lesson_id(
        8,
        "Hình8",
        52,
    )

    assert dai_52 == "T8_DAI_P052"
    assert hinh_52 == "T8_HINH_P052"

    assert build_fallback_lesson_id(
        7,
        "Đại7",
        5,
    ) == "T7_DAI_P005"

    assert build_fallback_lesson_id(
        7,
        "Hình7",
        5,
    ) == "T7_HINH_P005"

    # Hai phân môn cùng tiết không được trùng ID.
    assert dai_52 != hinh_52

    # Dữ liệu không hợp lệ phải trả về None.
    assert build_fallback_lesson_id(
        8,
        "Toán8",
        52,
    ) is None

    assert build_fallback_lesson_id(
        8,
        "Đại8",
        0,
    ) is None

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 70)
    print("LP-03C - LESSON KEY TEST")
    print("=" * 70)

    print("- Trích số bài 1 chữ số: PASS")
    print("- Trích số bài 2 chữ số: PASS")
    print("- Không phân biệt hoa/thường: PASS")
    print("- Luyện tập không sinh BAI_ID: PASS")

    print("- Tạo T7_B02: PASS")
    print("- Tạo T8_B12: PASS")
    print("- Tạo T9_B03: PASS")
    print("- Trường hợp không có số bài: PASS")

    print("- Chuẩn hóa Unicode decomposed: PASS")
    print("- Trích số bài từ Unicode decomposed: PASS")
    print("- Sinh ID từ Unicode decomposed: PASS")

    print("- Nhận diện Đại7: PASS")
    print("- Nhận diện Đại8: PASS")
    print("- Nhận diện Hình7: PASS")
    print("- Nhận diện Hình8: PASS")
    print("- Stream không xác định: PASS")

    print("- Fallback Đại8 tiết 52: PASS")
    print("- Fallback Hình8 tiết 52: PASS")
    print("- Fallback Đại7 tiết 5: PASS")
    print("- Fallback Hình7 tiết 5: PASS")
    print("- Đại/Hình cùng tiết không trùng ID: PASS")
    print("- Stream không hợp lệ: PASS")
    print("- Tiết không hợp lệ: PASS")

    print("\nKẾT QUẢ: 23/23 TEST PASS")


if __name__ == "__main__":
    main()