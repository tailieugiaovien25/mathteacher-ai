"""Client boundary for supported NotebookLM integrations.

This module contains only the provider client contract.
It does not implement private NotebookLM APIs or authentication.
"""

from __future__ import annotations

from typing import Protocol


class NotebookLMClient(Protocol):
    """Contract for a supported NotebookLM client implementation."""

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        """Synchronize one document and return an external source ID."""
        ...
