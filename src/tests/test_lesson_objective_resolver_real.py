import sys
from pathlib import Path

sys.path.insert(0, "src")

from services.lesson_objective_resolver import (
    LessonObjectiveResolver,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def expect_value_error(
    callback,
) -> None:
    try:
        callback()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but no error was raised."
    )


def main() -> None:
    resolver = LessonObjectiveResolver()

    # =========================================================
    # 1. TOÀN BÀI
    # =========================================================

    lesson = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="LESSON",
        status="draft",
    )

    assert lesson.mode == "LESSON"
    assert lesson.period_in_lesson is None

    assert lesson.yccd_ids == [
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    ]

    # =========================================================
    # 2. TIẾT 1
    # =========================================================

    period_1 = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=1,
        status="draft",
    )

    assert period_1.mode == "PERIOD"
    assert period_1.period_in_lesson == 1

    assert period_1.yccd_ids == [
        "T7_DAI_B03_Y01",
    ]

    # =========================================================
    # 3. TIẾT 2
    # =========================================================

    period_2 = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=2,
        status="draft",
    )

    assert period_2.yccd_ids == [
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
    ]

    # =========================================================
    # 4. TIẾT 3
    # =========================================================

    period_3 = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=3,
        status="draft",
    )

    assert period_3.yccd_ids == [
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    ]

    # =========================================================
    # 5. TIẾT KHÔNG TỒN TẠI
    # =========================================================

    expect_value_error(
        lambda: resolver.get_objectives(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
            mode="PERIOD",
            period_in_lesson=4,
            status="draft",
        )
    )

    # =========================================================
    # 6. MODE SAI
    # =========================================================

    expect_value_error(
        lambda: resolver.get_objectives(
            file_path=EXCEL_FILE,
            lesson_key="T7_DAI_B03",
            mode="ABC",
            status="draft",
        )
    )

    # =========================================================
    # 7. BÀI KHÔNG TỒN TẠI
    # =========================================================

    expect_value_error(
        lambda: resolver.get_objectives(
            file_path=EXCEL_FILE,
            lesson_key="NOT_FOUND",
            mode="LESSON",
            status="draft",
        )
    )

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 72)
    print(
        "LP-03E.2B - "
        "LESSON OBJECTIVE RESOLVER REAL TEST"
    )
    print("=" * 72)

    print(
        "- LESSON -> Y01 + Y02 + Y03: PASS"
    )
    print(
        "- PERIOD 1 -> Y01: PASS"
    )
    print(
        "- PERIOD 2 -> Y01 + Y02: PASS"
    )
    print(
        "- PERIOD 3 -> Y02 + Y03: PASS"
    )
    print(
        "- PERIOD 4 không tồn tại bị chặn: PASS"
    )
    print(
        "- Mode sai bị chặn: PASS"
    )
    print(
        "- LESSON_KEY không tồn tại bị chặn: PASS"
    )

    print(
        "\nKẾT QUẢ: 7/7 TEST PASS"
    )


if __name__ == "__main__":
    main()