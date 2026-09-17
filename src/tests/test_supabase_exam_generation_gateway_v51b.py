from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import pytest

from assessment_generation_v2.adapters.supabase_exam_generation_gateway import (
    AssessmentGatewayResponseError,
    SupabaseAssessmentExamGenerationGateway,
)
from assessment_generation_v2.services.assessment_foundation import (
    ValidationResult,
    ValidationStatus,
)
from assessment_generation_v2.services.exam_generation_service import (
    AssessmentExamGenerationRequest,
)


USER_ID = "11111111-1111-4111-8111-111111111111"
BLUEPRINT_VERSION_ID = (
    "22222222-2222-4222-8222-222222222222"
)
EXAM_ID = "33333333-3333-4333-8333-333333333333"
EXAM_VERSION_ID = (
    "44444444-4444-4444-8444-444444444444"
)
EVIDENCE_ID = "55555555-5555-4555-8555-555555555555"
VALIDATION_INPUT_DIGEST = "a" * 64
EVIDENCE_DIGEST = "b" * 64


@dataclass
class FakeResponse:
    data: object


class FakeNotFilter:
    def __init__(self, query: "FakeQuery") -> None:
        self._query = query

    def is_(
        self,
        column: str,
        value: object,
    ) -> "FakeQuery":
        self._query.operations.append(
            ("not_is", column, value)
        )
        return self._query


class FakeQuery:
    def __init__(
        self,
        *,
        client: "FakeClient",
        table_name: str,
    ) -> None:
        self.client = client
        self.table_name = table_name
        self.operations: list[tuple[object, ...]] = []

    @property
    def not_(self) -> FakeNotFilter:
        return FakeNotFilter(self)

    def select(self, value: str) -> "FakeQuery":
        self.operations.append(("select", value))
        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> "FakeQuery":
        self.operations.append(("eq", column, value))
        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> "FakeQuery":
        self.operations.append(
            ("order", column, desc)
        )
        return self

    def limit(self, value: int) -> "FakeQuery":
        self.operations.append(("limit", value))
        return self

    def execute(self) -> FakeResponse:
        self.client.table_calls.append(
            (
                self.table_name,
                tuple(self.operations),
            )
        )

        if (
            self.table_name
            == "assessment_blueprint_versions"
        ):
            return FakeResponse(
                self.client.blueprint_data
            )

        if (
            self.table_name
            == "assessment_exam_versions"
        ):
            return FakeResponse(
                [
                    {
                        "assembly_status": (
                            self.client.exam_status
                        )
                    }
                ]
            )

        raise AssertionError(
            f"unexpected table: {self.table_name}"
        )


class FakeRpcCall:
    def __init__(
        self,
        *,
        client: "FakeClient",
        rpc_name: str,
        parameters: dict[str, object],
    ) -> None:
        self.client = client
        self.rpc_name = rpc_name
        self.parameters = parameters

    def execute(self) -> FakeResponse:
        self.client.rpc_calls.append(
            (
                self.rpc_name,
                dict(self.parameters),
            )
        )

        return FakeResponse(
            self.client.rpc_data[self.rpc_name]
        )


