from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
)
from educational_planning_v2.models.operational_data_lifecycle import (
    OperationalDataDerivation,
    OperationalDataLifecyclePolicy,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)


def expect_error(
    error_type,
    action,
):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def make_source(
    *,
    origin: OperationalDataOrigin,
    status: OperationalDataStatus,
    source_id: str = "SRC-001",
    academic_year: str = "2026-2027",
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=OperationalDataType.PPCT,
        origin=origin,
        owner_id="GV001",
        academic_year=academic_year,
        status=status,
        source_name="Operational data",
        source_version="v1",
    )


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-001A.4 - "
        "OPERATIONAL SOURCE LIFECYCLE POLICY TEST"
    )
    print("=" * 72)

    policy = OperationalDataLifecyclePolicy()
    tests = []

    uploaded_file = make_source(
        origin=OperationalDataOrigin.FILE_IMPORTED,
        status=OperationalDataStatus.UPLOADED,
    )

    mapped_file = policy.transition(
        source=uploaded_file,
        target_status=OperationalDataStatus.MAPPED,
    )

    tests.append((
        "ODL1 File import UPLOADED to MAPPED allowed",
        mapped_file.status
        is OperationalDataStatus.MAPPED,
    ))

    validated_file = policy.transition(
        source=mapped_file,
        target_status=OperationalDataStatus.VALIDATED,
    )

    tests.append((
        "ODL2 File import MAPPED to VALIDATED allowed",
        validated_file.status
        is OperationalDataStatus.VALIDATED,
    ))

    active_file = policy.transition(
        source=validated_file,
        target_status=OperationalDataStatus.ACTIVE,
    )

    tests.append((
        "ODL3 Validated file can become ACTIVE",
        active_file.status
        is OperationalDataStatus.ACTIVE,
    ))

    superseded_file = policy.transition(
        source=active_file,
        target_status=OperationalDataStatus.SUPERSEDED,
    )

    tests.append((
        "ODL4 ACTIVE can become SUPERSEDED",
        superseded_file.status
        is OperationalDataStatus.SUPERSEDED,
    ))

    tests.append((
        "ODL5 SUPERSEDED is terminal",
        not policy.can_transition(
            source=superseded_file,
            target_status=OperationalDataStatus.ACTIVE,
        ),
    ))

    tests.append((
        "ODL6 File import cannot skip mapping",
        expect_error(
            ValueError,
            lambda: policy.transition(
                source=uploaded_file,
                target_status=OperationalDataStatus.VALIDATED,
            ),
        ),
    ))

    user_uploaded = make_source(
        origin=OperationalDataOrigin.USER_ENTERED,
        status=OperationalDataStatus.UPLOADED,
    )

    user_validated = policy.transition(
        source=user_uploaded,
        target_status=OperationalDataStatus.VALIDATED,
    )

    tests.append((
        "ODL7 User-entered data can validate without mapping",
        user_validated.status
        is OperationalDataStatus.VALIDATED,
    ))

    admin_uploaded = make_source(
        origin=OperationalDataOrigin.ADMIN_ENTERED,
        status=OperationalDataStatus.UPLOADED,
    )

    admin_validated = policy.transition(
        source=admin_uploaded,
        target_status=OperationalDataStatus.VALIDATED,
    )

    tests.append((
        "ODL8 Admin-entered data can validate without mapping",
        admin_validated.status
        is OperationalDataStatus.VALIDATED,
    ))

    generated_validated = make_source(
        origin=OperationalDataOrigin.SYSTEM_GENERATED,
        status=OperationalDataStatus.VALIDATED,
    )

    generated_active = policy.transition(
        source=generated_validated,
        target_status=OperationalDataStatus.ACTIVE,
    )

    tests.append((
        "ODL9 System-generated validated data can activate",
        generated_active.status
        is OperationalDataStatus.ACTIVE,
    ))

    generated_uploaded = make_source(
        origin=OperationalDataOrigin.SYSTEM_GENERATED,
        status=OperationalDataStatus.UPLOADED,
    )

    tests.append((
        "ODL10 System-generated uploaded state cannot bypass policy",
        expect_error(
            ValueError,
            lambda: policy.transition(
                source=generated_uploaded,
                target_status=OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    tests.append((
        "ODL11 ACTIVE requires prior validation path",
        expect_error(
            ValueError,
            lambda: policy.transition(
                source=user_uploaded,
                target_status=OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    tests.append((
        "ODL12 Same-state transition blocked",
        expect_error(
            ValueError,
            lambda: policy.transition(
                source=active_file,
                target_status=OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    tests.append((
        "ODL13 Transition returns new immutable record",
        (
            uploaded_file.status
            is OperationalDataStatus.UPLOADED
            and
            mapped_file.status
            is OperationalDataStatus.MAPPED
            and
            uploaded_file is not mapped_file
        ),
    ))

    tests.append((
        "ODL14 Original source remains immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                uploaded_file,
                "status",
                OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    historical = make_source(
        origin=OperationalDataOrigin.FILE_IMPORTED,
        status=OperationalDataStatus.ACTIVE,
        source_id="PPCT-2025",
        academic_year="2025-2026",
    )

    derivation = policy.derive_for_academic_year(
        historical_source=historical,
        new_source_id="PPCT-2026",
        new_academic_year="2026-2027",
    )

    tests.append((
        "ODL15 Historical source derivation created",
        isinstance(
            derivation,
            OperationalDataDerivation,
        ),
    ))

    tests.append((
        "ODL16 Derived source receives new identity",
        (
            derivation.derived_source.source_id
            == "PPCT-2026"
            and
            historical.source_id
            == "PPCT-2025"
        ),
    ))

    tests.append((
        "ODL17 Derived source targets new academic year",
        (
            derivation.derived_source.academic_year
            == "2026-2027"
            and
            historical.academic_year
            == "2025-2026"
        ),
    ))

    tests.append((
        "ODL18 Historical reuse starts non-active",
        derivation.derived_source.status
        is OperationalDataStatus.UPLOADED,
    ))

    tests.append((
        "ODL19 Historical source remains unchanged",
        (
            historical.status
            is OperationalDataStatus.ACTIVE
            and
            historical.academic_year
            == "2025-2026"
        ),
    ))

    tests.append((
        "ODL20 Derivation preserves logical data type",
        derivation.derived_source.data_type
        is historical.data_type,
    ))

    tests.append((
        "ODL21 Derivation references SYSTEM_LIBRARY",
        derivation.input_reference.location
        is OperationalInputLocation.SYSTEM_LIBRARY,
    ))

    tests.append((
        "ODL22 Derivation preserves parent source reference",
        (
            derivation.input_reference.source_id
            == "PPCT-2025"
            and
            derivation.input_reference.source_academic_year
            == "2025-2026"
        ),
    ))

    tests.append((
        "ODL23 Reusing same source ID blocked",
        expect_error(
            ValueError,
            lambda: policy.derive_for_academic_year(
                historical_source=historical,
                new_source_id="PPCT-2025",
                new_academic_year="2026-2027",
            ),
        ),
    ))

    tests.append((
        "ODL24 Reusing same academic year blocked",
        expect_error(
            ValueError,
            lambda: policy.derive_for_academic_year(
                historical_source=historical,
                new_source_id="PPCT-COPY",
                new_academic_year="2025-2026",
            ),
        ),
    ))

    tests.append((
        "ODL25 Wrong source type blocked",
        expect_error(
            TypeError,
            lambda: policy.transition(
                source="not-a-source",
                target_status=OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    tests.append((
        "ODL26 Wrong target status blocked",
        expect_error(
            TypeError,
            lambda: policy.transition(
                source=validated_file,
                target_status="ACTIVE",
            ),
        ),
    ))

    lifecycle_module = inspect.getmodule(
        OperationalDataLifecyclePolicy
    )

    if lifecycle_module is None:
        lifecycle_module_source = ""
    else:
        lifecycle_module_source = inspect.getsource(
            lifecycle_module
        )

    import_lines = tuple(
        line.strip().lower()
        for line in lifecycle_module_source.splitlines()
        if line.strip().startswith(
            (
                "import ",
                "from ",
            )
        )
    )

    forbidden_import_tokens = (
        "openpyxl",
        "sqlite3",
        "supabase",
        "googleapiclient",
        "streamlit",
        "docx",
    )

    tests.append((
        "ODL27 Lifecycle owns no physical storage dependency",
        not any(
            token in import_line
            for import_line in import_lines
            for token in forbidden_import_tokens
        ),
    ))

    source_text = (
        inspect.getsource(
            OperationalDataLifecyclePolicy
        )
        + inspect.getsource(
            OperationalDataDerivation
        )
    )

    forbidden_values = (
        "140",
        "105",
        "70",
        "35",
        "KNTT",
        "Toán 6",
    )

    tests.append((
        "ODL28 Lifecycle contains no fixed educational values",
        not any(
            token
            in source_text
            for token in forbidden_values
        ),
    ))

    timetable = OperationalDataSource(
        source_id="TKB-001",
        data_type=OperationalDataType.TIMETABLE,
        origin=OperationalDataOrigin.USER_ENTERED,
        owner_id="GV001",
        academic_year="2026-2027",
        status=OperationalDataStatus.UPLOADED,
    )

    timetable_validated = policy.transition(
        source=timetable,
        target_status=OperationalDataStatus.VALIDATED,
    )

    tests.append((
        "ODL29 Policy is operational-data-type neutral",
        timetable_validated.data_type
        is OperationalDataType.TIMETABLE,
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
            "RESULT: PASS - OPERATIONAL SOURCE "
            "LIFECYCLE POLICY VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL SOURCE "
        "LIFECYCLE POLICY VIOLATED"
    )
    return False


def test_operational_data_lifecycle_contract():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()

