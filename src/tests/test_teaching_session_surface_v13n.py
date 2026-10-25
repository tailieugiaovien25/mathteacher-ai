from __future__ import annotations

from ai_kernel.teaching_classroom import ClassroomPhase, TeachingClassroomOrchestrator
from ai_kernel.teaching_classroom_executor import StreamlitClassroomRuntime
from ai_kernel.teaching_assistant import TeachingAssistantMode
from ai_kernel.teaching_session import TeachingSessionStatus
from ai_kernel.teaching_session_surface import (
    SESSION_CONTRACT_VERSION,
    SESSION_KEY,
    SESSION_VERSION_KEY,
    build_teaching_session_activities,
    get_or_create_teaching_session,
    plan_for_single_action,
    reset_teaching_session,
    session_status_label,
)


def draft():
    return {
        "source_lesson_id": "lesson-7",
        "slides": [
            {"id": "s1", "activity": "MO_DAU", "title": "Khởi động"},
            {"id": "s2", "activity": "HINH_THANH_KIEN_THUC", "title": "Khám phá"},
            {"id": "s3", "activity": "LUYEN_TAP", "title": "Luyện tập"},
            {"id": "s4", "activity": "VAN_DUNG", "title": "Vận dụng"},
        ],
        "activity_cards": [
            {
                "id": "c1", "kind": "TASK", "activity": "MO_DAU", "title": "Ôn bài cũ",
                "instruction": "Tìm nhanh một ví dụ.", "expected_product": "Một câu trả lời",
                "source_refs": ["sgk:1"], "duration_minutes": 1, "review_status": "TEACHER_APPROVED",
            },
            {
                "id": "c2", "kind": "QUICK_CHECK", "activity": "LUYEN_TAP", "title": "Kiểm tra nhanh",
                "instruction": "Chọn đáp án.", "expected_product": "Đáp án",
                "source_refs": ["question:q1"], "question_version_id": "q1",
                "question_display": [{"label": "A", "text": "2 + 2 = ?"}],
                "duration_minutes": 2, "review_status": "TEACHER_APPROVED",
            },
        ],
    }


def test_builds_four_canonical_activities_and_scopes_tools():
    items = build_teaching_session_activities(draft())
    assert len(items) == 4
    assert [item.phase for item in items] == [
        ClassroomPhase.OPENING,
        ClassroomPhase.NEW_KNOWLEDGE,
        ClassroomPhase.PRACTICE,
        ClassroomPhase.APPLICATION,
    ]
    assert items[0].selected_slide_id == "s1"
    assert items[2].question == "2 + 2 = ?"
    assert "classroom.quiz.display" in items[2].allowed_tools
    assert "classroom.quiz.display" not in items[1].allowed_tools


def test_session_manager_is_singleton_within_streamlit_state():
    state = {}
    a = get_or_create_teaching_session(state)
    b = get_or_create_teaching_session(state)
    assert a is b
    assert isinstance(a.executor.runtime, StreamlitClassroomRuntime)
    assert state[SESSION_VERSION_KEY] == SESSION_CONTRACT_VERSION
    assert state[SESSION_KEY] is a

    c = reset_teaching_session(state)
    assert c is not a
    assert c.status is TeachingSessionStatus.PREPARING


def test_plan_for_single_action_preserves_scope():
    state = {}
    manager = get_or_create_teaching_session(state)
    manager.start(lesson_id="lesson-7", activities=build_teaching_session_activities(draft()))
    plan = manager.build_plan(
        TeachingClassroomOrchestrator(),
        mode=TeachingAssistantMode.MC,
        include_slide=True,
        clear_overlays=True,
    )
    one = plan_for_single_action(plan, plan.actions[-1].action_id)
    assert len(one.actions) == 1
    assert one.lesson_id == plan.lesson_id
    assert one.activity_id == plan.activity_id


def test_status_labels_are_teacher_readable():
    assert session_status_label(TeachingSessionStatus.RUNNING) == "Đang dạy"
    assert session_status_label(TeachingSessionStatus.TEACHER_CONTROL) == "Giáo viên đang giữ quyền"
