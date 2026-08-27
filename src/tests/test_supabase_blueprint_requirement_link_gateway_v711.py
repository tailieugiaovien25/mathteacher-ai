from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from assessment_generation_v2.adapters.supabase_blueprint_requirement_link_gateway import (
    SupabaseBlueprintRequirementLinkGateway,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
    BlueprintRequirementLinkError,
)


BLUEPRINT_VERSION_ID = "11111111-1111-4111-8111-111111111111"


@dataclass
class FakeResponse:
    data: object


class FakeRpc:
    def __init__(self, client: "FakeClient") -> None:
        self._client = client

    def execute(self) -> FakeResponse:
        return FakeResponse(self._client.response_data)


class FakeClient:
    def __init__(self, response_data: object) -> None:
        self.response_data = response_data
        self.calls: list[tuple[str, dict[str, object]]] = []

    def rpc(self, name: str, params: dict[str, object]) -> FakeRpc:
        self.calls.append((name, params))
        return FakeRpc(self)


def _assignment() -> BlueprintRequirementAssignment:
    return BlueprintRequirementAssignment(
        requirement_code="YCCD-MATH-06-0001",
        coverage_role="PRIMARY",
        target_question_count=2,
        target_score=Decimal("1.00"),
        sequence_number=10,
        specification_note="Trọng tâm",
    )


def test_gateway_calls_rpc_and_verifies_round_trip() -> None:
    row = _assignment()
    client = FakeClient(
        [
            {
                "blueprint_version_id": BLUEPRINT_VERSION_ID,
                **row.as_rpc_record(),
            }
        ]
    )

    result = SupabaseBlueprintRequirementLinkGateway(
        client=client
    ).replace_requirement_links(
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        assignments=(row,),
    )

    assert result == (row,)
    assert client.calls == [
        (
            "replace_assessment_blueprint_requirement_links",
            {
                "target_blueprint_version_id": BLUEPRINT_VERSION_ID,
                "requirement_assignments": [row.as_rpc_record()],
            },
        )
    ]


def test_gateway_rejects_response_that_differs_from_request() -> None:
    row = _assignment()
    response = row.as_rpc_record()
    response["target_question_count"] = 3
    client = FakeClient([response])

    with pytest.raises(
        BlueprintRequirementLinkError,
        match="does not match request",
    ):
        SupabaseBlueprintRequirementLinkGateway(
            client=client
        ).replace_requirement_links(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            assignments=(row,),
        )
