from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID

from assessment_generation_v2.services.exam_generation_service import (
    AssessmentBlueprintSelection,
    AssessmentDraftIdentity,
    AssessmentExamGenerationRequest,
    AssessmentValidationReport,
)


class AssessmentGatewayResponseError(RuntimeError):
    """Raised when the persistence gateway returns an invalid contract."""


def _required_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise AssessmentGatewayResponseError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise AssessmentGatewayResponseError(
            f"{field_name} must not be blank"
        )

    return normalized


def _required_uuid(
    value: object,
    field_name: str,
) -> str:
    normalized = _required_text(
        value,
        field_name,
    )

    try:
        UUID(normalized)
    except ValueError as error:
        raise AssessmentGatewayResponseError(
            f"{field_name} must be a valid UUID"
        ) from error

    return normalized


def _response_data(response: object) -> object:
    if isinstance(response, dict):
        if "data" not in response:
            raise AssessmentGatewayResponseError(
                "gateway response does not contain data"
            )
        return response["data"]

    if not hasattr(response, "data"):
        raise AssessmentGatewayResponseError(
            "gateway response does not expose data"
        )

    return getattr(response, "data")


def _single_mapping(
    response: object,
    *,
    operation_name: str,
    allow_empty: bool = False,
) -> dict[str, Any] | None:
    data = _response_data(response)

    if data is None:
        if allow_empty:
            return None
        raise AssessmentGatewayResponseError(
            f"{operation_name} returned no data"
        )

    if isinstance(data, dict):
        return dict(data)

    if isinstance(data, list):
        if not data:
            if allow_empty:
                return None
            raise AssessmentGatewayResponseError(
                f"{operation_name} returned no rows"
            )

        if len(data) != 1:
            raise AssessmentGatewayResponseError(
                f"{operation_name} returned multiple rows"
            )

        row = data[0]

        if not isinstance(row, dict):
            raise AssessmentGatewayResponseError(
                f"{operation_name} returned an invalid row"
            )

        return dict(row)

    raise AssessmentGatewayResponseError(
        f"{operation_name} returned an invalid data shape"
    )


