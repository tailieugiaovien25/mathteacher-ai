from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)


class OperationalPayloadRepository(ABC):
    """
    Storage-neutral repository contract for operational payloads.

    Payload storage is independent from operational source
    catalog metadata storage.
    """

    @abstractmethod
    def save(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
    ) -> OperationalPayloadEnvelope:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> OperationalPayloadEnvelope | None:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> None:
        raise NotImplementedError
