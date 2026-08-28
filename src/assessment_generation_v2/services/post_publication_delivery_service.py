"""Post-publication assessment delivery orchestration.

This module deliberately starts from an immutable published snapshot.
It cannot approve or publish an assessment exam.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Protocol
from uuid import UUID


class AssessmentDeliveryValidationError(ValueError):
    """Raised when a delivery request violates its contract."""


class PublishedExamSnapshotUnavailableError(RuntimeError):
    """Raised when no usable immutable snapshot is available."""


class AssessmentExportPackageType(StrEnum):
    STUDENT_EXAM = "STUDENT_EXAM"
    ANSWER_KEY = "ANSWER_KEY"
    SCORING_GUIDE = "SCORING_GUIDE"


class AssessmentExportFormat(StrEnum):
    DOCX = "DOCX"
    PDF = "PDF"
    JSON = "JSON"


def _required_text(
    value: object,
    field_name: str,
    *,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise AssessmentDeliveryValidationError(
            f"{field_name} must be text"
        )

    normalized = value.strip()

    if not normalized:
        raise AssessmentDeliveryValidationError(
            f"{field_name} is required"
        )

    if len(normalized) > maximum_length:
        raise AssessmentDeliveryValidationError(
            f"{field_name} is too long"
        )

    return normalized


def _required_uuid(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise AssessmentDeliveryValidationError(
            f"{field_name} must be a UUID string"
        )

    try:
        return str(UUID(value))
    except ValueError as error:
        raise AssessmentDeliveryValidationError(
            f"{field_name} must be a valid UUID"
        ) from error


@dataclass(frozen=True, slots=True)
class PublishedAssessmentSnapshot:
    snapshot_id: str
    exam_version_id: str
    owner_user_id: str
    snapshot_hash: str
    hash_verified: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_id",
            _required_uuid(
                self.snapshot_id,
                "snapshot_id",
            ),
        )
        object.__setattr__(
            self,
            "exam_version_id",
            _required_uuid(
                self.exam_version_id,
                "exam_version_id",
            ),
        )
        object.__setattr__(
            self,
            "owner_user_id",
            _required_uuid(
                self.owner_user_id,
                "owner_user_id",
            ),
        )

        normalized_hash = _required_text(
            self.snapshot_hash,
            "snapshot_hash",
            maximum_length=64,
        ).lower()

        if (
            len(normalized_hash) != 64
            or any(
                character not in "0123456789abcdef"
                for character in normalized_hash
            )
        ):
            raise AssessmentDeliveryValidationError(
                "snapshot_hash must be a SHA-256 hex digest"
            )

        object.__setattr__(
            self,
            "snapshot_hash",
            normalized_hash,
        )

        if not isinstance(self.hash_verified, bool):
            raise AssessmentDeliveryValidationError(
                "hash_verified must be boolean"
            )


@dataclass(frozen=True, slots=True)
class AssessmentPostPublicationDeliveryRequest:
    exam_version_id: str
    owner_user_id: str
    variant_codes: tuple[str, ...]
    target_format: AssessmentExportFormat
    template_code: str
    template_version: str
    delivery_key: str
    package_types: tuple[
        AssessmentExportPackageType,
        ...
    ] = (
        AssessmentExportPackageType.STUDENT_EXAM,
        AssessmentExportPackageType.ANSWER_KEY,
        AssessmentExportPackageType.SCORING_GUIDE,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "exam_version_id",
            _required_uuid(
                self.exam_version_id,
                "exam_version_id",
            ),
        )
        object.__setattr__(
            self,
            "owner_user_id",
            _required_uuid(
                self.owner_user_id,
                "owner_user_id",
            ),
        )

        if not isinstance(self.variant_codes, tuple):
            raise AssessmentDeliveryValidationError(
                "variant_codes must be a tuple"
            )

        if not 1 <= len(self.variant_codes) <= 20:
            raise AssessmentDeliveryValidationError(
                "variant_codes must contain between 1 and 20 items"
            )

        normalized_variant_codes = tuple(
            _required_text(
                variant_code,
                "variant_code",
                maximum_length=50,
            ).upper()
            for variant_code in self.variant_codes
        )

        if (
            len(set(normalized_variant_codes))
            != len(normalized_variant_codes)
        ):
            raise AssessmentDeliveryValidationError(
                "variant_codes must be unique"
            )

        object.__setattr__(
            self,
            "variant_codes",
            normalized_variant_codes,
        )

        if not isinstance(
            self.target_format,
            AssessmentExportFormat,
        ):
            raise AssessmentDeliveryValidationError(
                "target_format is invalid"
            )

        object.__setattr__(
            self,
            "template_code",
            _required_text(
                self.template_code,
                "template_code",
                maximum_length=140,
            ),
        )
        object.__setattr__(
            self,
            "template_version",
            _required_text(
                self.template_version,
                "template_version",
                maximum_length=100,
            ),
        )
        object.__setattr__(
            self,
            "delivery_key",
            _required_text(
                self.delivery_key,
                "delivery_key",
                maximum_length=200,
            ),
        )

        if not isinstance(self.package_types, tuple):
            raise AssessmentDeliveryValidationError(
                "package_types must be a tuple"
            )

        if not self.package_types:
            raise AssessmentDeliveryValidationError(
                "package_types must not be empty"
            )

        if any(
            not isinstance(
                package_type,
                AssessmentExportPackageType,
            )
            for package_type in self.package_types
        ):
            raise AssessmentDeliveryValidationError(
                "package_types contains an invalid item"
            )

        if (
            len(set(self.package_types))
            != len(self.package_types)
        ):
            raise AssessmentDeliveryValidationError(
                "package_types must be unique"
            )


@dataclass(frozen=True, slots=True)
class AssessmentVariantDelivery:
    variant_code: str
    variant_id: str
    export_package_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "variant_code",
            _required_text(
                self.variant_code,
                "variant_code",
                maximum_length=50,
            ).upper(),
        )
        object.__setattr__(
            self,
            "variant_id",
            _required_uuid(
                self.variant_id,
                "variant_id",
            ),
        )

        if not isinstance(
            self.export_package_ids,
            tuple,
        ):
            raise AssessmentDeliveryValidationError(
                "export_package_ids must be a tuple"
            )

        normalized_package_ids = tuple(
            _required_uuid(
                package_id,
                "export_package_id",
            )
            for package_id in self.export_package_ids
        )

        if (
            len(set(normalized_package_ids))
            != len(normalized_package_ids)
        ):
            raise AssessmentDeliveryValidationError(
                "export package identifiers must be unique"
            )

        object.__setattr__(
            self,
            "export_package_ids",
            normalized_package_ids,
        )


@dataclass(frozen=True, slots=True)
class AssessmentPostPublicationDeliveryResult:
    snapshot_id: str
    deliveries: tuple[AssessmentVariantDelivery, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_id",
            _required_uuid(
                self.snapshot_id,
                "snapshot_id",
            ),
        )

        if not isinstance(self.deliveries, tuple):
            raise AssessmentDeliveryValidationError(
                "deliveries must be a tuple"
            )

        variant_ids = tuple(
            delivery.variant_id
            for delivery in self.deliveries
        )

        if len(set(variant_ids)) != len(variant_ids):
            raise AssessmentDeliveryValidationError(
                "variant identifiers must be unique"
            )


class AssessmentPostPublicationDeliveryGateway(Protocol):
    def find_published_snapshot(
        self,
        *,
        exam_version_id: str,
    ) -> PublishedAssessmentSnapshot | None:
        """Return the immutable snapshot visible to the caller."""

    def generate_exam_variant(
        self,
        *,
        snapshot_id: str,
        variant_code: str,
        generation_seed: str,
    ) -> str:
        """Call generate_assessment_exam_variant."""

    def create_export_package(
        self,
        *,
        variant_id: str,
        package_type: AssessmentExportPackageType,
        target_format: AssessmentExportFormat,
        template_code: str,
        template_version: str,
    ) -> str:
        """Call create_assessment_exam_export_package."""


class AssessmentPostPublicationDeliveryService:
    """Generate variants and exports after human publication.

    Approval, publication, and snapshot creation are intentionally
    outside this service.
    """

    def __init__(
        self,
        *,
        gateway: AssessmentPostPublicationDeliveryGateway,
    ) -> None:
        self._gateway = gateway

    def deliver(
        self,
        *,
        request: AssessmentPostPublicationDeliveryRequest,
    ) -> AssessmentPostPublicationDeliveryResult:
        snapshot = self._gateway.find_published_snapshot(
            exam_version_id=request.exam_version_id,
        )

        if snapshot is None:
            raise PublishedExamSnapshotUnavailableError(
                "no published immutable snapshot is available"
            )

        if snapshot.exam_version_id != request.exam_version_id:
            raise PublishedExamSnapshotUnavailableError(
                "snapshot does not match the requested exam version"
            )

        if snapshot.owner_user_id != request.owner_user_id:
            raise PermissionError(
                "snapshot owner does not match the request owner"
            )

        if not snapshot.hash_verified:
            raise PublishedExamSnapshotUnavailableError(
                "published snapshot integrity verification failed"
            )

        deliveries: list[AssessmentVariantDelivery] = []
        seen_variant_ids: set[str] = set()
        seen_package_ids: set[str] = set()

        for variant_code in request.variant_codes:
            generation_seed = sha256(
                (
                    f"{snapshot.snapshot_hash}:"
                    f"{request.delivery_key}:"
                    f"{variant_code}"
                ).encode("utf-8")
            ).hexdigest()

            raw_variant_id = (
                self._gateway.generate_exam_variant(
                    snapshot_id=snapshot.snapshot_id,
                    variant_code=variant_code,
                    generation_seed=generation_seed,
                )
            )

            try:
                variant_id = _required_uuid(
                    raw_variant_id,
                    "variant_id",
                )
            except AssessmentDeliveryValidationError as error:
                raise RuntimeError(
                    "gateway returned an invalid variant identifier"
                ) from error

            if variant_id in seen_variant_ids:
                raise RuntimeError(
                    "gateway returned duplicate variant identifiers"
                )

            seen_variant_ids.add(variant_id)
            package_ids: list[str] = []

            for package_type in request.package_types:
                raw_package_id = (
                    self._gateway.create_export_package(
                        variant_id=variant_id,
                        package_type=package_type,
                        target_format=request.target_format,
                        template_code=request.template_code,
                        template_version=(
                            request.template_version
                        ),
                    )
                )

                try:
                    package_id = _required_uuid(
                        raw_package_id,
                        "export_package_id",
                    )
                except AssessmentDeliveryValidationError as error:
                    raise RuntimeError(
                        "gateway returned an invalid "
                        "export package identifier"
                    ) from error

                if package_id in seen_package_ids:
                    raise RuntimeError(
                        "gateway returned duplicate "
                        "export package identifiers"
                    )

                seen_package_ids.add(package_id)
                package_ids.append(package_id)

            deliveries.append(
                AssessmentVariantDelivery(
                    variant_code=variant_code,
                    variant_id=variant_id,
                    export_package_ids=tuple(
                        package_ids
                    ),
                )
            )

        return AssessmentPostPublicationDeliveryResult(
            snapshot_id=snapshot.snapshot_id,
            deliveries=tuple(deliveries),
        )
