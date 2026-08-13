import sys

sys.path.insert(0, "src")

from utils.lesson_key import extract_stream


def main() -> None:
    assert extract_stream("Đại7") == "DAI"
    assert extract_stream("Đại8") == "DAI"

    assert extract_stream("Hình7") == "HINH"
    assert extract_stream("Hình8") == "HINH"

    assert extract_stream("Toán8") == "TOAN"

    assert extract_stream("Nhạc6") == "NHAC"
    assert extract_stream("Nhạc7") == "NHAC"
    assert extract_stream("Nhạc8") == "NHAC"
    assert extract_stream("Nhạc9") == "NHAC"

    assert extract_stream("CN7") == "CN"

    assert extract_stream("") is None
    assert extract_stream(None) is None

    print("=" * 70)
    print("LP-03C.5G - STREAM GENERALIZATION TEST")
    print("=" * 70)

    print("- Đại7 -> DAI: PASS")
    print("- Đại8 -> DAI: PASS")
    print("- Hình7 -> HINH: PASS")
    print("- Hình8 -> HINH: PASS")
    print("- Toán8 -> TOAN: PASS")
    print("- Nhạc6 -> NHAC: PASS")
    print("- Nhạc7 -> NHAC: PASS")
    print("- Nhạc8 -> NHAC: PASS")
    print("- Nhạc9 -> NHAC: PASS")
    print("- CN7 -> CN: PASS")
    print("- Empty value -> None: PASS")
    print("- None value -> None: PASS")

    print("\nKẾT QUẢ: 12/12 TEST PASS")


if __name__ == "__main__":
    main()