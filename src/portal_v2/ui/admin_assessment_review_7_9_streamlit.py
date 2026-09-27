"""Admin review queues for submitted Mathematics questions and assembled exams."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _rows(response: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in (getattr(response, "data", None) or [])
            if isinstance(row, Mapping)]


def _parent(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else {}
    return dict(value) if isinstance(value, Mapping) else {}


def _queue(client: Any, table: str, relation: str, grade: int,
           columns: str, status_column: str) -> list[dict[str, Any]]:
    # Apply grade and review status on the server BEFORE the result limit.
    return _rows(client.table(table).select(
        f"{columns},{relation}!inner(*)"
    ).eq(status_column, "PENDING_REVIEW")
        .eq(f"{relation}.grade_level", grade)
        .eq(f"{relation}.subject_code", "MATH")
        .order("created_at", desc=True).limit(201).execute())


def _choice(st: Any, key: str, label: str) -> tuple[str | None, str]:
    decision = st.selectbox(label, ("Chọn quyết định", "Phê duyệt", "Yêu cầu sửa", "Từ chối"),
                            key=f"{key}_decision")
    note = st.text_area("Nhận xét gửi giáo viên", key=f"{key}_note")
    return {"Phê duyệt": "APPROVED", "Yêu cầu sửa": "REVISION_REQUIRED",
            "Từ chối": "REJECTED"}.get(decision), note.strip()


def _question_details(st: Any, client: Any, version_id: str) -> None:
    for table, columns, title in (
        ("assessment_question_options", "option_code,option_text,is_correct", "Phương án"),
        ("assessment_question_statements", "statement_text,correct_value", "Các ý đúng/sai"),
        ("assessment_question_answers", "exact_answer_text,answer_explanation", "Đáp án"),
        ("assessment_question_solutions", "solution_text", "Lời giải"),
        ("assessment_question_scoring_steps", "step_description,step_score", "Thang điểm"),
        ("assessment_question_requirement_links", "requirement_code,link_role", "Yêu cầu cần đạt"),
        ("assessment_question_competency_links", "competency_code,link_role", "Năng lực"),
    ):
        rows = _rows(client.table(table).select(columns)
                     .eq("question_version_id", version_id).execute())
        if rows:
            st.markdown(f"**{title}**")
            st.dataframe(rows, hide_index=True, use_container_width=True)


def render_question_queue(st: Any, *, client: Any, reviewer_user_id: str) -> None:
    st.markdown("### Câu hỏi đang chờ duyệt")
    grade = st.selectbox("Lớp của câu hỏi", (7, 8, 9), key="admin_queue_question_grade")
    try:
        rows = _queue(client, "assessment_question_versions", "assessment_question_items",
                      grade, "question_version_id,question_type_code,cognitive_level_code,"
                      "prompt_text,default_score,created_at", "review_status")
    except Exception as exc:
        st.error(f"Không đọc được câu hỏi lớp {grade}: {exc}")
        return
    if not rows:
        st.info(f"Không có câu hỏi Toán {grade} ở trạng thái chờ duyệt mà tài khoản này nhìn thấy.")
        return
    if len(rows) > 200:
        st.warning("Có hơn 200 câu chờ duyệt. Đang hiển thị 200 câu mới nhất.")
    visible = rows[:200]
    st.caption(f"{len(visible)} câu hỏi đang hiển thị · PENDING_REVIEW · Lớp {grade}")
    choices = {str(row["question_version_id"]): row for row in visible}
    selected = st.selectbox("Chọn câu hỏi để kiểm tra", list(choices),
                            format_func=lambda key: (
                                f"{_parent(choices[key].get('assessment_question_items')).get('question_code', '')}"
                                f" · {str(choices[key].get('prompt_text', ''))[:95]}"),
                            key=f"admin_queue_question_{grade}")
    row = choices[selected]
    parent = _parent(row.get("assessment_question_items"))
    st.write({"Mã câu": parent.get("question_code"), "Lớp": grade,
              "Dạng": row.get("question_type_code"), "Mức độ": row.get("cognitive_level_code"),
              "Điểm": row.get("default_score"), "Chủ sở hữu": parent.get("owner_user_id")})
    st.markdown("**Nội dung câu hỏi**")
    st.markdown(str(row.get("prompt_text") or ""))
    try:
        _question_details(st, client, selected)
    except Exception as exc:
        st.error(f"Chưa đọc đủ đáp án và liên kết; không thể duyệt: {exc}")
        return
    if str(parent.get("owner_user_id")) == reviewer_user_id:
        st.warning("Câu hỏi thuộc chính tài khoản này. Cần ADMIN khác để duyệt.")
        return
    decision, note = _choice(st, f"review_question_{selected}", "Quyết định về câu hỏi")
    checked = st.checkbox("Đã kiểm tra nội dung, đáp án, lời giải và thang điểm",
                          key=f"review_question_{selected}_checked")
    if st.button("Ghi quyết định duyệt câu hỏi", type="primary",
                 disabled=not (checked and decision and (note or decision == "APPROVED")),
                 key=f"review_question_{selected}_submit"):
        try:
            client.table("assessment_question_reviews").insert({
                "question_version_id": selected, "reviewer_user_id": reviewer_user_id,
                "decision": decision, "review_note": note,
                "checklist": {"question_content_checked": True,
                              "answer_and_scoring_checked": True},
            }).execute()
        except Exception as exc:
            st.error(f"Không thể ghi quyết định: {exc}")
        else:
            st.success("Đã ghi quyết định duyệt câu hỏi.")
            st.rerun()


def render_exam_queue(st: Any, *, client: Any, reviewer_user_id: str) -> None:
    st.markdown("### Đề kiểm tra đã lắp ráp đang chờ duyệt")
    grade = st.selectbox("Lớp của đề kiểm tra", (7, 8, 9), key="admin_queue_exam_grade")
    try:
        rows = _queue(client, "assessment_exam_versions", "assessment_exams", grade,
                      "exam_version_id,exam_title,version_number,assembly_status,"
                      "duration_minutes,total_score,created_at", "assembly_status")
    except Exception as exc:
        st.error(f"Không đọc được đề kiểm tra lớp {grade}: {exc}")
        return
    if not rows:
        st.info(f"Không có bản đề Toán {grade} ở trạng thái chờ duyệt mà tài khoản này nhìn thấy.")
        st.caption("Câu hỏi gửi duyệt xuất hiện ở mục Câu hỏi; đề chỉ xuất hiện sau khi lắp ráp và gửi duyệt bản đề.")
        return
    if len(rows) > 200:
        st.warning("Có hơn 200 đề chờ duyệt. Đang hiển thị 200 đề mới nhất.")
    visible = rows[:200]
    st.caption(f"{len(visible)} bản đề đang hiển thị · PENDING_REVIEW · Lớp {grade}")
    choices = {str(row["exam_version_id"]): row for row in visible}
    selected = st.selectbox("Chọn đề để kiểm tra", list(choices),
                            format_func=lambda key: f"{choices[key]['exam_title']} · v{choices[key]['version_number']}",
                            key=f"admin_queue_exam_{grade}")
    row = choices[selected]
    parent = _parent(row.get("assessment_exams"))
    st.write({"Mã đề": parent.get("exam_code"), "Tên đề": row.get("exam_title"),
              "Lớp": grade, "Chủ sở hữu": parent.get("owner_user_id"),
              "Thời gian (phút)": row.get("duration_minutes"), "Tổng điểm": row.get("total_score")})
    try:
        questions = _rows(client.table("assessment_exam_questions").select(
            "display_number,assigned_score,question_version_id,"
            "assessment_question_versions(prompt_text,question_type_code)"
        ).eq("exam_version_id", selected).order("display_number").limit(201).execute())
    except Exception as exc:
        st.error(f"Chưa đọc được các câu trong đề; không thể duyệt: {exc}")
        return
    if not questions or len(questions) > 200:
        st.error("Đề không có câu hoặc vượt giới hạn hiển thị 200 câu; cần kiểm tra trước khi duyệt.")
        return
    st.dataframe([{"Câu": q["display_number"], "Dạng": _parent(q.get("assessment_question_versions")).get("question_type_code"),
                   "Nội dung": _parent(q.get("assessment_question_versions")).get("prompt_text"),
                   "Điểm": q["assigned_score"]} for q in questions],
                 hide_index=True, use_container_width=True)
    question_by_number = {int(q["display_number"]): q for q in questions}
    number = st.selectbox("Xem đáp án, lời giải và thang điểm của câu",
                          list(question_by_number), key=f"review_exam_{selected}_question")
    chosen_question = question_by_number[number]
    st.markdown(str(_parent(chosen_question.get("assessment_question_versions")).get("prompt_text") or ""))
    try:
        _question_details(st, client, str(chosen_question["question_version_id"]))
    except Exception as exc:
        st.error(f"Chưa đọc đủ đáp án câu {number}; không thể duyệt: {exc}")
        return
    if str(parent.get("owner_user_id")) == reviewer_user_id:
        st.warning("ADMIN không được duyệt bản đề do chính tài khoản này tạo.")
        return
    decision, note = _choice(st, f"review_exam_{selected}", "Quyết định về đề")
    checked = st.checkbox("Đã kiểm tra ma trận, toàn bộ câu hỏi, đáp án và thang điểm",
                          key=f"review_exam_{selected}_checked")
    if st.button("Ghi quyết định duyệt đề", type="primary",
                 disabled=not (checked and decision and (note or decision == "APPROVED")),
                 key=f"review_exam_{selected}_submit"):
        try:
            client.table("assessment_exam_reviews").insert({
                "exam_version_id": selected, "reviewer_user_id": reviewer_user_id,
                "decision": decision, "review_note": note,
                "checklist": {"matrix_checked": True, "questions_and_answers_checked": True,
                              "scoring_checked": True},
            }).execute()
        except Exception as exc:
            st.error(f"Không thể ghi quyết định duyệt đề: {exc}")
        else:
            st.success("Đã ghi quyết định duyệt đề kiểm tra.")
            st.rerun()
