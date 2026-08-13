import inspect

from curriculum_v2.providers import (
    EducationalDataProvider,
)
from curriculum_v2.providers.contracts import (
    EducationalDataQuery,
    EducationalDataResult,
)


EXPECTED_METHODS = {
    "query",
    "get_curriculum",
    "get_learning_requirements",
    "get_textbook_lessons",
    "get_textbook_requirement_mappings",
    "get_time_allocation",
}


def main():
    print("=" * 72)
    print(
        "WR-001D.11C - GENERIC EDUCATIONAL "
        "DATA PROVIDER BOUNDARY TEST"
    )
    print("=" * 72)

    results = []

    abstract_methods = set(
        EducationalDataProvider.__abstractmethods__
    )

    passed = abstract_methods == EXPECTED_METHODS
    results.append(passed)

    print(
        "EDPG1 Generic + compatibility methods locked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    query_method = EducationalDataProvider.query

    signature = inspect.signature(
        query_method
    )

    parameters = list(
        signature.parameters.values()
    )

    passed = (
        len(parameters) == 2
        and parameters[0].name == "self"
        and parameters[1].name == "query"
    )

    results.append(passed)

    print(
        "EDPG2 Generic query signature stable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    annotation = (
        signature
        .parameters["query"]
        .annotation
    )

    passed = (
        annotation
        is EducationalDataQuery
    )

    results.append(passed)

    print(
        "EDPG3 Query uses canonical query contract: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    passed = (
        signature.return_annotation
        is EducationalDataResult
    )

    results.append(passed)

    print(
        "EDPG4 Query returns canonical result contract: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    source = inspect.getsource(
        EducationalDataProvider
    ).lower()

    forbidden_tokens = (
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
    )

    violations = [
        token
        for token in forbidden_tokens
        if token in source
    ]

    passed = not violations
    results.append(passed)

    print(
        "EDPG5 Generic boundary remains data-independent: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    physical_tokens = (
        "file_path",
        "workbook",
        "worksheet",
        "database",
        "connection",
        "json_file",
        "excel_file",
    )

    parameter_names = {
        parameter.name
        for parameter in signature.parameters.values()
    }

    passed = not (
        parameter_names
        & set(physical_tokens)
    )

    results.append(passed)

    print(
        "EDPG6 Physical storage hidden: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    passed = inspect.isabstract(
        EducationalDataProvider
    )

    results.append(passed)

    print(
        "EDPG7 Provider remains abstract: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    compatibility_methods = (
        "get_curriculum",
        "get_learning_requirements",
        "get_textbook_lessons",
        "get_textbook_requirement_mappings",
        "get_time_allocation",
    )

    passed = all(
        hasattr(
            EducationalDataProvider,
            method_name,
        )
        for method_name in compatibility_methods
    )

    results.append(passed)

    print(
        "EDPG8 11A compatibility preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if violations:
        print(
            "HARD-CODE VIOLATIONS:",
            violations,
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - GENERIC EDUCATIONAL "
            "DATA PROVIDER BOUNDARY VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - GENERIC EDUCATIONAL "
            "DATA PROVIDER BOUNDARY VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
