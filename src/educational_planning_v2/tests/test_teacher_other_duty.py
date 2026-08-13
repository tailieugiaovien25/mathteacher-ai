from dataclasses import FrozenInstanceError

from educational_planning_v2.products import TeacherOtherDuty


def _expect_exception(exception_type, action):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 72)
    print("WR-001B.4.2 - TEACHER OTHER DUTY CONTRACT TEST")
    print("=" * 72)

    results = []

    # TOD1 - valid duty accepted
    duty = TeacherOtherDuty(
        duty_id="BDHSG",
        title="Boi duong hoc sinh gioi",
        description="Thuc hien theo ke hoach",
    )
    passed = (
        duty.duty_id == "BDHSG"
        and duty.title == "Boi duong hoc sinh gioi"
        and duty.description == "Thuc hien theo ke hoach"
    )
    results.append(passed)
    print(f"TOD1 Valid duty accepted: {'PASS' if passed else 'FAIL'}")

    # TOD2 - whitespace normalized
    duty = TeacherOtherDuty(
        duty_id="  BDHSG  ",
        title="  Boi duong hoc sinh gioi  ",
        description="  Thuc hien theo ke hoach  ",
    )
    passed = (
        duty.duty_id == "BDHSG"
        and duty.title == "Boi duong hoc sinh gioi"
        and duty.description == "Thuc hien theo ke hoach"
    )
    results.append(passed)
    print(f"TOD2 Whitespace normalized: {'PASS' if passed else 'FAIL'}")

    # TOD3 - empty duty_id blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherOtherDuty(
            duty_id="   ",
            title="Boi duong hoc sinh gioi",
        ),
    )
    results.append(passed)
    print(f"TOD3 Empty duty ID blocked: {'PASS' if passed else 'FAIL'}")

    # TOD4 - empty title blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherOtherDuty(
            duty_id="BDHSG",
            title="   ",
        ),
    )
    results.append(passed)
    print(f"TOD4 Empty title blocked: {'PASS' if passed else 'FAIL'}")

    # TOD5 - description may be empty
    duty = TeacherOtherDuty(
        duty_id="BDHSG",
        title="Boi duong hoc sinh gioi",
    )
    passed = duty.description == ""
    results.append(passed)
    print(f"TOD5 Empty description accepted: {'PASS' if passed else 'FAIL'}")

    # TOD6 - wrong duty_id type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherOtherDuty(
            duty_id=123,
            title="Boi duong hoc sinh gioi",
        ),
    )
    results.append(passed)
    print(f"TOD6 Wrong duty ID type blocked: {'PASS' if passed else 'FAIL'}")

    # TOD7 - wrong description type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherOtherDuty(
            duty_id="BDHSG",
            title="Boi duong hoc sinh gioi",
            description=None,
        ),
    )
    results.append(passed)
    print(
        f"TOD7 Wrong description type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TOD8 - immutable
    duty = TeacherOtherDuty(
        duty_id="BDHSG",
        title="Boi duong hoc sinh gioi",
    )
    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(duty, "title", "Changed"),
    )
    results.append(passed)
    print(f"TOD8 Duty immutable: {'PASS' if passed else 'FAIL'}")

    print()

    if all(results):
        print("RESULT: PASS - TEACHER OTHER DUTY CONTRACT VERIFIED")
    else:
        print("RESULT: FAIL - TEACHER OTHER DUTY CONTRACT VIOLATED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()