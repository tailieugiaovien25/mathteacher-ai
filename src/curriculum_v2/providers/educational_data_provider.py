from abc import ABC, abstractmethod
from typing import Any

from curriculum_v2.providers.contracts import (
    EducationalDataQuery,
    EducationalDataResult,
)


class EducationalDataProvider(ABC):
    """
    Stable read boundary between educational-domain consumers
    and replaceable/versioned educational data sources.

    Data sources may change without requiring consumers to know:
    - physical storage format;
    - file or database location;
    - textbook series;
    - curriculum edition;
    - regulation edition;
    - concrete educational values.

    Implementations are responsible for resolving source-specific
    data into canonical educational contracts.
    """

    @abstractmethod
    def query(
        self,
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        """
        Generic provider-neutral data query.

        New educational data capabilities should prefer this boundary
        instead of expanding the provider contract with source-specific
        or domain-instance-specific methods.
        """
        raise NotImplementedError

    @abstractmethod
    def get_curriculum(
        self,
        *,
        curriculum_ref: str,
    ) -> Any:
        """Backward-compatible curriculum capability."""
        raise NotImplementedError

    @abstractmethod
    def get_learning_requirements(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ) -> tuple[Any, ...]:
        """Backward-compatible learning-requirement capability."""
        raise NotImplementedError

    @abstractmethod
    def get_textbook_lessons(
        self,
        *,
        textbook_ref: str,
        subject: str,
        grade: int,
    ) -> tuple[Any, ...]:
        """Backward-compatible textbook lesson capability."""
        raise NotImplementedError

    @abstractmethod
    def get_textbook_requirement_mappings(
        self,
        *,
        textbook_ref: str,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ) -> tuple[Any, ...]:
        """Backward-compatible textbook mapping capability."""
        raise NotImplementedError

    @abstractmethod
    def get_time_allocation(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ) -> Any:
        """Backward-compatible time-allocation capability."""
        raise NotImplementedError
