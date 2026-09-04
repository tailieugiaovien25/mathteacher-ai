"""Read-only content loading for Smart Up candidates."""

from __future__ import annotations

from typing import Mapping, Protocol

from lesson_planning_v2.services.lesson_plan_smart_up_resolver import SmartUpDocument


class ReadOnlyDocumentStorage(Protocol):
    def download(self, file_id: str) -> bytes:
        ...


class SmartUpContentLoadError(RuntimeError):
    pass


def load_smart_up_content(
    document: SmartUpDocument,
    *,
    storages: Mapping[str, ReadOnlyDocumentStorage],
) -> bytes:
    provider = str(document.storage_provider or "").strip()
    file_id = str(document.storage_file_id or "").strip()

    if not provider:
        raise SmartUpContentLoadError("SMART_UP_STORAGE_PROVIDER_REQUIRED")
    if not file_id:
        raise SmartUpContentLoadError("SMART_UP_STORAGE_FILE_ID_REQUIRED")

    storage = storages.get(provider)
    if storage is None:
        raise SmartUpContentLoadError(
            f"SMART_UP_STORAGE_PROVIDER_UNAVAILABLE:{provider}"
        )

    content = storage.download(file_id)
    if not isinstance(content, bytes) or not content:
        raise SmartUpContentLoadError("SMART_UP_CONTENT_EMPTY")
    return content