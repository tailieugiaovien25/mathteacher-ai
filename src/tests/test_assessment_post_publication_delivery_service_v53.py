from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from assessment_generation_v2.services.post_publication_delivery_service import (
    AssessmentDeliveryValidationError,
    AssessmentExportFormat,
    AssessmentExportPackageType,
    AssessmentPostPublicationDeliveryRequest,
    AssessmentPostPublicationDeliveryService,
    PublishedAssessmentSnapshot,
    PublishedExamSnapshotUnavailableError,
)


EXAM_VERSION_ID = "11111111-1111-4111-8111-111111111111"
OWNER_USER_ID = "22222222-2222-4222-8222-222222222222"
SNAPSHOT_ID = "33333333-3333-4333-8333-333333333333"
VARIANT_IDS = (
    "44444444-4444-4444-8444-444444444444",
    "55555555-5555-4555-8555-555555555555",
)


class FakePostPublicationGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.snapshot: PublishedAssessmentSnapshot | None = (
            PublishedAssessmentSnapshot(
                snapshot_id=SNAPSHOT_ID,
                exam_version_id=EXAM_VERSION_ID,
                owner_user_id=OWNER_USER_ID,
                snapshot_hash="a" * 64,
                hash_verified=True,
            )
        )
        self.variant_ids: list[str] = list(VARIANT_IDS)
        self.package_counter = 0

    def find_published_snapshot(
        self,
        *,
        exam_version_id: str,
    ) -> PublishedAssessmentSnapshot | None:
        self.calls.append(
            (
                "find_snapshot",
                {"exam_version_id": exam_version_id},
            )
        )
        return self.snapshot

    def generate_exam_variant(
        self,
        *,
        snapshot_id: str,
        variant_code: str,
        generation_seed: str,
    ) -> str:
        self.calls.append(
            (
                "generate_variant",
                {
                    "snapshot_id": snapshot_id,
                    "variant_code": variant_code,
                    "generation_seed": generation_seed,
                },
            )
        )
        return self.variant_ids.pop(0)

    def create_export_package(
        self,
        *,
        variant_id: str,
        package_type: AssessmentExportPackageType,
        target_format: AssessmentExportFormat,
        template_code: str,
        template_version: str,
    ) -> str:
        self.calls.append(
            (
                "create_export",
                {
                    "variant_id": variant_id,
                    "package_type": package_type,
                    "target_format": target_format,
                    "template_code": template_code,
                    "template_version": template_version,
                },
            )
        )
        self.package_counter += 1
        return str(
            UUID(
                int=0x60000000000040008000000000000000
                + self.package_counter
            )
        )


def _request(
    **changes: object,
) -> AssessmentPostPublicationDeliveryRequest:
    values: dict[str, object] = {
        "exam_version_id": EXAM_VERSION_ID,
        "owner_user_id": OWNER_USER_ID,
        "variant_codes": ("101", "102"),
        "target_format": AssessmentExportFormat.DOCX,
        "template_code": "PHONG_GD_DIEN_BIEN",
        "template_version": "2026.1",
        "delivery_key": "toan6-ghk1-lan-1",
    }
    values.update(changes)
    return AssessmentPostPublicationDeliveryRequest(
        **values
    )


def test_delivery_uses_only_published_snapshot_path() -> None:
    gateway = FakePostPublicationGateway()
    service = AssessmentPostPublicationDeliveryService(
        gateway=gateway
    )

    result = service.deliver(request=_request())

    assert result.snapshot_id == SNAPSHOT_ID
    assert len(result.deliveries) == 2
    assert [
        call[0]
        for call in gateway.calls
    ] == [
        "find_snapshot",
        "generate_variant",
        "create_export",
        "create_export",
        "create_export",
        "generate_variant",
        "create_export",
        "create_export",
        "create_export",
    ]


def test_default_delivery_builds_three_package_types() -> None:
    gateway = FakePostPublicationGateway()
    service = AssessmentPostPublicationDeliveryService(
        gateway=gateway
    )

    result = service.deliver(
        request=_request(
            variant_codes=("101",),
        )
    )

    assert len(
        result.deliveries[0].export_package_ids
    ) == 3

    package_types = [
        call[1]["package_type"]
        for call in gateway.calls
        if call[0] == "create_export"
    ]

    assert package_types == [
        AssessmentExportPackageType.STUDENT_EXAM,
        AssessmentExportPackageType.ANSWER_KEY,
        AssessmentExportPackageType.SCORING_GUIDE,
    ]


def test_generation_seed_is_deterministic_and_scoped() -> None:
    first_gateway = FakePostPublicationGateway()
    second_gateway = FakePostPublicationGateway()

    AssessmentPostPublicationDeliveryService(
        gateway=first_gateway
    ).deliver(
        request=_request(variant_codes=("101",))
    )
    AssessmentPostPublicationDeliveryService(
        gateway=second_gateway
    ).deliver(
        request=_request(variant_codes=("101",))
    )

    first_seed = first_gateway.calls[1][1][
        "generation_seed"
    ]
    second_seed = second_gateway.calls[1][1][
        "generation_seed"
    ]

    assert first_seed == second_seed
    assert isinstance(first_seed, str)
    assert len(first_seed) == 64


