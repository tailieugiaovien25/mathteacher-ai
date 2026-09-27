from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from portal_v2.ui.admin_assessment_blueprint_review_streamlit import (
    render_admin_assessment_blueprint_review,
)
from portal_v2.ui.admin_assessment_blueprint_preview_streamlit import (
    render_blueprint_documents_preview,
)
from portal_v2.ui.assessment_exam_settings_streamlit import (
    SupabaseAssessmentExamSettingsCatalog,
)
from portal_v2.ui.admin_assessment_review_7_9_streamlit import (
    render_exam_queue,
    render_question_queue,
)


def render_admin_assessment_setting_review(
    st: Any,
    *,
    client: Any,
    reviewer_user_id: str,
) -> None:
    st.title("Duyệt hồ sơ kiểm tra")
    st.caption("Chọn đúng loại hồ sơ: thiết đặt, ma trận, câu hỏi hoặc bản đề đã lắp ráp.")

    if client is None:
        st.warning("Chưa có kết nối dữ liệu để tải hàng đợi duyệt.")
        return

    try:
        catalog = SupabaseAssessmentExamSettingsCatalog(
            client=client,
            user_id=reviewer_user_id,
        )
        if not catalog.is_admin():
            st.error("Tài khoản hiện tại không có quyền ADMIN để duyệt đề.")
            return
        pending = catalog.pending_reviews()
    except Exception as error:
        st.error(f"Không thể tải hàng đợi duyệt: {error}")
        return

    setting_tab, blueprint_tab, question_tab, exam_tab = st.tabs((
        "01 · Thiết đặt", "02 · Ma trận và đặc tả",
        "03 · Câu hỏi lớp 7–9", "04 · Duyệt đề lớp 7–9",
    ))
    with blueprint_tab:
        render_blueprint_documents_preview(st, client=client)
        render_admin_assessment_blueprint_review(st, client=client,
                                                 reviewer_user_id=reviewer_user_id)
    with question_tab:
        render_question_queue(st, client=client, reviewer_user_id=reviewer_user_id)
    with exam_tab:
        render_exam_queue(st, client=client, reviewer_user_id=reviewer_user_id)
    with setting_tab:
        _render_setting_queue(st, pending=pending, catalog=catalog)


def _render_setting_queue(st: Any, *, pending: list[dict[str, Any]], catalog: Any) -> None:
    st.markdown("### Thiết đặt đề kiểm tra đang chờ duyệt")

    if not pending:
        st.info("Không có thiết đặt đề kiểm tra nào đang chờ duyệt.")
        return

    pending_by_label: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for row in pending:
        relation = row.get("assessment_exam_setting_sets")
        setting_set = relation[0] if isinstance(relation, list) else relation
        setting_set = setting_set if isinstance(setting_set, Mapping) else {}
        owner = str(setting_set.get("owner_user_id", ""))
        label = (
            f"{setting_set.get('setting_name')} · {row.get('assessment_name')} "
            f"· {row.get('assessment_type_code')} · "
            f"Lớp {row.get('grade_level')} · v{row.get('version_number')} "
            f"· USER {owner[:8]}"
        )
        pending_by_label[label] = (dict(row), dict(setting_set))

    selected = st.selectbox(
        "Hồ sơ đang chờ duyệt",
        tuple(pending_by_label),
        key="admin_assessment_review_pending",
    )
    row, setting_set = pending_by_label[selected]

    st.write(
        {
            "Mã thiết đặt": setting_set.get("setting_code"),
            "Tên thiết đặt": setting_set.get("setting_name"),
            "Chủ sở hữu": setting_set.get("owner_user_id"),
            "Môn": row.get("subject_code"),
            "Loại kiểm tra": row.get("assessment_type_code"),
            "Lớp": row.get("grade_level"),
            "Năm học": row.get("academic_year"),
            "Thời lượng": row.get("duration_minutes"),
            "Tổng điểm": row.get("total_score"),
            "Phiên bản": row.get("version_number"),
            "Trạng thái": "PENDING_REVIEW",
        }
    )

    decision_map = {
        "Phê duyệt": "APPROVED",
        "Yêu cầu chỉnh sửa": "REVISION_REQUIRED",
        "Từ chối": "REJECTED",
    }
    decision_label = st.selectbox(
        "Quyết định",
        tuple(decision_map),
        key="admin_assessment_review_decision",
    )
    review_note = st.text_area(
        "Nhận xét của ADMIN",
        value=(
            "Thiết đặt đủ điều kiện áp dụng."
            if decision_map[decision_label] == "APPROVED"
            else ""
        ),
        key="admin_assessment_review_note",
    )

    decision = decision_map[decision_label]
    note_required = decision in {"REVISION_REQUIRED", "REJECTED"}
    if note_required and not review_note.strip():
        st.warning("Yêu cầu chỉnh sửa hoặc từ chối phải có nhận xét của ADMIN.")

    if st.button(
        "Ghi quyết định duyệt",
        type="primary",
        use_container_width=True,
        disabled=note_required and not review_note.strip(),
        key="admin_assessment_review_submit",
    ):
        try:
            catalog.review(
                setting_version_id=str(row.get("setting_version_id", "")),
                decision=decision,
                note=review_note.strip(),
            )
        except Exception as error:
            st.error(f"Không thể duyệt thiết đặt: {error}")
        else:
            st.success("Đã ghi quyết định duyệt thiết đặt đề kiểm tra.")
            st.rerun()
