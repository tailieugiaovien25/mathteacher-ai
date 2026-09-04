from __future__ import annotations

from teacher_document_library_v2.adapters.google_drive_oauth import (
    DRIVE_FILE_SCOPE,
    DRIVE_READONLY_SCOPE,
    GOOGLE_DRIVE_SCOPES,
    GoogleDriveFileStorage,
)


class _Request:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FilesApi:
    def __init__(self, rows_by_parent):
        self.rows_by_parent = rows_by_parent
        self.list_calls = []
        self.write_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        q = kwargs["q"]
        parent = q.split("'", 2)[1]
        return _Request({"files": self.rows_by_parent.get(parent, [])})

    def create(self, **kwargs):
        self.write_calls.append(("create", kwargs))
        raise AssertionError("read-only search must not create")

    def update(self, **kwargs):
        self.write_calls.append(("update", kwargs))
        raise AssertionError("read-only search must not update")

    def delete(self, **kwargs):
        self.write_calls.append(("delete", kwargs))
        raise AssertionError("read-only search must not delete")


class _DriveService:
    def __init__(self, rows_by_parent):
        self.files_api = _FilesApi(rows_by_parent)

    def files(self):
        return self.files_api


def _storage(rows_by_parent):
    storage = GoogleDriveFileStorage(credentials=object())
    storage._service = _DriveService(rows_by_parent)
    return storage


def test_oauth_requests_keep_upload_scope_and_add_readonly_scope():
    assert DRIVE_FILE_SCOPE in GOOGLE_DRIVE_SCOPES
    assert DRIVE_READONLY_SCOPE in GOOGLE_DRIVE_SCOPES


def test_folder_tree_search_is_recursive_and_read_only():
    folder_mime = "application/vnd.google-apps.folder"
    docx = (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    storage = _storage(
        {
            "root": [
                {"id": "sub", "name": "Tuan 03", "mimeType": folder_mime},
                {
                    "id": "f1",
                    "name": "KHBD.ANH6.TUAN3.docx",
                    "mimeType": docx,
                    "size": "100",
                    "webViewLink": "https://drive.example/f1",
                },
            ],
            "sub": [
                {
                    "id": "f2",
                    "name": "KHBD.ANH7.TUAN03.docx",
                    "mimeType": docx,
                    "size": "200",
                }
            ],
        }
    )

    result = storage.list_folder_tree("root", recursive=True, mime_type=docx)

    assert [item.file_id for item in result] == ["f1", "f2"]
    assert [item.file_name for item in result] == [
        "KHBD.ANH6.TUAN3.docx",
        "KHBD.ANH7.TUAN03.docx",
    ]
    assert storage._service.files_api.write_calls == []
    assert len(storage._service.files_api.list_calls) == 2


def test_non_recursive_search_does_not_descend():
    folder_mime = "application/vnd.google-apps.folder"
    docx = (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    storage = _storage(
        {
            "root": [
                {"id": "sub", "name": "Nested", "mimeType": folder_mime},
                {"id": "f1", "name": "KHBD.ANH6.TUAN03.docx", "mimeType": docx},
            ],
            "sub": [
                {"id": "f2", "name": "hidden.docx", "mimeType": docx}
            ],
        }
    )

    result = storage.list_folder_tree("root", recursive=False, mime_type=docx)

    assert [item.file_id for item in result] == ["f1"]
    assert len(storage._service.files_api.list_calls) == 1


def test_folder_tree_requires_folder_id():
    storage = _storage({})
    try:
        storage.list_folder_tree("   ")
    except ValueError as error:
        assert "folder_id" in str(error)
    else:
        raise AssertionError("expected ValueError")
