"""Teacher portal page for governed assessment document export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import UUID

from assessment_generation_v2.adapters import (
    SupabaseAssessmentDocumentExportGateway,
)
from assessment_generation_v2.services import (
    AssessmentDocumentExportRequest,
    AssessmentDocumentExportService,
)


DOCUMENT_TYPE_LABELS = {
    "MATRIX": "Ma trận",
    "SPECIFICATION": "Bản đặc tả",
    "STUDENT_EXAM": "Đề kiểm tra",
    "ANSWER_KEY": "Đáp án",
    "SCORING_GUIDE": "Hướng dẫn chấm",
}


class AssessmentExportCatalogError(RuntimeError):
    """Raised when the export catalog cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class PublishedExamVariantOption:
    exam_version_id: str
    variant_id: str
    exam_code: str
    exam_title: str
    variant_code: str

    @property
    def label(self) -> str:
        return (
            f"{self.exam_code} — {self.exam_title} "
            f"(Mã đề {self.variant_code})"
        )


@dataclass(frozen=True, slots=True)
class ActiveTemplateSetOption:
    template_set_code: str
    display_name: str
    authority_scope: str

    @property
    def label(self) -> str:
        return f"{self.display_name} — {self.authority_scope}"


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object, operation: str) -> list[dict[str, Any]]:
    value = _data(response)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if not isinstance(value, list) or any(
        not isinstance(item, Mapping) for item in value
    ):
        raise AssessmentExportCatalogError(
            f"{operation} returned invalid data"
        )
    return [dict(item) for item in value]


def _relation(value: object, name: str) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentExportCatalogError(
                f"{name} must contain one row"
            )
        value = value[0]
    if not isinstance(value, Mapping):
        raise AssessmentExportCatalogError(
            f"{name} relation is invalid"
        )
    return dict(value)


def _text(value: object, fallback: str = "") -> str:
    return value.strip() if isinstance(value, str) else fallback


def _uuid(value: object, field_name: str) -> str:
    try:
        return str(UUID(_text(value)))
    except (ValueError, AttributeError) as error:
        raise AssessmentExportCatalogError(
            f"{field_name} is invalid"
        ) from error


class SupabaseAssessmentExportCatalog:
    """Lists only locked variants and active approved template sets."""

    def __init__(self, *, client: Any, user_id: str) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client
        self._user_id = _uuid(user_id, "user_id")

    def list_published_variants(
        self,
    ) -> tuple[PublishedExamVariantOption, ...]:
        response = (
            self._client.table("assessment_exam_variants")
            .select(
                "variant_id,variant_code,variant_status,"
                "assessment_exam_snapshots!inner("
                "exam_version_id,"
                "assessment_exam_versions!inner("
                "exam_title,assessment_exams!inner("
                "exam_code,owner_user_id)))"
            )
            .eq("variant_status", "LOCKED")
            .eq(
                "assessment_exam_snapshots."
                "assessment_exam_versions."
                "assessment_exams.owner_user_id",
                self._user_id,
            )
            .order("created_at", desc=True)
            .execute()
        )
        options: list[PublishedExamVariantOption] = []
        for row in _rows(response, "published variant catalog"):
            snapshot = _relation(
                row.get("assessment_exam_snapshots"),
                "assessment_exam_snapshots",
            )
            version = _relation(
                snapshot.get("assessment_exam_versions"),
                "assessment_exam_versions",
            )
            exam = _relation(
                version.get("assessment_exams"),
                "assessment_exams",
            )
            if _uuid(exam.get("owner_user_id"), "owner_user_id") != self._user_id:
                raise PermissionError(
                    "catalog returned an assessment owned by another user"
                )
            options.append(
                PublishedExamVariantOption(
                    exam_version_id=_uuid(
                        snapshot.get("exam_version_id"),
                        "exam_version_id",
                    ),
                    variant_id=_uuid(row.get("variant_id"), "variant_id"),
                    exam_code=_text(exam.get("exam_code"), "Không mã"),
                    exam_title=_text(
                        version.get("exam_title"), "Đề kiểm tra"
                    ),
                    variant_code=_text(
                        row.get("variant_code"), "Gốc"
                    ),
                )
            )
        return tuple(options)

    def list_active_template_sets(
        self,
    ) -> tuple[ActiveTemplateSetOption, ...]:
        response = (
            self._client.table("assessment_document_template_sets")
            .select(
                "template_code,display_name,authority_scope,"
                "lifecycle_status,current_version_number,"
                "assessment_document_template_versions!inner("
                "version_number,review_status)"
            )
            .eq("lifecycle_status", "ACTIVE")
            .eq(
                "assessment_document_template_versions.review_status",
                "APPROVED",
            )
            .order("display_name")
            .execute()
        )
        options: list[ActiveTemplateSetOption] = []
        for row in _rows(response, "active template catalog"):
            versions = row.get("assessment_document_template_versions")
            if isinstance(versions, Mapping):
                versions = [versions]
            if not isinstance(versions, list):
                raise AssessmentExportCatalogError(
                    "template versions relation is invalid"
                )
            current = row.get("current_version_number")
            if not any(
                isinstance(item, Mapping)
                and item.get("version_number") == current
                and _text(item.get("review_status")).upper() == "APPROVED"
                for item in versions
            ):
                continue
            options.append(
                ActiveTemplateSetOption(
                    template_set_code=_text(
                        row.get("template_code")
                    ).upper(),
                    display_name=_text(
                        row.get("display_name"), "Bộ mẫu"
                    ),
                    authority_scope=_text(
                        row.get("authority_scope"), "USER"
                    ).upper(),
                )
            )
        return tuple(options)


