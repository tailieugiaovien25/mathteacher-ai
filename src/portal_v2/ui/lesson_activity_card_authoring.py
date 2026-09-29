"""Teacher controlled card authoring backed by reviewed lesson sources."""

from __future__ import annotations

import os
from uuid import uuid4

from portal_v2.ui.lesson_activity_card_ai import request_ai_cards
from portal_v2.ui.lesson_activity_cards import add_approved_card, validate_card
from portal_v2.ui.lesson_slide_designer import ACTIVITIES
from portal_v2.ui.lesson_textbook_sources import render_lesson_source_picker


def _rows(query) -> list[dict]:
    data = query.execute().data
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError("Nguồn dữ liệu trả về danh sách không hợp lệ.")
    return data


def load_lesson_catalog(client, *, grade: int, subject: str) -> list[dict]:
    grades = _rows(client.table("grades").select("grade_id")
                  .eq("grade_number", grade).eq("status", "ACTIVE").limit(2))
    subjects = _rows(client.table("subjects").select("subject_id,code,name").limit(100))
    subject_codes = {"Toán": {"math", "toan", "toán"},
                     "Tiếng Anh": {"english", "tieng anh", "tiếng anh"}}[subject]
    subject_ids = [row["subject_id"] for row in subjects if
                   str(row.get("code", "")).casefold() in subject_codes or
                   str(row.get("name", "")).casefold() in subject_codes]
    if not grades or not subject_ids:
        return []
    books = _rows(client.table("textbook_catalog")
                  .select("textbook_id,title,grade_id,subject_id")
                  .in_("grade_id", [row["grade_id"] for row in grades])
                  .in_("subject_id", subject_ids).eq("status", "ACTIVE").limit(100))
    if len(books) >= 100:
        raise ValueError("Danh mục sách vượt giới hạn; cần phân trang.")
    return books


def load_reviewed_requirements(client, lesson_id: str) -> list[dict]:
    evidence = _rows(client.rpc("get_textbook_unit_requirement_recommendations", {
        "target_textbook_unit_ids": [lesson_id],
    }))
    codes = {str(row["requirement_code"]) for row in evidence
             if row.get("textbook_unit_id") == lesson_id and row.get("requirement_code")}
    if not codes:
        return []
    if len(codes) > 40:
        raise ValueError("Quá nhiều YCCĐ; cần kiểm tra phạm vi bài.")
    requirements = _rows(client.table("assessment_learning_requirements")
                         .select("requirement_code,requirement_text")
                         .in_("requirement_code", sorted(codes))
                         .eq("status", "ACTIVE").limit(41))
    if len(requirements) > 40 or {row["requirement_code"] for row in requirements} != codes:
        raise ValueError("Không đọc đủ YCCĐ đã liên kết với bài học.")
    return requirements


def load_approved_questions(client, *, user_id: str, grade: int,
                            book_id: str, lesson_id: str) -> dict[str, str]:
    """Offer only teacher-owned approved questions with exact lesson metadata."""
    items = _rows(client.table("assessment_question_items")
                  .select("question_id").eq("owner_user_id", user_id)
                  .eq("grade_level", grade).limit(501))
    if len(items) >= 501:
        raise ValueError("Ngân hàng câu hỏi cần phân trang trước khi chọn câu.")
    if not items:
        return {}
    versions = _rows(client.table("assessment_question_versions")
                     .select("question_version_id,question_id,prompt_text,metadata,review_status")
                     .in_("question_id", [row["question_id"] for row in items])
                     .eq("review_status", "APPROVED").limit(501))
    if len(versions) >= 501:
        raise ValueError("Danh sách câu hỏi đã duyệt cần phân trang.")
    result = {}
    for version in versions:
        metadata = version.get("metadata") or {}
        scope = metadata.get("content_scope") or {}
        if (str(metadata.get("textbook_id")) == book_id and
                lesson_id in (scope.get("catalog_unit_ids") or [])):
            result[str(version["question_version_id"])] = str(version["prompt_text"])
    return result


def select_catalog_lesson(st, draft: dict, *, lesson_id: str, title: str,
                          revision: str) -> None:
    """Write the verified catalog selection before text widgets are rendered."""
    draft["source_lesson_id"] = lesson_id
    draft["lesson_title"] = title
    st.session_state["slide_source_lesson_" + revision] = lesson_id
    st.session_state["slide_lesson_title_" + revision] = title


