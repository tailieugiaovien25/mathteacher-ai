from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from curriculum_v2.governance.administrative_authorization import (
    GovernanceActor,
    GovernanceAuthorizationPolicy,
    GovernancePermission,
)


class AdministrativeDataState(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class AdministrativeDataAuditEvent:
    event_type: str
    actor_id: str
    occurred_at: datetime
    from_state: AdministrativeDataState
    to_state: AdministrativeDataState

    def __post_init__(self) -> None:
        for field_name in (
            "event_type",
            "actor_id",
        ):
            value = getattr(
                self,
                field_name,
            )

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

        if not isinstance(
            self.occurred_at,
            datetime,
        ):
            raise TypeError(
                "occurred_at must be datetime"
            )


@dataclass(frozen=True)
class AdministrativeDataSubmission:
    submission_id: str
    entered_by: str
    state: AdministrativeDataState
    version: int = 1
    audit_trail: tuple[
        AdministrativeDataAuditEvent,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "submission_id",
            "entered_by",
        ):
            value = getattr(
                self,
                field_name,
            )

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

        if not isinstance(
            self.state,
            AdministrativeDataState,
        ):
            raise TypeError(
                "state must be AdministrativeDataState"
            )

        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
        ):
            raise TypeError(
                "version must be int"
            )

        if self.version <= 0:
            raise ValueError(
                "version must be positive"
            )

        if not isinstance(
            self.audit_trail,
            tuple,
        ):
            raise TypeError(
                "audit_trail must be tuple"
            )

        for event in self.audit_trail:
            if not isinstance(
                event,
                AdministrativeDataAuditEvent,
            ):
                raise TypeError(
                    "audit_trail must contain "
                    "AdministrativeDataAuditEvent"
                )


class AdministrativeDataWorkflow:
    @staticmethod
    def create_draft(
        *,
        submission_id: str,
        actor: GovernanceActor,
    ) -> AdministrativeDataSubmission:
        GovernanceAuthorizationPolicy.require(
            actor=actor,
            permission=GovernancePermission.ENTER_DATA,
        )

        return AdministrativeDataSubmission(
            submission_id=submission_id,
            entered_by=actor.actor_id,
            state=AdministrativeDataState.DRAFT,
        )

    @classmethod
    def submit(
        cls,
        *,
        submission: AdministrativeDataSubmission,
        actor: GovernanceActor,
        occurred_at: datetime,
    ) -> AdministrativeDataSubmission:
        GovernanceAuthorizationPolicy.require(
            actor=actor,
            permission=GovernancePermission.ENTER_DATA,
        )

        if submission.state is not AdministrativeDataState.DRAFT:
            raise ValueError(
                "only DRAFT submission can be submitted"
            )

        return cls._transition(
            submission=submission,
            actor=actor,
            occurred_at=occurred_at,
            event_type="SUBMIT",
            target_state=AdministrativeDataState.PENDING,
        )

    @classmethod
    def verify(
        cls,
        *,
        submission: AdministrativeDataSubmission,
        actor: GovernanceActor,
        occurred_at: datetime,
    ) -> AdministrativeDataSubmission:
        GovernanceAuthorizationPolicy.require(
            actor=actor,
            permission=GovernancePermission.VERIFY_DATA,
        )

        if submission.state is not AdministrativeDataState.PENDING:
            raise ValueError(
                "only PENDING submission can be verified"
            )

        return cls._transition(
            submission=submission,
            actor=actor,
            occurred_at=occurred_at,
            event_type="VERIFY",
            target_state=AdministrativeDataState.VERIFIED,
        )

    @classmethod
    def publish(
        cls,
        *,
        submission: AdministrativeDataSubmission,
        actor: GovernanceActor,
        occurred_at: datetime,
    ) -> AdministrativeDataSubmission:
        GovernanceAuthorizationPolicy.require(
            actor=actor,
            permission=GovernancePermission.PUBLISH_DATA,
        )

        if submission.state is not AdministrativeDataState.VERIFIED:
            raise ValueError(
                "only VERIFIED submission can be published"
            )

        return cls._transition(
            submission=submission,
            actor=actor,
            occurred_at=occurred_at,
            event_type="PUBLISH",
            target_state=AdministrativeDataState.PUBLISHED,
        )

    @classmethod
    def supersede(
        cls,
        *,
        submission: AdministrativeDataSubmission,
        actor: GovernanceActor,
        occurred_at: datetime,
    ) -> AdministrativeDataSubmission:
        GovernanceAuthorizationPolicy.require(
            actor=actor,
            permission=GovernancePermission.SUPERSEDE_DATA,
        )

        if submission.state is not AdministrativeDataState.PUBLISHED:
            raise ValueError(
                "only PUBLISHED submission can be superseded"
            )

        return cls._transition(
            submission=submission,
            actor=actor,
            occurred_at=occurred_at,
            event_type="SUPERSEDE",
            target_state=AdministrativeDataState.SUPERSEDED,
        )

    @staticmethod
    def _transition(
        *,
        submission: AdministrativeDataSubmission,
        actor: GovernanceActor,
        occurred_at: datetime,
        event_type: str,
        target_state: AdministrativeDataState,
    ) -> AdministrativeDataSubmission:
        if not isinstance(
            submission,
            AdministrativeDataSubmission,
        ):
            raise TypeError(
                "submission must be AdministrativeDataSubmission"
            )

        if not isinstance(
            actor,
            GovernanceActor,
        ):
            raise TypeError(
                "actor must be GovernanceActor"
            )

        if not isinstance(
            occurred_at,
            datetime,
        ):
            raise TypeError(
                "occurred_at must be datetime"
            )

        event = AdministrativeDataAuditEvent(
            event_type=event_type,
            actor_id=actor.actor_id,
            occurred_at=occurred_at,
            from_state=submission.state,
            to_state=target_state,
        )

        return AdministrativeDataSubmission(
            submission_id=submission.submission_id,
            entered_by=submission.entered_by,
            state=target_state,
            version=submission.version + 1,
            audit_trail=(
                *submission.audit_trail,
                event,
            ),
        )
