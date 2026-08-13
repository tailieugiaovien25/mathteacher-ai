from educational_planning_v2.builders.teacher_educational_plan_builder import (
    TeacherEducationalPlanBuilder,
)
from educational_planning_v2.models.educational_plan import (
    EducationalPlan,
)
from educational_planning_v2.products import (
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
        "WR-001C.1 - "
        "TEACHER EDUCATIONAL PLAN PRODUCT BUILDER TEST"
    )
    print("=" * 72)

    results = []

    builder = TeacherEducationalPlanBuilder()

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

    # B1 - valid product built
    product = builder.build(
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
        f"B1 Valid product built: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B2 - domain identity preserved
    passed = (
        product.educational_plan
        is educational_plan
    )
    results.append(passed)
    print(
        f"B2 Domain identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B3 - default duties preserved
    passed = product.other_duties == ()
    results.append(passed)
    print(
        f"B3 Default duties preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B4 - valid duties passed through
    duty = TeacherOtherDuty(
        duty_id="BDHSG",
        title="Boi duong hoc sinh gioi",
    )

    product_with_duty = builder.build(
        product_id="TEP-002",
        context=context,
        educational_plan=educational_plan,
        other_duties=(duty,),
    )

    passed = (
        product_with_duty.other_duties == (duty,)
        and product_with_duty.other_duties[0] is duty
    )
    results.append(passed)
    print(
        f"B4 Other duties preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B5 - academic year mismatch blocked
    wrong_context = TeacherPlanContext(
        school_name="THCS A",
        professional_team="To Toan",
        teacher_name="Nguyen Van A",
        academic_year="2025-2026",
    )

    passed = _expect_exception(
        ValueError,
        lambda: builder.build(
            product_id="TEP-003",
            context=wrong_context,
            educational_plan=educational_plan,
        ),
    )
    results.append(passed)
    print(
        f"B5 Academic year mismatch blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B6 - wrong context type blocked
    passed = _expect_exception(
        TypeError,
        lambda: builder.build(
            product_id="TEP-004",
            context="invalid",
            educational_plan=educational_plan,
        ),
    )
    results.append(passed)
    print(
        f"B6 Wrong context type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B7 - wrong domain type blocked
    passed = _expect_exception(
        TypeError,
        lambda: builder.build(
            product_id="TEP-005",
            context=context,
            educational_plan="invalid",
        ),
    )
    results.append(passed)
    print(
        f"B7 Wrong domain type blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # B8 - metadata copied
    metadata = {
        "source": "WR-001",
    }

    product_with_metadata = builder.build(
        product_id="TEP-006",
        context=context,
        educational_plan=educational_plan,
        metadata=metadata,
    )

    metadata["source"] = "changed"

    passed = (
        product_with_metadata.metadata["source"]
        == "WR-001"
    )
    results.append(passed)
    print(
        f"B8 Metadata input isolated: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - TEACHER EDUCATIONAL "
            "PLAN PRODUCT BUILDER VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - TEACHER EDUCATIONAL "
            "PLAN PRODUCT BUILDER VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
