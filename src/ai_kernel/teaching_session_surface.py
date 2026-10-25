"""Pure helpers for wiring the V13M Teaching Session into the teacher UI.

No Streamlit import is allowed here. The UI module owns rendering while this
module owns lesson-draft -> TeachingSession activity translation and stable
session keys. This keeps session behavior testable without the UI runtime.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, MutableMapping, Sequence

from ai_kernel.teaching_assistant import (
    TeachingAssistantController,
    default_teaching_personas,
    default_teaching_policy,
)
from ai_kernel.teaching_classroom import ClassroomPhase, LessonActivityContext, TeachingActivityPlan
from ai_kernel.teaching_classroom_executor import (
    StreamlitClassroomRuntime,
    TeachingClassroomActionExecutor,
)
from ai_kernel.teaching_session import TeachingSessionManager, TeachingSessionStatus


SESSION_KEY = "ta_teaching_session_v13n"
SESSION_VERSION_KEY = "ta_teaching_session_contract_v13n"
SESSION_CONTRACT_VERSION = "V13N-1"

_ACTIVITY_PHASES = {
    "MO_DAU": ClassroomPhase.OPENING,
    "HINH_THANH_KIEN_THUC": ClassroomPhase.NEW_KNOWLEDGE,
    "LUYEN_TAP": ClassroomPhase.PRACTICE,
    "VAN_DUNG": ClassroomPhase.APPLICATION,
}

_ALLOWED_TOOLS = (
    "classroom.status.read",
    "classroom.surface.clear_overlays",
    "classroom.slide.open",
    "classroom.stage.show",
    "classroom.timer.start",
    "classroom.quiz.display",
    "classroom.whiteboard.show",
)


def _lesson_id_from_draft(draft: Mapping[str, Any]) -> str:
    return str(
        draft.get("source_lesson_id")
        or (draft.get("catalog_selection") or {}).get("lesson_id")
        or ""
    ).strip()


def _question_from_card(card: Mapping[str, Any]) -> str:
    display = card.get("question_display") or []
    if isinstance(display, list):
        for row in display:
            if isinstance(row, dict) and str(row.get("text", "")).strip():
                return str(row["text"]).strip()
    return str(card.get("instruction", "")).strip()


def build_teaching_session_activities(
    draft: Mapping[str, Any],
    *,
    prepared_stage_ids: Sequence[str] = (),
    include_empty_activities: bool = True,
) -> tuple[LessonActivityContext, ...]:
    """Build the canonical four-phase TeachingSession activities from a lesson draft.

    The lesson draft is the source of truth. Only teacher-approved activity cards
    contribute questions/objectives, and slide IDs come from the draft itself.
    """
    lesson_id = _lesson_id_from_draft(draft)
    if not lesson_id:
        raise ValueError("Bài giảng hiện tại chưa có source_lesson_id/canonical lesson_id.")

    slides = draft.get("slides") or []
    cards = draft.get("activity_cards") or []
    stage_ids = tuple(str(item) for item in prepared_stage_ids if str(item).strip())
    activities: list[LessonActivityContext] = []

    for activity_id in ("MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"):
        activity_slides = [row for row in slides if isinstance(row, dict) and row.get("activity") == activity_id]
        activity_cards = [
            row for row in cards
            if isinstance(row, dict)
            and row.get("activity") == activity_id
            and row.get("review_status") == "TEACHER_APPROVED"
        ]
        first_card = activity_cards[0] if activity_cards else None
        slide_id = str(activity_slides[0].get("id", "")).strip() if activity_slides else ""
        question = _question_from_card(first_card) if first_card else ""
        objective = str(first_card.get("title", "")).strip() if first_card else ""
        duration_seconds = int(first_card.get("duration_minutes", 0) or 0) * 60 if first_card else 0
        if not duration_seconds:
            duration_seconds = 60

        if not include_empty_activities and not activity_slides and not activity_cards:
            continue

        allowed = list(_ALLOWED_TOOLS)
        if not slide_id:
            allowed.remove("classroom.slide.open")
        if not question:
            allowed.remove("classroom.quiz.display")
        if not stage_ids:
            allowed.remove("classroom.stage.show")

        activities.append(
            LessonActivityContext(
                lesson_id=lesson_id,
                activity_id=activity_id,
                activity_title={
                    "MO_DAU": "Khởi động",
                    "HINH_THANH_KIEN_THUC": "Hình thành kiến thức mới",
                    "LUYEN_TAP": "Luyện tập",
                    "VAN_DUNG": "Vận dụng",
                }[activity_id],
                phase=_ACTIVITY_PHASES[activity_id],
                objective=objective,
                duration_seconds=duration_seconds,
                selected_slide_id=slide_id,
                question=question,
                allowed_tools=tuple(allowed),
            )
        )

    if not activities:
        raise ValueError("Bài giảng chưa có hoạt động hợp lệ để tạo phiên dạy.")
    return tuple(activities)


def reset_teaching_session(session_state: MutableMapping[str, Any]) -> TeachingSessionManager:
    """Discard the previous teaching session object and create a new one."""
    session_state.pop(SESSION_KEY, None)
    session_state.pop(SESSION_VERSION_KEY, None)
    return get_or_create_teaching_session(session_state)


def get_or_create_teaching_session(
    session_state: MutableMapping[str, Any],
) -> TeachingSessionManager:
    """Return the single TeachingSessionManager for the authenticated teacher session."""
    manager = session_state.get(SESSION_KEY)
    if (
        isinstance(manager, TeachingSessionManager)
        and session_state.get(SESSION_VERSION_KEY) == SESSION_CONTRACT_VERSION
    ):
        return manager

    persona = default_teaching_personas()[0]
    controller = TeachingAssistantController(
        persona=persona,
        policy=default_teaching_policy(persona.persona_id),
    )
    executor = TeachingClassroomActionExecutor(
        controller=controller,
        runtime=StreamlitClassroomRuntime(session_state),
    )
    manager = TeachingSessionManager(controller=controller, executor=executor)
    session_state[SESSION_KEY] = manager
    session_state[SESSION_VERSION_KEY] = SESSION_CONTRACT_VERSION
    return manager


def plan_for_single_action(plan: TeachingActivityPlan, action_id: str) -> TeachingActivityPlan:
    """Create a plan containing one action so UI execution is still session-audited."""
    action = next((item for item in plan.actions if item.action_id == action_id), None)
    if action is None:
        raise ValueError("Không tìm thấy Classroom Action trong plan.")
    return replace(plan, actions=(action,))


def session_status_label(status: TeachingSessionStatus) -> str:
    labels = {
        TeachingSessionStatus.PREPARING: "Sẵn sàng bắt đầu",
        TeachingSessionStatus.RUNNING: "Đang dạy",
        TeachingSessionStatus.WAITING_TEACHER: "Chờ giáo viên xác nhận",
        TeachingSessionStatus.TEACHER_CONTROL: "Giáo viên đang giữ quyền",
        TeachingSessionStatus.PAUSED: "Tạm dừng",
        TeachingSessionStatus.COMPLETED: "Đã hoàn thành",
        TeachingSessionStatus.STOPPED: "Đã dừng",
    }
    return labels[status]


__all__ = [
    "SESSION_CONTRACT_VERSION",
    "SESSION_KEY",
    "SESSION_VERSION_KEY",
    "build_teaching_session_activities",
    "get_or_create_teaching_session",
    "reset_teaching_session",
    "plan_for_single_action",
    "session_status_label",
]
