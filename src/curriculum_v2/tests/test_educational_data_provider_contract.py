import inspect

from curriculum_v2.providers import (
    EducationalDataProvider,
)


EXPECTED_COMPATIBILITY_METHODS = {
    "get_curriculum",
    "get_learning_requirements",
    "get_textbook_lessons",
    "get_textbook_requirement_mappings",
    "get_time_allocation",
}

EXPECTED_ABSTRACT_METHODS = (
    EXPECTED_COMPATIBILITY_METHODS
    | {"query"}
)


FORBIDDEN_CONTRACT_TOKENS = (
    "140",
    "2018",
    "5512",
    "7991",
    "kntt",
    "kết nối tri thức",
    "lbg-tuyen",
    ".xlsx",
    ".xlsm",
    "openpyxl",
    "load_workbook",
    "worksheet",
)


def main():
    print("=" * 72)
    print(
        "WR-001D.11A - EDUCATIONAL DATA "
        "PROVIDER CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    # --------------------------------------------------------
    # EDP1 - abstract contract
    # --------------------------------------------------------

    passed = inspect.isabstract(
        EducationalDataProvider
    )
    results.append(passed)

    print(
        "EDP1 Provider is abstract: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP2 - required capabilities
    # --------------------------------------------------------

    abstract_methods = set(
        EducationalDataProvider.__abstractmethods__
    )

    passed = (
        abstract_methods
        == EXPECTED_ABSTRACT_METHODS
    )
    results.append(passed)

    print(
        "EDP2 Required capabilities locked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP3 - cannot instantiate contract
    # --------------------------------------------------------

    try:
        EducationalDataProvider()
        passed = False
    except TypeError:
        passed = True

    results.append(passed)

    print(
        "EDP3 Abstract provider cannot instantiate: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP4 - no physical source parameters
    # --------------------------------------------------------

    forbidden_parameters = {
        "file_path",
        "path",
        "workbook",
        "worksheet",
        "sheet",
        "json_file",
        "excel_file",
        "database",
        "connection",
    }

    violations = []

    for method_name in EXPECTED_ABSTRACT_METHODS:
        method = getattr(
            EducationalDataProvider,
            method_name,
        )

        signature = inspect.signature(
            method
        )

        parameter_names = set(
            signature.parameters
        )

        found = (
            parameter_names
            & forbidden_parameters
        )

        if found:
            violations.append(
                (
                    method_name,
                    sorted(found),
                )
            )

    passed = not violations
    results.append(passed)

    print(
        "EDP4 Physical storage hidden: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP5 - no concrete educational values
    # --------------------------------------------------------

    source = inspect.getsource(
        EducationalDataProvider
    ).lower()

    token_violations = [
        token
        for token in FORBIDDEN_CONTRACT_TOKENS
        if token.lower() in source
    ]

    passed = not token_violations
    results.append(passed)

    print(
        "EDP5 No concrete educational data hard-coded: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP6 - compatibility methods remain keyword-only
    # --------------------------------------------------------

    keyword_only_valid = True

    for method_name in EXPECTED_COMPATIBILITY_METHODS:
        method = getattr(
            EducationalDataProvider,
            method_name,
        )

        signature = inspect.signature(
            method
        )

        parameters = list(
            signature.parameters.values()
        )[1:]

        for parameter in parameters:
            if (
                parameter.kind
                != inspect.Parameter.KEYWORD_ONLY
            ):
                keyword_only_valid = False

    results.append(keyword_only_valid)

    print(
        "EDP6 Compatibility query parameters keyword-only: "
        f"{'PASS' if keyword_only_valid else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP7 - provider owns no runtime data
    # --------------------------------------------------------

    passed = not hasattr(
        EducationalDataProvider,
        "__dataclass_fields__",
    )

    results.append(passed)

    print(
        "EDP7 Contract owns no dataset state: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP8 - curriculum remains reference-selected
    # --------------------------------------------------------

    curriculum_signature = inspect.signature(
        EducationalDataProvider.get_curriculum
    )

    passed = (
        "curriculum_ref"
        in curriculum_signature.parameters
    )

    results.append(passed)

    print(
        "EDP8 Curriculum selected by reference: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # EDP9 - generic boundary exists
    # --------------------------------------------------------

    passed = (
        "query"
        in abstract_methods
    )

    results.append(passed)

    print(
        "EDP9 Generic query boundary available: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()

    if violations:
        print(
            "PHYSICAL PARAMETER VIOLATIONS:",
            violations,
        )

    if token_violations:
        print(
            "HARD-CODE TOKEN VIOLATIONS:",
            token_violations,
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - EDUCATIONAL DATA "
            "PROVIDER CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - EDUCATIONAL DATA "
            "PROVIDER CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
