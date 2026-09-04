from lesson_planning_v2.services.lesson_plan_smart_up_content_loader import (
    SmartUpContentLoadError,
    load_smart_up_content,
)
from lesson_planning_v2.services.lesson_plan_smart_up_resolver import SmartUpDocument


class FakeStorage:
    def __init__(self, payload=b"docx-bytes"):
        self.payload = payload
        self.calls = []

    def download(self, file_id):
        self.calls.append(file_id)
        return self.payload


def doc(provider="google_drive_oauth", file_id="drive-1"):
    return SmartUpDocument(
        file_name="KHBD.TDS6.TUAN01.docx",
        storage_provider=provider,
        storage_file_id=file_id,
    )


def test_read_only_loader_downloads_by_registered_provider():
    storage = FakeStorage()
    content = load_smart_up_content(
        doc(),
        storages={"google_drive_oauth": storage},
    )
    assert content == b"docx-bytes"
    assert storage.calls == ["drive-1"]


def test_missing_provider_is_rejected():
    try:
        load_smart_up_content(doc(provider=""), storages={})
    except SmartUpContentLoadError as error:
        assert "STORAGE_PROVIDER_REQUIRED" in str(error)
    else:
        raise AssertionError("expected SmartUpContentLoadError")


def test_unavailable_provider_is_rejected():
    try:
        load_smart_up_content(doc(provider="other"), storages={})
    except SmartUpContentLoadError as error:
        assert "PROVIDER_UNAVAILABLE" in str(error)
    else:
        raise AssertionError("expected SmartUpContentLoadError")