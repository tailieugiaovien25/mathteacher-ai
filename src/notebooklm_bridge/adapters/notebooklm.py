"""NotebookLM adapter boundary.

This module intentionally does not implement private or unsupported
NotebookLM APIs. It provides a replaceable adapter boundary so the
synchronization workflow can remain provider-independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from notebooklm_bridge.adapters.notebooklm_client import NotebookLMClient
from notebooklm_bridge.sync import NotebookSourceAdapter


@dataclass(frozen=True)
class NotebookLMAdapterConfig:
    """Configuration for a supported NotebookLM integration mechanism."""

    enabled: bool = False


class NotebookLMAdapter(NotebookSourceAdapter):
    """Safe boundary for a future supported NotebookLM integration.

    No Google credentials, cookies, session tokens, or private NotebookLM
    endpoints are accepted or stored here.
    """

    def __init__(
        self,
        config: NotebookLMAdapterConfig | None = None,
        client: NotebookLMClient | None = None,
    ) -> None:
        self._config = config or NotebookLMAdapterConfig()
        self._client = client

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        """Synchronize one source through the configured client."""

        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        if not document_id.strip():
            raise ValueError("document_id must not be empty")

        if not self._config.enabled:
            raise RuntimeError(
                "NotebookLM integration is disabled"
            )

        if self._client is None:
            raise NotImplementedError(
                "No supported NotebookLM integration mechanism "
                "has been configured yet"
            )

        return self._client.sync_source(
            notebook_id=notebook_id,
            document_id=document_id,
        )

    def upload_file(
        self,
        *,
        notebook_id: str,
        file_path: str | Path,
        display_name: str,
        content_type: str,
    ) -> str:
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        if not str(file_path).strip():
            raise ValueError("file_path must not be empty")

        if not display_name.strip():
            raise ValueError("display_name must not be empty")

        if not content_type.strip():
            raise ValueError("content_type must not be empty")

        if not self._config.enabled:
            raise RuntimeError("NotebookLM integration is disabled")

        if self._client is None:
            raise NotImplementedError(
                "No supported NotebookLM integration mechanism "
                "has been configured yet"
            )

        return self._client.upload_file(
            notebook_id=notebook_id,
            file_path=file_path,
            display_name=display_name,
            content_type=content_type,
        )