def load_question_display(client, question_version_id: str) -> list[dict]:
    """Snapshot visible choices from a reviewed version without reading correct answers."""
    versions = _rows(client.table("assessment_question_versions")
                     .select("question_type_code").eq("question_version_id", question_version_id)
                     .eq("review_status", "APPROVED").limit(1))
    if len(versions) != 1:
        raise ValueError("Câu hỏi đã chọn không còn ở trạng thái duyệt.")
    kind = versions[0]["question_type_code"]
    if kind == "MULTIPLE_CHOICE":
        rows = _rows(client.table("assessment_question_options")
                     .select("option_code,option_text,sequence_number")
                     .eq("question_version_id", question_version_id)
                     .order("sequence_number").limit(13))
        display = [{"label": str(row["option_code"]), "text": str(row["option_text"])} for row in rows]
    elif kind == "TRUE_FALSE":
        rows = _rows(client.table("assessment_question_statements")
                     .select("statement_code,statement_text,sequence_number")
                     .eq("question_version_id", question_version_id)
                     .order("sequence_number").limit(13))
        display = [{"label": str(row["statement_code"]), "text": str(row["statement_text"])} for row in rows]
    else:
        return []
    if not display or len(display) > 12:
        raise ValueError("Câu hỏi chưa có đủ phương án để trình chiếu.")
    return display


