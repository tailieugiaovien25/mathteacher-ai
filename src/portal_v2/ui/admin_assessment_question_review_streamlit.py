from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from portal_v2.ui.assessment_exam_settings_streamlit import (
    SupabaseAssessmentExamSettingsCatalog,
)


QUESTION_PREFIX = "TOAN7-FINAL-HK1-7A2-"
EXPECTED_QUESTION_COUNT = 40


def _rows(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    return [dict(row) for row in data or [] if isinstance(row, Mapping)]


def _pending_questions(client: Any) -> list[dict[str, Any]]:
    return _rows(
        client.table("assessment_question_versions")
        .select(
            "question_version_id,question_type_code,cognitive_level_code,"
            "prompt_text,default_score,assessment_question_items!inner("
            "question_code,owner_user_id,grade_level)"
        )
        .eq("review_status", "PENDING_REVIEW")
        .eq("assessment_question_items.grade_level", 7)
        .like("assessment_question_items.question_code", QUESTION_PREFIX + "%")
        .order("question_version_id")
        .execute()
    )


def _review_payload(
    questions: list[dict[str, Any]], reviewer_user_id: str
) -> list[dict[str, Any]]:
    if len(questions) != EXPECTED_QUESTION_COUNT:
        raise ValueError("Cần đủ đúng 40 câu đang chờ duyệt.")
    codes: set[str] = set()
    payload: list[dict[str, Any]] = []
    for question in questions:
        relation = question.get("assessment_question_items")
        item = relation[0] if isinstance(relation, list) else relation
        if not isinstance(item, Mapping):
            raise ValueError("Không xác định được câu hỏi gốc.")
        code = str(item.get("question_code", ""))
        if (
            not code.startswith(QUESTION_PREFIX)
            or code in codes
            or item.get("owner_user_id") != reviewer_user_id
            or item.get("grade_level") != 7
        ):
            raise ValueError("Phạm vi hoặc chủ sở hữu của hàng đợi đã thay đổi.")
        codes.add(code)
        payload.append(
            {
                "question_version_id": question["question_version_id"],
                "reviewer_user_id": reviewer_user_id,
                "decision": "APPROVED",
                "review_note": (
                    "Quản trị viên duyệt trong phiên đăng nhập thật sau khi "
                    "xem bộ 40 câu Toán 7 HK1; nội dung do Codex chuẩn bị "
                    "theo ủy quyền và được quản trị viên xác nhận."
                ),
                "checklist": {
                    "scope": "TOAN7-FINAL-HK1-7A2",
                    "review_mode": "ADMIN_CONFIRMED_BATCH",
                    "question_content_checked": True,
                    "answer_and_scoring_checked": True,
                },
            }
        )
    return payload


def render_admin_assessment_question_review(
    st: Any, *, client: Any, reviewer_user_id: str
) -> None:
    st.subheader("Duyệt ngân hàng câu hỏi Toán 7 cuối HK1")
    if client is None:
        st.warning("Chưa kết nối dữ liệu câu hỏi.")
        return
    try:
        catalog = SupabaseAssessmentExamSettingsCatalog(
            client=client, user_id=reviewer_user_id
        )
        if not catalog.is_admin():
            st.error("Chỉ tài khoản quản trị mới được duyệt câu hỏi.")
            return
        questions = _pending_questions(client)
    except Exception as error:
        st.error(f"Không tải được hàng đợi câu hỏi: {error}")
        return

    if not questions:
        st.info("Không có câu hỏi Toán 7 HK1 đang chờ duyệt.")
        return
    st.write(f"Có {len(questions)} câu đang chờ duyệt trong phạm vi lớp 7A2.")
    by_code: dict[str, dict[str, Any]] = {}
    for question in questions:
        item = question.get("assessment_question_items")
        item = item[0] if isinstance(item, list) else item
        if isinstance(item, Mapping):
            by_code[str(item.get("question_code", ""))] = question
    selected_code = st.selectbox(
        "Xem câu hỏi", sorted(by_code), key="admin_math7_question_to_review"
    )
    selected = by_code[selected_code]
    st.write(
        {
            "Mã câu": selected_code,
            "Dạng": selected.get("question_type_code"),
            "Mức độ": selected.get("cognitive_level_code"),
            "Điểm": selected.get("default_score"),
            "Nội dung": selected.get("prompt_text"),
        }
    )
    st.caption("Đối chiếu đáp án, lời giải và YCCĐ trong phiếu rà soát trước khi duyệt.")
    checked = st.checkbox(
        "Tôi đã rà soát phiếu 40 câu và đồng ý duyệt bằng tài khoản quản trị của mình",
        key="admin_math7_question_review_confirm",
    )
    if st.button(
        "Duyệt 40 câu Toán 7 HK1",
        disabled=not checked or len(questions) != EXPECTED_QUESTION_COUNT,
        type="primary",
        key="admin_math7_question_review_submit",
    ):
        try:
            payload = _review_payload(questions, reviewer_user_id)
            result = client.table("assessment_question_reviews").insert(payload).execute()
            if len(_rows(result)) != EXPECTED_QUESTION_COUNT:
                raise ValueError("Chưa xác nhận được kết quả duyệt đủ 40 câu.")
        except Exception as error:
            st.error(f"Không thể duyệt câu hỏi: {error}")
        else:
            st.success("Đã ghi quyết định duyệt 40 câu hỏi.")
            st.rerun()
