"""Session bridge for runtime-supplied assessment PPCT data.

This module contains no database access. The authenticated outer runtime is
responsible for loading the ACTIVE PPCT source. This bridge only validates and
publishes already-normalized PPCTRow values into Streamlit-like session state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import MutableMapping

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


ASSESSMENT_PPCT_ROWS_SESSION_KEY = "assessment_ppct_rows"
ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY = "assessment_ppct_evidence"


@dataclass(frozen=True, slots=True)
class AssessmentPpctRuntimeEvidence:
    academic_year: str
    source_id: str
    source_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "academic_year",
            "source_id",
            "source_version",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )


def inject_assessment_ppct_rows(
    *,
    session_state: MutableMapping[str, object],
    rows: tuple[PPCTRow, ...],
    evidence: AssessmentPpctRuntimeEvidence | None = None,
) -> None:
    """Publish normalized PPCT rows supplied by the authenticated runtime."""
    if not isinstance(session_state, MutableMapping):
        raise TypeError(
            "session_state must be a mutable mapping"
        )

    if not isinstance(rows, tuple):
        raise TypeError(
            "rows must be a tuple"
        )

    if not rows:
        raise ValueError(
            "rows must not be empty"
        )

    if not all(
        isinstance(row, PPCTRow)
        for row in rows
    ):
        raise TypeError(
            "rows must contain PPCTRow values"
        )

    if (
        evidence is not None
        and not isinstance(
            evidence,
            AssessmentPpctRuntimeEvidence,
        )
    ):
        raise TypeError(
            "evidence must be AssessmentPpctRuntimeEvidence or None"
        )

    session_state[
        ASSESSMENT_PPCT_ROWS_SESSION_KEY
    ] = rows

    if evidence is None:
        session_state.pop(
            ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY,
            None,
        )
    else:
        session_state[
            ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY
        ] = evidence


def clear_assessment_ppct_rows(
    *,
    session_state: MutableMapping[str, object],
) -> None:
    """Remove assessment PPCT runtime data from the current session."""
    if not isinstance(session_state, MutableMapping):
        raise TypeError(
            "session_state must be a mutable mapping"
        )

    session_state.pop(
        ASSESSMENT_PPCT_ROWS_SESSION_KEY,
        None,
    )
    session_state.pop(
        ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY,
        None,
    )