def test_missing_snapshot_stops_before_variant_generation() -> None:
    gateway = FakePostPublicationGateway()
    gateway.snapshot = None
    service = AssessmentPostPublicationDeliveryService(
        gateway=gateway
    )

    with pytest.raises(
        PublishedExamSnapshotUnavailableError,
        match="no published",
    ):
        service.deliver(request=_request())

    assert [
        call[0]
        for call in gateway.calls
    ] == ["find_snapshot"]


def test_snapshot_with_invalid_integrity_is_rejected() -> None:
    gateway = FakePostPublicationGateway()
    gateway.snapshot = PublishedAssessmentSnapshot(
        snapshot_id=SNAPSHOT_ID,
        exam_version_id=EXAM_VERSION_ID,
        owner_user_id=OWNER_USER_ID,
        snapshot_hash="b" * 64,
        hash_verified=False,
    )

    with pytest.raises(
        PublishedExamSnapshotUnavailableError,
        match="integrity",
    ):
        AssessmentPostPublicationDeliveryService(
            gateway=gateway
        ).deliver(request=_request())

    assert not any(
        call[0] == "generate_variant"
        for call in gateway.calls
    )


def test_owner_mismatch_stops_delivery() -> None:
    gateway = FakePostPublicationGateway()

    with pytest.raises(
        PermissionError,
        match="owner",
    ):
        AssessmentPostPublicationDeliveryService(
            gateway=gateway
        ).deliver(
            request=_request(
                owner_user_id=(
                    "99999999-9999-4999-8999-"
                    "999999999999"
                ),
            )
        )

    assert not any(
        call[0] == "generate_variant"
        for call in gateway.calls
    )


@pytest.mark.parametrize(
    "variant_codes",
    (
        ["101"],
        (),
        ("101", "101"),
        ("101", " 101 "),
    ),
)
def test_invalid_variant_code_contract_is_rejected(
    variant_codes: object,
) -> None:
    with pytest.raises(
        AssessmentDeliveryValidationError
    ):
        _request(variant_codes=variant_codes)


def test_selected_package_subset_is_respected() -> None:
    gateway = FakePostPublicationGateway()

    result = AssessmentPostPublicationDeliveryService(
        gateway=gateway
    ).deliver(
        request=_request(
            variant_codes=("101",),
            package_types=(
                AssessmentExportPackageType.STUDENT_EXAM,
            ),
            target_format=AssessmentExportFormat.PDF,
        )
    )

    assert len(
        result.deliveries[0].export_package_ids
    ) == 1

    export_call = next(
        call
        for call in gateway.calls
        if call[0] == "create_export"
    )

    assert export_call[1]["target_format"] == (
        AssessmentExportFormat.PDF
    )


def test_invalid_variant_identifier_stops_exports() -> None:
    gateway = FakePostPublicationGateway()
    gateway.variant_ids[0] = "not-a-uuid"

    with pytest.raises(
        RuntimeError,
        match="invalid variant",
    ):
        AssessmentPostPublicationDeliveryService(
            gateway=gateway
        ).deliver(
            request=_request(variant_codes=("101",))
        )

    assert not any(
        call[0] == "create_export"
        for call in gateway.calls
    )


def test_duplicate_variant_identifier_is_rejected() -> None:
    gateway = FakePostPublicationGateway()
    gateway.variant_ids = [
        VARIANT_IDS[0],
        VARIANT_IDS[0],
    ]

    with pytest.raises(
        RuntimeError,
        match="duplicate variant",
    ):
        AssessmentPostPublicationDeliveryService(
            gateway=gateway
        ).deliver(request=_request())


def test_invalid_export_identifier_stops_delivery() -> None:
    class InvalidExportGateway(
        FakePostPublicationGateway
    ):
        def create_export_package(
            self,
            **kwargs: object,
        ) -> str:
            super().create_export_package(**kwargs)
            return "invalid-package-id"

    gateway = InvalidExportGateway()

    with pytest.raises(
        RuntimeError,
        match="invalid export package",
    ):
        AssessmentPostPublicationDeliveryService(
            gateway=gateway
        ).deliver(
            request=_request(variant_codes=("101",))
        )


def test_contracts_are_immutable() -> None:
    request = _request()

    with pytest.raises(FrozenInstanceError):
        request.template_code = "CHANGED"


def test_service_has_no_governance_methods() -> None:
    forbidden_methods = (
        "approve_exam",
        "publish_exam",
        "capture_snapshot",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            AssessmentPostPublicationDeliveryService,
            method_name,
        )


def test_service_source_has_no_application_imports() -> None:
    from pathlib import Path

    source = Path(
        "src/assessment_generation_v2/services/"
        "post_publication_delivery_service.py"
    ).read_text(encoding="utf-8-sig")

    forbidden_imports = (
        "import streamlit",
        "from streamlit",
        "import supabase",
        "from supabase",
        "from portal_v2",
    )

    for forbidden_import in forbidden_imports:
        assert forbidden_import not in source
