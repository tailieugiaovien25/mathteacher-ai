from educational_planning_v2.models.operational_data_source import (
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.services.ppct_import_service import (
    PPCTImportRequest,
    PPCTImportService,
)
from educational_planning_v2.tests.test_ppct_import_service import (
    MemoryPayloadRepository,
    MemorySourceRepository,
    _workbook_bytes,
)


def test_ppct_update_supersedes_previous_active():
    source_repository = MemorySourceRepository()
    payload_repository = MemoryPayloadRepository()

    service = PPCTImportService(
        source_repository=source_repository,
        payload_repository=payload_repository,
    )

    first = service.import_workbook(
        request=PPCTImportRequest(
            owner_id="teacher-001",
            academic_year="2026-2027",
            source_id="ppct-v1",
            source_name="PPCT v1",
            source_version="1",
        ),
        workbook_bytes=_workbook_bytes(),
    )

    second = service.import_workbook(
        request=PPCTImportRequest(
            owner_id="teacher-001",
            academic_year="2026-2027",
            source_id="ppct-v2",
            source_name="PPCT v2",
            source_version="2",
        ),
        workbook_bytes=_workbook_bytes(),
    )

    old_source = source_repository.get(
        source_id=first.source.source_id,
    )

    assert old_source is not None
    assert (
        old_source.status
        is OperationalDataStatus.SUPERSEDED
    )

    assert (
        second.source.status
        is OperationalDataStatus.ACTIVE
    )

    active = source_repository.list_sources(
        owner_id="teacher-001",
        academic_year="2026-2027",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
    )

    assert len(active) == 1
    assert active[0].source_id == "ppct-v2"


def test_duplicate_ppct_source_id_blocked():
    source_repository = MemorySourceRepository()
    payload_repository = MemoryPayloadRepository()

    service = PPCTImportService(
        source_repository=source_repository,
        payload_repository=payload_repository,
    )

    request = PPCTImportRequest(
        owner_id="teacher-001",
        academic_year="2026-2027",
        source_id="same-source",
        source_name="PPCT",
        source_version="1",
    )

    service.import_workbook(
        request=request,
        workbook_bytes=_workbook_bytes(),
    )

    try:
        service.import_workbook(
            request=request,
            workbook_bytes=_workbook_bytes(),
        )
    except ValueError:
        return

    raise AssertionError(
        "duplicate PPCT source_id must be blocked"
    )