def render_card_authoring(st, *, draft: dict, client, user_id: str,
                          revision: str) -> None:
    with st.expander("Chọn bài SGK · AI tạo thẻ hoạt động", expanded=True):
        _render_approved_cards(st, draft, client=client)
        st.caption("Dùng bài SGK đã đăng ký; đoạn kiến thức phải do giáo viên kiểm tra trước khi gửi AI.")
        try:
            books = load_lesson_catalog(client, grade=draft["grade"], subject=draft["subject"])
            if not books:
                st.info("Chưa có danh mục sách ACTIVE của môn và lớp này.")
                return
            book = st.selectbox("Sách giáo khoa", books, format_func=lambda row: row["title"],
                                key=f"card_book_{draft['subject']}_{draft['grade']}")
            lessons = _rows(client.table("textbook_units")
                            .select("textbook_unit_id,title,unit_type")
                            .eq("textbook_id", book["textbook_id"]).eq("status", "ACTIVE")
                            .eq("unit_type", "LESSON").order("display_order").limit(501))
            if len(lessons) >= 501:
                raise ValueError("Danh mục bài học vượt giới hạn hiển thị.")
            if not lessons:
                st.info("Sách chưa có danh mục bài học ACTIVE.")
                return
            lesson = st.selectbox("Bài học", lessons,
                                  format_func=lambda row: row["title"],
                                  key="card_lesson_" + str(book["textbook_id"]))
            lesson_id = str(lesson["textbook_unit_id"])
            if st.button("Dùng bài SGK này cho bài giảng", key="card_use_lesson_" + lesson_id):
                if (draft.get("activity_cards") and draft.get("verified_source") and
                        draft["verified_source"].get("lesson_id") != lesson_id):
                    st.error("Bài giảng đã có thẻ của bài SGK khác. Bỏ các thẻ đó trước khi đổi bài.")
                else:
                    next_revision = str(uuid4())
                    select_catalog_lesson(st, draft, lesson_id=lesson_id,
                                          title=str(lesson["title"]), revision=next_revision)
                    st.session_state["lesson_slide_revision"] = next_revision
                    st.rerun()
            try:
                requirements = load_reviewed_requirements(client, lesson_id)
            except Exception as exc:
                st.warning(f"Chưa lấy được YCCĐ đã rà soát: {exc}")
                requirements = []
            selected_codes = st.multiselect("YCCĐ đề xuất để giáo viên chọn",
                [row["requirement_code"] for row in requirements],
                format_func=lambda code: next((row["requirement_text"] for row in requirements
                                               if row["requirement_code"] == code), code),
                key="card_requirements_" + lesson_id)
            requirements = [row for row in requirements
                            if row["requirement_code"] in selected_codes]
            questions = load_approved_questions(client, user_id=user_id, grade=draft["grade"],
                                                book_id=str(book["textbook_id"]), lesson_id=lesson_id)
        except Exception as exc:
            st.error(f"Chưa đọc được nguồn bài học: {exc}")
            return
        st.caption(f"Câu hỏi đã duyệt gắn đúng bài: {len(questions)}. "
                   "Nếu không có, xưởng chỉ tạo thẻ Giao nhiệm vụ.")
        try:
            excerpt, excerpt_ref = render_lesson_source_picker(
                st, client=client, user_id=user_id, book_id=str(book["textbook_id"]),
                lesson_id=lesson_id, lesson_title=str(lesson["title"]))
        except Exception as exc:
            st.error(f"Chưa đọc được kho nội dung SGK: {exc}")
            return
        source_identity = (lesson_id, excerpt_ref, tuple(sorted(selected_codes)),
                           tuple(sorted(questions)))
        if st.session_state.get("card_proposal_identity") != source_identity:
            st.session_state["card_proposals"] = []
        if st.button("AI đề xuất thẻ hoạt động", key="card_generate"):
            if not excerpt_ref or len(excerpt.strip()) < 80:
                st.error("Bài học cần một đoạn kiến thức đã lưu và giáo viên đối chiếu trước khi tạo thẻ.")
            else:
                try:
                    try:
                        api_key = str(st.secrets.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", ""))
                    except Exception:
                        api_key = str(os.getenv("GEMINI_API_KEY", ""))
                    proposals = request_ai_cards(
                        api_key=api_key, lesson_title=lesson["title"], lesson_id=lesson_id,
                        excerpt=excerpt.strip(), excerpt_ref=excerpt_ref,
                        requirements=requirements, approved_questions=questions)
                    st.session_state["card_proposals"] = proposals
                    st.session_state["card_proposal_identity"] = source_identity
                except Exception as exc:
                    st.error(f"AI chưa đề xuất được thẻ: {exc}")
        proposals = st.session_state.get("card_proposals", [])
        if st.session_state.get("card_proposal_identity") != source_identity:
            proposals = []
        for proposal in proposals:
            card_id = proposal["id"]
            with st.container(border=True):
                st.markdown("**AI đề xuất: " + ("Giao nhiệm vụ" if proposal["kind"] == "TASK" else "Kiểm tra nhanh") + "**")
                st.caption("Nguồn: " + ", ".join(proposal["source_refs"]))
                title = st.text_input("Tên thẻ", value=proposal["title"], max_chars=180,
                                      key="card_title_" + card_id)
                activity = st.selectbox("Đặt tại hoạt động", [key for key, _ in ACTIVITIES],
                    index=[key for key, _ in ACTIVITIES].index(proposal["activity"]),
                    format_func=dict(ACTIVITIES).get, key="card_activity_" + card_id)
                instruction = st.text_area("Nhiệm vụ / câu hỏi", value=proposal["instruction"],
                    disabled=proposal["kind"] == "QUICK_CHECK", max_chars=3000,
                    key="card_instruction_" + card_id)
                if proposal["kind"] == "QUICK_CHECK":
                    st.caption("Câu hỏi đã duyệt được giữ nguyên. Sửa câu hỏi trong Ngân hàng câu hỏi.")
                product = st.text_input("Sản phẩm học tập", value=proposal["expected_product"],
                    max_chars=500, key="card_product_" + card_id)
                duration = st.number_input("Thời lượng (phút)", min_value=1, max_value=45,
                    value=proposal["duration_minutes"], step=1, key="card_duration_" + card_id)
                teacher_note = st.text_area("Ghi chú riêng cho giáo viên", value="",
                    max_chars=1000, key="card_note_" + card_id)
                if st.button("Duyệt và thêm vào bài", key="card_approve_" + card_id):
                    try:
                        previous_source = draft.get("verified_source")
                        if previous_source and draft.get("activity_cards") and (previous_source.get("lesson_id") != lesson_id or
                                                previous_source.get("textbook_id") != str(book["textbook_id"])):
                            raise ValueError("Bài giảng đang gắn bài SGK khác; tạo bản nháp riêng cho bài này.")
                        approved = dict(proposal, title=title, activity=activity,
                                        instruction=instruction, expected_product=product,
                                        duration_minutes=int(duration), teacher_note=teacher_note,
                                        review_status="TEACHER_APPROVED")
                        if approved["kind"] == "QUICK_CHECK":
                            approved["question_display"] = load_question_display(
                                client, approved["question_version_id"])
                        validate_card(approved, allowed_sources={"lesson:" + lesson_id, excerpt_ref,
                            *("requirement:" + code for code in selected_codes),
                            *("question:" + key for key in questions)},
                            allowed_questions=set(questions))
                        add_approved_card(draft, approved)
                        draft["verified_source"] = {"textbook_id": str(book["textbook_id"]),
                                                    "lesson_id": lesson_id}
                        draft.setdefault("source_evidence", {})[excerpt_ref] = excerpt.strip()
                        st.session_state["card_proposals"] = [p for p in proposals if p["id"] != card_id]
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Chưa thêm được thẻ: {exc}")


def _render_approved_cards(st, draft: dict, *, client) -> None:
    if not draft.get("activity_cards"):
        return
    st.subheader("Thẻ đã được giáo viên duyệt")
    for card in list(draft["activity_cards"]):
        with st.expander(card["title"], expanded=False):
            st.caption("Nguồn: " + ", ".join(card["source_refs"]))
            if card["kind"] == "QUICK_CHECK" and "question_display" not in card:
                if st.button("Bổ sung phương án từ câu hỏi đã duyệt", key="card_display_" + card["id"]):
                    try:
                        card["question_display"] = load_question_display(client, card["question_version_id"])
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Chưa bổ sung được phương án: {exc}")
            with st.form("card_edit_" + card["id"]):
                title = st.text_input("Tên thẻ", value=card["title"], max_chars=180)
                instruction = st.text_area("Nội dung", value=card["instruction"],
                    max_chars=3000, disabled=card["kind"] == "QUICK_CHECK")
                product = st.text_input("Sản phẩm", value=card["expected_product"], max_chars=500)
                note = st.text_area("Ghi chú giáo viên", value=card["teacher_note"], max_chars=1000)
                save = st.form_submit_button("Lưu chỉnh sửa")
            if save:
                updated = dict(card, title=title, instruction=instruction,
                               expected_product=product, teacher_note=note)
                try:
                    validate_card(updated)
                    card.update(updated)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if st.button("Bỏ thẻ khỏi bài", key="card_remove_" + card["id"]):
                draft["activity_cards"].remove(card)
                st.rerun()
