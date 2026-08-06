import sys
from pathlib import Path

sys.path.insert(0, "src")

from intelligence.lesson_model_builder import LessonModelBuilder


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)
SHEET_NAME = "LuuBG"

TEST_CASES = (
    {
        "row": 81,
        "grade": "8C4",
        "lesson_name": "Bài 2. Đa thức (tiết 1)",
        "period_count": 2,
        "subject_area": "Đại",
        "period_number": 1,
    },
    {
        "row": 82,
        "grade": "8C4",
        "lesson_name": "Bài 2. Đa thức (tiết 2)",
        "period_count": 2,
        "subject_area": "Đại",
        "period_number": 2,
    },
    {
        "row": 83,
        "grade": "8C4",
        "lesson_name": "Bài 11. Hình thang cân (tiết 2)",
        "period_count": 2,
        "subject_area": "Hình",
        "period_number": 2,
    },
    {
        "row": 150,
        "grade": "8C4",
        "lesson_name": "Bài 12. Hình bình hành (tiết 1)",
        "period_count": 3,
        "subject_area": "Hình",
        "period_number": 1,
    },
    {
        "row": 151,
        "grade": "8C4",
        "lesson_name": "Bài 12. Hình bình hành (tiết 2)",
        "period_count": 3,
        "subject_area": "Hình",
        "period_number": 2,
    },
)


def main() -> None:
    """Kiểm thử LessonModelBuilder trên nhiều hàng LuuBG."""
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file Excel: {EXCEL_FILE}"
        )

    builder = LessonModelBuilder()

    print("=" * 70)
    print("AI-101.5 - MULTI-ROW LESSON MODEL TEST")
    print("=" * 70)

    passed = 0

    for case in TEST_CASES:
        row = case["row"]

        lesson = builder.build_from_luubg_row(
            file_path=str(EXCEL_FILE),
            sheet_name=SHEET_NAME,
            data_row=row,
        )

        assert lesson.subject == "Toán"
        assert lesson.grade == case["grade"]
        assert lesson.lesson_name == case["lesson_name"]
        assert lesson.period_count == case["period_count"]
        assert lesson.metadata["subject_area"] == case["subject_area"]
        assert lesson.metadata["period_number"] == case["period_number"]
        assert not lesson.warnings

        passed += 1

        print(
            f"- Hàng {row}: PASS | "
            f"{lesson.lesson_name}"
        )

    print("\n" + "=" * 70)
    print(
        f"KẾT QUẢ: {passed}/{len(TEST_CASES)} TEST PASS"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()