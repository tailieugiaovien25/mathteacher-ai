from educational_planning_v2.products.teacher_plan_enrichment import (
    TeacherPlanEnrichment,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False
    return False


def main():
    print("=" * 72)
    print("WR-001C.13 - TEACHER PLAN ENRICHMENT CONTRACT TEST")
    print("=" * 72)

    results = []

    value = TeacherPlanEnrichment(
        default_teaching_location="  Phòng học  ",
        default_teaching_equipment=(
            "  Máy chiếu  ",
            "Thước thẳng",
        ),
    )

    checks = [
        (
            "TPE1 Valid enrichment accepted",
            value.default_teaching_location == "Phòng học",
        ),
        (
            "TPE2 Location normalized",
            value.default_teaching_location == "Phòng học",
        ),
        (
            "TPE3 Equipment normalized",
            value.default_teaching_equipment
            == ("Máy chiếu", "Thước thẳng"),
        ),
        (
            "TPE4 Empty defaults accepted",
            TeacherPlanEnrichment()
            == TeacherPlanEnrichment(
                default_teaching_location=None,
                default_teaching_equipment=(),
            ),
        ),
        (
            "TPE5 Wrong equipment container blocked",
            expect_error(
                TypeError,
                lambda: TeacherPlanEnrichment(
                    default_teaching_equipment=["Máy chiếu"],
                ),
            ),
        ),
        (
            "TPE6 Empty location blocked",
            expect_error(
                ValueError,
                lambda: TeacherPlanEnrichment(
                    default_teaching_location="   ",
                ),
            ),
        ),
        (
            "TPE7 Invalid equipment item blocked",
            expect_error(
                TypeError,
                lambda: TeacherPlanEnrichment(
                    default_teaching_equipment=(123,),
                ),
            ),
        ),
    ]

    for label, passed in checks:
        results.append(passed)
        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    immutable = False

    try:
        value.default_teaching_location = "Khác"
    except Exception:
        immutable = True

    results.append(immutable)

    print(
        "TPE8 Enrichment immutable: "
        f"{'PASS' if immutable else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "TEACHER PLAN ENRICHMENT CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "TEACHER PLAN ENRICHMENT CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
