"""Human-governed ADMIN workflow for assessment document templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID


DEFAULT_TEMPLATE_CODE = "MATHTEACHER_DEFAULT_FLEXIBLE"


@dataclass(frozen=True, slots=True)
class TemplateWorkflowState:
    template_set_id: str
    template_version_id: str
    template_name: str
    lifecycle_status: str
    review_status: str
    version_number: int


@dataclass(frozen=True, slots=True)
class AssessmentProfileWorkflowState:
    profile_code: str
    profile_name: str
    subject_code: str
    grade_min: int
    grade_max: int
    total_score: float
    duration_minutes: int
    status: str


@dataclass(frozen=True, slots=True)
class PendingBlueprintReview:
    blueprint_version_id: str
    blueprint_code: str
    blueprint_name: str
    owner_user_id: str
    subject_code: str
    grade_level: int
    profile_code: str
    version_number: int
    total_score: float

    @property
    def label(self) -> str:
        return (
            f"{self.blueprint_code} — {self.blueprint_name} · "
            f"Lớp {self.grade_level} · v{self.version_number}"
        )


def _relation(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError(
                f"Quan hệ {field_name} phải có đúng một bản ghi."
            )
        value = value[0]
    if not isinstance(value, Mapping):
        raise ValueError(f"Quan hệ {field_name} không hợp lệ.")
    return value


def _load_pending_blueprint_reviews(
    *,
    client: Any,
) -> tuple[PendingBlueprintReview, ...]:
    response = (
        client.table("assessment_blueprint_versions")
        .select(
            "blueprint_version_id,blueprint_name,profile_code,"
            "version_number,total_score,review_status,locked_at,"
            "assessment_blueprints!inner(blueprint_code,owner_user_id,"
            "subject_code,grade_level,lifecycle_status)"
        )
        .eq("review_status", "PENDING_REVIEW")
        .is_("locked_at", "null")
        .order("updated_at")
        .execute()
    )
    data = getattr(response, "data", None)
    rows = data if isinstance(data, list) else []
    result = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        blueprint = _relation(
            row.get("assessment_blueprints"),
            "assessment_blueprints",
        )
        result.append(
            PendingBlueprintReview(
                blueprint_version_id=str(
                    row.get("blueprint_version_id", "")
                ),
                blueprint_code=str(
                    blueprint.get("blueprint_code", "")
                ),
                blueprint_name=str(row.get("blueprint_name", "")),
                owner_user_id=str(
                    blueprint.get("owner_user_id", "")
                ),
                subject_code=str(
                    blueprint.get("subject_code", "")
                ),
                grade_level=int(blueprint.get("grade_level", 0) or 0),
                profile_code=str(row.get("profile_code", "")),
                version_number=int(
                    row.get("version_number", 0) or 0
                ),
                total_score=float(row.get("total_score", 0) or 0),
            )
        )
    return tuple(result)


def _render_blueprint_review_queue(
    *,
    st: Any,
    client: Any,
    reviewer_user_id: str,
) -> None:
    st.subheader("Duyệt ma trận và bản đặc tả")
    st.caption(
        "Chỉ ma trận do giáo viên gửi duyệt mới xuất hiện. Người duyệt "
        "phải khác chủ sở hữu; phê duyệt sẽ khóa phiên bản và kích hoạt "
        "ma trận."
    )
    try:
        reviewer_id = str(UUID(str(reviewer_user_id).strip()))
        pending = _load_pending_blueprint_reviews(client=client)
    except Exception as error:
        st.error(f"Không thể tải hàng đợi duyệt ma trận: {error}")
        return
    if not pending:
        st.info("Không có ma trận nào đang chờ duyệt.")
        return
    review_by_label = {item.label: item for item in pending}
    selected_label = st.selectbox(
        "Ma trận chờ duyệt",
        tuple(review_by_label),
        key="assessment_blueprint_review_pending",
    )
    selected = review_by_label[selected_label]
    metrics = st.columns(4)
    metrics[0].metric("Môn", selected.subject_code)
    metrics[1].metric("Lớp", selected.grade_level)
    metrics[2].metric("Tổng điểm", f"{selected.total_score:g}")
    metrics[3].metric("Phiên bản", selected.version_number)
    st.caption(
        f"Hồ sơ: {selected.profile_code} · "
        f"Chủ sở hữu: {selected.owner_user_id}"
    )
    own_blueprint = selected.owner_user_id == reviewer_id
    if own_blueprint:
        st.warning(
            "Tài khoản này là chủ sở hữu ma trận nên không được tự duyệt."
        )
    review_note = st.text_area(
        "Nhận xét duyệt ma trận",
        value="Ma trận và bản đặc tả đủ điều kiện sử dụng.",
        key=(
            "assessment_blueprint_review_note_"
            + selected.blueprint_version_id
        ),
    )
    decision_labels = {
        "Phê duyệt": "APPROVED",
        "Yêu cầu chỉnh sửa": "REVISION_REQUIRED",
        "Từ chối": "REJECTED",
    }
    decision_label = st.selectbox(
        "Quyết định",
        tuple(decision_labels),
        key=(
            "assessment_blueprint_review_decision_"
            + selected.blueprint_version_id
        ),
    )
    if not st.button(
        "Ghi quyết định duyệt ma trận",
        type="primary",
        use_container_width=True,
        disabled=own_blueprint,
        key=(
            "assessment_blueprint_review_action_"
            + selected.blueprint_version_id
        ),
    ):
        return
    try:
        client.rpc(
            "review_assessment_blueprint",
            {
                "target_blueprint_version_id": (
                    selected.blueprint_version_id
                ),
                "target_decision": decision_labels[decision_label],
                "target_review_note": review_note.strip(),
            },
        ).execute()
    except Exception as error:
        st.error(f"Không thể ghi quyết định duyệt ma trận: {error}")
        return
    st.success("Đã ghi quyết định duyệt ma trận.")
    st.rerun()


def _load_assessment_profiles(
    *,
    client: Any,
) -> tuple[AssessmentProfileWorkflowState, ...]:
    response = (
        client.table("assessment_profiles")
        .select(
            "profile_code,profile_name,subject_code,grade_min,grade_max,"
            "total_score,duration_minutes,status"
        )
        .order("subject_code")
        .order("profile_code")
        .execute()
    )
    data = getattr(response, "data", None)
    rows = data if isinstance(data, list) else []
    return tuple(
        AssessmentProfileWorkflowState(
            profile_code=str(row.get("profile_code", "")),
            profile_name=str(row.get("profile_name", "")),
            subject_code=str(row.get("subject_code", "")),
            grade_min=int(row.get("grade_min", 0) or 0),
            grade_max=int(row.get("grade_max", 0) or 0),
            total_score=float(row.get("total_score", 0) or 0),
            duration_minutes=int(row.get("duration_minutes", 0) or 0),
            status=str(row.get("status", "DRAFT")).upper(),
        )
        for row in rows
        if isinstance(row, Mapping)
    )


def _render_assessment_profile_activation(
    *,
    st: Any,
    client: Any,
) -> None:
    st.subheader("Hồ sơ cấu trúc đề kiểm tra")
    st.caption(
        "Hồ sơ là dữ liệu cấu hình số câu, điểm, thời lượng và mức độ; "
        "không được mã hóa cứng trong giao diện giáo viên."
    )
    try:
        profiles = _load_assessment_profiles(client=client)
    except Exception as error:
        st.error(f"Không thể tải hồ sơ đánh giá: {error}")
        return
    if not profiles:
        st.warning("Chưa có hồ sơ đánh giá trong cơ sở dữ liệu.")
        return
    for profile in profiles:
        with st.container(border=True):
            st.write(
                f"**{profile.profile_name}**  "
                f"`{profile.profile_code}`"
            )
            st.caption(
                f"{profile.subject_code} · Lớp "
                f"{profile.grade_min}–{profile.grade_max} · "
                f"{profile.duration_minutes} phút · "
                f"{profile.total_score:g} điểm · {profile.status}"
            )
            if profile.status == "ACTIVE":
                st.success("Hồ sơ đang hoạt động.")
                continue
            _action(
                st=st,
                client=client,
                label="Kiểm tra và kích hoạt hồ sơ",
                key=(
                    "assessment_profile_activate_"
                    + profile.profile_code
                ),
                function_name="activate_assessment_profile",
                parameters={
                    "target_profile_code": profile.profile_code,
                },
                success_message="Đã kích hoạt hồ sơ đánh giá.",
                disabled=profile.status != "DRAFT",
            )


def _load_state(*, client: Any) -> TemplateWorkflowState | None:
    response = (
        client.table("assessment_document_template_sets")
        .select(
            "template_set_id,template_code,template_name,"
            "lifecycle_status,current_version_number,"
            "assessment_document_template_versions("
            "template_version_id,version_number,review_status)"
        )
        .eq("template_code", DEFAULT_TEMPLATE_CODE)
        .limit(1)
        .execute()
    )
    data = getattr(response, "data", None)
    rows = data if isinstance(data, list) else []
    if not rows:
        return None
    row = rows[0]
    versions = row.get("assessment_document_template_versions")
    if isinstance(versions, Mapping):
        version_rows = [versions]
    elif isinstance(versions, list):
        version_rows = [
            item for item in versions if isinstance(item, Mapping)
        ]
    else:
        version_rows = []
    if not version_rows:
        raise ValueError("Bộ mẫu chưa có phiên bản.")
    version = max(
        version_rows,
        key=lambda item: int(item.get("version_number", 0) or 0),
    )
    return TemplateWorkflowState(
        template_set_id=str(row.get("template_set_id", "")),
        template_version_id=str(
            version.get("template_version_id", "")
        ),
        template_name=str(row.get("template_name", "Bộ mẫu")),
        lifecycle_status=str(
            row.get("lifecycle_status", "DRAFT")
        ).upper(),
        review_status=str(
            version.get("review_status", "DRAFT")
        ).upper(),
        version_number=int(version.get("version_number", 1) or 1),
    )


def _action(
    *,
    st: Any,
    client: Any,
    label: str,
    key: str,
    function_name: str,
    parameters: Mapping[str, object],
    success_message: str,
    disabled: bool = False,
) -> None:
    if not st.button(
        label,
        key=key,
        disabled=disabled,
        type="primary" if not disabled else "secondary",
        use_container_width=True,
    ):
        return
    try:
        client.rpc(function_name, dict(parameters)).execute()
    except Exception as error:
        st.error(f"Không thể thực hiện thao tác: {error}")
    else:
        st.success(success_message)
        st.rerun()


def render_admin_assessment_template_workflow(
    st: Any,
    *,
    client: Any,
    reviewer_user_id: str,
) -> None:
    st.title("Quản trị bộ mẫu đề kiểm tra")
    st.caption(
        "Tạo, gửi duyệt, phê duyệt và kích hoạt bộ mẫu dùng cho "
        "ma trận, bản đặc tả, đề, đáp án và hướng dẫn chấm."
    )
    st.info(
        "Mỗi nút chỉ thực hiện một bước. Hệ thống không tự phê duyệt "
        "hoặc tự kích hoạt bộ mẫu."
    )
    if client is None:
        st.warning("Chưa có kết nối Supabase.")
        return
    _render_assessment_profile_activation(
        st=st,
        client=client,
    )
    st.divider()
    _render_blueprint_review_queue(
        st=st,
        client=client,
        reviewer_user_id=reviewer_user_id,
    )
    st.divider()
    st.subheader("Bộ mẫu tài liệu đề kiểm tra")
    try:
        state = _load_state(client=client)
    except Exception as error:
        st.error(f"Không thể tải trạng thái bộ mẫu: {error}")
        return
    if state is None:
        st.warning("Chưa có bộ mẫu mặc định.")
        _action(
            st=st,
            client=client,
            label="1. Tạo bản nháp bộ mẫu",
            key="assessment_template_create_draft",
            function_name=(
                "create_default_assessment_document_template_draft"
            ),
            parameters={},
            success_message="Đã tạo bản nháp bộ mẫu.",
        )
        return
    metrics = st.columns(3)
    metrics[0].metric("Bộ mẫu", state.template_name)
    metrics[1].metric("Trạng thái duyệt", state.review_status)
    metrics[2].metric("Vòng đời", state.lifecycle_status)
    st.write(f"Phiên bản: {state.version_number}")
    _action(
        st=st,
        client=client,
        label="2. Gửi bộ mẫu để duyệt",
        key="assessment_template_submit",
        function_name=(
            "submit_assessment_document_template_for_review"
        ),
        parameters={
            "target_template_version_id": state.template_version_id,
        },
        success_message="Đã gửi bộ mẫu để duyệt.",
        disabled=state.review_status not in {
            "DRAFT",
            "REVISION_REQUIRED",
        },
    )
    review_comment = st.text_area(
        "Nhận xét phê duyệt",
        value="Bộ mẫu mặc định đủ điều kiện vận hành.",
        key="assessment_template_review_comment",
        disabled=state.review_status != "PENDING_REVIEW",
    )
    _action(
        st=st,
        client=client,
        label="3. Phê duyệt bộ mẫu",
        key="assessment_template_approve",
        function_name="review_assessment_document_template",
        parameters={
            "target_template_version_id": state.template_version_id,
            "target_decision": "APPROVED",
            "target_review_comment": review_comment,
        },
        success_message="Đã phê duyệt bộ mẫu.",
        disabled=state.review_status != "PENDING_REVIEW",
    )
    _action(
        st=st,
        client=client,
        label="4. Kích hoạt bộ mẫu",
        key="assessment_template_activate",
        function_name=(
            "activate_assessment_document_template_version"
        ),
        parameters={
            "target_template_version_id": state.template_version_id,
        },
        success_message="Đã kích hoạt bộ mẫu.",
        disabled=(
            state.review_status != "APPROVED"
            or state.lifecycle_status == "ACTIVE"
        ),
    )
    if (
        state.review_status == "APPROVED"
        and state.lifecycle_status == "ACTIVE"
    ):
        st.success("Bộ mẫu đã được phê duyệt và đang hoạt động.")