class FakeClient:
    def __init__(self) -> None:
        self.blueprint_data: object = [
            {
                "blueprint_version_id": (
                    BLUEPRINT_VERSION_ID
                ),
                "version_number": 1,
                "review_status": "APPROVED",
                "locked_at": "2026-08-25T00:00:00Z",
                "assessment_blueprints": {
                    "blueprint_code": "TOAN6_GHK1",
                    "owner_user_id": USER_ID,
                    "lifecycle_status": "ACTIVE",
                },
            }
        ]
        self.exam_status = "AI_PROPOSED"
        self.rpc_data: dict[str, object] = {
            "create_assessment_exam_draft": {
                "exam_id": EXAM_ID,
                "exam_version_id": EXAM_VERSION_ID,
                "blueprint_version_id": (
                    BLUEPRINT_VERSION_ID
                ),
                "reused": False,
            },
            "assemble_assessment_exam_from_blueprint": {
                "exam_version_id": EXAM_VERSION_ID,
                "blueprint_version_id": (
                    BLUEPRINT_VERSION_ID
                ),
                "question_count": 26,
                "assembly_status": "ASSEMBLED",
            },
            "assessment_exam_validation_report": {
                "is_valid": True,
                "violations": [],
                "metrics": {
                    "question_count": 26,
                    "expected_question_count": 26,
                    "assigned_score": 10,
                    "expected_score": 10,
                },
            },
            "confirm_assessment_exam_validation_warnings": None,
            "submit_assessment_exam_for_review": None,
        }
        self.table_calls: list[
            tuple[str, tuple[tuple[object, ...], ...]]
        ] = []
        self.rpc_calls: list[
            tuple[str, dict[str, object]]
        ] = []

    def table(self, table_name: str) -> FakeQuery:
        return FakeQuery(
            client=self,
            table_name=table_name,
        )

    def rpc(
        self,
        rpc_name: str,
        parameters: dict[str, object],
    ) -> FakeRpcCall:
        return FakeRpcCall(
            client=self,
            rpc_name=rpc_name,
            parameters=parameters,
        )


def _gateway(
    client: FakeClient | None = None,
) -> tuple[
    SupabaseAssessmentExamGenerationGateway,
    FakeClient,
]:
    resolved_client = client or FakeClient()

    return (
        SupabaseAssessmentExamGenerationGateway(
            client=resolved_client,
            user_id=USER_ID,
        ),
        resolved_client,
    )


def _request(
    *,
    owner_user_id: str = USER_ID,
) -> AssessmentExamGenerationRequest:
    return AssessmentExamGenerationRequest(
        blueprint_code="TOAN6_GHK1",
        owner_user_id=owner_user_id,
        exam_code="KT_GHK1_TOAN6_001",
        title="Kiem tra giua hoc ky I mon Toan 6",
        submit_for_review=True,
        idempotency_key="teacher-1-toan6-ghk1-001",
    )


def _canonical_payload(
    *,
    status: object = "PASS",
    errors: object = None,
    warnings: object = None,
    metrics: object = None,
    include_evidence: bool = True,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": status,
        "errors": [] if errors is None else errors,
        "warnings": [] if warnings is None else warnings,
        "metrics": {} if metrics is None else metrics,
    }
    if include_evidence:
        payload.update(
            {
                "validation_evidence_id": EVIDENCE_ID,
                "validation_input_digest": VALIDATION_INPUT_DIGEST,
                "evidence_digest": EVIDENCE_DIGEST,
                "validation_schema_version": 1,
                "validated_at": "2026-09-13T10:00:00+07:00",
            }
        )
    return payload


def _validate_payload(payload: dict[str, object]) -> object:
    client = FakeClient()
    client.rpc_data["assessment_exam_validation_report"] = payload
    gateway, _ = _gateway(client)
    return gateway.validate_exam_version(
        exam_version_id=EXAM_VERSION_ID
    )


def test_blueprint_lookup_maps_governed_result() -> None:
    gateway, client = _gateway()

    result = gateway.find_active_approved_blueprint(
        blueprint_code="TOAN6_GHK1"
    )

    assert result is not None
    assert (
        result.blueprint_version_id
        == BLUEPRINT_VERSION_ID
    )
    assert result.blueprint_code == "TOAN6_GHK1"
    assert result.lifecycle_status == "ACTIVE"
    assert result.review_status == "APPROVED"

    table_name, operations = client.table_calls[0]

    assert table_name == "assessment_blueprint_versions"
    assert (
        "eq",
        "assessment_blueprints.owner_user_id",
        USER_ID,
    ) in operations
    assert ("eq", "review_status", "APPROVED") in operations
    assert ("not_is", "locked_at", "null") in operations


