from __future__ import annotations

from dataclasses import dataclass

from shared_knowledge_library.library import KnowledgeDocument


@dataclass(frozen=True)
class FakeNotebookLMResult:
    document_id: str
    target: str
    external_id: str


class FakeNotebookLMAdapter:
    """Local-only NotebookLM adapter for contract testing."""

    def upload_file(self, document: KnowledgeDocument) -> FakeNotebookLMResult:
        return FakeNotebookLMResult(
            document_id=document.document_id,
            target="notebooklm",
            external_id=f"fake-notebooklm:{document.document_id}",
        )
