"""Supabase adapter for governed post-publication document export."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping
from uuid import UUID

from assessment_generation_v2.renderers import (
    AssessmentTemplateDefinition,
)
from assessment_generation_v2.services import (
    ApprovedAssessmentTemplate,
    PublishedAssessmentRenderSource,
)


class AssessmentDocumentExportGatewayError(RuntimeError):
    """Raised when Supabase returns an invalid export contract."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssessmentDocumentExportGatewayError(
            f"{field_name} must be non-blank text"
        )
    return value.strip()


def _uuid(value: object, field_name: str) -> str:
    try:
        return str(UUID(_text(value, field_name)))
    except ValueError as error:
        raise AssessmentDocumentExportGatewayError(
            f"{field_name} must be a valid UUID"
        ) from error


def _mapping(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AssessmentDocumentExportGatewayError(
            f"{field_name} must be an object"
        )
    return dict(value)


def _relation(value: object, field_name: str) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentDocumentExportGatewayError(
                f"{field_name} must contain one row"
            )
        value = value[0]
    return _mapping(value, field_name)


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        if "data" not in response:
            raise AssessmentDocumentExportGatewayError(
                "Supabase response does not contain data"
            )
        return response["data"]
    if not hasattr(response, "data"):
        raise AssessmentDocumentExportGatewayError(
            "Supabase response does not expose data"
        )
    return getattr(response, "data")


def _rows(response: object, operation: str) -> list[dict[str, Any]]:
    value = _data(response)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if not isinstance(value, list):
        raise AssessmentDocumentExportGatewayError(
            f"{operation} returned an invalid data shape"
        )
    if any(not isinstance(item, Mapping) for item in value):
        raise AssessmentDocumentExportGatewayError(
            f"{operation} returned an invalid row"
        )
    return [dict(item) for item in value]


def _single(
    response: object,
    operation: str,
    *,
    allow_empty: bool = False,
) -> dict[str, Any] | None:
    values = _rows(response, operation)
    if not values:
        if allow_empty:
            return None
        raise AssessmentDocumentExportGatewayError(
            f"{operation} returned no rows"
        )
    if len(values) != 1:
        raise AssessmentDocumentExportGatewayError(
            f"{operation} returned multiple rows"
        )
    return values[0]


def _boolean(response: object, operation: str) -> bool:
    value = _data(response)
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, bool):
        raise AssessmentDocumentExportGatewayError(
            f"{operation} did not return boolean"
        )
    return value


