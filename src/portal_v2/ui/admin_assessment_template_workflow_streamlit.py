"""Human-governed ADMIN workflow for assessment document templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


DEFAULT_TEMPLATE_CODE = "MATHTEACHER_DEFAULT_FLEXIBLE"


@dataclass(frozen=True, slots=True)
class TemplateWorkflowState:
    template_set_id: str
    template_version_id: str
    template_name: str
    lifecycle_status: str
    review_status: str
    version_number: int


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