class SupabaseAssessmentExamGenerationGateway:
    """
    Supabase implementation of the draft-generation gateway.

    The adapter owns persistence translation only. It does not
    approve, publish, snapshot, generate variants, or export exams.
    """

    BLUEPRINT_VERSION_TABLE = (
        "assessment_blueprint_versions"
    )
    EXAM_VERSION_TABLE = "assessment_exam_versions"

    CREATE_DRAFT_RPC = "create_assessment_exam_draft"
    ASSEMBLE_RPC = (
        "assemble_assessment_exam_from_blueprint"
    )
    VALIDATION_RPC = (
        "assessment_exam_validation_report"
    )
    SUBMIT_RPC = "submit_assessment_exam_for_review"

    def __init__(
        self,
        *,
        client: Any,
        user_id: str,
    ) -> None:
        if client is None:
            raise ValueError("client must not be None")

        try:
            normalized_user_id = str(
                UUID(
                    _required_text(
                        user_id,
                        "user_id",
                    )
                )
            )
        except (
            ValueError,
            AssessmentGatewayResponseError,
        ) as error:
            raise ValueError(
                "user_id must be a valid UUID"
            ) from error

        self._client = client
        self._user_id = normalized_user_id

    def find_active_approved_blueprint(
        self,
        *,
        blueprint_code: str,
    ) -> AssessmentBlueprintSelection | None:
        normalized_code = _required_text(
            blueprint_code,
            "blueprint_code",
        )

        response = (
            self._client
            .table(self.BLUEPRINT_VERSION_TABLE)
            .select(
                "blueprint_version_id,"
                "version_number,"
                "review_status,"
                "locked_at,"
                "assessment_blueprints!inner("
                "blueprint_code,"
                "owner_user_id,"
                "lifecycle_status"
                ")"
            )
            .eq(
                "assessment_blueprints.blueprint_code",
                normalized_code,
            )
            .eq(
                "assessment_blueprints.owner_user_id",
                self._user_id,
            )
            .eq(
                "assessment_blueprints.lifecycle_status",
                "ACTIVE",
            )
            .eq(
                "review_status",
                "APPROVED",
            )
            .not_
            .is_(
                "locked_at",
                "null",
            )
            .order(
                "version_number",
                desc=True,
            )
            .limit(1)
            .execute()
        )

        row = _single_mapping(
            response,
            operation_name="blueprint lookup",
            allow_empty=True,
        )

        if row is None:
            return None

        blueprint_relation = row.get(
            "assessment_blueprints"
        )

        if isinstance(blueprint_relation, list):
            if len(blueprint_relation) != 1:
                raise AssessmentGatewayResponseError(
                    "blueprint relation must contain one row"
                )
            blueprint_relation = blueprint_relation[0]

        if not isinstance(blueprint_relation, dict):
            raise AssessmentGatewayResponseError(
                "blueprint relation is missing"
            )

        return AssessmentBlueprintSelection(
            blueprint_version_id=_required_uuid(
                row.get("blueprint_version_id"),
                "blueprint_version_id",
            ),
            blueprint_code=_required_text(
                blueprint_relation.get("blueprint_code"),
                "blueprint_code",
            ),
            lifecycle_status=_required_text(
                blueprint_relation.get(
                    "lifecycle_status"
                ),
                "lifecycle_status",
            ),
            review_status=_required_text(
                row.get("review_status"),
                "review_status",
            ),
        )

    def create_exam_draft(
        self,
        *,
        request: AssessmentExamGenerationRequest,
        blueprint_version_id: str,
    ) -> AssessmentDraftIdentity:
        if not isinstance(
            request,
            AssessmentExamGenerationRequest,
        ):
            raise TypeError(
                "request must be "
                "AssessmentExamGenerationRequest"
            )

        request_owner_id = str(
            UUID(request.owner_user_id)
        )

        if request_owner_id != self._user_id:
            raise PermissionError(
                "request owner does not match gateway user"
            )

        normalized_blueprint_version_id = (
            _required_uuid(
                blueprint_version_id,
                "blueprint_version_id",
            )
        )

        response = (
            self._client
            .rpc(
                self.CREATE_DRAFT_RPC,
                {
                    "target_blueprint_version_id": (
                        normalized_blueprint_version_id
                    ),
                    "target_exam_code": request.exam_code,
                    "target_exam_title": request.title,
                    "target_idempotency_key": (
                        request.idempotency_key
                    ),
                },
            )
            .execute()
        )

        row = _single_mapping(
            response,
            operation_name="create exam draft",
        )

        assert row is not None

        returned_blueprint_version_id = (
            _required_uuid(
                row.get("blueprint_version_id"),
                "blueprint_version_id",
            )
        )

        if (
            returned_blueprint_version_id
            != normalized_blueprint_version_id
        ):
            raise AssessmentGatewayResponseError(
                "draft response blueprint does not match request"
            )

        return AssessmentDraftIdentity(
            exam_id=_required_uuid(
                row.get("exam_id"),
                "exam_id",
            ),
            exam_version_id=_required_uuid(
                row.get("exam_version_id"),
                "exam_version_id",
            ),
        )

    def assemble_exam_version(
        self,
        *,
        exam_version_id: str,
        blueprint_version_id: str,
    ) -> None:
        normalized_exam_version_id = _required_uuid(
            exam_version_id,
            "exam_version_id",
        )
        normalized_blueprint_version_id = (
            _required_uuid(
                blueprint_version_id,
                "blueprint_version_id",
            )
        )

        current_status = self._exam_assembly_status(
            normalized_exam_version_id
        )

        if current_status in (
            "ASSEMBLED",
            "PENDING_REVIEW",
        ):
            return

        selection_seed = sha256(
            (
                normalized_exam_version_id
                + ":"
                + normalized_blueprint_version_id
            ).encode("utf-8")
        ).hexdigest()

        response = (
            self._client
            .rpc(
                self.ASSEMBLE_RPC,
                {
                    "target_exam_version_id": (
                        normalized_exam_version_id
                    ),
                    "target_selection_seed": (
                        selection_seed
                    ),
                },
            )
            .execute()
        )

        row = _single_mapping(
            response,
            operation_name="assemble exam",
        )

        assert row is not None

        returned_exam_version_id = _required_uuid(
            row.get("exam_version_id"),
            "exam_version_id",
        )
        returned_blueprint_version_id = (
            _required_uuid(
                row.get("blueprint_version_id"),
                "blueprint_version_id",
            )
        )

        if (
            returned_exam_version_id
            != normalized_exam_version_id
        ):
            raise AssessmentGatewayResponseError(
                "assembly response exam version mismatch"
            )

        if (
            returned_blueprint_version_id
            != normalized_blueprint_version_id
        ):
            raise AssessmentGatewayResponseError(
                "assembly response blueprint mismatch"
            )

        if row.get("assembly_status") != "ASSEMBLED":
            raise AssessmentGatewayResponseError(
                "assembly response has invalid status"
            )

    def validate_exam_version(
        self,
        *,
        exam_version_id: str,
    ) -> AssessmentValidationReport:
        normalized_exam_version_id = _required_uuid(
            exam_version_id,
            "exam_version_id",
        )

        response = (
            self._client
            .rpc(
                self.VALIDATION_RPC,
                {
                    "target_exam_version_id": (
                        normalized_exam_version_id
                    )
                },
            )
            .execute()
        )

        row = _single_mapping(
            response,
            operation_name="validate exam",
        )

        assert row is not None

        is_valid = row.get("is_valid")

        if not isinstance(is_valid, bool):
            raise AssessmentGatewayResponseError(
                "validation is_valid must be boolean"
            )

        raw_violations = row.get("violations")

        if not isinstance(raw_violations, list):
            raise AssessmentGatewayResponseError(
                "validation violations must be a list"
            )

        violations: list[str] = []

        for violation in raw_violations:
            violations.append(
                _required_text(
                    violation,
                    "validation violation",
                )
            )

        raw_metrics = row.get("metrics")

        if not isinstance(raw_metrics, dict):
            raise AssessmentGatewayResponseError(
                "validation metrics must be an object"
            )

        return AssessmentValidationReport(
            is_valid=is_valid,
            violations=tuple(violations),
            metrics=dict(raw_metrics),
        )

    def submit_exam_for_review(
        self,
        *,
        exam_version_id: str,
    ) -> None:
        normalized_exam_version_id = _required_uuid(
            exam_version_id,
            "exam_version_id",
        )

        current_status = self._exam_assembly_status(
            normalized_exam_version_id
        )

        if current_status == "PENDING_REVIEW":
            return

        (
            self._client
            .rpc(
                self.SUBMIT_RPC,
                {
                    "target_exam_version_id": (
                        normalized_exam_version_id
                    )
                },
            )
            .execute()
        )

    def _exam_assembly_status(
        self,
        exam_version_id: str,
    ) -> str:
        response = (
            self._client
            .table(self.EXAM_VERSION_TABLE)
            .select("assembly_status")
            .eq(
                "exam_version_id",
                exam_version_id,
            )
            .limit(1)
            .execute()
        )

        row = _single_mapping(
            response,
            operation_name="exam status lookup",
        )

        assert row is not None

        return _required_text(
            row.get("assembly_status"),
            "assembly_status",
        )
