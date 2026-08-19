from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from educational_planning_v2.models.assignment_round import (
    AssignmentRound,
    AssignmentRoundStatus,
)
from educational_planning_v2.repositories.assignment_round_repository import (
    AssignmentRoundRepository,
)


class SupabaseAssignmentRoundRepository(
    AssignmentRoundRepository,
):
    TABLE_NAME = "assignment_rounds"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def save(
        self,
        *,
        assignment_round: AssignmentRound,
    ) -> AssignmentRound:
        if not isinstance(
            assignment_round,
            AssignmentRound,
        ):
            raise TypeError(
                "assignment_round must be AssignmentRound"
            )

        row = {
            "round_id": assignment_round.round_id,
            "academic_year": (
                assignment_round.academic_year
            ),
            "round_number": (
                assignment_round.round_number
            ),
            "effective_from": (
                assignment_round.effective_from.isoformat()
            ),
            "label": assignment_round.label,
            "status": (
                assignment_round.status.value
            ),
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                row,
                on_conflict="round_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return assignment_round

        return self._from_row(
            rows[0]
        )

    def get(
        self,
        *,
        round_id: str,
    ) -> AssignmentRound | None:
        normalized_id = self._required_text(
            round_id,
            "round_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "round_id",
                normalized_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def list_rounds(
        self,
        *,
        academic_year: str,
        status: AssignmentRoundStatus | None = None,
    ) -> tuple[
        AssignmentRound,
        ...,
    ]:
        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_year",
                normalized_year,
            )
        )

        if status is not None:
            if not isinstance(
                status,
                AssignmentRoundStatus,
            ):
                raise TypeError(
                    "status must be "
                    "AssignmentRoundStatus or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order(
                "round_number"
            )
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def delete(
        self,
        *,
        round_id: str,
    ) -> None:
        normalized_id = self._required_text(
            round_id,
            "round_id",
        )

        (
            self._client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "round_id",
                normalized_id,
            )
            .execute()
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> AssignmentRound:
        return AssignmentRound(
            round_id=str(
                row["round_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            round_number=int(
                row["round_number"]
            ),
            effective_from=date.fromisoformat(
                str(
                    row["effective_from"]
                )
            ),
            label=str(
                row["label"]
            ),
            status=AssignmentRoundStatus(
                str(
                    row["status"]
                )
            ),
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if data is None:
            return []

        if not isinstance(
            data,
            list,
        ):
            raise TypeError(
                "Supabase response data "
                "must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows "
                "must be dict"
            )

        return data
