from dataclasses import FrozenInstanceError

from educational_planning_v2.products import TeacherPlanContext


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
    print(
        "WR-001B.3.2 - "
        "TEACHER PLAN CONTEXT CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    # TPC1 - valid context accepted
    context = TeacherPlanContext(
        school_name="THCS A",
        professional_team="To Toan - Tin",
        teacher_name="Nguyen Van A",
        academic_year="2026-2027",
    )

    passed = (
        context.school_name == "THCS A"
        and context.professional_team == "To Toan - Tin"
        and context.teacher_name == "Nguyen Van A"
        and context.academic_year == "2026-2027"
    )

    results.append(passed)

    print(
        f"TPC1 Valid context accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC2 - whitespace normalized
    context = TeacherPlanContext(
        school_name="  THCS A  ",
        professional_team="  To Toan - Tin  ",
        teacher_name="  Nguyen Van A  ",
        academic_year="  2026-2027  ",
    )

    passed = (
        context.school_name == "THCS A"
        and context.professional_team == "To Toan - Tin"
        and context.teacher_name == "Nguyen Van A"
        and context.academic_year == "2026-2027"
    )

    results.append(passed)

    print(
        f"TPC2 Whitespace normalized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC3 - empty school blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherPlanContext(
            school_name="   ",
            professional_team="To Toan - Tin",
            teacher_name="Nguyen Van A",
            academic_year="2026-2027",
        ),
    )

    results.append(passed)

    print(
        f"TPC3 Empty school blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC4 - empty professional team blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherPlanContext(
            school_name="THCS A",
            professional_team="   ",
            teacher_name="Nguyen Van A",
            academic_year="2026-2027",
        ),
    )

    results.append(passed)

    print(
        f"TPC4 Empty professional team blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC5 - empty teacher blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherPlanContext(
            school_name="THCS A",
            professional_team="To Toan - Tin",
            teacher_name="   ",
            academic_year="2026-2027",
        ),
    )

    results.append(passed)

    print(
        f"TPC5 Empty teacher blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC6 - empty academic year blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherPlanContext(
            school_name="THCS A",
            professional_team="To Toan - Tin",
            teacher_name="Nguyen Van A",
            academic_year="   ",
        ),
    )

    results.append(passed)

    print(
        f"TPC6 Empty academic year blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC7 - wrong type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherPlanContext(
            school_name=123,
            professional_team="To Toan - Tin",
            teacher_name="Nguyen Van A",
            academic_year="2026-2027",
        ),
    )

    results.append(passed)

    print(
        f"TPC7 Wrong type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TPC8 - immutable
    context = TeacherPlanContext(
        school_name="THCS A",
        professional_team="To Toan - Tin",
        teacher_name="Nguyen Van A",
        academic_year="2026-2027",
    )

    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(
            context,
            "teacher_name",
            "Another Teacher",
        ),
    )

    results.append(passed)

    print(
        f"TPC8 Context immutable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - TEACHER PLAN "
            "CONTEXT CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - TEACHER PLAN "
            "CONTEXT CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()