def test_blueprint_lookup_returns_none_when_empty() -> None:
    client = FakeClient()
    client.blueprint_data = []
    gateway, _ = _gateway(client)

    assert (
        gateway.find_active_approved_blueprint(
            blueprint_code="TOAN6_GHK1"
        )
        is None
    )


def test_create_draft_calls_v52_rpc() -> None:
    gateway, client = _gateway()

    result = gateway.create_exam_draft(
        request=_request(),
        blueprint_version_id=BLUEPRINT_VERSION_ID,
    )

    assert result.exam_id == EXAM_ID
    assert result.exam_version_id == EXAM_VERSION_ID

    rpc_name, parameters = client.rpc_calls[0]

    assert rpc_name == "create_assessment_exam_draft"
    assert parameters == {
        "target_blueprint_version_id": (
            BLUEPRINT_VERSION_ID
        ),
        "target_exam_code": "KT_GHK1_TOAN6_001",
        "target_exam_title": (
            "Kiem tra giua hoc ky I mon Toan 6"
        ),
        "target_idempotency_key": (
            "teacher-1-toan6-ghk1-001"
        ),
    }


def test_create_draft_accepts_equivalent_uuid_case() -> None:
    canonical_user_id = (
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    )
    client = FakeClient()
    gateway = SupabaseAssessmentExamGenerationGateway(
        client=client,
        user_id=canonical_user_id,
    )

    request = AssessmentExamGenerationRequest(
        blueprint_code="TOAN6_GHK1",
        owner_user_id=canonical_user_id.upper(),
        exam_code="KT_GHK1_TOAN6_001",
        title="Kiem tra giua hoc ky I mon Toan 6",
        submit_for_review=True,
        idempotency_key="teacher-1-toan6-ghk1-001",
    )

    result = gateway.create_exam_draft(
        request=request,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
    )

    assert result.exam_id == EXAM_ID
    assert client.rpc_calls[0][0] == (
        "create_assessment_exam_draft"
    )


def test_create_draft_rejects_owner_mismatch() -> None:
    gateway, client = _gateway()

    with pytest.raises(PermissionError):
        gateway.create_exam_draft(
            request=_request(
                owner_user_id=(
                    "99999999-9999-4999-8999-999999999999"
                )
            ),
            blueprint_version_id=BLUEPRINT_VERSION_ID,
        )

    assert client.rpc_calls == []


def test_assembly_calls_v52_rpc_with_stable_seed() -> None:
    gateway, client = _gateway()

    gateway.assemble_exam_version(
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
    )

    rpc_name, parameters = client.rpc_calls[0]

    assert (
        rpc_name
        == "assemble_assessment_exam_from_blueprint"
    )
    assert parameters["target_exam_version_id"] == (
        EXAM_VERSION_ID
    )

    seed = parameters["target_selection_seed"]

    assert isinstance(seed, str)
    assert len(seed) == 64

    gateway.assemble_exam_version(
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
    )

    assert (
        client.rpc_calls[1][1]["target_selection_seed"]
        == seed
    )


@pytest.mark.parametrize(
    "status",
    (
        "ASSEMBLED",
        "PENDING_REVIEW",
    ),
)
def test_assembly_retry_is_noop_after_completion(
    status: str,
) -> None:
    client = FakeClient()
    client.exam_status = status
    gateway, _ = _gateway(client)

    gateway.assemble_exam_version(
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
    )

    assert client.rpc_calls == []


def test_validation_report_maps_rpc_payload() -> None:
    gateway, client = _gateway()

    report = gateway.validate_exam_version(
        exam_version_id=EXAM_VERSION_ID
    )

    assert report.is_valid
    assert report.violations == ()
    assert report.metrics["expected_score"] == 10

    assert client.rpc_calls[0][0] == (
        "assessment_exam_validation_report"
    )


def test_legacy_fail_validation_report_is_unchanged() -> None:
    report = _validate_payload(
        {
            "is_valid": False,
            "violations": ["First failure.", "Second failure."],
            "metrics": {"failure_count": 2},
        }
    )

    assert report.is_valid is False
    assert report.violations == (
        "First failure.",
        "Second failure.",
    )
    assert report.metrics == {"failure_count": 2}


