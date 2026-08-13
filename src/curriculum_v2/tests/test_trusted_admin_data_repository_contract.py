from __future__ import annotations

import inspect

from curriculum_v2.governance.trusted_admin_data_repository import (
    TrustedAdministrativeDataRepository,
)


def check(label: str, condition: bool) -> bool:
    result = "PASS" if condition else "FAIL"
    print(f"{label}: {result}")
    return condition


def main() -> None:
    print("=" * 72)
    print(
        "WR-001D.12C.6A.2 - "
        "TRUSTED ADMIN DATA REPOSITORY CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    results.append(
        check(
            "TADR1 Contract is abstract",
            inspect.isabstract(
                TrustedAdministrativeDataRepository
            ),
        )
    )

    abstract_methods = (
        TrustedAdministrativeDataRepository.__abstractmethods__
    )

    results.append(
        check(
            "TADR2 Required persistence capabilities locked",
            abstract_methods
            == {
                "save",
                "get",
                "list_records",
                "delete",
            },
        )
    )

    try:
        TrustedAdministrativeDataRepository()
        cannot_instantiate = False
    except TypeError:
        cannot_instantiate = True

    results.append(
        check(
            "TADR3 Abstract repository cannot instantiate",
            cannot_instantiate,
        )
    )

    save_signature = inspect.signature(
        TrustedAdministrativeDataRepository.save
    )
    get_signature = inspect.signature(
        TrustedAdministrativeDataRepository.get
    )
    list_signature = inspect.signature(
        TrustedAdministrativeDataRepository.list_records
    )
    delete_signature = inspect.signature(
        TrustedAdministrativeDataRepository.delete
    )

    def keyword_only_after_self(signature) -> bool:
        parameters = list(signature.parameters.values())

        if not parameters:
            return False

        if parameters[0].name != "self":
            return False

        return all(
            parameter.kind
            == inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters[1:]
        )

    results.append(
        check(
            "TADR4 Save parameters keyword-only",
            keyword_only_after_self(save_signature),
        )
    )

    results.append(
        check(
            "TADR5 Read parameters keyword-only",
            keyword_only_after_self(get_signature)
            and keyword_only_after_self(list_signature),
        )
    )

    results.append(
        check(
            "TADR6 Delete parameters keyword-only",
            keyword_only_after_self(delete_signature),
        )
    )

    source = inspect.getsource(
        TrustedAdministrativeDataRepository
    ).lower()

    forbidden_storage_terms = (
        "openpyxl",
        "load_workbook",
        "worksheet",
        "workbook",
        ".xlsx",
        ".xlsm",
        "sqlite",
        "sqlalchemy",
        "postgres",
        "json.load",
        "json.dump",
        "file_path",
    )

    results.append(
        check(
            "TADR7 Physical storage hidden",
            not any(
                term in source
                for term in forbidden_storage_terms
            ),
        )
    )

    forbidden_educational_values = (
        "140",
        "mathematics",
        "toán",
        "grade 6",
        "yccd",
        "lesson_key",
        "curriculum-math-2018",
    )

    results.append(
        check(
            "TADR8 No concrete educational value encoded",
            not any(
                value in source
                for value in forbidden_educational_values
            ),
        )
    )

    class_metadata = {
        "__module__",
        "__doc__",
        "__abstractmethods__",
        "_abc_impl",
        "__dict__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }

    unexpected_private_state = {
        name
        for name in vars(
            TrustedAdministrativeDataRepository
        )
        if name.startswith("_")
        and name not in class_metadata
    }

    results.append(
        check(
            "TADR9 Contract owns no repository state",
            not unexpected_private_state,
        )
    )

    results.append(
        check(
            "TADR10 Logical identity used instead of physical path",
            "record_id" in save_signature.parameters
            and "record_id" in get_signature.parameters
            and "record_id" in delete_signature.parameters
            and "file_path" not in save_signature.parameters
            and "file_path" not in get_signature.parameters
            and "file_path" not in delete_signature.parameters,
        )
    )

    results.append(
        check(
            "TADR11 Repository is educational-data-type neutral",
            "record_type"
            in list_signature.parameters,
        )
    )

    passed = all(results)

    print()

    if passed:
        print(
            "RESULT: PASS - TRUSTED ADMIN DATA "
            "REPOSITORY CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - TRUSTED ADMIN DATA "
        "REPOSITORY CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