class SupabaseAssessmentDocumentExportGateway:
    """Read-only adapter for snapshots, payloads, templates and assets."""

    VARIANT_TABLE = "assessment_exam_variants"
    EXPORT_PACKAGE_TABLE = "assessment_exam_export_packages"
    TEMPLATE_VERSION_TABLE = "assessment_document_template_versions"
    SNAPSHOT_HASH_RPC = "assessment_exam_snapshot_hash_matches"
    PACKAGE_HASH_RPC = "assessment_exam_export_package_hash_matches"
    REQUIRED_PACKAGE_TYPES = (
        "STUDENT_EXAM",
        "ANSWER_KEY",
        "SCORING_GUIDE",
    )

    def __init__(
        self,
        *,
        client: Any,
        user_id: str,
        template_asset_bucket: str = (
            "assessment-document-templates"
        ),
        maximum_asset_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        if client is None:
            raise ValueError("client must not be None")
        try:
            normalized_user_id = str(UUID(_text(user_id, "user_id")))
        except (ValueError, AssessmentDocumentExportGatewayError) as error:
            raise ValueError("user_id must be a valid UUID") from error
        bucket = _text(template_asset_bucket, "template_asset_bucket")
        if "/" in bucket or "\\" in bucket:
            raise ValueError("template_asset_bucket must be a bucket name")
        if (
            isinstance(maximum_asset_bytes, bool)
            or not isinstance(maximum_asset_bytes, int)
            or maximum_asset_bytes < 1024
        ):
            raise ValueError("maximum_asset_bytes is invalid")
        self._client = client
        self._user_id = normalized_user_id
        self._template_asset_bucket = bucket
        self._maximum_asset_bytes = maximum_asset_bytes

    def load_published_render_source(
        self,
        *,
        exam_version_id: str,
        variant_id: str,
    ) -> PublishedAssessmentRenderSource | None:
        normalized_exam_version_id = _uuid(
            exam_version_id, "exam_version_id"
        )
        normalized_variant_id = _uuid(variant_id, "variant_id")
        response = (
            self._client.table(self.VARIANT_TABLE)
            .select(
                "variant_id,variant_status,"
                "assessment_exam_snapshots!inner("
                "snapshot_id,exam_version_id,snapshot_document,"
                "snapshot_hash,"
                "assessment_exam_versions!inner("
                "assessment_exams!inner(owner_user_id)))"
            )
            .eq("variant_id", normalized_variant_id)
            .eq(
                "assessment_exam_snapshots.exam_version_id",
                normalized_exam_version_id,
            )
            .eq("variant_status", "LOCKED")
            .limit(1)
            .execute()
        )
        row = _single(
            response,
            "published variant lookup",
            allow_empty=True,
        )
        if row is None:
            return None
        snapshot = _relation(
            row.get("assessment_exam_snapshots"),
            "assessment_exam_snapshots",
        )
        exam_version = _relation(
            snapshot.get("assessment_exam_versions"),
            "assessment_exam_versions",
        )
        exam = _relation(
            exam_version.get("assessment_exams"),
            "assessment_exams",
        )
        owner_user_id = _uuid(
            exam.get("owner_user_id"), "owner_user_id"
        )
        if owner_user_id != self._user_id:
            raise PermissionError(
                "published assessment is not owned by gateway user"
            )
        snapshot_id = _uuid(snapshot.get("snapshot_id"), "snapshot_id")
        snapshot_hash = _text(
            snapshot.get("snapshot_hash"), "snapshot_hash"
        )
        hash_verified = _boolean(
            self._client.rpc(
                self.SNAPSHOT_HASH_RPC,
                {"target_snapshot_id": snapshot_id},
            ).execute(),
            "snapshot hash verification",
        )
        packages = self._load_packages(normalized_variant_id)
        return PublishedAssessmentRenderSource(
            exam_version_id=_uuid(
                snapshot.get("exam_version_id"),
                "snapshot.exam_version_id",
            ),
            variant_id=_uuid(row.get("variant_id"), "variant_id"),
            owner_user_id=owner_user_id,
            snapshot_hash=snapshot_hash,
            hash_verified=hash_verified,
            snapshot_document=_mapping(
                snapshot.get("snapshot_document"),
                "snapshot_document",
            ),
            student_exam_payload=packages["STUDENT_EXAM"],
            answer_key_payload=packages["ANSWER_KEY"],
            scoring_guide_payload=packages["SCORING_GUIDE"],
        )

    def _load_packages(
        self, variant_id: str
    ) -> dict[str, dict[str, Any]]:
        response = (
            self._client.table(self.EXPORT_PACKAGE_TABLE)
            .select(
                "export_package_id,package_type,package_payload,"
                "package_hash,package_status,created_at"
            )
            .eq("variant_id", variant_id)
            .eq("package_status", "LOCKED")
            .order("created_at", desc=True)
            .execute()
        )
        selected: dict[str, dict[str, Any]] = {}
        for row in _rows(response, "export package lookup"):
            package_type = _text(
                row.get("package_type"), "package_type"
            ).upper()
            if package_type not in self.REQUIRED_PACKAGE_TYPES:
                continue
            if package_type in selected:
                continue
            package_id = _uuid(
                row.get("export_package_id"), "export_package_id"
            )
            if not _boolean(
                self._client.rpc(
                    self.PACKAGE_HASH_RPC,
                    {"target_export_package_id": package_id},
                ).execute(),
                "export package hash verification",
            ):
                raise AssessmentDocumentExportGatewayError(
                    f"export package hash does not match: {package_type}"
                )
            selected[package_type] = _mapping(
                row.get("package_payload"), "package_payload"
            )
        missing = tuple(
            value
            for value in self.REQUIRED_PACKAGE_TYPES
            if value not in selected
        )
        if missing:
            raise AssessmentDocumentExportGatewayError(
                "required export packages are unavailable: "
                + ", ".join(missing)
            )
        return selected

    def find_active_template(
        self,
        *,
        template_set_code: str,
        document_type: str,
    ) -> ApprovedAssessmentTemplate | None:
        code = _text(template_set_code, "template_set_code").upper()
        document = _text(document_type, "document_type").upper()
        response = (
            self._client.table(self.TEMPLATE_VERSION_TABLE)
            .select(
                "template_version_id,version_number,review_status,"
                "global_layout_schema,global_style_schema,"
                "assessment_document_template_sets!inner("
                "template_code,lifecycle_status,current_version_number),"
                "assessment_document_template_definitions!inner("
                "document_type_code,renderer_code,supported_formats,"
                "layout_schema,style_schema,binding_schema,section_schema,"
                "template_asset_path,template_asset_hash,sort_order)"
            )
            .eq(
                "assessment_document_template_sets.template_code",
                code,
            )
            .eq(
                "assessment_document_template_sets.lifecycle_status",
                "ACTIVE",
            )
            .eq("review_status", "APPROVED")
            .eq(
                "assessment_document_template_definitions.document_type_code",
                document,
            )
            .order("version_number", desc=True)
            .execute()
        )
        for row in _rows(response, "active template lookup"):
            template_set = _relation(
                row.get("assessment_document_template_sets"),
                "assessment_document_template_sets",
            )
            version_number = row.get("version_number")
            if (
                not isinstance(version_number, int)
                or version_number
                != template_set.get("current_version_number")
            ):
                continue
            definitions = row.get(
                "assessment_document_template_definitions"
            )
            if isinstance(definitions, Mapping):
                definitions = [definitions]
            if not isinstance(definitions, list):
                raise AssessmentDocumentExportGatewayError(
                    "template definitions relation is invalid"
                )
            matching = [
                _mapping(value, "template definition")
                for value in definitions
                if isinstance(value, Mapping)
                and str(value.get("document_type_code", "")).upper()
                == document
            ]
            if len(matching) != 1:
                raise AssessmentDocumentExportGatewayError(
                    "active template must have one document definition"
                )
            definition = matching[0]
            formats = definition.get("supported_formats")
            if not isinstance(formats, list) or "DOCX" not in formats:
                raise AssessmentDocumentExportGatewayError(
                    "active template does not support DOCX"
                )
            layout = _mapping(
                row.get("global_layout_schema"),
                "global_layout_schema",
            )
            layout.update(
                _mapping(definition.get("layout_schema"), "layout_schema")
            )
            styles = _mapping(
                row.get("global_style_schema"),
                "global_style_schema",
            )
            styles.update(
                _mapping(definition.get("style_schema"), "style_schema")
            )
            return ApprovedAssessmentTemplate(
                template_version_id=_uuid(
                    row.get("template_version_id"),
                    "template_version_id",
                ),
                template_set_code=_text(
                    template_set.get("template_code"),
                    "template_code",
                ),
                review_status=_text(
                    row.get("review_status"), "review_status"
                ),
                lifecycle_status=_text(
                    template_set.get("lifecycle_status"),
                    "lifecycle_status",
                ),
                definition=AssessmentTemplateDefinition(
                    document_type_code=document,
                    renderer_code=_text(
                        definition.get("renderer_code"),
                        "renderer_code",
                    ),
                    layout_schema=layout,
                    style_schema=styles,
                    binding_schema=_mapping(
                        definition.get("binding_schema"),
                        "binding_schema",
                    ),
                    section_schema=tuple(
                        definition.get("section_schema", ())
                    ),
                    template_asset_path=definition.get(
                        "template_asset_path"
                    ),
                    template_asset_hash=definition.get(
                        "template_asset_hash"
                    ),
                ),
            )
        return None

    def load_template_asset(self, *, asset_path: str) -> bytes:
        normalized = _text(asset_path, "asset_path")
        path = PurePosixPath(normalized)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in normalized
        ):
            raise AssessmentDocumentExportGatewayError(
                "template asset path is unsafe"
            )
        response = (
            self._client.storage
            .from_(self._template_asset_bucket)
            .download(normalized)
        )
        content = _data(response) if not isinstance(response, bytes) else response
        if not isinstance(content, bytes):
            raise AssessmentDocumentExportGatewayError(
                "template asset download did not return bytes"
            )
        if not content or len(content) > self._maximum_asset_bytes:
            raise AssessmentDocumentExportGatewayError(
                "template asset size is invalid"
            )
        return content
