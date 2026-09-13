"""Portal contracts for governed assessment draft generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from assessment_generation_v2.services import (
    AssessmentExamGenerationResult,
    AssessmentValidationReport,
    ExamGenerationState,
    TeacherValidationConfirmation,
    ValidationResult,
    ValidationStatus,
)
from portal_v2.ui.assessment_exam_generation_streamlit import (
    ApprovedBlueprintOption,
    SupabaseAssessmentGenerationCatalog,
    render_assessment_exam_generation_page,
)


USER_ID = "11111111-1111-4111-8111-111111111111"
ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "portal_v2" / "ui" / "assessment_exam_generation_streamlit.py"
APP_FILE = ROOT.parent / "scripts" / "teacher_portal" / "app.py"
OTHER_USER_ID = "99999999-9999-4999-8999-999999999999"
EXAM_ID = "44444444-4444-4444-8444-444444444444"
EXAM_VERSION_ID = "55555555-5555-4555-8555-555555555555"
BLUEPRINT_VERSION_ID = "66666666-6666-4666-8666-666666666666"


@dataclass
class _Response:
    data: object


class _NotFilter:
    def __init__(self, query: "_Query") -> None:
        self.query = query

    def is_(self, column: str, value: object) -> "_Query":
        self.query.operations.append(("not_is", column, value))
        return self.query


class _Query:
    def __init__(self, rows: object) -> None:
        self.rows = rows
        self.operations: list[tuple[object, ...]] = []

    @property
    def not_(self) -> _NotFilter:
        return _NotFilter(self)

    def select(self, value: str) -> "_Query":
        self.operations.append(("select", value))
        return self

    def eq(self, column: str, value: object) -> "_Query":
        self.operations.append(("eq", column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "_Query":
        self.operations.append(("order", column, desc))
        return self

    def execute(self) -> _Response:
        return _Response(self.rows)


class _Client:
    def __init__(self, rows: object) -> None:
        self.query = _Query(rows)
        self.table_name = ""

    def table(self, name: str) -> _Query:
        self.table_name = name
        return self.query


class _Form:
    def __enter__(self) -> "_Form":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _Streamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.submitted = False
        self.acknowledged = False
        self.confirm_requested = False
        self.submit_for_review = False
        self.events: list[tuple[str, object]] = []
        self.acknowledgement_defaults: list[bool] = []

    def _record(self, kind: str, value: object) -> None:
        self.events.append((kind, value))

    def title(self, value: object) -> None:
        self._record("title", value)

    def caption(self, value: object) -> None:
        self._record("caption", value)

    def info(self, value: object) -> None:
        self._record("info", value)

    def success(self, value: object) -> None:
        self._record("success", value)

    def warning(self, value: object) -> None:
        self._record("warning", value)

    def error(self, value: object) -> None:
        self._record("error", value)

    def write(self, value: object) -> None:
        self._record("write", value)

    def json(self, value: object) -> None:
        self._record("json", value)

    def form(self, key: str) -> _Form:
        self._record("form", key)
        return _Form()

    def selectbox(self, label: str, options: tuple[str, ...]) -> str:
        self._record("selectbox", label)
        return options[0]

    def text_input(self, label: str, **kwargs: object) -> str:
        values = {
            "Mã đề nội bộ": "TOAN6_GHK1_001",
            "Tên đề kiểm tra": "Đề kiểm tra giữa học kỳ I",
            "Khóa chống tạo trùng": "toan6-ghk1-001",
        }
        return values[label]

    def checkbox(
        self,
        label: str,
        *,
        value: bool,
        **kwargs: object,
    ) -> bool:
        self._record("checkbox", label)
        if label == "Gửi duyệt ngay khi bản nháp hợp lệ":
            return self.submit_for_review
        self.acknowledgement_defaults.append(value)
        return self.acknowledged

    def form_submit_button(self, label: str, **kwargs: object) -> bool:
        self._record("form_submit_button", label)
        return self.submitted

    def button(self, label: str, **kwargs: object) -> bool:
        self._record("button", label)
        return self.confirm_requested


class _Catalog:
    def list_blueprints(self) -> tuple[ApprovedBlueprintOption, ...]:
        return (
            ApprovedBlueprintOption(
                blueprint_version_id=BLUEPRINT_VERSION_ID,
                setting_version_id=(
                    "77777777-7777-4777-8777-777777777777"
                ),
                blueprint_code="TOAN6_GHK1",
                blueprint_name="Giữa học kỳ I",
                profile_code="TOAN6_90P",
                grade_level=6,
                duration_minutes=90,
                total_score=10,
            ),
        )


class _Service:
    def __init__(
        self,
        results: list[AssessmentExamGenerationResult | Exception],
    ) -> None:
        self.results = list(results)
        self.requests: list[object] = []

    def factory(self, **kwargs: object) -> "_Service":
        return self

    def generate(self, *, request: object) -> AssessmentExamGenerationResult:
        self.requests.append(request)
        outcome = self.results.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _result(
    report: AssessmentValidationReport | ValidationResult,
    *,
    state: ExamGenerationState = ExamGenerationState.DRAFT,
    confirmation: object = None,
) -> AssessmentExamGenerationResult:
    return AssessmentExamGenerationResult(
        exam_id=EXAM_ID,
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        state=state,
        validation_report=report,
        teacher_confirmation=confirmation,
    )


def _render(
    st: _Streamlit,
    service: _Service,
    *,
    user_id: str = USER_ID,
) -> None:
    render_assessment_exam_generation_page(
        st=st,
        client=object(),
        user_id=user_id,
        catalog=_Catalog(),
        service_factory=service.factory,
    )


def _values(st: _Streamlit, kind: str) -> list[object]:
    return [value for event_kind, value in st.events if event_kind == kind]


def test_catalog_lists_only_governed_blueprints() -> None:
    client = _Client(
        [
            {
                "blueprint_version_id": (
                    "22222222-2222-4222-8222-222222222222"
                ),
                "setting_version_id": (
                    "33333333-3333-4333-8333-333333333333"
                ),
                "profile_code": "TOAN6_90P",
                "blueprint_name": 'Giữa học kỳ I',
                "duration_minutes": 90,
                "total_score": 10,
                "review_status": "APPROVED",
                "locked_at": "2026-08-26T00:00:00Z",
                "assessment_blueprints": {
                    "blueprint_code": "TOAN6_GHK1",
                    "grade_level": 6,
                    "owner_user_id": USER_ID,
                    "lifecycle_status": "ACTIVE",
                },
            }
        ]
    )

    options = SupabaseAssessmentGenerationCatalog(
        client=client,
        user_id=USER_ID,
    ).list_blueprints()

    assert len(options) == 1
    assert options[0].blueprint_code == "TOAN6_GHK1"
    assert options[0].grade_level == 6
    assert client.table_name == "assessment_blueprint_versions"
    assert ("eq", "review_status", "APPROVED") in client.query.operations
    assert (
        "eq",
        "assessment_blueprints.lifecycle_status",
        "ACTIVE",
    ) in client.query.operations
    assert ("not_is", "locked_at", "null") in client.query.operations
    assert (
        "not_is",
        "setting_version_id",
        "null",
    ) in client.query.operations


def test_catalog_accepts_empty_state() -> None:
    client = _Client([])
    options = SupabaseAssessmentGenerationCatalog(
        client=client,
        user_id=USER_ID,
    ).list_blueprints()
    assert options == ()


def test_page_uses_existing_generation_service_contract() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    assert "AssessmentExamGenerationRequest" in text
    assert "AssessmentExamGenerationService" in text
    assert "SupabaseAssessmentExamGenerationGateway" in text
    assert ".generate(request=request)" in text


def test_page_does_not_approve_publish_variant_or_export() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    for forbidden in (
        "apply_assessment_exam_review",
        "publish_assessment_exam",
        "create_assessment_exam_variants",
        "AssessmentDocumentExportService",
        ".insert(",
        ".update(",
        ".delete(",
        "service_role",
    ):
        assert forbidden not in text


def test_submit_for_review_requires_explicit_teacher_choice() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    assert '"Gửi duyệt ngay khi bản nháp hợp lệ"' in text
    assert "value=False" in text
    assert "submit_for_review=submit_for_review" in text


def test_teacher_portal_wires_generation_before_export() -> None:
    text = APP_FILE.read_text(encoding="utf-8-sig")
    assert "'T\\u1ea1o \\u0111\\u1ec1 ki\\u1ec3m tra'" in text
    assert 'selected == "Tạo đề kiểm tra"' in text
    assert "render_assessment_exam_generation_page" in text
    assert text.index('selected == "Tạo đề kiểm tra"') < text.index(
        'selected == "Xuất đề kiểm tra"'
    )


def test_legacy_valid_rendering_remains_supported() -> None:
    st = _Streamlit()
    st.submitted = True
    service = _Service(
        [
            _result(
                AssessmentValidationReport(
                    is_valid=True,
                    metrics={"total_score": 10},
                ),
                state=ExamGenerationState.READY_FOR_REVIEW,
            )
        ]
    )

    _render(st, service)

    assert _values(st, "success") == [
        "Bản nháp đã được tạo và xác thực thành công."
    ]
    assert _values(st, "json") == [{"total_score": 10}]
    assert _values(st, "button") == []


def test_legacy_invalid_rendering_remains_supported() -> None:
    st = _Streamlit()
    st.submitted = True
    service = _Service(
        [
            _result(
                AssessmentValidationReport(
                    is_valid=False,
                    violations=("Thiếu câu hỏi đại số.",),
                    metrics={"question_count": 8},
                ),
                state=ExamGenerationState.REVISION_REQUIRED,
            )
        ]
    )

    _render(st, service)

    assert "Không đạt — cần chỉnh sửa trước khi gửi duyệt" in _values(
        st,
        "error",
    )
    assert _values(st, "write") == ["Thiếu câu hỏi đại số."]
    assert _values(st, "json") == [{"question_count": 8}]
    assert _values(st, "button") == []


def test_canonical_pass_has_no_warning_confirmation_controls() -> None:
    st = _Streamlit()
    st.submitted = True
    service = _Service(
        [
            _result(
                ValidationResult(status=ValidationStatus.PASS),
                state=ExamGenerationState.PENDING_REVIEW,
            )
        ]
    )

    _render(st, service)

    assert _values(st, "success")
    assert _values(st, "button") == []
    assert not any(
        "pending_warning" in key for key in st.session_state
    )


def test_canonical_fail_shows_exact_errors_without_confirmation() -> None:
    errors = ("Sai tổng điểm.", "Thiếu phạm vi Hình học.")
    st = _Streamlit()
    st.submitted = True
    service = _Service(
        [
            _result(
                ValidationResult(
                    status=ValidationStatus.FAIL,
                    errors=errors,
                    metrics={"total_score": 9},
                ),
                state=ExamGenerationState.REVISION_REQUIRED,
            )
        ]
    )

    _render(st, service)

    assert _values(st, "write") == list(errors)
    assert _values(st, "button") == []
    assert len(service.requests) == 1


def test_warning_is_exact_visible_pending_and_not_automatically_retried() -> None:
    warnings = ("Giữ nguyên cảnh báo Z.", "Giữ nguyên cảnh báo A.")
    st = _Streamlit()
    st.submitted = True
    service = _Service(
        [
            _result(
                ValidationResult(
                    status=ValidationStatus.WARNING,
                    warnings=warnings,
                    metrics={"warning_count": 2},
                )
            )
        ]
    )

    _render(st, service)

    warning_text = "\n".join(str(value) for value in _values(st, "warning"))
    assert "Cảnh báo — cần giáo viên xác nhận" in warning_text
    assert "Kết quả này không phải Đạt (PASS)" in warning_text
    assert "Bản nháp chưa được tiếp tục/gửi duyệt." in warning_text
    assert _values(st, "write") == list(warnings)
    assert _values(st, "json") == [{"warning_count": 2}]
    assert len(service.requests) == 1
    assert st.acknowledgement_defaults == [False]
    assert any("pending_warning_request" in key for key in st.session_state)
    assert all(
        request.teacher_confirmation is None
        for request in service.requests
    )


def test_warning_confirmation_button_requires_acknowledgement() -> None:
    st = _Streamlit()
    st.submitted = True
    st.confirm_requested = True
    warning = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=("Cần giáo viên xem xét.",),
    )
    service = _Service([_result(warning)])

    _render(st, service)

    assert len(service.requests) == 1
    assert any(
        "Vui lòng đánh dấu xác nhận" in str(value)
        for value in _values(st, "warning")
    )


def test_confirmed_warning_retries_immutable_request_once_and_stays_warning() -> None:
    warnings = ("Không đổi cảnh báo thứ hai.", "Không đổi cảnh báo thứ nhất.")
    warning = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=warnings,
        metrics={"warning_count": 2},
    )
    accepted_confirmation = TeacherValidationConfirmation(
        teacher_user_id=USER_ID,
        confirmed_warnings=warnings,
    )
    st = _Streamlit()
    st.submitted = True
    st.submit_for_review = True
    service = _Service(
        [
            _result(warning),
            _result(
                warning,
                state=ExamGenerationState.PENDING_REVIEW,
                confirmation=accepted_confirmation,
            ),
        ]
    )
    _render(st, service)
    original_request = service.requests[0]

    st.submitted = False
    st.acknowledged = True
    st.confirm_requested = True
    _render(st, service)

    assert len(service.requests) == 2
    retry_request = service.requests[1]
    assert retry_request is not original_request
    for field_name in (
        "blueprint_code",
        "owner_user_id",
        "exam_code",
        "title",
        "submit_for_review",
        "idempotency_key",
    ):
        assert getattr(retry_request, field_name) == getattr(
            original_request,
            field_name,
        )
    assert retry_request.teacher_confirmation.teacher_user_id == USER_ID
    assert retry_request.teacher_confirmation.confirmed_warnings == warnings
    assert _values(st, "write")[-2:] == list(warnings)
    assert any(
        "Cảnh báo — cần giáo viên xác nhận" in str(value)
        for value in _values(st, "warning")
    )
    assert any(
        value == "Trạng thái tạo đề: PENDING_REVIEW."
        for value in _values(st, "caption")
    )
    assert any(
        "đã chấp nhận xác nhận" in str(value)
        for value in _values(st, "success")
    )
    assert not any(
        "pending_warning" in key for key in st.session_state
    )


def test_owner_change_blocks_retry_and_clears_pending_warning() -> None:
    st = _Streamlit()
    st.submitted = True
    warning = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=("Cần xác nhận đúng chủ sở hữu.",),
    )
    service = _Service([_result(warning)])
    _render(st, service)

    st.submitted = False
    st.acknowledged = True
    st.confirm_requested = True
    _render(st, service, user_id=OTHER_USER_ID)

    assert len(service.requests) == 1
    assert any(
        "Tài khoản đã xác thực đã thay đổi" in str(value)
        for value in _values(st, "error")
    )
    assert not any(
        "pending_warning" in key for key in st.session_state
    )


def test_confirmation_failure_clears_pending_and_keeps_warning_evidence() -> None:
    warning = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=("Bằng chứng cảnh báo phải được giữ lại.",),
    )
    st = _Streamlit()
    st.submitted = True
    service = _Service([_result(warning), RuntimeError("retry failed")])
    _render(st, service)

    st.submitted = False
    st.acknowledged = True
    st.confirm_requested = True
    _render(st, service)

    assert len(service.requests) == 2
    assert not any(
        "pending_warning" in key for key in st.session_state
    )
    stored_result = st.session_state["assessment_exam_generation_result"]
    assert stored_result.canonical_validation_result is warning
    assert any(
        "Không thể tiếp tục sau khi xác nhận cảnh báo" in str(value)
        for value in _values(st, "error")
    )
