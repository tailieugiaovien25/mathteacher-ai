from curriculum_v2.textbooks import (
    TextbookRequirementMapping,
    TextbookRequirementMappingProvenance,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def make_provenance():
    return TextbookRequirementMappingProvenance(
        source_document_id="SRC-MAP-MATH6-KNTT-CT2018",
        mapping_method="MANUAL_VERIFIED",
        verified_by="CURRICULUM_REVIEW",
        source_location="Bài 1",
        source_version="1.0",
    )


def make_mapping():
    return TextbookRequirementMapping(
        mapping_id="TBMAP-MATH6-KNTT-0001",
        lesson_id="TB-MATH6-KNTT-L001",
        canonical_requirement_id="YCCD-MATH-06-0001",
        provenance=make_provenance(),
        status="verified",
    )


def main():
    print("=" * 72)
    print(
        "WR-001D.7 - TEXTBOOK REQUIREMENT "
        "MAPPING CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    mapping = make_mapping()

    checks = [
        (
            "TRM1 Valid mapping accepted",
            mapping.lesson_id == "TB-MATH6-KNTT-L001",
        ),
        (
            "TRM2 Mapping ID preserved",
            mapping.mapping_id
            == "TBMAP-MATH6-KNTT-0001",
        ),
        (
            "TRM3 Canonical requirement preserved",
            mapping.canonical_requirement_id
            == "YCCD-MATH-06-0001",
        ),
        (
            "TRM4 Status normalized",
            mapping.status == "VERIFIED",
        ),
        (
            "TRM5 Provenance preserved",
            (
                mapping.provenance.mapping_method
                == "MANUAL_VERIFIED"
            ),
        ),
        (
            "TRM6 Empty mapping ID blocked",
            expect_error(
                ValueError,
                lambda: TextbookRequirementMapping(
                    mapping_id="   ",
                    lesson_id="L1",
                    canonical_requirement_id="Y1",
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "TRM7 Empty lesson ID blocked",
            expect_error(
                ValueError,
                lambda: TextbookRequirementMapping(
                    mapping_id="M1",
                    lesson_id="   ",
                    canonical_requirement_id="Y1",
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "TRM8 Empty YCCD ID blocked",
            expect_error(
                ValueError,
                lambda: TextbookRequirementMapping(
                    mapping_id="M1",
                    lesson_id="L1",
                    canonical_requirement_id="   ",
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "TRM9 Invalid provenance blocked",
            expect_error(
                TypeError,
                lambda: TextbookRequirementMapping(
                    mapping_id="M1",
                    lesson_id="L1",
                    canonical_requirement_id="Y1",
                    provenance="invalid",
                ),
            ),
        ),
        (
            "TRM10 Invalid status blocked",
            expect_error(
                ValueError,
                lambda: TextbookRequirementMapping(
                    mapping_id="M1",
                    lesson_id="L1",
                    canonical_requirement_id="Y1",
                    provenance=make_provenance(),
                    status="UNKNOWN",
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
        mapping.lesson_id = "Changed"
    except Exception:
        immutable = True

    results.append(immutable)

    print(
        "TRM11 Mapping immutable: "
        f"{'PASS' if immutable else 'FAIL'}"
    )

    provenance_immutable = False

    try:
        mapping.provenance.mapping_method = "Changed"
    except Exception:
        provenance_immutable = True

    results.append(provenance_immutable)

    print(
        "TRM12 Provenance immutable: "
        f"{'PASS' if provenance_immutable else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "TEXTBOOK REQUIREMENT MAPPING "
            "CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "TEXTBOOK REQUIREMENT MAPPING "
            "CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
