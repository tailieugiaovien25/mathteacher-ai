from scripts.teacher_portal.app import (
    connect_document_library_runtime,
)


class FakeRepository:
    pass


def test_runtime_builds_catalog_without_drive_credentials():
    state = {
        "document_library_repository":
            FakeRepository(),
    }

    result = connect_document_library_runtime(
        state
    )

    assert result is not None

    assert (
        state["document_library_catalog"]
        is result
    )

    assert (
        "document_library_upload_service"
        not in state
    )


def test_runtime_clears_stale_drive_services_without_credentials():
    state = {
        "document_library_repository":
            FakeRepository(),
        "document_library_storage":
            object(),
        "document_library_upload_service":
            object(),
    }

    connect_document_library_runtime(
        state
    )

    assert (
        "document_library_storage"
        not in state
    )

    assert (
        "document_library_upload_service"
        not in state
    )


def test_runtime_returns_none_without_repository():
    state = {}

    result = connect_document_library_runtime(
        state
    )

    assert result is None
