from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposalProvenance:
    """Trace identity for an AI/provider-generated pedagogical proposal."""

    proposal_id: str
    provider_id: str

    request_id: str | None = None
    execution_id: str | None = None
    trace_id: str | None = None
