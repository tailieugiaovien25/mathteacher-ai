from dataclasses import FrozenInstanceError
import inspect

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
    OperationalOutputDestination,
    OperationalOutputPlan,
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


def main():
    print("=" * 72)
    print(
        "MVP-OPS-001A.3B - "
        "INPUT LOCATION & OUTPUT DESTINATION CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    local_input = OperationalInputReference(
        location=OperationalInputLocation.LOCAL_UPLOAD,
    )

    tests.append((
        "ODIO1 Local upload accepted",
        local_input.location
        is OperationalInputLocation.LOCAL_UPLOAD,
    ))

    library_input = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id=" PPCT-2025-001 ",
        source_academic_year=" 2025-2026 ",
    )

    tests.append((
        "ODIO2 System library input accepted",
        library_input.location
        is OperationalInputLocation.SYSTEM_LIBRARY,
    ))

    tests.append((
        "ODIO3 Library source identity normalized",
        library_input.source_id
        == "PPCT-2025-001",
    ))

    tests.append((
        "ODIO4 Source academic year preserved",
        library_input.source_academic_year
        == "2025-2026",
    ))

    generated_input = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_GENERATED,
    )

    tests.append((
        "ODIO5 System-generated input accepted",
        generated_input.location
        is OperationalInputLocation.SYSTEM_GENERATED,
    ))

    tests.append((
        "ODIO6 Library input requires source ID",
        expect_error(
            ValueError,
            lambda: OperationalInputReference(
                location=(
                    OperationalInputLocation.SYSTEM_LIBRARY
                ),
            ),
        ),
    ))

    tests.append((
        "ODIO7 Wrong input location blocked",
        expect_error(
            TypeError,
            lambda: OperationalInputReference(
                location="LOCAL_UPLOAD",
            ),
        ),
    ))

    output_plan = OperationalOutputPlan(
        destinations=(
            OperationalOutputDestination.SYSTEM_STORAGE,
            OperationalOutputDestination.DOWNLOAD,
        ),
    )

    tests.append((
        "ODIO8 Multiple output destinations accepted",
        len(output_plan.destinations) == 2,
    ))

    tests.append((
        "ODIO9 System storage destination detected",
        output_plan.includes(
            OperationalOutputDestination.SYSTEM_STORAGE
        ),
    ))

    tests.append((
        "ODIO10 Download destination detected",
        output_plan.includes(
            OperationalOutputDestination.DOWNLOAD
        ),
    ))

    drive_plan = OperationalOutputPlan(
        destinations=(
            OperationalOutputDestination.GOOGLE_DRIVE,
        ),
    )

    tests.append((
        "ODIO11 Google Drive destination supported",
        drive_plan.includes(
            OperationalOutputDestination.GOOGLE_DRIVE
        ),
    ))

    vtsmas_plan = OperationalOutputPlan(
        destinations=(
            OperationalOutputDestination.VTSMAS,
        ),
    )

    tests.append((
        "ODIO12 VTsmas destination represented generically",
        vtsmas_plan.includes(
            OperationalOutputDestination.VTSMAS
        ),
    ))

    tests.append((
        "ODIO13 Empty output plan blocked",
        expect_error(
            ValueError,
            lambda: OperationalOutputPlan(
                destinations=(),
            ),
        ),
    ))

    tests.append((
        "ODIO14 Non-tuple destinations blocked",
        expect_error(
            TypeError,
            lambda: OperationalOutputPlan(
                destinations=[
                    OperationalOutputDestination.DOWNLOAD
                ],
            ),
        ),
    ))

    tests.append((
        "ODIO15 Invalid destination blocked",
        expect_error(
            TypeError,
            lambda: OperationalOutputPlan(
                destinations=("DOWNLOAD",),
            ),
        ),
    ))

    duplicate_plan = OperationalOutputPlan(
        destinations=(
            OperationalOutputDestination.DOWNLOAD,
            OperationalOutputDestination.DOWNLOAD,
            OperationalOutputDestination.SYSTEM_STORAGE,
        ),
    )

    tests.append((
        "ODIO16 Duplicate destinations normalized",
        duplicate_plan.destinations
        == (
            OperationalOutputDestination.DOWNLOAD,
            OperationalOutputDestination.SYSTEM_STORAGE,
        ),
    ))

    tests.append((
        "ODIO17 Input reference immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                library_input,
                "source_id",
                "CHANGED",
            ),
        ),
    ))

    tests.append((
        "ODIO18 Output plan immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                output_plan,
                "destinations",
                (),
            ),
        ),
    ))

    input_locations = {
        item.value
        for item in OperationalInputLocation
    }

    tests.append((
        "ODIO19 Required input locations available",
        input_locations
        == {
            "LOCAL_UPLOAD",
            "SYSTEM_LIBRARY",
            "SYSTEM_GENERATED",
        },
    ))

    output_destinations = {
        item.value
        for item in OperationalOutputDestination
    }

    tests.append((
        "ODIO20 Required output destinations available",
        output_destinations
        == {
            "SYSTEM_STORAGE",
            "DOWNLOAD",
            "GOOGLE_DRIVE",
            "VTSMAS",
        },
    ))

    contract_source = (
        inspect.getsource(OperationalInputReference)
        + inspect.getsource(OperationalOutputPlan)
    )

    forbidden_dependencies = (
        "openpyxl",
        "sqlite3",
        "supabase",
        "googleapiclient",
        "requests",
        "streamlit",
        "Path(",
        "open(",
    )

    tests.append((
        "ODIO21 Contract owns no physical I/O implementation",
        not any(
            token.lower()
            in contract_source.lower()
            for token in forbidden_dependencies
        ),
    ))

    old_year = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id="PPCT-OLD",
        source_academic_year="2025-2026",
    )

    tests.append((
        "ODIO22 Previous-year source can be referenced",
        (
            old_year.source_id == "PPCT-OLD"
            and
            old_year.source_academic_year == "2025-2026"
        ),
    ))

    tests.append((
        "ODIO23 Input and output concerns remain independent",
        (
            library_input.location
            is OperationalInputLocation.SYSTEM_LIBRARY
            and
            output_plan.includes(
                OperationalOutputDestination.SYSTEM_STORAGE
            )
            and
            output_plan.includes(
                OperationalOutputDestination.DOWNLOAD
            )
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
            "RESULT: PASS - OPERATIONAL DATA I/O "
            "CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - OPERATIONAL DATA I/O "
        "CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
