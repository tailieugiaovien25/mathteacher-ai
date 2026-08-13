import sys
from pathlib import Path

sys.path.insert(0, "src")

from services.lesson_objective_resolver import (
    LessonObjectiveResolver,
)
from services.mathematical_competency_selector import (
    MathematicalCompetencySelector,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def main() -> None:
    resolver = LessonObjectiveResolver()
    selector = MathematicalCompetencySelector()

    # =========================================================
    # 1. TOÀN BÀI
    # =========================================================

    lesson_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="LESSON",
        status="draft",
    )

    lesson_competencies = selector.select(
        lesson_selection
    )

    assert "NLT_TDLL" in lesson_competencies
    assert "NLT_GQVD" in lesson_competencies

    # =========================================================
    # 2. TIẾT 1
    # =========================================================

    period_1_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=1,
        status="draft",
    )

    period_1_competencies = selector.select(
        period_1_selection
    )

    assert period_1_competencies == [
        "NLT_TDLL",
    ]

    # =========================================================
    # 3. TIẾT 2
    # =========================================================

    period_2_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=2,
        status="draft",
    )

    period_2_competencies = selector.select(
        period_2_selection
    )

    assert "NLT_TDLL" in period_2_competencies
    assert "NLT_GQVD" in period_2_competencies

    # =========================================================
    # 4. TIẾT 3
    # =========================================================

    period_3_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=3,
        status="draft",
    )

    period_3_competencies = selector.select(
        period_3_selection
    )

    assert "NLT_TDLL" in period_3_competencies
    assert "NLT_GQVD" in period_3_competencies

    # =========================================================
    # 5. KHÔNG SINH MÃ NGOÀI FRAMEWORK
    # =========================================================

    allowed_codes = {
        "NLT_TDLL",
        "NLT_MHH",
        "NLT_GQVD",
        "NLT_GT",
        "NLT_CCPT",
    }

    assert set(
        lesson_competencies
    ).issubset(
        allowed_codes
    )

    # =========================================================
    # 6. KHÔNG TRÙNG MÃ
    # =========================================================

    assert (
        len(lesson_competencies)
        == len(set(lesson_competencies))
    )

    print("=" * 72)
    print(
        "LP-03F.4 - "
        "MATHEMATICAL COMPETENCY SELECTOR REAL TEST"
    )
    print("=" * 72)

    print(
        "- LESSON có NLT_TDLL: PASS"
    )
    print(
        "- LESSON có NLT_GQVD: PASS"
    )
    print(
        "- PERIOD 1 -> NLT_TDLL: PASS"
    )
    print(
        "- PERIOD 2 có TDLL + GQVD: PASS"
    )
    print(
        "- PERIOD 3 có TDLL + GQVD: PASS"
    )
    print(
        "- Không sinh mã ngoài framework: PASS"
    )
    print(
        "- Không trùng mã năng lực: PASS"
    )

    print(
        "\nKẾT QUẢ: 7/7 TEST PASS"
    )


if __name__ == "__main__":
    main()