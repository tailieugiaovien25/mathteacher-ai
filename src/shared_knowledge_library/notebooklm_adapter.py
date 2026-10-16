from __future__ import annotations

from shared_knowledge_library.library import KnowledgeDocument


class SharedKnowledgeNotebookLMAdapter:
    """Adapter boundary between Shared Knowledge Library and NotebookLM Bridge."""

    def __init__(self, notebooklm_client) -> None:
        self._client = notebooklm_client

    def sync(self, document: KnowledgeDocument) -> str:
        return self._client.upload_file(
            notebook_id="dry-run-notebook",
            file_path=document.file_name,
            display_name=document.title,
            content_type=document.mime_type,
        )
