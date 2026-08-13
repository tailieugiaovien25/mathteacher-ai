from dataclasses import FrozenInstanceError

from educational_planning_v2.models.educational_plan import (
    EducationalPlan,
)
from educational_planning_v2.products import (
    TeacherEducationalPlan,
    TeacherOtherDuty,
    TeacherPlanContext,
)


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
        "WR-001B.5.2 - "
        "TEACHER EDUCATIONAL PLAN CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    context = TeacherPlanContext(
        school_name="THCS A",
        professional_team="To Toan",
        teacher_name="Nguyen Van A",
        academic_year="2026-2027",
    )

    educational_plan = EducationalPlan(
        educational_plan_id="EP-001",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
    )

    # TEP1 - valid product accepted
    product = TeacherEducationalPlan(
        product_id="TEP-001",
        context=context,
        educational_plan=educational_plan,
    )

    passed = (
        product.product_id == "TEP-001"
        and product.context is context
        and product.educational_plan is educational_plan
    )

    results.append(passed)

    print(
        f"TEP1 Valid product accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP2 - product ID normalized
    product = TeacherEducationalPlan(
        product_id="  TEP-001  ",
        context=context,
        educational_plan=educational_plan,
    )

    passed = product.product_id == "TEP-001"

    results.append(passed)

    print(
        f"TEP2 Product ID normalized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP3 - empty product ID blocked
    passed = _expect_exception(
        ValueError,
        lambda: TeacherEducationalPlan(
            product_id="   ",
            context=context,
            educational_plan=educational_plan,
        ),
    )

    results.append(passed)

    print(
        f"TEP3 Empty product ID blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP4 - wrong context type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherEducationalPlan(
            product_id="TEP-001",
            context="invalid",
            educational_plan=educational_plan,
        ),
    )

    results.append(passed)

    print(
        f"TEP4 Wrong context type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP5 - wrong educational plan type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherEducationalPlan(
            product_id="TEP-001",
            context=context,
            educational_plan="invalid",
        ),
    )

    results.append(passed)

    print(
        f"TEP5 Wrong educational plan type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP6 - default duties empty
    product = TeacherEducationalPlan(
        product_id="TEP-001",
        context=context,
        educational_plan=educational_plan,
    )

    passed = product.other_duties == ()

    results.append(passed)

    print(
        f"TEP6 Default duties empty: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP7 - valid duties accepted
    duty = TeacherOtherDuty(
        duty_id="BDHSG",
        title="Boi duong hoc sinh gioi",
    )

    product = TeacherEducationalPlan(
        product_id="TEP-001",
        context=context,
        educational_plan=educational_plan,
        other_duties=(duty,),
    )

    passed = (
        product.other_duties == (duty,)
        and product.other_duties[0] is duty
    )

    results.append(passed)

    print(
        f"TEP7 Valid duties accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP8 - duties must be tuple
    passed = _expect_exception(
        TypeError,
        lambda: TeacherEducationalPlan(
            product_id="TEP-001",
            context=context,
            educational_plan=educational_plan,
            other_duties=[duty],
        ),
    )

    results.append(passed)

    print(
        f"TEP8 Non-tuple duties blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP9 - invalid duty type blocked
    passed = _expect_exception(
        TypeError,
        lambda: TeacherEducationalPlan(
            product_id="TEP-001",
            context=context,
            educational_plan=educational_plan,
            other_duties=("invalid",),
        ),
    )

    results.append(passed)

    print(
        f"TEP9 Invalid duty type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP10 - product keeps original domain object
    product = TeacherEducationalPlan(
        product_id="TEP-001",
        context=context,
        educational_plan=educational_plan,
    )

    passed = (
        product.educational_plan
        is educational_plan
    )

    results.append(passed)

    print(
        f"TEP10 Domain object identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP11 - subject/grade remain domain-owned
    passed = (
        product.educational_plan.subject
        == "Mathematics"
        and product.educational_plan.grade
        == 6
    )

    results.append(passed)

    print(
        f"TEP11 Subject and grade domain-owned: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # TEP12 - immutable
    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(
            product,
            "product_id",
            "TEP-002",
        ),
    )

    results.append(passed)

    print(
        f"TEP12 Product immutable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - TEACHER EDUCATIONAL "
            "PLAN CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - TEACHER EDUCATIONAL "
            "PLAN CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()