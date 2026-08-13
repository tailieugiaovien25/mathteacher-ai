from types import MappingProxyType
from typing import Callable, Mapping

from curriculum_v2.providers.contracts import (
    EducationalDataQuery,
    EducationalDataResult,
)
from curriculum_v2.providers.educational_data_provider import (
    EducationalDataProvider,
)


EducationalDataHandler = Callable[
    [EducationalDataQuery],
    EducationalDataResult,
]


class CapabilityEducationalDataProvider(
    EducationalDataProvider
):
    """
    Generic provider implementation backed by injected
    capability handlers.

    The provider owns no physical educational data source.
    Source-specific adapters/loaders are injected externally.
    """

    def __init__(
        self,
        *,
        handlers: Mapping[
            str,
            EducationalDataHandler,
        ],
    ) -> None:
        if not isinstance(
            handlers,
            Mapping,
        ):
            raise TypeError(
                "handlers must be a mapping"
            )

        normalized = {}

        for capability, handler in handlers.items():
            capability = self._required_text(
                capability,
                "capability",
            )

            if not callable(handler):
                raise TypeError(
                    "handler must be callable"
                )

            normalized[
                capability
            ] = handler

        if not normalized:
            raise ValueError(
                "handlers must not be empty"
            )

        self._handlers = MappingProxyType(
            normalized
        )

    @property
    def capabilities(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                self._handlers
            )
        )

    def query(
        self,
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        if not isinstance(
            query,
            EducationalDataQuery,
        ):
            raise TypeError(
                "query must be EducationalDataQuery"
            )

        try:
            handler = self._handlers[
                query.capability
            ]
        except KeyError as error:
            raise LookupError(
                "unsupported educational data capability: "
                f"{query.capability}"
            ) from error

        result = handler(
            query
        )

        if not isinstance(
            result,
            EducationalDataResult,
        ):
            raise TypeError(
                "handler must return EducationalDataResult"
            )

        if (
            result.capability
            != query.capability
        ):
            raise ValueError(
                "result capability does not match query"
            )

        return result

    def get_curriculum(
        self,
        *,
        curriculum_ref: str,
    ):
        return self.query(
            EducationalDataQuery(
                capability="curriculum",
                curriculum_ref=curriculum_ref,
            )
        )

    def get_learning_requirements(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return self.query(
            EducationalDataQuery(
                capability="learning_requirements",
                curriculum_ref=curriculum_ref,
                subject_ref=str(subject),
                grade_ref=str(grade),
            )
        )

    def get_textbook_lessons(
        self,
        *,
        textbook_ref: str,
        subject: str,
        grade: int,
    ):
        return self.query(
            EducationalDataQuery(
                capability="textbook_lessons",
                textbook_ref=textbook_ref,
                subject_ref=str(subject),
                grade_ref=str(grade),
            )
        )

    def get_textbook_requirement_mappings(
        self,
        *,
        textbook_ref: str,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return self.query(
            EducationalDataQuery(
                capability="textbook_requirement_mappings",
                textbook_ref=textbook_ref,
                curriculum_ref=curriculum_ref,
                subject_ref=str(subject),
                grade_ref=str(grade),
            )
        )

    def get_time_allocation(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return self.query(
            EducationalDataQuery(
                capability="time_allocation",
                curriculum_ref=curriculum_ref,
                subject_ref=str(subject),
                grade_ref=str(grade),
            )
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
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
