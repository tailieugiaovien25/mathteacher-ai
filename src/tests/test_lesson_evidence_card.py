import pytest

from portal_v2.ui.lesson_activity_cards import make_card
from portal_v2.ui.lesson_classroom_tools import add_tool
from portal_v2.ui.lesson_evidence_card import add_evidence_card, record_evidence, validate_evidence_card
from portal_v2.ui.lesson_slide_designer import build_presentation_html, new_draft, validate_draft


def test_multiple_sources_record_real_teacher_observations():
    draft = new_draft()
    tool = add_tool(draft, activity="MO_DAU", kind="LUCKY_WHEEL", session_id="owner-session", title="Ôn tập")
    quick = make_card(kind="QUICK_CHECK", activity="MO_DAU", title="Câu nhanh",
                      instruction="2 + 2 = ?", expected_product="4", source_refs=["question:q"],
                      question_version_id="q", review_status="TEACHER_APPROVED")
    draft["activity_cards"].append(quick)
    evidence = add_evidence_card(draft, activity="MO_DAU", title="Quan sát lớp",
                                 source_ids=[tool["id"], quick["id"], "TEACHER_OBSERVATION"])
    record_evidence(evidence, source_id=tool["id"], participated=30, completed=25,
                    needs_help=3, note="Một nhóm cần gợi ý.")
    assert validate_draft(draft) is draft
    html = build_presentation_html(draft)
    assert "30 tham gia, 25 hoàn thành, 3 cần hỗ trợ" in html
    assert "Một nhóm cần gợi ý." not in html


def test_card_rejects_wrong_activity_and_bad_counts():
    draft = new_draft()
    tool = add_tool(draft, activity="LUYEN_TAP", kind="GAMESHOW", session_id="s", title="Game")
    with pytest.raises(ValueError, match="không còn thuộc hoạt động"):
        add_evidence_card(draft, activity="MO_DAU", title="Ghi nhận", source_ids=[tool["id"]])
    card = add_evidence_card(draft, activity="MO_DAU", title="Ghi nhận", source_ids=["TEACHER_OBSERVATION"])
    with pytest.raises(ValueError, match="vượt số tham gia"):
        record_evidence(card, source_id="TEACHER_OBSERVATION", participated=5,
                        completed=6, needs_help=0, note="")
    assert card["entries"] == []
    record_evidence(card, source_id="TEACHER_OBSERVATION", participated=5,
                    completed=4, needs_help=1, note="")
    card["entries"][0]["completed"] = True
    with pytest.raises(ValueError, match="Số lượng"):
        validate_evidence_card(card)
