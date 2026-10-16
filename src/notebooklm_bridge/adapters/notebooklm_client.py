"""Client boundary for supported NotebookLM integrations.

This module contains only the provider client contract.
It does not implement private NotebookLM APIs or authentication.
"""

from __future__ import annotations

from pathlib import Path
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

    def upload_file(
        self,
        *,
        notebook_id: str,
        file_path: str | Path,
        display_name: str,
        content_type: str,
    ) -> str:
        """Upload one local file as a Notebook source."""
        ...
