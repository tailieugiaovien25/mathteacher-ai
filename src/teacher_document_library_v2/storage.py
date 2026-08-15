"""Provider-neutral file storage boundary for teacher documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredDocumentFile:
    provider: str
    file_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    web_view_link: str | None = None


class DocumentFileStorage(Protocol):
    def upload(self, content: bytes, file_name: str, mime_type: str) -> StoredDocumentFile: ...
    def delete(self, file_id: str) -> bool: ...
