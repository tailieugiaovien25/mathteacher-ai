import inspect

from curriculum_v2.authority import (
    AuthorityDataSource,
)


EXPECTED_METHODS = {
    "requirements_for_grade",
    "requirement_by_id",
    "nodes_for_grade",
    "node_by_id",
    "time_allocation",
}


def main():
    print("=" * 72)
    print(
        "WR-001D.12C.4 - AUTHORITY DATA SOURCE "
        "TIME ALLOCATION CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    passed = inspect.isabstract(
        AuthorityDataSource
    )
    results.append(passed)

    print(
        "ADS1 Contract is abstract: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    methods = set(
        AuthorityDataSource.__abstractmethods__
    )

    passed = methods == EXPECTED_METHODS
    results.append(passed)

    print(
        "ADS2 Required read capabilities locked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    try:
        AuthorityDataSource()
        passed = False
    except TypeError:
        passed = True

    results.append(passed)

    print(
        "ADS3 Abstract source cannot instantiate: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    keyword_only = True

    for method_name in EXPECTED_METHODS:
        signature = inspect.signature(
            getattr(
                AuthorityDataSource,
                method_name,
            )
        )

        parameters = list(
            signature.parameters.values()
        )[1:]

        for parameter in parameters:
            if (
                parameter.kind
                != inspect.Parameter.KEYWORD_ONLY
            ):
                keyword_only = False

    results.append(keyword_only)

    print(
        "ADS4 Query parameters keyword-only: "
        f"{'PASS' if keyword_only else 'FAIL'}"
    )

    source = inspect.getsource(
        AuthorityDataSource
    ).lower()

    forbidden = (
        "openpyxl",
        "load_workbook",
        "json.load",
        ".json",
        ".xlsm",
        ".xlsx",
        "data/input/",
        "data\\input\\",
        "path(",
        "open(",
        "kntt",
        "kết nối tri thức",
        "140",
        "105",
        "70",
        "35",
        "5512",
        "2018",
    )

    violations = [
        token
        for token in forbidden
        if token in source
    ]

    passed = not violations
    results.append(passed)

    print(
        "ADS5 Physical storage hidden: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    passed = (
        "time_allocation"
        in methods
    )

    results.append(passed)

    print(
        "ADS6 Time allocation authority capability available: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    signature = inspect.signature(
        AuthorityDataSource.time_allocation
    )

    passed = all(
        name in signature.parameters
        for name in (
            "curriculum_ref",
            "subject_ref",
            "grade",
        )
    )

    results.append(passed)

    print(
        "ADS7 Allocation selected by logical references: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if violations:
        print(
            "VIOLATIONS:",
            violations,
        )

    if all(results):
        print(
            "RESULT: PASS - AUTHORITY DATA SOURCE "
            "TIME ALLOCATION CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - AUTHORITY DATA SOURCE "
            "TIME ALLOCATION CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
