from teacher_document_library_v2.storage import (
    DocumentFileStorage,
)


def test_document_storage_contract_has_download():
    assert hasattr(
        DocumentFileStorage,
        "download",
    )