@pytest.mark.parametrize(
    ("status", "errors", "warnings"),
    (
        ("PASS", [], []),
        ("FAIL", ["Canonical failure."], []),
        (
            "WARNING",
            [],
            ["First warning.", "Second warning."],
        ),
    ),
)
def test_canonical_validation_preserves_status_messages_and_evidence(
    status: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    result = _validate_payload(
        _canonical_payload(
            status=status,
            errors=errors,
            warnings=warnings,
            metrics={"question_count": 26},
        )
    )

    assert isinstance(result, ValidationResult)
    assert result.status is ValidationStatus(status)
    assert result.errors == tuple(errors)
    assert result.warnings == tuple(warnings)
    assert result.metrics == {"question_count": 26}
    assert result.evidence_identity is not None
    assert result.evidence_identity.validation_evidence_id == EVIDENCE_ID
    assert result.evidence_identity.validation_input_digest == (
        VALIDATION_INPUT_DIGEST
    )
    assert result.evidence_identity.evidence_digest == EVIDENCE_DIGEST
    assert result.evidence_identity.validation_schema_version == 1


def test_canonical_validation_allows_absent_evidence_identity() -> None:
    result = _validate_payload(
        _canonical_payload(include_evidence=False)
    )

    assert isinstance(result, ValidationResult)
    assert result.evidence_identity is None


@pytest.mark.parametrize(
    "missing_field",
    (
        "validation_evidence_id",
        "validation_input_digest",
        "evidence_digest",
        "validation_schema_version",
        "validated_at",
    ),
)
def test_partial_canonical_evidence_identity_is_rejected(
    missing_field: str,
) -> None:
    payload = _canonical_payload()
    del payload[missing_field]

    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("validation_evidence_id", "not-a-uuid"),
        ("validation_input_digest", "A" * 64),
        ("evidence_digest", "b" * 63),
        ("validation_schema_version", 0),
        ("validation_schema_version", True),
    ),
)
def test_invalid_canonical_evidence_value_is_gateway_error(
    field_name: str,
    invalid_value: object,
) -> None:
    payload = _canonical_payload()
    payload[field_name] = invalid_value

    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(payload)


@pytest.mark.parametrize("status", ("UNKNOWN", "pass", " PASS", 1))
def test_invalid_canonical_status_is_gateway_error(status: object) -> None:
    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(_canonical_payload(status=status))


@pytest.mark.parametrize(
    ("status", "errors", "warnings"),
    (
        ("PASS", ["Unexpected error."], []),
        ("PASS", [], ["Unexpected warning."]),
        ("WARNING", ["Unexpected error."], ["Warning."]),
        ("WARNING", [], []),
        ("FAIL", [], []),
    ),
)
def test_invalid_canonical_status_message_state_is_gateway_error(
    status: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(
            _canonical_payload(
                status=status,
                errors=errors,
                warnings=warnings,
            )
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("errors", "not-a-list"),
        ("warnings", ("not", "a", "list")),
        ("metrics", []),
    ),
)
def test_invalid_canonical_collection_type_is_gateway_error(
    field_name: str,
    invalid_value: object,
) -> None:
    payload = _canonical_payload()
    payload[field_name] = invalid_value

    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(payload)


def test_canonical_aware_offset_timestamp_is_preserved() -> None:
    result = _validate_payload(_canonical_payload())

    assert isinstance(result, ValidationResult)
    assert result.evidence_identity is not None
    assert result.evidence_identity.validated_at.utcoffset() == timedelta(
        hours=7
    )


