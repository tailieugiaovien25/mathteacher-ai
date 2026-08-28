"""Read-only diagnostics for the assessment export runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


READINESS_PASS = "PASS"
READINESS_WARNING = "WARNING"
READINESS_BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class AssessmentRuntimeReadinessCheck:
    check_code: str
    label: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        for name in ("check_code", "label", "detail"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-blank text")
            object.__setattr__(self, name, value.strip())
        normalized = self.status.strip().upper()
        if normalized not in {
            READINESS_PASS,
            READINESS_WARNING,
            READINESS_BLOCKED,
        }:
            raise ValueError("status is invalid")
        object.__setattr__(self, "status", normalized)


@dataclass(frozen=True, slots=True)
class AssessmentRuntimeReadinessReport:
    checks: tuple[AssessmentRuntimeReadinessCheck, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.checks, tuple) or not self.checks:
            raise ValueError("checks must be a non-empty tuple")
        if len({item.check_code for item in self.checks}) != len(self.checks):
            raise ValueError("check codes must be unique")

    @property
    def blocked_count(self) -> int:
        return sum(item.status == READINESS_BLOCKED for item in self.checks)

    @property
    def warning_count(self) -> int:
        return sum(item.status == READINESS_WARNING for item in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(item.status == READINESS_PASS for item in self.checks)

    @property
    def is_operational(self) -> bool:
        return self.blocked_count == 0 and self.warning_count == 0


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


class SupabaseAssessmentRuntimeReadinessService:
    """Probe required Supabase contracts without mutating remote state."""

    TABLE_PROBES = (
        (
            "schema_curriculum",
            "Dữ liệu chương trình",
            "assessment_curriculum_programs",
            "program_code",
        ),
        (
            "schema_question_bank",
            "Ngân hàng câu hỏi",
            "assessment_question_items",
            "question_id",
        ),
        (
            "schema_blueprints",
            "Ma trận và bản đặc tả",
            "assessment_blueprints",
            "blueprint_id",
        ),
        (
            "schema_exams",
            "Đề và phiên bản đề",
            "assessment_exams",
            "exam_id",
        ),
        (
            "schema_snapshots",
            "Snapshot đã xuất bản",
            "assessment_exam_snapshots",
            "snapshot_id",
        ),
        (
            "schema_variants",
            "Mã đề",
            "assessment_exam_variants",
            "variant_id",
        ),
        (
            "schema_export_packages",
            "Gói dữ liệu xuất",
            "assessment_exam_export_packages",
            "export_package_id",
        ),
        (
            "schema_templates",
            "Bộ mẫu tài liệu",
            "assessment_document_template_sets",
            "template_set_id",
        ),
    )

    ZERO_UUID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client

    def inspect(self) -> AssessmentRuntimeReadinessReport:
        checks: list[AssessmentRuntimeReadinessCheck] = []
        for code, label, table_name, primary_key in self.TABLE_PROBES:
            checks.append(
                self._probe_table(
                    code=code,
                    label=label,
                    table_name=table_name,
                    primary_key=primary_key,
                )
            )
        checks.extend(
            (
                self._probe_boolean_rpc(
                    code="rpc_snapshot_hash",
                    label="RPC kiểm tra hash snapshot",
                    function_name="assessment_exam_snapshot_hash_matches",
                    parameters={"target_snapshot_id": self.ZERO_UUID},
                ),
                self._probe_boolean_rpc(
                    code="rpc_export_hash",
                    label="RPC kiểm tra hash gói xuất",
                    function_name=(
                        "assessment_exam_export_package_hash_matches"
                    ),
                    parameters={
                        "target_export_package_id": self.ZERO_UUID
                    },
                ),
                self._probe_storage(),
                self._probe_data(
                    code="data_snapshots",
                    label="Snapshot thực tế",
                    table_name="assessment_exam_snapshots",
                    primary_key="snapshot_id",
                    filters=(),
                    empty_detail="Chưa có đề nào được xuất bản thành snapshot.",
                ),
                self._probe_data(
                    code="data_variants",
                    label="Mã đề đã khóa",
                    table_name="assessment_exam_variants",
                    primary_key="variant_id",
                    filters=(("variant_status", "LOCKED"),),
                    empty_detail="Chưa có mã đề ở trạng thái LOCKED.",
                ),
                self._probe_data(
                    code="data_export_packages",
                    label="Gói dữ liệu xuất đã khóa",
                    table_name="assessment_exam_export_packages",
                    primary_key="export_package_id",
                    filters=(("package_status", "LOCKED"),),
                    empty_detail="Chưa có gói dữ liệu xuất ở trạng thái LOCKED.",
                ),
                self._probe_data(
                    code="data_templates",
                    label="Bộ mẫu đang hoạt động",
                    table_name="assessment_document_template_sets",
                    primary_key="template_set_id",
                    filters=(("lifecycle_status", "ACTIVE"),),
                    empty_detail="Chưa có bộ mẫu ở trạng thái ACTIVE.",
                ),
            )
        )
        return AssessmentRuntimeReadinessReport(checks=tuple(checks))

    def _probe_table(
        self, *, code: str, label: str, table_name: str, primary_key: str
    ) -> AssessmentRuntimeReadinessCheck:
        try:
            (
                self._client.table(table_name)
                .select(primary_key)
                .limit(1)
                .execute()
            )
        except Exception as error:
            return AssessmentRuntimeReadinessCheck(
                code,
                label,
                READINESS_BLOCKED,
                f"Không truy cập được {table_name}: {error}",
            )
        return AssessmentRuntimeReadinessCheck(
            code,
            label,
            READINESS_PASS,
            f"Đã xác nhận bảng {table_name}.",
        )

    def _probe_boolean_rpc(
        self,
        *,
        code: str,
        label: str,
        function_name: str,
        parameters: dict[str, str],
    ) -> AssessmentRuntimeReadinessCheck:
        try:
            value = _data(
                self._client.rpc(function_name, parameters).execute()
            )
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            if not isinstance(value, bool):
                raise TypeError("RPC không trả về boolean")
        except Exception as error:
            return AssessmentRuntimeReadinessCheck(
                code,
                label,
                READINESS_BLOCKED,
                f"Không gọi được {function_name}: {error}",
            )
        return AssessmentRuntimeReadinessCheck(
            code,
            label,
            READINESS_PASS,
            f"Đã xác nhận RPC {function_name}.",
        )

    def _probe_storage(self) -> AssessmentRuntimeReadinessCheck:
        try:
            value = (
                self._client.storage
                .from_("assessment-document-templates")
                .list(path="", options={"limit": 1})
            )
            if value is None:
                raise TypeError("Storage không trả về danh sách")
        except Exception as error:
            return AssessmentRuntimeReadinessCheck(
                "storage_template_assets",
                "Storage mẫu DOCX riêng tư",
                READINESS_BLOCKED,
                "Không truy cập được bucket "
                f"assessment-document-templates: {error}",
            )
        return AssessmentRuntimeReadinessCheck(
            "storage_template_assets",
            "Storage mẫu DOCX riêng tư",
            READINESS_PASS,
            "Đã xác nhận bucket assessment-document-templates.",
        )

    def _probe_data(
        self,
        *,
        code: str,
        label: str,
        table_name: str,
        primary_key: str,
        filters: tuple[tuple[str, str], ...],
        empty_detail: str,
    ) -> AssessmentRuntimeReadinessCheck:
        try:
            query = self._client.table(table_name).select(primary_key)
            for field_name, value in filters:
                query = query.eq(field_name, value)
            rows = _data(query.limit(1).execute())
            if rows is None:
                rows = []
            if isinstance(rows, Mapping):
                rows = [rows]
            if not isinstance(rows, list):
                raise TypeError("Kết quả dữ liệu không hợp lệ")
        except Exception as error:
            return AssessmentRuntimeReadinessCheck(
                code,
                label,
                READINESS_BLOCKED,
                f"Không kiểm tra được dữ liệu: {error}",
            )
        if not rows:
            return AssessmentRuntimeReadinessCheck(
                code,
                label,
                READINESS_WARNING,
                empty_detail,
            )
        return AssessmentRuntimeReadinessCheck(
            code,
            label,
            READINESS_PASS,
            "Đã tìm thấy dữ liệu sẵn sàng.",
        )
