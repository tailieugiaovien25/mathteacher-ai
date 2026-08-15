from __future__ import annotations

import inspect

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)
from educational_planning_v2.services.operational_input_selection_service import (
    OperationalInputSelection,
)
from educational_planning_v2.services.operational_payload_resolver_service import (
    OperationalPayloadResolution,
    OperationalPayloadResolverService,
)


class FakeOperationalPayloadRepository(
    OperationalPayloadRepository
):
    def __init__(
        self,
        envelopes: tuple[OperationalPayloadEnvelope, ...] = (),
    ) -> None:
        self._items = {
            envelope.reference: envelope
            for envelope in envelopes
        }

    def save(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
    ) -> OperationalPayloadEnvelope:
        self._items[
            envelope.reference
        ] = envelope

        return envelope

    def get(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> OperationalPayloadEnvelope | None:
        return self._items.get(
            reference
        )

    def delete(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> None:
        self._items.pop(
            reference,
            None,
        )


def make_source(
    *,
    source_id: str = "PPCT-2026",
    data_type: OperationalDataType = OperationalDataType.PPCT,
    version: str | None = "v1",
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=data_type,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id="GV001",
        academic_year="2026-2027",
        status=OperationalDataStatus.ACTIVE,
        source_name="Operational source",
        source_version=version,
    )


def expect_error(
    error_type,
    action,
) -> bool:
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-002D - "
        "OPERATIONAL PAYLOAD RESOLVER SERVICE TEST"
    )
    print("=" * 72)

    tests = []

    local_reference = OperationalInputReference(
        location=OperationalInputLocation.LOCAL_UPLOAD,
    )

    local_selection = OperationalInputSelection(
        reference=local_reference,
        source=None,
    )

    local_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="UPLOAD-001",
            data_type=OperationalDataType.PPCT,
            payload_version="v1",
        ),
        payload=b"local-payload",
    )

    service = OperationalPayloadResolverService(
        FakeOperationalPayloadRepository()
    )

    local_resolution = service.resolve(
        selection=local_selection,
        supplied_envelope=local_envelope,
    )

    tests.append((
        "OPR1 Local supplied payload resolved",
        isinstance(
            local_resolution,
            OperationalPayloadResolution,
        ),
    ))

    tests.append((
        "OPR2 Local payload preserved",
        local_resolution.envelope
        is local_envelope,
    ))

    tests.append((
        "OPR3 Local payload requires supplied envelope",
        expect_error(
            ValueError,
            lambda: service.resolve(
                selection=local_selection,
            ),
        ),
    ))

    source = make_source()

    library_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id=source.source_id,
        source_academic_year=source.academic_year,
    )

    library_selection = OperationalInputSelection(
        reference=library_reference,
        source=source,
    )

    library_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="PPCT-2026",
            data_type=OperationalDataType.PPCT,
            payload_version="v1",
        ),
        payload=(
            {"period": 1},
            {"period": 2},
        ),
    )

    library_service = OperationalPayloadResolverService(
        FakeOperationalPayloadRepository(
            (
                library_envelope,
            )
        )
    )

    library_resolution = library_service.resolve(
        selection=library_selection,
    )

    tests.append((
        "OPR4 System library payload resolved",
        library_resolution.envelope
        is library_envelope,
    ))

    tests.append((
        "OPR5 Library source identity preserved",
        (
            library_resolution
            .envelope
            .reference
            .source_id
            == source.source_id
        ),
    ))

    tests.append((
        "OPR6 Library data type preserved",
        (
            library_resolution
            .envelope
            .reference
            .data_type
            is source.data_type
        ),
    ))

    tests.append((
        "OPR7 Library payload version preserved",
        (
            library_resolution
            .envelope
            .reference
            .payload_version
            == "v1"
        ),
    ))

    missing_service = OperationalPayloadResolverService(
        FakeOperationalPayloadRepository()
    )

    tests.append((
        "OPR8 Missing stored payload blocked",
        expect_error(
            LookupError,
            lambda: missing_service.resolve(
                selection=library_selection,
            ),
        ),
    ))

    tests.append((
        "OPR9 Library supplied payload bypass blocked",
        expect_error(
            ValueError,
            lambda: library_service.resolve(
                selection=library_selection,
                supplied_envelope=library_envelope,
            ),
        ),
    ))

    wrong_source_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="OTHER",
            data_type=OperationalDataType.PPCT,
            payload_version="v1",
        ),
        payload=("payload",),
    )

    tests.append((
        "OPR10 Catalog source mismatch detected",
        expect_error(
            ValueError,
            lambda: (
                OperationalPayloadResolverService
                ._validate_catalog_identity(
                    selection=library_selection,
                    envelope=wrong_source_envelope,
                )
            ),
        ),
    ))

    wrong_type_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="PPCT-2026",
            data_type=OperationalDataType.TIMETABLE,
            payload_version="v1",
        ),
        payload=("payload",),
    )

    tests.append((
        "OPR11 Catalog data type mismatch detected",
        expect_error(
            ValueError,
            lambda: (
                OperationalPayloadResolverService
                ._validate_catalog_identity(
                    selection=library_selection,
                    envelope=wrong_type_envelope,
                )
            ),
        ),
    ))

    wrong_version_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="PPCT-2026",
            data_type=OperationalDataType.PPCT,
            payload_version="v2",
        ),
        payload=("payload",),
    )

    tests.append((
        "OPR12 Catalog version mismatch detected",
        expect_error(
            ValueError,
            lambda: (
                OperationalPayloadResolverService
                ._validate_catalog_identity(
                    selection=library_selection,
                    envelope=wrong_version_envelope,
                )
            ),
        ),
    ))

    generated_selection = OperationalInputSelection(
        reference=OperationalInputReference(
            location=OperationalInputLocation.SYSTEM_GENERATED,
        ),
        source=None,
    )

    generated_envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="SYSTEM-001",
            data_type=OperationalDataType.TIMETABLE,
        ),
        payload=("generated",),
    )

    generated_resolution = service.resolve(
        selection=generated_selection,
        supplied_envelope=generated_envelope,
    )

    tests.append((
        "OPR13 System-generated payload supported",
        generated_resolution.envelope
        is generated_envelope,
    ))

    tests.append((
        "OPR14 Wrong selection type blocked",
        expect_error(
            TypeError,
            lambda: service.resolve(
                selection="bad-selection",
                supplied_envelope=local_envelope,
            ),
        ),
    ))

    tests.append((
        "OPR15 Wrong repository type blocked",
        expect_error(
            TypeError,
            lambda: OperationalPayloadResolverService(
                object()
            ),
        ),
    ))

    tests.append((
        "OPR16 Resolution requires valid selection",
        expect_error(
            TypeError,
            lambda: OperationalPayloadResolution(
                selection="bad",
                envelope=local_envelope,
            ),
        ),
    ))

    tests.append((
        "OPR17 Resolution requires valid envelope",
        expect_error(
            TypeError,
            lambda: OperationalPayloadResolution(
                selection=local_selection,
                envelope="bad",
            ),
        ),
    ))

    service_source = inspect.getsource(
        OperationalPayloadResolverService
    )

    forbidden_dependencies = (
        "openpyxl",
        "sqlite3",
        "supabase",
        "streamlit",
        "googleapiclient",
        ".xlsx",
        ".docx",
        "Path(",
        "open(",
    )

    tests.append((
        "OPR18 Resolver owns no physical I/O dependency",
        not any(
            token.lower()
            in service_source.lower()
            for token in forbidden_dependencies
        ),
    ))

    tests.append((
        "OPR19 Resolver uses payload repository boundary",
        "_repository.get"
        in service_source,
    ))

    tests.append((
        "OPR20 Resolver owns no educational payload fields",
        not any(
            token
            in service_source
            for token in (
                "lesson_title",
                "period_number",
                "teaching_date",
                "timetable_period",
            )
        ),
    ))

    tests.append((
        "OPR21 Resolver remains data-type neutral",
        not any(
            token
            in service_source
            for token in (
                "OperationalDataType.PPCT",
                "OperationalDataType.TIMETABLE",
                "OperationalDataType.ACADEMIC_WEEK",
                "OperationalDataType.WEEKLY_SCHEDULE_TEMPLATE",
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
            "RESULT: PASS - OPERATIONAL "
            "PAYLOAD RESOLVER VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL "
        "PAYLOAD RESOLVER VIOLATED"
    )

    return False


def test_operational_payload_resolver_service():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
