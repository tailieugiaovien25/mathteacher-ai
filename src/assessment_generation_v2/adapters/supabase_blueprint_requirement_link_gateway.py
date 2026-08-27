from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
    BlueprintRequirementLinkError,
)


class SupabaseBlueprintRequirementLinkGateway:
    RPC_NAME = "replace_assessment_blueprint_requirement_links"

    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client

    @staticmethod
    def _response_rows(response: object) -> list[Mapping[str, object]]:
        data = (
            response.get("data")
            if isinstance(response, Mapping)
            else getattr(response, "data", None)
        )
        if not isinstance(data, list):
            raise BlueprintRequirementLinkError(
                "requirement-link RPC must return a row list"
            )
        if any(not isinstance(row, Mapping) for row in data):
            raise BlueprintRequirementLinkError(
                "requirement-link RPC returned an invalid row"
            )
        return list(data)

    def replace_requirement_links(
        self,
        *,
        blueprint_version_id: str,
        assignments: Sequence[BlueprintRequirementAssignment],
    ) -> tuple[BlueprintRequirementAssignment, ...]:
        response = self._client.rpc(
            self.RPC_NAME,
            {
                "target_blueprint_version_id": blueprint_version_id,
                "requirement_assignments": [
                    assignment.as_rpc_record()
                    for assignment in assignments
                ],
            },
        ).execute()

        result = tuple(
            BlueprintRequirementAssignment(
                requirement_code=str(row.get("requirement_code", "")),
                coverage_role=str(row.get("coverage_role", "")),
                target_question_count=int(
                    row.get("target_question_count", 0)
                ),
                target_score=(
                    None
                    if row.get("target_score") is None
                    else Decimal(str(row["target_score"]))
                ),
                sequence_number=int(row.get("sequence_number", -1)),
                specification_note=str(
                    row.get("specification_note") or ""
                ),
            )
            for row in self._response_rows(response)
        )

        expected = tuple(
            sorted(
                assignments,
                key=lambda row: (
                    row.sequence_number,
                    row.requirement_code,
                ),
            )
        )
        if result != expected:
            raise BlueprintRequirementLinkError(
                "requirement-link RPC result does not match request"
            )

        return result
