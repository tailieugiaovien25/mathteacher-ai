from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from portal_v2.ui.admin_review_selection_controls import (
    clear_review_selection,
    render_review_selection_controls,
)
from portal_v2.ui.assessment_exam_settings_streamlit import (
    SupabaseAssessmentExamSettingsCatalog,
)


GRADES = (6, 7, 8, 9)


def _rows(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    return [dict(row) for row in data or [] if isinstance(row, Mapping)]


def _item(question: dict[str, Any]) -> Mapping[str, Any]:
    relation = question.get("assessment_question_items")
    item = relation[0] if isinstance(relation, list) else relation
    if not isinstance(item, Mapping):
        raise ValueError("Không xác định được câu hỏi gốc.")
    return item


def _pending_questions(client: Any) -> list[dict[str, Any]]:
    return _rows(
        client.table("assessment_question_versions")
        .select(
            "question_version_id,question_type_code,cognitive_level_code,"
            "prompt_text,default_score,version_number,"
            "assessment_question_items!inner("
            "question_code,owner_user_id,subject_code,grade_level,lifecycle_status)"
        )
        .eq("review_status", "PENDING_REVIEW")
        .eq("assessment_question_items.subject_code", "MATH")
        .in_("assessment_question_items.grade_level", list(GRADES))
        .order("created_at")
        .execute()
    )


def _code(question: dict[str, Any]) -> str:
    return str(_item(question).get("question_code", "")).strip()


def _grade(question: dict[str, Any]) -> int:
    return int(_item(question).get("grade_level") or 0)


def _label(question: dict[str, Any]) -> str:
    code = _code(question) or str(question["question_version_id"])[:8]
    prompt = str(question.get("prompt_text") or "").replace("\n", " ").strip()
    if len(prompt) > 95:
        prompt = prompt[:92].rstrip() + "…"
    return f"{code} · {prompt}"


def _approve(
    st: Any,
    *,
    client: Any,
    questions: list[dict[str, Any]],
    reviewer_user_id: str,
    review_mode: str,
    selection_key_prefix: str,
) -> None:
    if not questions:
        st.warning("Chưa chọn câu hỏi để duyệt.")
        return
    payload = [
        {
            "question_version_id": row["question_version_id"],
            "reviewer_user_id": reviewer_user_id,
            "decision": "APPROVED",
            "review_note": "ADMIN duyệt trên trang duyệt câu hỏi môn Toán.",
            "checklist": {
                "review_mode": review_mode,
                "question_content_checked": True,
                "answer_and_scoring_checked": True,
            },
        }
        for row in questions
    ]
    try:
        result = client.table("assessment_question_reviews").insert(payload).execute()
        if len(_rows(result)) != len(payload):
            raise ValueError(
                f"Chưa xác nhận được kết quả duyệt đủ {len(payload)} câu."
            )
    except Exception as error:
        st.error(f"Không thể duyệt câu hỏi: {error}")
    else:
        clear_review_selection(st, key_prefix=selection_key_prefix)
        st.success(f"Đã duyệt {len(payload)} câu hỏi.")
        st.rerun()


def _render_grade(
    st: Any,
    *,
    client: Any,
    reviewer_user_id: str,
    questions: list[dict[str, Any]],
    grade: int,
) -> None:
    rows = [row for row in questions if _grade(row) == grade]
    st.info(f"Toán {grade}: {len(rows)} câu hỏi đang chờ duyệt.")

    if not rows:
        return

    by_id = {str(row["question_version_id"]): row for row in rows}
    key_prefix = f"admin_math_question_review_g{grade}"

    selected_ids = render_review_selection_controls(
        st,
        item_ids=list(by_id),
        label_for_id=lambda qid: _label(by_id[qid]),
        key_prefix=key_prefix,
        noun="câu",
    )

    st.dataframe(
        [
            {
                "Mã câu": _code(row),
                "Dạng": row.get("question_type_code"),
                "Mức độ": row.get("cognitive_level_code"),
                "Điểm": row.get("default_score"),
                "Câu hỏi": row.get("prompt_text"),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )

    preview_id = st.selectbox(
        "Kiểm tra một câu trong danh sách",
        options=list(by_id),
        format_func=lambda qid: _label(by_id[qid]),
        key=f"{key_prefix}_preview",
    )
    preview = by_id[preview_id]
    st.write(
        {
            "Mã câu": _code(preview),
            "Dạng": preview.get("question_type_code"),
            "Mức độ": preview.get("cognitive_level_code"),
            "Điểm": preview.get("default_score"),
            "Nội dung": preview.get("prompt_text"),
        }
    )

    confirmed = st.checkbox(
        "Tôi đã rà soát nội dung, đáp án và thang điểm của phạm vi sẽ duyệt",
        key=f"{key_prefix}_confirm",
    )
    selected_rows = [by_id[qid] for qid in selected_ids if qid in by_id]

    a, b, c = st.columns(3)
    if a.button(
        "Duyệt câu đang xem",
        disabled=not confirmed,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_one",
    ):
        _approve(
            st,
            client=client,
            questions=[preview],
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_SINGLE",
            selection_key_prefix=key_prefix,
        )

    if b.button(
        f"Duyệt nhóm ({len(selected_rows)})",
        disabled=not confirmed or not selected_rows,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_group",
    ):
        _approve(
            st,
            client=client,
            questions=selected_rows,
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_GROUP",
            selection_key_prefix=key_prefix,
        )

    if c.button(
        f"Duyệt tất cả ({len(rows)})",
        disabled=not confirmed,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_all",
    ):
        _approve(
            st,
            client=client,
            questions=rows,
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_ALL_VISIBLE",
            selection_key_prefix=key_prefix,
        )


def render_admin_assessment_question_review(
    st: Any, *, client: Any, reviewer_user_id: str
) -> None:
    st.subheader("Duyệt câu hỏi môn Toán")
    st.caption(
        "Chọn từng câu, một nhóm hoặc tất cả câu đang hiển thị; "
        "mọi quyết định vẫn đi qua bảng review và trigger governance hiện hành."
    )
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

    tabs = st.tabs([f"Câu hỏi Toán {grade}" for grade in GRADES])
    for tab, grade in zip(tabs, GRADES):
        with tab:
            _render_grade(
                st,
                client=client,
                reviewer_user_id=reviewer_user_id,
                questions=questions,
                grade=grade,
            )
