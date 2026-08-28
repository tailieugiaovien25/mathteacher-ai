from __future__ import annotations

from decimal import Decimal

import pytest

from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
    BlueprintRequirementLinkError,
    BlueprintRequirementLinkService,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
)


BLUEPRINT_VERSION_ID = "11111111-1111-4111-8111-111111111111"


class RecordingGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[BlueprintRequirementAssignment, ...]]] = []

    def replace_requirement_links(
        self,
        *,
        blueprint_version_id: str,
        assignments: tuple[BlueprintRequirementAssignment, ...],
    ) -> tuple[BlueprintRequirementAssignment, ...]:
        rows = tuple(assignments)
        self.calls.append((blueprint_version_id, rows))
        return rows


def _selection(*, finalized: bool = True) -> CanonicalAssessmentSelection:
    return CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code="MOET-GDPT2018-MATH-THCS",
        selected_topic_codes=("CURR-NODE-MATH-G6-004",),
        selected_requirement_codes=(
            "YCCD-MATH-06-0001",
            "YCCD-MATH-06-0002",
        ),
        finalized=finalized,
    )


def _assignments() -> tuple[BlueprintRequirementAssignment, ...]:
    return (
        BlueprintRequirementAssignment(
            requirement_code="YCCD-MATH-06-0002",
            coverage_role="SUPPORTING",
            target_question_count=1,
            target_score=Decimal("0.50"),
            sequence_number=20,
        ),
        BlueprintRequirementAssignment(
            requirement_code="YCCD-MATH-06-0001",
            coverage_role="PRIMARY",
            target_question_count=2,
            target_score=Decimal("1.00"),
            sequence_number=10,
            specification_note="Yêu cầu trọng tâm",
        ),
    )


def test_service_persists_exact_finalized_selection_in_stable_order() -> None:
    gateway = RecordingGateway()
    service = BlueprintRequirementLinkService(gateway=gateway)

    result = service.replace_from_selection(
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        selection=_selection(),
        assignments=_assignments(),
    )

    assert [row.requirement_code for row in result] == [
        "YCCD-MATH-06-0001",
        "YCCD-MATH-06-0002",
    ]
    assert gateway.calls == [(BLUEPRINT_VERSION_ID, result)]


def test_service_rejects_unfinalized_selection() -> None:
    with pytest.raises(
        BlueprintRequirementLinkError,
        match="must be finalized",
    ):
        BlueprintRequirementLinkService(
            gateway=RecordingGateway()
        ).replace_from_selection(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            selection=_selection(finalized=False),
            assignments=_assignments(),
        )


def test_service_rejects_assignment_set_that_differs_from_selection() -> None:
    with pytest.raises(
        BlueprintRequirementLinkError,
        match="exactly match",
    ):
        BlueprintRequirementLinkService(
            gateway=RecordingGateway()
        ).replace_from_selection(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            selection=_selection(),
            assignments=_assignments()[:1],
        )


def test_assignment_serializes_decimal_without_float_loss() -> None:
    record = _assignments()[0].as_rpc_record()

    assert record["target_score"] == "0.50"
    assert record["coverage_role"] == "SUPPORTING"