def _default_service(*, client: Any, user_id: str):
    gateway = SupabaseAssessmentDocumentExportGateway(
        client=client,
        user_id=user_id,
    )
    return AssessmentDocumentExportService(gateway=gateway)


def render_assessment_document_export_page(
    *,
    st: Any,
    client: Any,
    user_id: str,
    catalog: Any | None = None,
    service_factory: Callable[..., Any] = _default_service,
) -> None:
    """Render a post-publication export page for a signed-in user."""

    st.title("Xuất đề kiểm tra")
    st.caption(
        "Xuất ma trận, bản đặc tả, đề, đáp án và hướng dẫn chấm "
        "từ phiên bản đã được duyệt và xuất bản."
    )
    st.info(
        "Trang này không phê duyệt hoặc xuất bản đề. Hệ thống chỉ dùng "
        "snapshot đã khóa và bộ mẫu đang hoạt động."
    )

    try:
        source_catalog = catalog or SupabaseAssessmentExportCatalog(
            client=client,
            user_id=user_id,
        )
        variants = source_catalog.list_published_variants()
        templates = source_catalog.list_active_template_sets()
    except Exception as error:
        st.error(f"Không thể tải dữ liệu xuất đề: {error}")
        return

    if not variants:
        st.warning(
            "Chưa có đề đã xuất bản và mã đề đã khóa để xuất tài liệu."
        )
        return
    if not templates:
        st.warning(
            "Chưa có bộ mẫu đã được phê duyệt và kích hoạt."
        )
        return

    variant_by_label = {item.label: item for item in variants}
    template_by_label = {item.label: item for item in templates}

    with st.form("assessment_document_export_form"):
        selected_variant_label = st.selectbox(
            "Đề và mã đề",
            tuple(variant_by_label),
        )
        selected_template_label = st.selectbox(
            "Bộ mẫu tài liệu",
            tuple(template_by_label),
        )
        selected_labels = st.multiselect(
            "Tài liệu cần xuất",
            tuple(DOCUMENT_TYPE_LABELS.values()),
            default=tuple(DOCUMENT_TYPE_LABELS.values()),
        )
        bundle_name = st.text_input(
            "Tên bộ tài liệu",
            value="bo-de-kiem-tra",
            max_chars=120,
        )
        submitted = st.form_submit_button(
            "Tạo bộ tài liệu",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        reverse_labels = {
            label: code for code, label in DOCUMENT_TYPE_LABELS.items()
        }
        document_types = tuple(
            reverse_labels[label]
            for label in selected_labels
            if label in reverse_labels
        )
        if not document_types:
            st.error("Bạn cần chọn ít nhất một loại tài liệu.")
        else:
            variant = variant_by_label[selected_variant_label]
            template = template_by_label[selected_template_label]
            try:
                request = AssessmentDocumentExportRequest(
                    exam_version_id=variant.exam_version_id,
                    variant_id=variant.variant_id,
                    owner_user_id=user_id,
                    template_set_code=template.template_set_code,
                    bundle_name=bundle_name,
                    document_types=document_types,
                )
                result = service_factory(
                    client=client,
                    user_id=user_id,
                ).export(request=request)
                st.session_state["assessment_export_result"] = result
                st.success(
                    f"Đã tạo {len(result.documents)} tài liệu."
                )
            except Exception as error:
                st.session_state.pop("assessment_export_result", None)
                st.error(f"Không thể xuất bộ tài liệu: {error}")

    result = st.session_state.get("assessment_export_result")
    if result is not None:
        st.download_button(
            "Tải bộ tài liệu ZIP",
            data=result.bundle_content,
            file_name=result.bundle_filename,
            mime="application/zip",
            use_container_width=True,
        )
        st.caption(f"SHA-256: {result.bundle_hash}")
