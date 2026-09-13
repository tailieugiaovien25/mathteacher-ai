"""Teacher workspace for governed assessment draft generation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping
from uuid import UUID

from assessment_generation_v2.adapters import (
    SupabaseAssessmentExamGenerationGateway,
)
from assessment_generation_v2.services import (
    AssessmentExamGenerationRequest,
    AssessmentExamGenerationService,
    TeacherValidationConfirmation,
    ValidationStatus,
)


_RESULT_KEY = "assessment_exam_generation_result"
_PENDING_REQUEST_KEY = (
    "assessment_exam_generation_pending_warning_request"
)
_PENDING_RESULT_KEY = (
    "assessment_exam_generation_pending_warning_result"
)
_PENDING_OWNER_KEY = (
    "assessment_exam_generation_pending_warning_owner_user_id"
)
_ACKNOWLEDGEMENT_KEY = (
    "assessment_exam_generation_warning_acknowledged"
)
_CONFIRMATION_ACCEPTED_KEY = (
    "assessment_exam_generation_warning_confirmation_accepted"
)


class AssessmentGenerationCatalogError(RuntimeError):
    """Raised when the blueprint catalog violates its contract."""


@dataclass(frozen=True, slots=True)
class ApprovedBlueprintOption:
    blueprint_version_id: str
    setting_version_id: str
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
                "blueprint_version_id,profile_code,blueprint_name,"
                "setting_version_id,"
                "duration_minutes,total_score,review_status,locked_at,"
                "assessment_blueprints!inner("
                "blueprint_code,grade_level,owner_user_id,"
                "lifecycle_status)"
            )
            .eq("assessment_blueprints.owner_user_id", self._user_id)
            .eq("assessment_blueprints.lifecycle_status", "ACTIVE")
            .eq("review_status", "APPROVED")
            .not_.is_("locked_at", "null")
            .not_.is_("setting_version_id", "null")
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
                    blueprint_version_id=_required_text(
                        row.get("blueprint_version_id"),
                        "blueprint_version_id",
                    ),
                    setting_version_id=_required_text(
                        row.get("setting_version_id"),
                        "setting_version_id",
                    ),
                    blueprint_code=_required_text(
                        blueprint.get("blueprint_code"),
                        "blueprint_code",
                    ),
                    blueprint_name=_required_text(
                        row.get("blueprint_name"),
                        "blueprint_name",
                    ),
                    profile_code=_required_text(
                        row.get("profile_code"),
                        "profile_code",
                    ),
                    grade_level=int(
                        blueprint.get("grade_level", 0)
                    ),
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


def _clear_pending_warning_state(st: Any) -> None:
    for key in (
        _PENDING_REQUEST_KEY,
        _PENDING_RESULT_KEY,
        _PENDING_OWNER_KEY,
        _ACKNOWLEDGEMENT_KEY,
    ):
        st.session_state.pop(key, None)


def _render_generation_result(
    *,
    st: Any,
    result: Any,
    confirmation_accepted: bool = False,
) -> None:
    canonical = result.canonical_validation_result

    if canonical.status is ValidationStatus.PASS:
        st.success("Bản nháp đã được tạo và xác thực thành công.")
    elif canonical.status is ValidationStatus.FAIL:
        st.error("Không đạt — cần chỉnh sửa trước khi gửi duyệt")
        for error in canonical.errors:
            st.write(error)
    else:
        st.warning(
            "Cảnh báo — cần giáo viên xác nhận\n\n"
            "Kết quả này không phải Đạt (PASS) và cũng không phải "
            "Không đạt (FAIL).\n"
            "Bản nháp chưa được tiếp tục/gửi duyệt."
        )
        for warning in canonical.warnings:
            st.write(warning)
        if confirmation_accepted:
            st.success(
                "Giáo viên đã xác nhận cảnh báo; hệ thống đã chấp nhận "
                "xác nhận và hoàn tất bước tiếp tục theo yêu cầu."
            )

    st.caption(f"Trạng thái tạo đề: {result.state.value}.")
    st.caption(f"Exam version ID: {result.exam_version_id}")
    if canonical.metrics:
        st.json(dict(canonical.metrics))


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
        st.caption(
            "Thiết đặt quản trị: "
            + selected.setting_version_id
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

    if submitted:
        _clear_pending_warning_state(st)
        st.session_state.pop(_RESULT_KEY, None)
        st.session_state.pop(_CONFIRMATION_ACCEPTED_KEY, None)
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
            _clear_pending_warning_state(st)
            st.error(f"Không thể tạo bản nháp đề: {error}")
            return

        st.session_state[_RESULT_KEY] = result
        canonical = result.canonical_validation_result
        if canonical.status is ValidationStatus.WARNING:
            st.session_state[_PENDING_REQUEST_KEY] = request
            st.session_state[_PENDING_RESULT_KEY] = result
            st.session_state[_PENDING_OWNER_KEY] = user_id

    result = st.session_state.get(_RESULT_KEY)
    if result is None:
        return

    _render_generation_result(
        st=st,
        result=result,
        confirmation_accepted=st.session_state.get(
            _CONFIRMATION_ACCEPTED_KEY,
            False,
        ),
    )

    original_request = st.session_state.get(_PENDING_REQUEST_KEY)
    pending_result = st.session_state.get(_PENDING_RESULT_KEY)
    stored_owner_user_id = st.session_state.get(_PENDING_OWNER_KEY)
    if original_request is None or pending_result is None:
        return

    if (
        user_id != original_request.owner_user_id
        or stored_owner_user_id != original_request.owner_user_id
    ):
        _clear_pending_warning_state(st)
        st.session_state.pop(_CONFIRMATION_ACCEPTED_KEY, None)
        st.error(
            "Tài khoản đã xác thực đã thay đổi. Xác nhận cảnh báo cũ "
            "không còn hợp lệ; vui lòng tạo lại yêu cầu."
        )
        return

    acknowledged = st.checkbox(
        "Tôi đã đọc và chấp nhận các cảnh báo trên",
        value=False,
        key=_ACKNOWLEDGEMENT_KEY,
    )
    confirm_requested = st.button(
        "Xác nhận cảnh báo và tiếp tục",
        type="primary",
    )
    if not confirm_requested:
        return
    if not acknowledged:
        st.warning(
            "Vui lòng đánh dấu xác nhận đã đọc cảnh báo trước khi tiếp tục."
        )
        return

    current_canonical = pending_result.canonical_validation_result
    confirmation = TeacherValidationConfirmation(
        teacher_user_id=user_id,
        confirmed_warnings=current_canonical.warnings,
    )
    retry_request = replace(
        original_request,
        teacher_confirmation=confirmation,
    )
    try:
        retry_result = service_factory(
            client=client,
            user_id=user_id,
        ).generate(request=retry_request)
    except Exception as error:
        _clear_pending_warning_state(st)
        st.session_state.pop(_CONFIRMATION_ACCEPTED_KEY, None)
        st.error(f"Không thể tiếp tục sau khi xác nhận cảnh báo: {error}")
        return

    st.session_state[_RESULT_KEY] = retry_result
    st.session_state[_CONFIRMATION_ACCEPTED_KEY] = (
        retry_result.teacher_confirmation is not None
    )
    _clear_pending_warning_state(st)
    _render_generation_result(
        st=st,
        result=retry_result,
        confirmation_accepted=st.session_state[
            _CONFIRMATION_ACCEPTED_KEY
        ],
    )
