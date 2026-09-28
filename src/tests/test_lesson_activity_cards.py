import pytest

from portal_v2.ui.lesson_activity_cards import add_approved_card, validate_card
from portal_v2.ui.lesson_activity_card_ai import build_ai_cards
from portal_v2.ui.lesson_slide_designer import build_presentation_html, new_draft, validate_draft
from portal_v2.ui.lesson_activity_card_authoring import select_catalog_lesson


LESSON_ID = "unit-math-kntt-g6-lesson-001"
EXCERPT_REF = "teacher_excerpt:checked"
QUESTION_ID = "a0000000-0000-4000-8000-000000000001"


def payload(question_id=QUESTION_ID):
    return {"cards": [
        {"kind": "TASK", "activity": "HINH_THANH_KIEN_THUC", "title": "Khám phá",
         "instruction": "Dùng số nguyên để giải thích ví dụ trong SGK.",
         "expected_product": "Lời giải cá nhân", "duration_minutes": 6,
         "source_refs": ["lesson:" + LESSON_ID, EXCERPT_REF, "requirement:REQ-1"]},
        {"kind": "QUICK_CHECK", "activity": "LUYEN_TAP", "title": "Kiểm tra nhanh",
         "instruction": "AI cố gắng thay nội dung câu hỏi đã duyệt", "expected_product": "Một đáp án",
         "duration_minutes": 3, "question_version_id": question_id,
         "source_refs": ["lesson:" + LESSON_ID, EXCERPT_REF, "question:" + question_id]},
    ]}


def propose(data=None):
    return build_ai_cards(data or payload(), lesson_id=LESSON_ID,
                          excerpt_ref=EXCERPT_REF, allowed_requirements={"REQ-1"},
                          approved_questions={QUESTION_ID: "Câu hỏi đã được duyệt?"})


def test_ai_uses_exact_approved_question_and_does_not_save_proposal():
    draft = new_draft()
    task, question = propose()
    assert question["instruction"] == "Câu hỏi đã được duyệt?"
    assert question["review_status"] == "AI_PROPOSED"
    with pytest.raises(ValueError, match="Giáo viên"):
        add_approved_card(draft, question)
    assert draft["activity_cards"] == []
    add_approved_card(draft, dict(question, review_status="TEACHER_APPROVED"))
    assert draft["activity_cards"][0]["question_version_id"] == QUESTION_ID
    assert task["kind"] == "TASK"


def test_ai_cannot_use_invented_question_or_requirement():
    data = payload("b0000000-0000-4000-8000-000000000002")
    with pytest.raises(ValueError, match="chưa duyệt"):
        propose(data)
    data = payload()
    data["cards"][0]["source_refs"].append("requirement:INVENTED")
    with pytest.raises(ValueError, match="nguồn không có"):
        propose(data)


def test_verified_sources_are_attached_when_ai_omits_citations():
    data = payload()
    data["cards"][0].pop("source_refs")
    data["cards"][1]["source_refs"] = []
    task, question = propose(data)
    assert task["source_refs"][:2] == ["lesson:" + LESSON_ID, EXCERPT_REF]
    assert question["source_refs"] == ["lesson:" + LESSON_ID, EXCERPT_REF,
                                       "question:" + QUESTION_ID]


def test_malformed_model_citations_fall_back_to_verified_sources():
    data = payload()
    data["cards"][0]["source_refs"] = "nguồn bài học"
    data["cards"][1]["source_refs"] = [None]
    task, question = propose(data)
    assert task["source_refs"] == ["lesson:" + LESSON_ID, EXCERPT_REF]
    assert question["source_refs"] == ["lesson:" + LESSON_ID, EXCERPT_REF,
                                       "question:" + QUESTION_ID]


def test_teacher_edits_stay_in_draft_when_new_ai_proposal_arrives():
    draft = new_draft()
    card = dict(propose()[0], review_status="TEACHER_APPROVED")
    card["instruction"] = "Giáo viên sửa nhiệm vụ cho lớp 6A2."
    add_approved_card(draft, card)
    _new_proposal = propose()[0]
    assert draft["activity_cards"][0]["instruction"] == "Giáo viên sửa nhiệm vụ cho lớp 6A2."


def test_presentation_hides_teacher_notes_and_unapproved_cards():
    draft = new_draft()
    card = dict(propose()[0], review_status="TEACHER_APPROVED",
                teacher_note="Đáp án và ghi chú riêng")
    add_approved_card(draft, card)
    html = build_presentation_html(draft)
    assert "Khám phá" in html
    assert "Đáp án và ghi chú riêng" not in html
    draft["activity_cards"].append(propose()[1])
    with pytest.raises(ValueError, match="giáo viên"):
        validate_draft(draft)


def test_legacy_slide_drafts_remain_importable():
    draft = new_draft()
    draft.pop("activity_cards")
    assert validate_draft(draft) is draft


def test_catalog_selection_prefills_lesson_fields_before_widgets():
    class FakeStreamlit:
        session_state = {}

    draft = new_draft()
    st = FakeStreamlit()
    select_catalog_lesson(st, draft, lesson_id=LESSON_ID,
                          title="Số nguyên", revision="r1")
    assert draft["source_lesson_id"] == LESSON_ID
    assert draft["lesson_title"] == "Số nguyên"
    assert st.session_state["slide_source_lesson_r1"] == LESSON_ID


def test_quick_check_requires_matching_question_source():
    with pytest.raises(ValueError, match="truy vết câu hỏi"):
        validate_card({"id": "one", "kind": "QUICK_CHECK", "activity": "LUYEN_TAP",
                       "review_status": "AI_PROPOSED", "title": "Câu hỏi",
                       "instruction": "Câu hỏi có sẵn", "expected_product": "Đáp án",
                       "teacher_note": "", "duration_minutes": 2,
                       "source_refs": ["lesson:" + LESSON_ID],
                       "question_version_id": QUESTION_ID})
