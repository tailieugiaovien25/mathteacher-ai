"""Render a governed assessment document bundle after publication."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import PurePath, PurePosixPath
from typing import Mapping, Protocol
from uuid import UUID
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocument,
    CanonicalAssessmentDocumentBuilder,
)
from assessment_generation_v2.renderers import (
    AssessmentDocxRenderPlanRenderer,
    AssessmentTemplateDefinition,
    DynamicAssessmentDocumentRenderer,
)


class AssessmentDocumentExportError(RuntimeError):
    """Raised when a governed document bundle cannot be exported."""


class AssessmentDocumentExportValidationError(ValueError):
    """Raised when an export request or gateway result is invalid."""


DOCUMENT_TYPES = (
    "MATRIX",
    "SPECIFICATION",
    "STUDENT_EXAM",
    "ANSWER_KEY",
    "SCORING_GUIDE",
)

DOCUMENT_FILENAMES = {
    "MATRIX": "ma-tran.docx",
    "SPECIFICATION": "ban-dac-ta.docx",
    "STUDENT_EXAM": "de-kiem-tra.docx",
    "ANSWER_KEY": "dap-an.docx",
    "SCORING_GUIDE": "huong-dan-cham.docx",
}


def _required_text(value: object, field_name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssessmentDocumentExportValidationError(
            f"{field_name} is required"
        )
    normalized = value.strip()
    if len(normalized) > limit:
        raise AssessmentDocumentExportValidationError(
            f"{field_name} is too long"
        )
    return normalized


def _required_uuid(value: object, field_name: str) -> str:
    text = _required_text(value, field_name, 50)
    try:
        return str(UUID(text))
    except ValueError as error:
        raise AssessmentDocumentExportValidationError(
            f"{field_name} must be a valid UUID"
        ) from error


def _sha256_digest(value: object, field_name: str) -> str:
    digest = _required_text(value, field_name, 64).lower()
    if len(digest) != 64 or any(
        character not in "0123456789abcdef"
        for character in digest
    ):
        raise AssessmentDocumentExportValidationError(
            f"{field_name} must be a SHA-256 digest"
        )
    return digest


@dataclass(frozen=True, slots=True)
class AssessmentDocumentExportRequest:
    exam_version_id: str
    variant_id: str
    owner_user_id: str
    template_set_code: str
    bundle_name: str
    document_types: tuple[str, ...] = DOCUMENT_TYPES

    def __post_init__(self) -> None:
        for field_name in (
            "exam_version_id",
            "variant_id",
            "owner_user_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_uuid(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "template_set_code",
            _required_text(
                self.template_set_code,
                "template_set_code",
                140,
            ).upper(),
        )
        object.__setattr__(
            self,
            "bundle_name",
            _required_text(self.bundle_name, "bundle_name", 120),
        )
        if not isinstance(self.document_types, tuple):
            raise AssessmentDocumentExportValidationError(
                "document_types must be a tuple"
            )
        normalized = tuple(
            _required_text(value, "document_type", 50).upper()
            for value in self.document_types
        )
        if not normalized:
            raise AssessmentDocumentExportValidationError(
                "document_types must not be empty"
            )
        if len(set(normalized)) != len(normalized):
            raise AssessmentDocumentExportValidationError(
                "document_types must be unique"
            )
        if any(value not in DOCUMENT_TYPES for value in normalized):
            raise AssessmentDocumentExportValidationError(
                "document_types contains an unsupported value"
            )
        object.__setattr__(self, "document_types", normalized)


@dataclass(frozen=True, slots=True)
class PublishedAssessmentRenderSource:
    exam_version_id: str
    variant_id: str
    owner_user_id: str
    snapshot_hash: str
    hash_verified: bool
    snapshot_document: Mapping[str, object]
    student_exam_payload: Mapping[str, object]
    answer_key_payload: Mapping[str, object]
    scoring_guide_payload: Mapping[str, object]

    def __post_init__(self) -> None:
        for field_name in (
            "exam_version_id",
            "variant_id",
            "owner_user_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_uuid(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "snapshot_hash",
            _sha256_digest(self.snapshot_hash, "snapshot_hash"),
        )
        if not isinstance(self.hash_verified, bool):
            raise AssessmentDocumentExportValidationError(
                "hash_verified must be boolean"
            )
        for field_name in (
            "snapshot_document",
            "student_exam_payload",
            "answer_key_payload",
            "scoring_guide_payload",
        ):
            if not isinstance(getattr(self, field_name), Mapping):
                raise AssessmentDocumentExportValidationError(
                    f"{field_name} must be an object"
                )


@dataclass(frozen=True, slots=True)
class ApprovedAssessmentTemplate:
    template_version_id: str
    template_set_code: str
    review_status: str
    lifecycle_status: str
    definition: AssessmentTemplateDefinition

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "template_version_id",
            _required_uuid(
                self.template_version_id,
                "template_version_id",
            ),
        )
        object.__setattr__(
            self,
            "template_set_code",
            _required_text(
                self.template_set_code,
                "template_set_code",
                140,
            ).upper(),
        )
        for field_name in ("review_status", "lifecycle_status"):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name), field_name, 30
                ).upper(),
            )
        if not isinstance(self.definition, AssessmentTemplateDefinition):
            raise AssessmentDocumentExportValidationError(
                "definition must be an assessment template"
            )


@dataclass(frozen=True, slots=True)
class RenderedAssessmentDocument:
    document_type: str
    filename: str
    template_version_id: str
    content: bytes
    content_hash: str


@dataclass(frozen=True, slots=True)
class AssessmentDocumentExportResult:
    bundle_filename: str
    bundle_content: bytes
    bundle_hash: str
    documents: tuple[RenderedAssessmentDocument, ...]


class AssessmentDocumentExportGateway(Protocol):
    def load_published_render_source(
        self, *, exam_version_id: str, variant_id: str
    ) -> PublishedAssessmentRenderSource | None: ...

    def find_active_template(
        self, *, template_set_code: str, document_type: str
    ) -> ApprovedAssessmentTemplate | None: ...

    def load_template_asset(self, *, asset_path: str) -> bytes: ...


class AssessmentDocumentExportService:
    """Build canonical data and export a deterministic DOCX bundle."""

    def __init__(
        self,
        *,
        gateway: AssessmentDocumentExportGateway,
        builder: CanonicalAssessmentDocumentBuilder | None = None,
        plan_renderer: DynamicAssessmentDocumentRenderer | None = None,
        docx_renderer: AssessmentDocxRenderPlanRenderer | None = None,
    ) -> None:
        self._gateway = gateway
        self._builder = builder or CanonicalAssessmentDocumentBuilder()
        self._plan_renderer = (
            plan_renderer or DynamicAssessmentDocumentRenderer()
        )
        self._docx_renderer = (
            docx_renderer or AssessmentDocxRenderPlanRenderer()
        )

    def export(
        self, *, request: AssessmentDocumentExportRequest
    ) -> AssessmentDocumentExportResult:
        if not isinstance(request, AssessmentDocumentExportRequest):
            raise AssessmentDocumentExportValidationError(
                "assessment document export request is required"
            )
        source = self._gateway.load_published_render_source(
            exam_version_id=request.exam_version_id,
            variant_id=request.variant_id,
        )
        if source is None:
            raise AssessmentDocumentExportError(
                "published render source is unavailable"
            )
        self._verify_source(request=request, source=source)
        canonical = self._build_canonical(source)
        rendered: list[RenderedAssessmentDocument] = []
        for document_type in request.document_types:
            template = self._gateway.find_active_template(
                template_set_code=request.template_set_code,
                document_type=document_type,
            )
            self._verify_template(
                request=request,
                document_type=document_type,
                template=template,
            )
            assert template is not None
            asset = self._load_asset(template)
            plan = self._plan_renderer.render(
                document=canonical,
                template=template.definition,
            )
            content = self._docx_renderer.render(
                plan=plan,
                template_asset=asset,
            )
            if not isinstance(content, bytes) or not content.startswith(b"PK"):
                raise AssessmentDocumentExportError(
                    "DOCX renderer returned invalid content"
                )
            content = self._normalize_docx(content)
            rendered.append(
                RenderedAssessmentDocument(
                    document_type=document_type,
                    filename=DOCUMENT_FILENAMES[document_type],
                    template_version_id=template.template_version_id,
                    content=content,
                    content_hash=sha256(content).hexdigest(),
                )
            )
        bundle = self._bundle(
            request=request,
            source=source,
            documents=tuple(rendered),
        )
        return AssessmentDocumentExportResult(
            bundle_filename=f"{self._safe_name(request.bundle_name)}.zip",
            bundle_content=bundle,
            bundle_hash=sha256(bundle).hexdigest(),
            documents=tuple(rendered),
        )

    @staticmethod
    def _verify_source(*, request, source) -> None:
        if not isinstance(source, PublishedAssessmentRenderSource):
            raise AssessmentDocumentExportError(
                "gateway returned an invalid render source"
            )
        if source.exam_version_id != request.exam_version_id:
            raise AssessmentDocumentExportError(
                "render source exam version does not match"
            )
        if source.variant_id != request.variant_id:
            raise AssessmentDocumentExportError(
                "render source variant does not match"
            )
        if source.owner_user_id != request.owner_user_id:
            raise PermissionError(
                "render source owner does not match request owner"
            )
        if not source.hash_verified:
            raise AssessmentDocumentExportError(
                "published snapshot integrity verification failed"
            )

    def _build_canonical(
        self, source: PublishedAssessmentRenderSource
    ) -> CanonicalAssessmentDocument:
        try:
            return self._builder.build(
                snapshot_document=dict(source.snapshot_document),
                student_exam_payload=dict(source.student_exam_payload),
                answer_key_payload=dict(source.answer_key_payload),
                scoring_guide_payload=dict(source.scoring_guide_payload),
            )
        except Exception as error:
            raise AssessmentDocumentExportError(
                "canonical assessment document could not be built"
            ) from error

    @staticmethod
    def _verify_template(
        *, request, document_type, template
    ) -> None:
        if template is None:
            raise AssessmentDocumentExportError(
                f"active template is unavailable: {document_type}"
            )
        if not isinstance(template, ApprovedAssessmentTemplate):
            raise AssessmentDocumentExportError(
                "gateway returned an invalid template"
            )
        if template.template_set_code != request.template_set_code:
            raise AssessmentDocumentExportError(
                "template set does not match request"
            )
        if template.review_status != "APPROVED":
            raise AssessmentDocumentExportError(
                "template version is not approved"
            )
        if template.lifecycle_status != "ACTIVE":
            raise AssessmentDocumentExportError(
                "template version is not active"
            )
        if template.definition.document_type_code != document_type:
            raise AssessmentDocumentExportError(
                "template document type does not match"
            )

    def _load_asset(
        self, template: ApprovedAssessmentTemplate
    ) -> bytes | None:
        path = template.definition.template_asset_path
        expected_hash = template.definition.template_asset_hash
        if path is None:
            return None
        content = self._gateway.load_template_asset(asset_path=path)
        if not isinstance(content, bytes):
            raise AssessmentDocumentExportError(
                "template asset must be bytes"
            )
        if sha256(content).hexdigest() != expected_hash:
            raise AssessmentDocumentExportError(
                "template asset integrity verification failed"
            )
        return content

    @classmethod
    def _bundle(cls, *, request, source, documents) -> bytes:
        manifest = {
            "schema_version": 1,
            "exam_version_id": request.exam_version_id,
            "variant_id": request.variant_id,
            "snapshot_hash": source.snapshot_hash,
            "template_set_code": request.template_set_code,
            "documents": [
                {
                    "document_type": item.document_type,
                    "filename": item.filename,
                    "template_version_id": item.template_version_id,
                    "content_hash": item.content_hash,
                }
                for item in documents
            ],
        }
        stream = BytesIO()
        with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
            for item in documents:
                cls._write_zip_entry(
                    archive, item.filename, item.content
                )
            cls._write_zip_entry(
                archive,
                "manifest.json",
                dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8"),
            )
        return stream.getvalue()

    @staticmethod
    def _write_zip_entry(
        archive,
        filename,
        content,
        *,
        allow_path: bool = False,
    ) -> None:
        path = PurePosixPath(filename)
        if (
            (not allow_path and PurePath(filename).name != filename)
            or path.is_absolute()
            or ".." in path.parts
        ):
            raise AssessmentDocumentExportError(
                "bundle filename must not contain a path"
            )
        info = ZipInfo(filename=filename, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, content)

    @classmethod
    def _normalize_docx(cls, content: bytes) -> bytes:
        """Remove volatile ZIP timestamps from generated DOCX bytes."""

        output = BytesIO()
        try:
            with ZipFile(BytesIO(content), "r") as source:
                names = tuple(sorted(source.namelist()))
                if "[Content_Types].xml" not in names:
                    raise AssessmentDocumentExportError(
                        "DOCX package is missing its content types"
                    )
                with ZipFile(
                    output,
                    "w",
                    compression=ZIP_DEFLATED,
                ) as target:
                    for name in names:
                        if name.endswith("/"):
                            continue
                        cls._write_zip_entry(
                            target,
                            name,
                            source.read(name),
                            allow_path=True,
                        )
        except BadZipFile as error:
            raise AssessmentDocumentExportError(
                "DOCX renderer returned a corrupt package"
            ) from error
        return output.getvalue()

    @staticmethod
    def _safe_name(value: str) -> str:
        normalized = "".join(
            character.lower()
            if character.isascii() and character.isalnum()
            else "-"
            for character in value
        )
        while "--" in normalized:
            normalized = normalized.replace("--", "-")
        normalized = normalized.strip("-")
        return normalized or "assessment-documents"
