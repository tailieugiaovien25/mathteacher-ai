"""Teacher workspace for governed assessment draft generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import UUID

from assessment_generation_v2.adapters import (
    SupabaseAssessmentExamGenerationGateway,
)
from assessment_generation_v2.services import (
    AssessmentExamGenerationRequest,
    AssessmentExamGenerationService,
)


class AssessmentGenerationCatalogError(RuntimeError):
    """Raised when the blueprint catalog violates its contract."""


@dataclass(frozen=True, slots=True)
class ApprovedBlueprintOption:
    blueprint_code: str
    blueprint_name: str
    profile_code: str
    grade_level: int
    duration_minutes: int
    total_score: float

    @property
    def label(self) -> str:
        return (
            f"{self.blueprint_code} — {self.blueprint_name} "
            f"(Lớp {self.grade_level}, {self.duration_minutes} phút)"
        )


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object) -> list[dict[str, Any]]:
    value = _data(response)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if not isinstance(value, list) or any(
        not isinstance(item, Mapping) for item in value
    ):
        raise AssessmentGenerationCatalogError(
            "Danh mục ma trận trả về dữ liệu không hợp lệ."
        )
    return [dict(item) for item in value]


def _relation(value: object, name: str) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentGenerationCatalogError(
                f"Quan hệ {name} phải có đúng một bản ghi."
            )
        value = value[0]
    if not isinstance(value, Mapping):
        raise AssessmentGenerationCatalogError(
            f"Quan hệ {name} không hợp lệ."
        )
    return dict(value)


def _required_text(value: object, name: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise AssessmentGenerationCatalogError(
            f"Thiếu trường {name}."
        )
    return normalized


def _user_id(value: object) -> str:
    try:
        return str(UUID(_required_text(value, "user_id")))
    except ValueError as error:
        raise AssessmentGenerationCatalogError(
            "Tài khoản giáo viên không hợp lệ."
        ) from error


class SupabaseAssessmentGenerationCatalog:
    """List active, approved and locked blueprints owned by a teacher."""

    def __init__(self, *, client: Any, user_id: str) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client
        self._user_id = _user_id(user_id)

    def list_blueprints(self) -> tuple[ApprovedBlueprintOption, ...]:
        response = (
            self._client.table("assessment_blueprint_versions")
            .select(
                "blueprint_version_id,profile_code,grade_level,"
                "duration_minutes,total_score,review_status,locked_at,"
                "assessment_blueprints!inner("
                "blueprint_code,blueprint_name,owner_user_id,"
                "lifecycle_status)"
            )
            .eq("assessment_blueprints.owner_user_id", self._user_id)
            .eq("assessment_blueprints.lifecycle_status", "ACTIVE")
            .eq("review_status", "APPROVED")
            .not_.is_("locked_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        options: list[ApprovedBlueprintOption] = []
        for row in _rows(response):
            blueprint = _relation(
                row.get("assessment_blueprints"),
                "assessment_blueprints",
            )
            if _user_id(blueprint.get("owner_user_id")) != self._user_id:
                raise PermissionError(
                    "Danh mục trả về ma trận của tài khoản khác."
                )
            options.append(
                ApprovedBlueprintOption(
                    blueprint_code=_required_text(
                        blueprint.get("blueprint_code"),
                        "blueprint_code",
                    ),
                    blueprint_name=_required_text(
                        blueprint.get("blueprint_name"),
                        "blueprint_name",
                    ),
                    profile_code=_required_text(
                        row.get("profile_code"),
                        "profile_code",
                    ),
                    grade_level=int(row.get("grade_level", 0)),
                    duration_minutes=int(
                        row.get("duration_minutes", 0)
                    ),
                    total_score=float(row.get("total_score", 0)),
                )
            )
        return tuple(options)


def _default_service(*, client: Any, user_id: str):
    gateway = SupabaseAssessmentExamGenerationGateway(
        client=client,
        user_id=user_id,
    )
    return AssessmentExamGenerationService(gateway=gateway)


def render_assessment_exam_generation_page(
    *,
    st: Any,
    client: Any,
    user_id: str,
    catalog: Any | None = None,
    service_factory: Callable[..., Any] = _default_service,
) -> None:
    """Render draft generation without approving or publishing an exam."""

    st.title("Tạo đề kiểm tra")
    st.caption(
        "Tạo bản nháp đề từ ma trận đã được phê duyệt, "
        "ngân hàng câu hỏi và cấu hình đánh giá hiện hành."
    )
    st.info(
        "Trang này chỉ tạo, lắp ráp và xác thực bản nháp. "
        "Hệ thống không tự phê duyệt, xuất bản, sinh mã đề "
        "hoặc xuất DOCX."
    )

    try:
        source_catalog = catalog or SupabaseAssessmentGenerationCatalog(
            client=client,
            user_id=user_id,
        )
        blueprints = source_catalog.list_blueprints()
    except Exception as error:
        st.error(f"Không thể tải ma trận đã duyệt: {error}")
        return

    if not blueprints:
        st.warning(
            "Chưa có ma trận thuộc tài khoản này ở trạng thái ACTIVE, "
            "APPROVED và đã khóa. Hãy hoàn thiện ma trận trước "
            "khi tạo đề."
        )
        return

    by_label = {option.label: option for option in blueprints}
    with st.form("assessment_exam_generation_form"):
        selected_label = st.selectbox(
            "Ma trận và bản đặc tả",
            tuple(by_label),
        )
        selected = by_label[selected_label]
        st.caption(
            f"Hồ sơ: {selected.profile_code} · "
            f"Thời lượng: {selected.duration_minutes} phút · "
            f"Điểm: {selected.total_score:g}"
        )
        exam_code = st.text_input(
            "Mã đề nội bộ",
            placeholder="Ví dụ: TOAN6_GHK1_2026_001",
            max_chars=140,
        )
        title = st.text_input(
            "Tên đề kiểm tra",
            placeholder="Ví dụ: Đề kiểm tra giữa học kỳ I môn Toán 6",
            max_chars=300,
        )
        idempotency_key = st.text_input(
            "Khóa chống tạo trùng",
            placeholder="Ví dụ: toan6-ghk1-2026-001",
            max_chars=200,
            help=(
                "Dùng lại cùng khóa sẽ không tạo thêm "
                "một bản nháp trùng."
            ),
        )
        submit_for_review = st.checkbox(
            "Gửi duyệt ngay khi bản nháp hợp lệ",
            value=False,
        )
        submitted = st.form_submit_button(
            "Tạo và xác thực bản nháp đề",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        request = AssessmentExamGenerationRequest(
            blueprint_code=selected.blueprint_code,
            owner_user_id=user_id,
            exam_code=exam_code,
            title=title,
            submit_for_review=submit_for_review,
            idempotency_key=idempotency_key,
        )
        result = service_factory(
            client=client,
            user_id=user_id,
        ).generate(request=request)
    except Exception as error:
        st.session_state.pop("assessment_generation_result", None)
        st.error(f"Không thể tạo bản nháp đề: {error}")
        return

    st.session_state["assessment_generation_result"] = result
    if result.validation_report.is_valid:
        st.success(
            "Bản nháp đã được tạo và xác thực thành công. "
            f"Trạng thái: {result.state.value}."
        )
    else:
        st.warning(
            "Bản nháp đã được tạo nhưng cần sửa trước "
            "khi gửi duyệt."
        )
        for violation in result.validation_report.violations:
            st.write(f"- {violation}")

    st.caption(f"Exam version ID: {result.exam_version_id}")
    if result.validation_report.metrics:
        st.json(dict(result.validation_report.metrics))
