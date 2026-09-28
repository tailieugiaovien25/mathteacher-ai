from portal_v2.ui.assessment_workspace_hub import (
    ASSESSMENT_EXPERIMENTAL_DESTINATIONS,
    ASSESSMENT_LEGACY_DESTINATIONS,
    ASSESSMENT_PRIMARY_DESTINATIONS,
    open_assessment_destination,
)
from portal_v2.ui.workspace_navigation import route_from_label, visible_teacher_labels
from scripts.teacher_portal.app import select_portal_page
from portal_v2.ui.assessment_content_question_streamlit import _candidate_from_saved_question


def test_hub_destinations_keep_legacy_routes_without_duplicates():
    targets = [target for _, target, _ in (
        *ASSESSMENT_PRIMARY_DESTINATIONS, *ASSESSMENT_EXPERIMENTAL_DESTINATIONS
    )]
    assert len(targets) == len(ASSESSMENT_LEGACY_DESTINATIONS) + 1
    assert len(set(targets)) == len(ASSESSMENT_LEGACY_DESTINATIONS)
    assert all(route_from_label(target).space == "teacher" for target in targets)
    assert "Đề kiểm tra" in visible_teacher_labels()
    assert {"Tạo đề kiểm tra Toán 6", "Tạo đề kiểm tra Toán 6–9", "Xưởng câu hỏi"} <= {
        target for _, target, _ in ASSESSMENT_EXPERIMENTAL_DESTINATIONS
    }


def test_hub_navigation_only_queues_a_request():
    state = {"portal_page": "Đề kiểm tra"}
    select_portal_page(state, "Tạo đề kiểm tra")
    assert state == {"portal_page": "Đề kiểm tra",
                     "portal_navigation_request": "Tạo đề kiểm tra"}


def test_teacher_authoring_opens_existing_editor_directly():
    class FakeStreamlit:
        session_state = {}

        def rerun(self):
            self.reran = True

    st = FakeStreamlit()
    targets = []
    open_assessment_destination(st, label="Giáo viên tạo câu hỏi",
                                target="AI xây dựng ngân hàng câu hỏi",
                                navigate=targets.append)
    assert st.session_state["content_ai_workspace_view"] == "Soạn câu hỏi mới"
    assert targets == ["AI xây dựng ngân hàng câu hỏi"]
    assert st.reran


def test_saved_question_prefills_editable_answer_and_scoring():
    candidate = _candidate_from_saved_question({"prompt_text": "Tính 1+1"}, {
        "answers": [{"exact_answer_text": "2"}],
        "solutions": [{"solution_text": "1+1=2", "is_primary": True}],
        "options": [], "statements": [],
        "scoring": [{"step_description": "Lập luận đúng", "step_score": 1,
                     "sequence_number": 1}],
    })
    assert candidate["prompt_text"] == "Tính 1+1"
    assert candidate["answer"] == "2"
    assert candidate["solution"] == "1+1=2"
    assert candidate["scoring_steps"] == [{"description": "Lập luận đúng", "score": 1.0}]
