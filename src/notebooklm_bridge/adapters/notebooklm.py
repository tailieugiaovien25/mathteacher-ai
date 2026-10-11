"""NotebookLM adapter boundary.

This module intentionally does not implement private or unsupported
NotebookLM APIs. It provides a replaceable adapter boundary so the
synchronization workflow can remain provider-independent.
"""

from __future__ import annotations

from dataclasses import dataclass

from notebooklm_bridge.sync import NotebookSourceAdapter


@dataclass(frozen=True)
class NotebookLMAdapterConfig:
    """Configuration for a supported NotebookLM integration mechanism."""

    enabled: bool = False


class NotebookLMAdapter(NotebookSourceAdapter):
    """Safe placeholder for a future supported NotebookLM integration.

    No Google credentials, cookies, session tokens, or private NotebookLM
    endpoints are accepted or stored here.
    """

    def __init__(
        self,
        config: NotebookLMAdapterConfig | None = None,
    ) -> None:
        self._config = config or NotebookLMAdapterConfig()

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        """Synchronize one source through a supported external mechanism.

        The real implementation must be added only after the supported
        NotebookLM integration mechanism is established.
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        if not document_id.strip():
            raise ValueError("document_id must not be empty")

        if not self._config.enabled:
            raise RuntimeError(
                "NotebookLM integration is disabled"
            )

        raise NotImplementedError(
            "No supported NotebookLM integration mechanism "
            "has been configured yet"
        )