from __future__ import annotations

from abc import ABC
import inspect

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


def main():
    print("=" * 72)
    print(
        "MVP-OPS-001A.5 - "
        "OPERATIONAL DATA SOURCE REPOSITORY CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    tests.append((
        "ODR1 Repository is abstract",
        issubclass(
            OperationalDataSourceRepository,
            ABC,
        ),
    ))

    abstract_methods = (
        OperationalDataSourceRepository
        .__abstractmethods__
    )

    tests.append((
        "ODR2 Required repository capabilities locked",
        abstract_methods
        == {
            "save",
            "get",
            "list_sources",
            "delete",
        },
    ))

    tests.append((
        "ODR3 Abstract repository cannot instantiate",
        _cannot_instantiate(),
    ))

    save_signature = inspect.signature(
        OperationalDataSourceRepository.save
    )

    tests.append((
        "ODR4 Save uses keyword-only source",
        _keyword_only_parameter(
            save_signature,
            "source",
        ),
    ))

    get_signature = inspect.signature(
        OperationalDataSourceRepository.get
    )

    tests.append((
        "ODR5 Get uses keyword-only logical source ID",
        _keyword_only_parameter(
            get_signature,
            "source_id",
        ),
    ))

    list_signature = inspect.signature(
        OperationalDataSourceRepository.list_sources
    )

    tests.append((
        "ODR6 List filters are keyword-only",
        all(
            _keyword_only_parameter(
                list_signature,
                name,
            )
            for name in (
                "owner_id",
                "academic_year",
                "data_type",
                "status",
            )
        ),
    ))

    delete_signature = inspect.signature(
        OperationalDataSourceRepository.delete
    )

    tests.append((
        "ODR7 Delete uses keyword-only logical source ID",
        _keyword_only_parameter(
            delete_signature,
            "source_id",
        ),
    ))

    source_annotation = (
        save_signature.parameters[
            "source"
        ].annotation
    )

    tests.append((
        "ODR8 Save accepts OperationalDataSource",
        (
            source_annotation
            is OperationalDataSource
            or
            source_annotation
            == "OperationalDataSource"
        ),
    ))

    return_annotation = (
        save_signature.return_annotation
    )

    tests.append((
        "ODR9 Save returns OperationalDataSource",
        (
            return_annotation
            is OperationalDataSource
            or
            return_annotation
            == "OperationalDataSource"
        ),
    ))

    list_return = (
        list_signature.return_annotation
    )

    tests.append((
        "ODR10 List returns immutable tuple contract",
        (
            list_return
            == tuple[
                OperationalDataSource,
                ...
            ]
            or
            list_return
            == "tuple[OperationalDataSource, ...]"
        ),
    ))

    data_type_annotation = (
        list_signature.parameters[
            "data_type"
        ].annotation
    )

    tests.append((
        "ODR11 Data type filter is logical",
        (
            "OperationalDataType"
            in str(data_type_annotation)
        ),
    ))

    status_annotation = (
        list_signature.parameters[
            "status"
        ].annotation
    )

    tests.append((
        "ODR12 Status filter is logical",
        (
            "OperationalDataStatus"
            in str(status_annotation)
        ),
    ))

    source_text = inspect.getsource(
        OperationalDataSourceRepository
    )

    forbidden_storage_tokens = (
        "sqlite3",
        "supabase",
        "openpyxl",
        "googleapiclient",
        "streamlit",
        ".xlsx",
        ".docx",
        "Path(",
        "open(",
        "SELECT ",
        "INSERT ",
        "UPDATE ",
        "DELETE FROM",
    )

    tests.append((
        "ODR13 Repository contract contains no physical storage dependency",
        not any(
            token.lower()
            in source_text.lower()
            for token in forbidden_storage_tokens
        ),
    ))

    forbidden_payload_terms = (
        "lesson_title",
        "period_number",
        "timetable_period",
        "teaching_date",
        "workbook_bytes",
        "document_bytes",
    )

    tests.append((
        "ODR14 Repository owns no educational payload fields",
        not any(
            token
            in source_text
            for token in forbidden_payload_terms
        ),
    ))

    forbidden_values = (
        "140",
        "105",
        "70",
        "35",
        "KNTT",
        "Toán 6",
    )

    tests.append((
        "ODR15 Repository contains no fixed educational values",
        not any(
            token
            in source_text
            for token in forbidden_values
        ),
    ))

    forbidden_concrete_data_type_refs = (
        "OperationalDataType.PPCT",
        "OperationalDataType.TIMETABLE",
        "OperationalDataType.ACADEMIC_WEEK",
        "OperationalDataType.WEEKLY_SCHEDULE_TEMPLATE",
    )

    tests.append((
        "ODR16 Repository catalog remains data-type neutral",
        not any(
            token
            in source_text
            for token
            in forbidden_concrete_data_type_refs
        ),
    ))

    tests.append((
        "ODR17 Repository contract owns no instance state",
        _owns_no_instance_state(),
    ))

    tests.append((
        "ODR18 Physical source path is not part of identity",
        (
            "path"
            not in {
                name.lower()
                for name in get_signature.parameters
            }
            and
            "path"
            not in {
                name.lower()
                for name in delete_signature.parameters
            }
        ),
    ))

    results = []

    for label, passed in tests:
        results.append(passed)
        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - OPERATIONAL DATA "
            "SOURCE REPOSITORY CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - OPERATIONAL DATA "
        "SOURCE REPOSITORY CONTRACT VIOLATED"
    )
    raise SystemExit(1)


def _cannot_instantiate() -> bool:
    try:
        OperationalDataSourceRepository()
    except TypeError:
        return True
    return False


def _keyword_only_parameter(
    signature,
    name: str,
) -> bool:
    parameter = signature.parameters[name]

    return (
        parameter.kind
        is inspect.Parameter.KEYWORD_ONLY
    )


def _owns_no_instance_state() -> bool:
    allowed = {
        "__module__",
        "__doc__",
        "__abstractmethods__",
        "_abc_impl",
        "save",
        "get",
        "list_sources",
        "delete",
    }

    runtime_metadata = {
        "__dict__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }

    names = set(
        OperationalDataSourceRepository.__dict__
    )

    unexpected = (
        names
        - allowed
        - runtime_metadata
    )

    return not unexpected


def test_operational_data_source_repository_contract():
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0


if __name__ == "__main__":
    main()
