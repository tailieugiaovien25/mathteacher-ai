from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.assignment_round import (
    AssignmentRound,
    AssignmentRoundStatus,
)


class AssignmentRoundRepository(
    ABC,
):
    @abstractmethod
    def save(
        self,
        *,
        assignment_round: AssignmentRound,
    ) -> AssignmentRound:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        round_id: str,
    ) -> AssignmentRound | None:
        raise NotImplementedError

    @abstractmethod
    def list_rounds(
        self,
        *,
        academic_year: str,
        status: AssignmentRoundStatus | None = None,
    ) -> tuple[
        AssignmentRound,
        ...,
    ]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        round_id: str,
    ) -> None:
        raise NotImplementedError
