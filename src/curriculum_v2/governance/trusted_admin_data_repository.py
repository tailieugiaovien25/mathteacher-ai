from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TrustedAdministrativeDataRepository(ABC):
    """
    Persistence boundary for administratively governed educational data.

    This contract owns no physical-storage knowledge and no concrete
    educational values.
    """

    @abstractmethod
    def save(
        self,
        *,
        record_id: str,
        record: Any,
    ) -> None:
        """Persist one governed record."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        record_id: str,
    ) -> Any | None:
        """Return one governed record by logical identity."""
        raise NotImplementedError

    @abstractmethod
    def list_records(
        self,
        *,
        record_type: str | None = None,
    ) -> tuple[Any, ...]:
        """Return governed records, optionally filtered by logical type."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        record_id: str,
    ) -> None:
        """
        Remove a persisted record.

        Authorization and governance rules belong outside the repository.
        """
        raise NotImplementedError
