import sys

sys.path.insert(0, "src")

from models.lesson_objective_selection import (
    LessonObjectiveSelection,
)


def expect_value_error(
    selection: LessonObjectiveSelection,
) -> None:
    try:
        selection.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. MODE LESSON HỢP LỆ
    # =========================================================

    lesson_selection = LessonObjectiveSelection(
        lesson_key="T7_DAI_B03",
        mode="LESSON",
        period_in_lesson=None,
        yccd_records=[],
    )

    lesson_selection.validate()

    # =========================================================
    # 2. MODE PERIOD HỢP LỆ
    # =========================================================

    period_selection = LessonObjectiveSelection(
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=2,
        yccd_records=[],
    )

    period_selection.validate()

    # =========================================================
    # 3. MODE KHÔNG HỢP LỆ
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="T7_DAI_B03",
            mode="ALL",
            period_in_lesson=None,
            yccd_records=[],
        )
    )

    # =========================================================
    # 4. LESSON KHÔNG ĐƯỢC CÓ TIẾT
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="T7_DAI_B03",
            mode="LESSON",
            period_in_lesson=1,
            yccd_records=[],
        )
    )

    # =========================================================
    # 5. PERIOD BẮT BUỘC CÓ TIẾT
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="T7_DAI_B03",
            mode="PERIOD",
            period_in_lesson=None,
            yccd_records=[],
        )
    )

    # =========================================================
    # 6. PERIOD = 0 BỊ TỪ CHỐI
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="T7_DAI_B03",
            mode="PERIOD",
            period_in_lesson=0,
            yccd_records=[],
        )
    )

    # =========================================================
    # 7. PERIOD KHÔNG PHẢI SỐ
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="T7_DAI_B03",
            mode="PERIOD",
            period_in_lesson="abc",
            yccd_records=[],
        )
    )

    # =========================================================
    # 8. LESSON_KEY RỖNG
    # =========================================================

    expect_value_error(
        LessonObjectiveSelection(
            lesson_key="",
            mode="LESSON",
            period_in_lesson=None,
            yccd_records=[],
        )
    )

    print("=" * 70)
    print(
        "LP-03E.1 - "
        "LESSON OBJECTIVE SELECTION TEST"
    )
    print("=" * 70)

    print("- Mode LESSON hợp lệ: PASS")
    print("- Mode PERIOD hợp lệ: PASS")
    print("- Mode sai bị từ chối: PASS")
    print("- LESSON không được có tiết: PASS")
    print("- PERIOD bắt buộc có tiết: PASS")
    print("- PERIOD = 0 bị từ chối: PASS")
    print("- PERIOD không phải số bị từ chối: PASS")
    print("- LESSON_KEY rỗng bị từ chối: PASS")

    print(
        "\nKẾT QUẢ: 8/8 TEST PASS"
    )


if __name__ == "__main__":
    main()