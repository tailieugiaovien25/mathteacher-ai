from dataclasses import FrozenInstanceError
import inspect

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


def main():
    print("=" * 72)
    print(
        "MVP-OPS-001A.3 - "
        "OPERATIONAL DATA SOURCE CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    source = OperationalDataSource(
        source_id=" SRC-001 ",
        data_type=OperationalDataType.PPCT,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id=" GV001 ",
        academic_year=" 2026-2027 ",
        status=OperationalDataStatus.UPLOADED,
        source_name=" PPCT Toan 6 ",
        source_version=" v1 ",
    )

    tests.append((
        "ODS1 Valid source accepted",
        isinstance(
            source,
            OperationalDataSource,
        ),
    ))

    tests.append((
        "ODS2 Identity normalized",
        source.source_id == "SRC-001",
    ))

    tests.append((
        "ODS3 Owner normalized",
        source.owner_id == "GV001",
    ))

    tests.append((
        "ODS4 Academic year normalized",
        source.academic_year == "2026-2027",
    ))

    tests.append((
        "ODS5 Source metadata normalized",
        (
            source.source_name
            == "PPCT Toan 6"
            and
            source.source_version
            == "v1"
        ),
    ))

    tests.append((
        "ODS6 Data type preserved",
        source.data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "ODS7 Origin preserved",
        source.origin
        is OperationalDataOrigin.FILE_IMPORTED,
    ))

    tests.append((
        "ODS8 Status preserved",
        source.status
        is OperationalDataStatus.UPLOADED,
    ))

    tests.append((
        "ODS9 Empty source ID blocked",
        expect_error(
            ValueError,
            lambda: OperationalDataSource(
                source_id=" ",
                data_type=OperationalDataType.PPCT,
                origin=OperationalDataOrigin.USER_ENTERED,
                owner_id="GV001",
                academic_year="2026-2027",
                status=OperationalDataStatus.UPLOADED,
            ),
        ),
    ))

    tests.append((
        "ODS10 Empty owner blocked",
        expect_error(
            ValueError,
            lambda: OperationalDataSource(
                source_id="SRC",
                data_type=OperationalDataType.PPCT,
                origin=OperationalDataOrigin.USER_ENTERED,
                owner_id=" ",
                academic_year="2026-2027",
                status=OperationalDataStatus.UPLOADED,
            ),
        ),
    ))

    tests.append((
        "ODS11 Empty academic year blocked",
        expect_error(
            ValueError,
            lambda: OperationalDataSource(
                source_id="SRC",
                data_type=OperationalDataType.PPCT,
                origin=OperationalDataOrigin.USER_ENTERED,
                owner_id="GV001",
                academic_year=" ",
                status=OperationalDataStatus.UPLOADED,
            ),
        ),
    ))

    tests.append((
        "ODS12 Wrong data type blocked",
        expect_error(
            TypeError,
            lambda: OperationalDataSource(
                source_id="SRC",
                data_type="PPCT",
                origin=OperationalDataOrigin.USER_ENTERED,
                owner_id="GV001",
                academic_year="2026-2027",
                status=OperationalDataStatus.UPLOADED,
            ),
        ),
    ))

    tests.append((
        "ODS13 Wrong origin blocked",
        expect_error(
            TypeError,
            lambda: OperationalDataSource(
                source_id="SRC",
                data_type=OperationalDataType.PPCT,
                origin="FILE_IMPORTED",
                owner_id="GV001",
                academic_year="2026-2027",
                status=OperationalDataStatus.UPLOADED,
            ),
        ),
    ))

    tests.append((
        "ODS14 Wrong status blocked",
        expect_error(
            TypeError,
            lambda: OperationalDataSource(
                source_id="SRC",
                data_type=OperationalDataType.PPCT,
                origin=OperationalDataOrigin.FILE_IMPORTED,
                owner_id="GV001",
                academic_year="2026-2027",
                status="ACTIVE",
            ),
        ),
    ))

    tests.append((
        "ODS15 Contract immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                source,
                "status",
                OperationalDataStatus.ACTIVE,
            ),
        ),
    ))

    all_types = {
        item.value
        for item in OperationalDataType
    }

    tests.append((
        "ODS16 Required operational types available",
        all_types
        == {
            "PPCT",
            "TIMETABLE",
            "ACADEMIC_WEEK",
            "WEEKLY_SCHEDULE_TEMPLATE",
        },
    ))

    all_origins = {
        item.value
        for item in OperationalDataOrigin
    }

    tests.append((
        "ODS17 Dual input origins supported",
        {
            "SYSTEM_GENERATED",
            "USER_ENTERED",
            "ADMIN_ENTERED",
            "FILE_IMPORTED",
        }.issubset(all_origins),
    ))

    all_statuses = {
        item.value
        for item in OperationalDataStatus
    }

    tests.append((
        "ODS18 Lifecycle states available",
        all_statuses
        == {
            "UPLOADED",
            "MAPPED",
            "VALIDATED",
            "ACTIVE",
            "SUPERSEDED",
        },
    ))

    contract_source = inspect.getsource(
        OperationalDataSource
    )

    forbidden_storage_tokens = (
        "openpyxl",
        "sqlite",
        "supabase",
        "google drive",
        ".xlsx",
        ".docx",
        "Path(",
        "open(",
    )

    tests.append((
        "ODS19 Contract contains no physical storage dependency",
        not any(
            token.lower()
            in contract_source.lower()
            for token in forbidden_storage_tokens
        ),
    ))

    forbidden_domain_values = (
        "140",
        "105",
        "70",
        "35",
        "KNTT",
        "Toan 6",
        "Toán 6",
    )

    tests.append((
        "ODS20 Contract contains no fixed educational values",
        not any(
            token
            in contract_source
            for token in forbidden_domain_values
        ),
    ))

    future_source = OperationalDataSource(
        source_id="SRC-FUTURE",
        data_type=OperationalDataType.TIMETABLE,
        origin=OperationalDataOrigin.SYSTEM_GENERATED,
        owner_id="SYSTEM",
        academic_year="2030-2031",
        status=OperationalDataStatus.ACTIVE,
    )

    tests.append((
        "ODS21 System-generated source uses same contract",
        (
            future_source.origin
            is OperationalDataOrigin.SYSTEM_GENERATED
            and
            future_source.status
            is OperationalDataStatus.ACTIVE
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
            "SOURCE CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - OPERATIONAL DATA "
        "SOURCE CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
