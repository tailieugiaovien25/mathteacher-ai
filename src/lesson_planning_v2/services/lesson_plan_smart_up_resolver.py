"""Read-only candidate ranking for lesson-plan Smart Up.

This module deliberately keeps canonical filenames separate from business IDs.
It does not rename files, write storage, or mutate document metadata.
"""

from __future__ import annotations
import re

from dataclasses import dataclass
from pathlib import PurePath
from typing import Iterable, Protocol, Sequence


@dataclass(frozen=True)
class SmartUpContext:
    expected_file_name: str
    preferred_file_name: str = ""
    subject_ref: str = ""
    component_ref: str = ""
    grade: str = ""
    week_number: int | None = None
    lesson_id: str = ""
    lesson_title: str = ""
    curriculum_periods: tuple[int, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class SmartUpDocument:
    file_name: str
    storage_provider: str
    storage_file_id: str
    title: str = ""
    description: str = ""
    tags: tuple[str, ...] = ()
    updated_at: object | None = None
    web_view_link: str | None = None


@dataclass(frozen=True)
class SmartUpCandidate:
    document: SmartUpDocument
    score: int
    match_reason: str


@dataclass(frozen=True)
class SmartUpResolution:
    status: str
    candidates: tuple[SmartUpCandidate, ...]

    @property
    def best(self) -> SmartUpCandidate | None:
        return self.candidates[0] if self.candidates else None


class SmartUpDocumentCatalog(Protocol):
    def search(self, criteria: object | None = None) -> Sequence[object]:
        ...


def _norm(value: object) -> str:
    return str(value or "").strip().casefold()


def _basename(value: str) -> str:
    return PurePath(value).name


def _tokens(context: SmartUpContext) -> tuple[str, ...]:
    values: list[str] = [
        context.subject_ref,
        context.component_ref,
        context.grade,
        context.lesson_id,
        context.lesson_title,
    ]
    if context.week_number is not None:
        values.extend((f"tuan{context.week_number:02d}", f"w{context.week_number:02d}"))
    values.extend(f"{period:03d}" for period in context.curriculum_periods)
    return tuple(dict.fromkeys(v for v in (_norm(item) for item in values) if v))


def _normalized_filename_identity(value: str) -> str:
    # Normalize harmless filename formatting differences only.
    text = _norm(_basename(value))
    if not text:
        return ""
    text = re.sub(r"\.docx$", "", text)
    text = re.sub(r"[\s_-]+", ".", text)
    text = re.sub(r"\.+", ".", text).strip(".")
    text = re.sub(
        r"(?<=tuan)(\d{1,2})$",
        lambda match: f"{int(match.group(1)):02d}",
        text,
    )
    text = re.sub(
        r"(?<=bai)(\d{1,2})$",
        lambda match: f"{int(match.group(1)):02d}",
        text,
    )
    return text

def rank_document(document: SmartUpDocument, context: SmartUpContext) -> SmartUpCandidate | None:
    actual = _norm(_basename(document.file_name))
    preferred = _norm(_basename(context.preferred_file_name))
    expected = _norm(_basename(context.expected_file_name))
    aliases = {_norm(_basename(item)) for item in context.aliases if _norm(item)}

    if preferred and actual == preferred:
        return SmartUpCandidate(document=document, score=1100, match_reason="EXACT_PREFERRED_FILENAME")
    preferred_identity = _normalized_filename_identity(context.preferred_file_name or "")
    document_identity = _normalized_filename_identity(document.file_name)
    if preferred_identity and document_identity == preferred_identity:
        return SmartUpCandidate(document=document, score=1075, match_reason="NORMALIZED_PREFERRED_FILENAME")

    if expected and actual == expected:
        return SmartUpCandidate(document=document, score=1000, match_reason="EXACT_CANONICAL_FILENAME")

    expected_identity = _normalized_filename_identity(
        context.expected_file_name or ""
    )
    if (
        expected_identity
        and document_identity
        and document_identity == expected_identity
    ):
        return SmartUpCandidate(
            document=document,
            score=975,
            match_reason="NORMALIZED_CANONICAL_FILENAME",
        )

    if actual in aliases:
        return SmartUpCandidate(document=document, score=900, match_reason="KNOWN_ALIAS_FILENAME")

    haystack = " ".join(
        _norm(item)
        for item in (
            document.file_name,
            document.title,
            document.description,
            *document.tags,
        )
        if _norm(item)
    )
    matched = tuple(token for token in _tokens(context) if token in haystack)
    if not matched:
        return None

    week_tokens = ()
    if context.week_number is not None:
        week_tokens = (f"tuan{context.week_number:02d}", f"w{context.week_number:02d}")
    lesson_tokens = tuple(x for x in (_norm(context.lesson_id), _norm(context.lesson_title)) if x)
    period_tokens = tuple(f"{x:03d}" for x in context.curriculum_periods)
    if week_tokens:
        if not any(x in haystack for x in week_tokens): return None
    elif lesson_tokens:
        if not any(x in haystack for x in lesson_tokens): return None
    elif period_tokens:
        if not any(x in haystack for x in period_tokens): return None
    else:
        return None
    score = min(800, 300 + 60 * len(matched))
    return SmartUpCandidate(
        document=document,
        score=score,
        match_reason="CONTEXT_METADATA:" + ",".join(matched),
    )


# G1B_H5E_R1_CATALOG_RESOLVER_DIAGNOSTIC
def debug_resolve_documents(documents, context):
    docs = tuple(documents or ())
    resolution = resolve_documents(docs, context)
    rows = []
    for doc in docs:
        rows.append({
            "file_name": getattr(doc, "file_name", ""),
            "title": getattr(doc, "title", ""),
            "storage_provider": getattr(doc, "storage_provider", ""),
            "storage_file_id": getattr(doc, "storage_file_id", ""),
        })
    return {
        "preferred_file_name": getattr(context, "preferred_file_name", ""),
        "expected_file_name": getattr(context, "expected_file_name", ""),
        "aliases": tuple(getattr(context, "aliases", ()) or ()),
        "curriculum_periods": tuple(getattr(context, "curriculum_periods", ()) or ()),
        "document_count": len(docs),
        "documents": tuple(rows),
        "resolution_status": getattr(resolution, "status", ""),
        "candidate_count": len(tuple(getattr(resolution, "candidates", ()) or ())),
        "candidates": tuple(
            {
                "file_name": getattr(getattr(candidate, "document", None), "file_name", ""),
                "score": getattr(candidate, "score", None),
                "reason": getattr(candidate, "reason", ""),
            }
            for candidate in tuple(getattr(resolution, "candidates", ()) or ())
        ),
    }

def resolve_documents(
    documents: Iterable[SmartUpDocument],
    context: SmartUpContext,
) -> SmartUpResolution:
    ranked = [
        candidate
        for document in documents
        if (candidate := rank_document(document, context)) is not None
    ]
    ranked.sort(
        key=lambda item: (
            item.score,
            _norm(item.document.file_name),
            _norm(item.document.storage_file_id),
        ),
        reverse=True,
    )
    if not ranked:
        return SmartUpResolution(status="NOT_FOUND", candidates=())

    top_score = ranked[0].score
    top_count = sum(1 for item in ranked if item.score == top_score)
    status = "FOUND" if top_count == 1 else "MULTIPLE"
    return SmartUpResolution(status=status, candidates=tuple(ranked))


def from_teacher_document(document: object) -> SmartUpDocument:
    return SmartUpDocument(
        file_name=str(getattr(document, "file_name", "")),
        storage_provider=str(getattr(document, "storage_provider", "")),
        storage_file_id=str(getattr(document, "storage_file_id", "")),
        title=str(getattr(document, "title", "")),
        description=str(getattr(document, "description", "") or ""),
        tags=tuple(getattr(document, "tags", ()) or ()),
        updated_at=getattr(document, "updated_at", None),
        web_view_link=getattr(document, "web_view_link", None),
    )


def resolve_from_catalog(catalog: SmartUpDocumentCatalog, context: SmartUpContext) -> SmartUpResolution:
    """Resolve from the existing per-user catalog without writing storage.

    The existing TeacherDocumentCatalog.search() may be passed directly.
    Search criteria is intentionally omitted here so exact filename matching
    can inspect the user's catalog even though the legacy text query currently
    searches title/description/tags rather than file_name.
    """
    documents = tuple(from_teacher_document(item) for item in catalog.search())
    return resolve_documents(documents, context)
