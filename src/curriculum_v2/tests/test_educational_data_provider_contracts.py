from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
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
    print(
        "WR-001D.11B - EDUCATIONAL DATA "
        "QUERY/RESULT CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    query = EducationalDataQuery(
        capability=" learning_requirements ",
        curriculum_ref=" CURRICULUM-A ",
        subject_ref=" SUBJECT-A ",
        grade_ref=" GRADE-A ",
        version_ref=" VERSION-A ",
        filters=(
            (" status ", "VERIFIED"),
        ),
    )

    version = EducationalDataVersion(
        version_id=" V1 ",
        effective_from=" 2026-01-01 ",
    )

    provenance = EducationalDataProvenance(
        source_id=" SOURCE-A ",
        authority_type=" OFFICIAL ",
        status=" verified ",
    )

    result = EducationalDataResult(
        capability=" learning_requirements ",
        data=("A", "B"),
        provenance=provenance,
        version=version,
        status=" ok ",
    )

    checks = [
        (
            "EDC1 Query accepted",
            query.capability
            == "learning_requirements",
        ),
        (
            "EDC2 Query references normalized",
            query.curriculum_ref
            == "CURRICULUM-A",
        ),
        (
            "EDC3 Filters normalized",
            query.filters
            == (("status", "VERIFIED"),),
        ),
        (
            "EDC4 Version accepted",
            version.version_id == "V1",
        ),
        (
            "EDC5 Provenance accepted",
            provenance.source_id
            == "SOURCE-A",
        ),
        (
            "EDC6 Provenance status normalized",
            provenance.status
            == "VERIFIED",
        ),
        (
            "EDC7 Result accepted",
            result.data
            == ("A", "B"),
        ),
        (
            "EDC8 Result status normalized",
            result.status == "OK",
        ),
        (
            "EDC9 Empty capability blocked",
            expect_error(
                ValueError,
                lambda: EducationalDataQuery(
                    capability="   ",
                ),
            ),
        ),
        (
            "EDC10 Non-tuple filters blocked",
            expect_error(
                TypeError,
                lambda: EducationalDataQuery(
                    capability="X",
                    filters=[],
                ),
            ),
        ),
        (
            "EDC11 Non-tuple result data blocked",
            expect_error(
                TypeError,
                lambda: EducationalDataResult(
                    capability="X",
                    data=[],
                    provenance=provenance,
                    version=version,
                ),
            ),
        ),
        (
            "EDC12 Invalid provenance blocked",
            expect_error(
                TypeError,
                lambda: EducationalDataResult(
                    capability="X",
                    data=(),
                    provenance="bad",
                    version=version,
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

    immutable_checks = []

    for obj, field_name, new_value in (
        (query, "capability", "X"),
        (version, "version_id", "X"),
        (provenance, "source_id", "X"),
        (result, "status", "X"),
    ):
        try:
            setattr(
                obj,
                field_name,
                new_value,
            )
            immutable_checks.append(False)
        except Exception:
            immutable_checks.append(True)

    immutable = all(
        immutable_checks
    )

    results.append(immutable)

    print(
        "EDC13 Contracts immutable: "
        f"{'PASS' if immutable else 'FAIL'}"
    )

    forbidden_values = (
        "140",
        "2018",
        "5512",
        "kntt",
        "kết nối tri thức",
        ".xlsm",
        ".xlsx",
    )

    combined = (
        repr(query)
        + repr(version)
        + repr(provenance)
    ).lower()

    passed = not any(
        token in combined
        for token in forbidden_values
    )

    results.append(passed)

    print(
        "EDC14 No fixed educational value required: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - EDUCATIONAL DATA "
            "QUERY/RESULT CONTRACTS VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - EDUCATIONAL DATA "
            "QUERY/RESULT CONTRACTS VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
