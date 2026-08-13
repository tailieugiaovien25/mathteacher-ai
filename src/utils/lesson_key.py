import re
import unicodedata


def normalize_lesson_name(
    value: str,
) -> str:
    """Chuẩn hóa Unicode và khoảng trắng của tên bài học."""

    if not value:
        return ""

    normalized = unicodedata.normalize(
        "NFC",
        str(value),
    )

    return " ".join(
        normalized.strip().split()
    )


def extract_lesson_number(
    lesson_name: str,
) -> int | None:
    """Trích số bài từ tên bài học.

    Ví dụ:
    Bài 2. Đa thức -> 2
    Bài 12. Hình bình hành -> 12
    """

    normalized_name = normalize_lesson_name(
        lesson_name
    )

    if not normalized_name:
        return None

    match = re.search(
        r"\bbài\s+(\d+)\b",
        normalized_name,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return int(match.group(1))


def build_lesson_id(
    grade: int | str,
    lesson_name: str,
) -> str | None:
    """Tạo BAI_ID cho bài học có số.

    Ví dụ:
    grade=7
    lesson_name='Bài 2. ...'

    -> T7_B02
    """

    lesson_number = extract_lesson_number(
        lesson_name
    )

    if lesson_number is None:
        return None

    grade_text = str(grade).strip()

    if not grade_text:
        return None

    return (
        f"T{grade_text}_"
        f"B{lesson_number:02d}"
    )


def extract_stream(
    subject_grade: str,
) -> str | None:
    """Trích mã môn/phân môn từ giá trị Môn-lớp.

    Ví dụ:
    Đại8  -> DAI
    Hình8 -> HINH
    Nhạc6 -> NHAC
    CN7   -> CN
    """

    if not subject_grade:
        return None

    normalized = normalize_lesson_name(
        str(subject_grade)
    )

    # Bỏ phần số khối ở cuối.
    stream_text = re.sub(
        r"\d+$",
        "",
        normalized,
    ).strip()

    if not stream_text:
        return None

    # Chuyển Unicode có dấu sang dạng không dấu.
    decomposed = unicodedata.normalize(
        "NFD",
        stream_text,
    )

    ascii_text = "".join(
        char
        for char in decomposed
        if unicodedata.category(char) != "Mn"
    )

    # NFD không tự chuyển đ/Đ thành d/D.
    ascii_text = (
        ascii_text
        .replace("đ", "d")
        .replace("Đ", "D")
    )

    # Chỉ giữ chữ và số.
    stream_code = re.sub(
        r"[^A-Za-z0-9]+",
        "",
        ascii_text,
    ).upper()

    if not stream_code:
        return None

    return stream_code


def build_fallback_lesson_id(
    grade: int | str,
    subject_grade: str,
    period: int | str,
) -> str | None:
    """Tạo BAI_ID dự phòng cho nội dung không có số bài.

    Ví dụ:
    grade=8
    subject_grade='Hình8'
    period=52

    -> T8_HINH_P052

    grade=6
    subject_grade='Nhạc6'
    period=1

    -> T6_NHAC_P001
    """

    grade_text = str(grade).strip()

    if not grade_text:
        return None

    stream = extract_stream(
        subject_grade
    )

    if stream is None:
        return None

    try:
        period_number = int(period)
    except (TypeError, ValueError):
        return None

    if period_number <= 0:
        return None

    return (
        f"T{grade_text}_"
        f"{stream}_"
        f"P{period_number:03d}"
    )
def build_lesson_id_v2(
    grade: int | str,
    subject_grade: str,
    lesson_name: str,
) -> str | None:
    """Tạo BAI_ID v2 có chứa stream.

    Ví dụ:
    Hình7 + Bài 12 -> T7_HINH_B12
    CN7 + Bài 12   -> T7_CN_B12
    """

    lesson_number = extract_lesson_number(
        lesson_name
    )

    if lesson_number is None:
        return None

    grade_text = str(grade).strip()

    if not grade_text:
        return None

    stream = extract_stream(
        subject_grade
    )

    if stream is None:
        return None

    return (
        f"T{grade_text}_"
        f"{stream}_"
        f"B{lesson_number:02d}"
    )
def build_lesson_id_v2(
    grade: int | str,
    subject_grade: str,
    lesson_name: str,
) -> str | None:
    """Tạo BAI_ID v2 có chứa stream.

    Ví dụ:
    Hình7 + Bài 12 -> T7_HINH_B12
    CN7 + Bài 12   -> T7_CN_B12
    """

    lesson_number = extract_lesson_number(
        lesson_name
    )

    if lesson_number is None:
        return None

    grade_text = str(grade).strip()

    if not grade_text:
        return None

    stream = extract_stream(
        subject_grade
    )

    if stream is None:
        return None

    return (
        f"T{grade_text}_"
        f"{stream}_"
        f"B{lesson_number:02d}"
    )
def build_lesson_key(
    grade: int | str,
    subject_grade: str,
    lesson_name: str,
    period: int | str,
) -> str | None:
    """Tạo LessonKey chuẩn cho một dòng PPCT.

    Quy tắc:
    1. Nếu tên bài có số bài:
       -> dùng LessonKey V2.

       Ví dụ:
       Hình7 + Bài 12
       -> T7_HINH_B12

    2. Nếu tên bài không có số bài:
       -> dùng fallback theo stream + tiết.

       Ví dụ:
       Nhạc6 + Tiết 1
       -> T6_NHAC_P001
    """

    lesson_id = build_lesson_id_v2(
        grade=grade,
        subject_grade=subject_grade,
        lesson_name=lesson_name,
    )

    if lesson_id is not None:
        return lesson_id

    return build_fallback_lesson_id(
        grade=grade,
        subject_grade=subject_grade,
        period=period,
    )