def test_canonical_z_timestamp_is_aware() -> None:
    payload = _canonical_payload()
    payload["validated_at"] = "2026-09-13T03:00:00Z"

    result = _validate_payload(payload)

    assert isinstance(result, ValidationResult)
    assert result.evidence_identity is not None
    assert result.evidence_identity.validated_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "timestamp",
    (
        "2026-09-13T10:00:00",
        "not-a-timestamp",
        "",
        None,
    ),
)
def test_invalid_canonical_timestamp_is_gateway_error(
    timestamp: object,
) -> None:
    payload = _canonical_payload()
    payload["validated_at"] = timestamp

    with pytest.raises(AssessmentGatewayResponseError):
        _validate_payload(payload)


def test_canonical_marker_wins_over_legacy_aliases() -> None:
    payload = _canonical_payload(
        status="FAIL",
        errors=["Canonical failure."],
    )
    payload.update({"is_valid": True, "violations": []})

    result = _validate_payload(payload)

    assert isinstance(result, ValidationResult)
    assert result.status is ValidationStatus.FAIL


def test_zero_canonical_markers_uses_legacy_parser() -> None:
    result = _validate_payload(
        {
            "is_valid": True,
            "violations": [],
            "metrics": {},
            "unknown_field": "ignored",
        }
    )

    assert result.is_valid is True


def test_confirmation_rpc_uses_exact_payload_and_warning_order() -> None:
    gateway, client = _gateway()

    gateway.confirm_validation_warnings(
        exam_version_id=EXAM_VERSION_ID,
        validation_evidence_digest=EVIDENCE_DIGEST,
        confirmed_warnings=("First warning.", "Second warning."),
    )

    assert client.rpc_calls == [
        (
            "confirm_assessment_exam_validation_warnings",
            {
                "target_exam_version_id": EXAM_VERSION_ID,
                "target_validation_evidence_digest": EVIDENCE_DIGEST,
                "target_confirmed_warnings": [
                    "First warning.",
                    "Second warning.",
                ],
            },
        )
    ]


def test_invalid_validation_contract_is_rejected() -> None:
    client = FakeClient()
    client.rpc_data[
        "assessment_exam_validation_report"
    ] = {
        "is_valid": "yes",
        "violations": [],
        "metrics": {},
    }
    gateway, _ = _gateway(client)

    with pytest.raises(
        AssessmentGatewayResponseError,
        match="boolean",
    ):
        gateway.validate_exam_version(
            exam_version_id=EXAM_VERSION_ID
        )


def test_submit_calls_governed_v47_rpc() -> None:
    client = FakeClient()
    client.exam_status = "ASSEMBLED"
    gateway, _ = _gateway(client)

    gateway.submit_exam_for_review(
        exam_version_id=EXAM_VERSION_ID
    )

    assert client.rpc_calls == [
        (
            "submit_assessment_exam_for_review",
            {
                "target_exam_version_id": (
                    EXAM_VERSION_ID
                )
            },
        )
    ]


def test_submit_retry_is_noop_when_pending() -> None:
    client = FakeClient()
    client.exam_status = "PENDING_REVIEW"
    gateway, _ = _gateway(client)

    gateway.submit_exam_for_review(
        exam_version_id=EXAM_VERSION_ID
    )

    assert client.rpc_calls == []


@pytest.mark.parametrize(
    "response_data",
    (
        None,
        [],
        [{"exam_id": EXAM_ID}, {"exam_id": EXAM_ID}],
    ),
)
def test_invalid_draft_response_shape_is_rejected(
    response_data: object,
) -> None:
    client = FakeClient()
    client.rpc_data[
        "create_assessment_exam_draft"
    ] = response_data
    gateway, _ = _gateway(client)

    with pytest.raises(AssessmentGatewayResponseError):
        gateway.create_exam_draft(
            request=_request(),
            blueprint_version_id=BLUEPRINT_VERSION_ID,
        )


def test_adapter_has_no_ui_or_secret_dependency() -> None:
    text = (
        __import__(
            "inspect"
        )
        .getsource(
            SupabaseAssessmentExamGenerationGateway
        )
        .lower()
    )

    assert "streamlit" not in text
    assert "os.environ" not in text
    assert "service_role" not in text
    assert "publish_assessment_exam" not in text
    assert "generate_assessment_exam_variant" not in text
