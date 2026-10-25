"""Teacher-facing AI Teaching Assistant avatar surface.

V13E keeps the avatar presentation layer separate from classroom actions.
Voice input may call the local TeachingAssistantVoiceBridge, but no tool/action
is executed from this UI. Any classroom control remains behind the existing
TeachingAssistantController / Safe Agent / Approval boundaries.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def _default_avatar_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".." / "assets" / "avatars" / "math_assistant_female_vi.svg"


def _read_avatar_svg(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_avatar_surface_html(
    *,
    avatar_svg: str,
    display_name: str,
    state: str,
    audio_data_uri: str | None = None,
    speech_text: str = "",
) -> str:
    """Build a dependency-light browser avatar surface with audio-driven mouth motion.

    The browser uses WebAudio locally; no cloud service or avatar engine is required.
    A heavier engine (e.g. MuseTalk) can later replace this surface without changing
    the Teaching Assistant contracts.
    """
    safe_name = html.escape(display_name)
    safe_state = html.escape(state)
    speech_payload = json.dumps(speech_text or "", ensure_ascii=False)
    svg = avatar_svg.strip()
    if not svg:
        avatar_markup = "<div class='avatar-fallback'>AI</div>"
    else:
        avatar_markup = svg

    audio_markup = ""
    if audio_data_uri:
        safe_audio = html.escape(audio_data_uri, quote=True)
        audio_markup = f"<audio id='ta-audio' controls preload='auto' src='{safe_audio}'></audio>"

    return f"""
<!doctype html>
<html lang='vi'>
<head>
<meta charset='utf-8'>
<style>
:root {{ color-scheme: light; }}
body {{ margin:0; font-family: Arial, sans-serif; background: transparent; }}
.card {{ border:1px solid #d7dee8; border-radius:18px; padding:18px; background:#fff; box-shadow:0 3px 16px rgba(0,0,0,.06); }}
.top {{ display:flex; gap:18px; align-items:center; }}
.avatar {{ width:180px; min-width:180px; height:180px; border-radius:50%; overflow:hidden; border:4px solid #dbeafe; background:#f8fafc; display:flex; align-items:center; justify-content:center; }}
.avatar svg {{ width:100%; height:100%; }}
.avatar-fallback {{ font-size:48px; font-weight:700; color:#1d4ed8; }}
.name {{ font-size:24px; font-weight:700; margin-bottom:8px; color:#0f172a; }}
.state {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:14px; font-weight:600; }}
.hint {{ margin-top:10px; color:#64748b; font-size:13px; }}
.pulse {{ width:12px; height:12px; display:inline-block; margin-right:7px; border-radius:50%; background:#10b981; box-shadow:0 0 0 5px rgba(16,185,129,.12); }}
#ta-audio {{ width:100%; margin-top:14px; }}
.speech-controls {{ margin-top:12px; }}
#ta-speak {{
  border:0;
  border-radius:10px;
  padding:9px 16px;
  font-size:15px;
  font-weight:600;
  cursor:pointer;
  background:#eef2ff;
  color:#3730a3;
}}
#ta-speak:disabled {{
  opacity:.7;
  cursor:default;
}}
#avatar-mouth {{ transform-box: fill-box; transform-origin:center; }}
</style>
</head>
<body>
<div class='card'>
  <div class='top'>
    <div class='avatar'>{avatar_markup}</div>
    <div>
      <div class='name'>{safe_name}</div>
      <div class='state'><span class='pulse'></span>{safe_state}</div>
      <div class=hint>Lip-sync nhẹ chạy cục bộ theo biên độ audio. Avatar chỉ trình bày; Quyền điều khiển lớp học vẫn thuộc Kernel/Policy.</div>
    </div>
  </div>
  {audio_markup}
  <div class='speech-controls'>
    <button id='ta-speak' type='button'>🔊 Nói</button>
  </div>
</div>
<script>
const taSpeechText = {speech_payload};

(function() {{
  const button = document.getElementById('ta-speak');

  if (!button || !('speechSynthesis' in window)) return;

  button.addEventListener('click', function() {{
    const text = taSpeechText || '';
    if (!text.trim()) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'vi-VN';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const viVoice = voices.find(
      v => (v.lang || '').toLowerCase().startsWith('vi')
    );

    if (viVoice) {{
      utterance.voice = viVoice;
    }}

    button.disabled = true;
    button.textContent = '🔊 Đang nói...';

    utterance.onend = function() {{
      button.disabled = false;
      button.textContent = '🔊 Nói';
    }};

    utterance.onerror = function() {{
      button.disabled = false;
      button.textContent = '🔊 Nói';
    }};

    window.speechSynthesis.speak(utterance);
  }});
}})();
(function() {{
  const audio = document.getElementById('ta-audio');
  const mouth = document.getElementById('avatar-mouth');
  if (!audio || !mouth || !window.AudioContext) return;
  let ctx = null, analyser = null, data = null, source = null, connected = false;
  function ensureAudio() {{
    if (connected) return;
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    data = new Uint8Array(analyser.frequencyBinCount);
    try {{
      source = ctx.createMediaElementSource(audio);
      source.connect(analyser);
      analyser.connect(ctx.destination);
      connected = true;
    }} catch (_) {{ return; }}
  }}
  audio.addEventListener('play', async function() {{
    ensureAudio();
    if (ctx && ctx.state === 'suspended') {{ try {{ await ctx.resume(); }} catch (_) {{}} }}
    animate();
  }});
  function animate() {{
    if (!analyser || !data || audio.paused) {{
      mouth.style.transform = 'scaleY(1)';
      return;
    }}
    analyser.getByteFrequencyData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i];
    const level = Math.min(1, (sum / Math.max(1, data.length)) / 96);
    mouth.style.transform = 'scaleY(' + (1 + level * 2.2).toFixed(3) + ')';
    requestAnimationFrame(animate);
  }}
}})();
</script>
</body>
</html>
"""


def _save_audio_upload(uploaded: Any) -> Path:
    suffix = Path(getattr(uploaded, "name", "turn.wav") or "turn.wav").suffix or ".wav"
    raw = uploaded.getvalue()
    digest = hashlib.sha256(raw).hexdigest()[:16]
    out = Path(tempfile.gettempdir()) / "mathteacher_ai_voice" / f"browser_turn_{digest}{suffix}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return out


def render_teaching_assistant_avatar_surface(st: Any, *, client: Any | None = None, user_id: str | None = None) -> None:
    """Render the first browser-facing avatar + local voice surface."""
    del client, user_id
    # Lazy imports keep the rest of the portal import-safe when optional voice
    # dependencies are not installed.
    from ai_kernel.teaching_avatar import AvatarState
    from ai_kernel.teaching_session import TeachingSessionStatus
    from ai_kernel.teaching_session_surface import (
        build_teaching_session_activities,
        get_or_create_teaching_session,
        plan_for_single_action,
        reset_teaching_session,
        session_status_label,
    )

    teaching_session = get_or_create_teaching_session(st.session_state)
    controller = teaching_session.controller
    persona = controller.persona

    state_key = "ta_avatar_state_v13e"
    audio_key = "ta_avatar_audio_data_v13f"
    if audio_key not in st.session_state:
        st.session_state[audio_key] = None
    if state_key not in st.session_state:
        st.session_state[state_key] = AvatarState.IDLE.value

    avatar_path = Path(__file__).resolve().parents[2] / ".." / "assets" / "avatars" / "math_assistant_female_vi.svg"
    svg = _read_avatar_svg(avatar_path)
    try:
        from ai_kernel.teaching_realtime_transport import LiveKitTransportConfig, livekit_environment_status
        livekit_status = livekit_environment_status(LiveKitTransportConfig.from_env())
    except Exception:
        livekit_status = {"transport": "local-browser", "sdk_installed": False}
    try:
        import streamlit.components.v1 as components
        components.html(
            build_avatar_surface_html(
                avatar_svg=svg,
                display_name=persona.display_name,
                state=st.session_state[state_key],
                audio_data_uri=st.session_state.get(audio_key),
                speech_text=st.session_state.get("ta_speech_text", ""),
            ),
            height=340,
            scrolling=False,
        )
    except Exception:
        st.image(str(avatar_path), width=240)
        st.caption(f"{persona.display_name} · {st.session_state[state_key]}")

    if livekit_status.get("sdk_installed"):
        st.caption(f"Realtime transport: LiveKit available · {livekit_status.get('url')} · room={livekit_status.get('room_name')}")
    else:
        st.caption("Realtime transport hiện tại: local browser audio. LiveKit là adapter tùy chọn để self-host WebRTC.")

    enable_livekit = str(os.environ.get("MATHTEACHER_ENABLE_LIVEKIT", "false")).lower() in {"1", "true", "yes", "on"}
    if enable_livekit:
        render_livekit_realtime_panel(st, identity="teacher")

    left, center, right = st.columns(3)
    with left:
        if st.button("🎙 Bắt đầu nghe", use_container_width=True):
            st.session_state[state_key] = AvatarState.LISTENING.value
            st.rerun()
    with center:
        if st.button("✋ Giáo viên giành quyền", use_container_width=True):
            if teaching_session.status not in {TeachingSessionStatus.PREPARING, TeachingSessionStatus.COMPLETED, TeachingSessionStatus.STOPPED}:
                teaching_session.teacher_take_control(reason="Giáo viên giành quyền từ giao diện AI Trợ giảng.")
            else:
                controller.teacher_take_control()
            st.session_state[state_key] = AvatarState.INTERRUPTED.value
            st.session_state["ta_teacher_control_v13e"] = True
            st.session_state[audio_key] = None
            st.rerun()
    with right:
        if st.button("⏹ Dừng trợ giảng", use_container_width=True):
            if teaching_session.status not in {TeachingSessionStatus.PREPARING, TeachingSessionStatus.COMPLETED, TeachingSessionStatus.STOPPED}:
                teaching_session.stop(reason="Giáo viên dừng Trợ giảng.")
            controller.stop()
            st.session_state[state_key] = AvatarState.STOPPED.value
            st.session_state["ta_teacher_control_v13e"] = True
            st.session_state[audio_key] = None
            st.rerun()

    # V13N: one TeachingSessionManager is the source of truth for the live lesson.
    with st.expander("ðŸ§­ PhiÃªn dáº¡y hiá»‡n táº¡i", expanded=True):
        snapshot = teaching_session.snapshot()
        st.info(
            f"Trạng thái: **{session_status_label(snapshot.status)}** · "
            f"Hoáº¡t Ä‘á»™ng {snapshot.activity_index + 1 if snapshot.current_activity_id else 0}/{snapshot.total_activities} Â· "
            f"{snapshot.current_activity_id or 'chÆ°a báº¯t Ä‘áº§u'} Â· "
            f"event={snapshot.event_count}"
        )
        draft = st.session_state.get("lesson_slide_draft") or {}
        lesson_id = str(
            draft.get("source_lesson_id")
            or (draft.get("catalog_selection") or {}).get("lesson_id")
            or ""
        ).strip()
        start_col, next_col, release_col, stop_col = st.columns(4)
        if snapshot.status in {TeachingSessionStatus.PREPARING, TeachingSessionStatus.COMPLETED, TeachingSessionStatus.STOPPED}:
            with start_col:
                if st.button("â–¶ï¸ Báº¯t Ä‘áº§u tiáº¿t dáº¡y", type="primary", use_container_width=True, disabled=not bool(lesson_id)):
                    try:
                        if snapshot.status in {snapshot.status.COMPLETED, snapshot.status.STOPPED}:
                            teaching_session = reset_teaching_session(st.session_state)
                        activities = build_teaching_session_activities(
                            draft,
                            prepared_stage_ids=tuple((st.session_state.get("lesson_integrated_stages") or {}).keys()),
                            include_empty_activities=True,
                        )
                        teaching_session.start(lesson_id=lesson_id, activities=activities)
                        st.session_state["ta_v13i_plan"] = None
                        st.session_state["ta_v13j_action_results"] = {}
                        st.session_state[state_key] = AvatarState.IDLE.value
                        st.rerun()
                    except Exception as exc:
                        st.error(f"KhÃ´ng thá»ƒ báº¯t Ä‘áº§u phiÃªn dáº¡y: {exc}")
            if not lesson_id:
                st.caption("HÃ£y má»Ÿ bÃ i giáº£ng cÃ³ lesson_id trÆ°á»›c khi báº¯t Ä‘áº§u phiÃªn dáº¡y.")
        else:
            with next_col:
                if st.button("â­ï¸ Chuyá»ƒn hoáº¡t Ä‘á»™ng", use_container_width=True):
                    try:
                        teaching_session.advance()
                        st.session_state["ta_v13i_plan"] = None
                        st.session_state["ta_v13j_action_results"] = {}
                        st.rerun()
                    except Exception as exc:
                        st.warning(f"ChÆ°a thá»ƒ chuyá»ƒn hoáº¡t Ä‘á»™ng: {exc}")
            with release_col:
                if snapshot.status.name == "TEACHER_CONTROL" and st.button("â–¶ï¸ Tráº£ quyá»n cho Trá»£ giáº£ng", use_container_width=True):
                    teaching_session.teacher_release_control()
                    st.session_state["ta_teacher_control_v13e"] = False
                    st.session_state[state_key] = AvatarState.LISTENING.value
                    st.rerun()
            with stop_col:
                if st.button("⏹ Kết thúc phiên", use_container_width=True):
                    teaching_session.stop(reason="Giáo viên kết thúc phiên dạy.")
                    st.session_state["ta_teacher_control_v13e"] = True
                    st.rerun()
        current = teaching_session.current_activity
        if current is not None:
            st.caption(
                f"Hoáº¡t Ä‘á»™ng hiá»‡n táº¡i: **{current.activity_title}** Â· phase={current.phase.value} Â· "
                f"slide={current.selected_slide_id or 'â€”'}"
            )
            if current.question:
                st.caption("CÃ¢u há»i Ä‘Ã£ Ä‘Æ°á»£c giÃ¡o viÃªn duyá»‡t: " + current.question)

    # V13I: MC + activity facilitation planner.
    # The planner creates a reviewable teaching plan; it does not execute classroom tools.
    with st.expander("ðŸŽ¬ MC & Ä‘iá»u phá»‘i hoáº¡t Ä‘á»™ng", expanded=True):
        try:
            from ai_kernel.teaching_assistant import TeachingAssistantMode
            from ai_kernel.teaching_classroom import ClassroomPhase, LessonActivityContext, TeachingClassroomOrchestrator
            from ai_kernel.teaching_classroom_executor import StreamlitClassroomRuntime, TeachingClassroomActionExecutor, ClassroomExecutionStatus

            mode_label = st.selectbox(
                "Vai trò của Trợ giảng",
                options=[
                    ("MC â€“ dáº«n chÆ°Æ¡ng trÃ¬nh", TeachingAssistantMode.MC),
                    ("Äiá»u phá»‘i hoáº¡t Ä‘á»™ng", TeachingAssistantMode.ACTIVITY_FACILITATOR),
                    ("Điều hành kỹ thuật", TeachingAssistantMode.TECHNICAL_OPERATOR),
                    ("Äá»“ng giáº£ng", TeachingAssistantMode.CO_TEACHER),
                ],
                format_func=lambda item: item[0],
                key="ta_v13i_mode",
            )
            c1, c2 = st.columns(2)
            with c1:
                lesson_id = st.text_input("Mã bài học", value=st.session_state.get("ta_v13i_lesson_id", "lesson-demo"), key="ta_v13i_lesson_id")
                activity_id = st.text_input("MÃ£ hoáº¡t Ä‘á»™ng", value=st.session_state.get("ta_v13i_activity_id", "opening-1"), key="ta_v13i_activity_id")
                activity_title = st.text_input("TÃªn hoáº¡t Ä‘á»™ng", value=st.session_state.get("ta_v13i_activity_title", "Khá»Ÿi Ä‘á»™ng"), key="ta_v13i_activity_title")
            with c2:
                phase_label = st.selectbox(
                    "Giai Ä‘oáº¡n",
                    options=list(ClassroomPhase),
                    format_func=lambda item: {
                        ClassroomPhase.OPENING: "Má»Ÿ Ä‘áº§u",
                        ClassroomPhase.NEW_KNOWLEDGE: "Hình thành kiến thức",
                        ClassroomPhase.PRACTICE: "Luyá»‡n táº­p",
                        ClassroomPhase.APPLICATION: "Vận dụng",
                        ClassroomPhase.TRANSITION: "Chuyá»ƒn hoáº¡t Ä‘á»™ng",
                        ClassroomPhase.CLOSING: "Kết thúc",
                    }[item],
                    key="ta_v13i_phase",
                )
                duration_seconds = st.number_input("Thời lượng (giây)", min_value=0, max_value=3600, value=60, step=10, key="ta_v13i_duration")
                question = st.text_area("CÃ¢u há»i/Prompt hoáº¡t Ä‘á»™ng", value="", key="ta_v13i_question")

            objective = st.text_input("Má»¥c tiÃªu hoáº¡t Ä‘á»™ng", value="", key="ta_v13i_objective")
            a1, a2, a3, a4, a5 = st.columns(5)
            with a1:
                include_slide = st.checkbox("Má»Ÿ slide", value=False, key="ta_v13i_slide")
            with a2:
                include_timer = st.checkbox("Bấm giờ", value=True, key="ta_v13i_timer")
            with a3:
                include_quiz = st.checkbox("Hiá»ƒn thá»‹ cÃ¢u há»i", value=False, key="ta_v13i_quiz")
            with a4:
                stage_ids = tuple(str(k) for k in (st.session_state.get("lesson_integrated_stages", {}) or {}).keys())
                include_stage = st.checkbox("Má»Ÿ sÃ¢n kháº¥u", value=False, disabled=not stage_ids, key="ta_v13k_stage")
            with a5:
                include_whiteboard = st.checkbox("Má»Ÿ báº£ng", value=False, key="ta_v13k_whiteboard")
            selected_slide_id = st.text_input(
                "MÃ£ slide cáº§n má»Ÿ (náº¿u cÃ³)",
                value=str(st.session_state.get("lesson_slide_selected", "")),
                key="ta_v13j_selected_slide_id",
            )
            stage_content_id = ""
            if stage_ids:
                stage_content_id = st.selectbox(
                    "Sân khấu tích hợp",
                    options=stage_ids,
                    index=0,
                    key="ta_v13k_stage_content_id",
                    disabled=not include_stage,
                )

            if st.button("ðŸ§© Láº­p ká»‹ch báº£n & káº¿ hoáº¡ch", type="primary", use_container_width=True, key="ta_v13i_build_plan"):
                allowed_tools = (
                    "classroom.status.read",
                    "classroom.slide.open",
                    "classroom.stage.show",
                    "classroom.timer.start",
                    "classroom.quiz.display",
                    "classroom.whiteboard.show",
                )
                context = LessonActivityContext(
                    lesson_id=lesson_id,
                    activity_id=activity_id,
                    activity_title=activity_title,
                    phase=phase_label,
                    objective=objective,
                    duration_seconds=int(duration_seconds),
                    selected_slide_id=selected_slide_id,
                    stage_content_id=stage_content_id,
                    question=question,
                    allowed_tools=allowed_tools,
                )
                try:
                    if teaching_session.status not in {TeachingSessionStatus.PREPARING, TeachingSessionStatus.COMPLETED, TeachingSessionStatus.STOPPED}:
                        current_session_activity = teaching_session.current_activity
                        if current_session_activity and current_session_activity.activity_id == activity_id and current_session_activity.lesson_id == lesson_id:
                            plan = teaching_session.build_plan(
                                TeachingClassroomOrchestrator(),
                                mode=mode_label[1],
                                include_timer=include_timer,
                                include_slide=include_slide,
                                include_quiz=include_quiz,
                                include_stage=include_stage,
                                include_whiteboard=include_whiteboard,
                                clear_overlays=True,
                            )
                        else:
                            raise ValueError("Hoáº¡t Ä‘á»™ng trong form khÃ´ng trÃ¹ng activity hiá»‡n táº¡i cá»§a phiÃªn dáº¡y.")
                    else:
                        plan = TeachingClassroomOrchestrator().build_plan(
                            context=context,
                            mode=mode_label[1],
                            include_timer=include_timer,
                            include_slide=include_slide,
                            include_quiz=include_quiz,
                            include_stage=include_stage,
                            include_whiteboard=include_whiteboard,
                        )
                    st.session_state["ta_v13i_plan"] = plan
                except Exception as exc:
                    st.error(f"KhÃ´ng thá»ƒ láº­p káº¿ hoáº¡ch cho phiÃªn dáº¡y: {exc}")

            plan = st.session_state.get("ta_v13i_plan")
            if plan is not None:
                st.success("ÄÃ£ láº­p káº¿ hoáº¡ch. Classroom Action chá»‰ thá»±c thi khi giÃ¡o viÃªn xÃ¡c nháº­n tá»«ng thao tÃ¡c.")
                for idx, line in enumerate(plan.script, start=1):
                    st.write(f"**{idx}. {line.speaker}:** {line.text}")
                if plan.actions:
                    st.markdown("**Thao tác kỹ thuật:**")
                    st.session_state.setdefault("ta_v13j_action_results", {})
                    executor = TeachingClassroomActionExecutor(
                        controller=controller,
                        runtime=StreamlitClassroomRuntime(st.session_state),
                    )
                    for action in plan.actions:
                        result = st.session_state["ta_v13j_action_results"].get(action.action_id)
                        if result:
                            icon = "âœ…" if result.status is ClassroomExecutionStatus.EXECUTED else "â¸ï¸"
                            st.write(f"{icon} **{action.label}** · {result.message}")
                            continue
                        a_left, a_right = st.columns([3, 1])
                        with a_left:
                            approval = "Xác nhận của giáo viên" if action.requires_teacher_confirmation else "Theo policy"
                            st.write(f"- {action.label} · {approval}")
                        with a_right:
                            if st.button("â–¶ Thá»±c hiá»‡n", key="ta_v13j_exec_" + action.action_id, use_container_width=True):
                                if teaching_session.status not in {TeachingSessionStatus.PREPARING, TeachingSessionStatus.COMPLETED, TeachingSessionStatus.STOPPED}:
                                    try:
                                        session_plan = plan_for_single_action(plan, action.action_id)
                                        session_results = teaching_session.execute_plan(session_plan, teacher_confirmed=True)
                                        exec_result = session_results[0] if session_results else executor.execute(action, teacher_confirmed=True)
                                    except Exception as exc:
                                        st.error(f"KhÃ´ng thá»ƒ thá»±c thi theo Teaching Session: {exc}")
                                        exec_result = executor.execute(action, teacher_confirmed=True)
                                else:
                                    exec_result = executor.execute(action, teacher_confirmed=True)
                                st.session_state["ta_v13j_action_results"][action.action_id] = exec_result
                                st.rerun()
                else:
                    st.caption("Ká»‹ch báº£n nÃ y chá»‰ gá»“m lá»i dáº«n, chÆ°a Ä‘á» xuáº¥t thao tÃ¡c ká»¹ thuáº­t.")
                status = StreamlitClassroomRuntime(st.session_state).read_status()
                if status:
                    with st.expander("Tráº¡ng thÃ¡i lá»›p há»c do Trá»£ giáº£ng vá»«a cáº­p nháº­t", expanded=False):
                        st.json(status)
                st.caption("V13K: Action Ä‘Æ°á»£c Ä‘áº©y vÃ o BÃ i giáº£ng/SÃ¢n kháº¥u/Timer/Quiz/Whiteboard sau xÃ¡c nháº­n; Teacher Override luÃ´n cháº·n executor.")
        except Exception as exc:
            st.warning(f"ChÆ°a thá»ƒ má»Ÿ bá»™ láº­p káº¿ hoáº¡ch MC/hoáº¡t Ä‘á»™ng: {exc}")

    teacher_control = bool(st.session_state.get("ta_teacher_control_v13e", False))
    if teacher_control:
        st.warning("GiÃ¡o viÃªn Ä‘ang giá»¯ quyá»n Ä‘iá»u khiá»ƒn. Avatar khÃ´ng xá»­ lÃ½ há»™i thoáº¡i má»›i cho tá»›i khi Ä‘Æ°á»£c báº­t láº¡i.")
        if st.button("â–¶ï¸ Cho phÃ©p Trá»£ giáº£ng tiáº¿p tá»¥c", use_container_width=True):
            if teaching_session.status.name == "TEACHER_CONTROL":
                teaching_session.teacher_release_control()
            else:
                controller.teacher_release_control()
            st.session_state["ta_teacher_control_v13e"] = False
            st.session_state[state_key] = AvatarState.LISTENING.value
            st.rerun()
        return

    uploaded = None
    audio_input = getattr(st, "audio_input", None)
    if callable(audio_input):
        uploaded = audio_input("NÃ³i vá»›i Trá»£ giáº£ng", key="ta_browser_audio_v13e")
    else:
        st.info("PhiÃªn báº£n Streamlit hiá»‡n táº¡i chÆ°a cÃ³ audio_input; cÃ³ thá»ƒ dÃ¹ng Voice Bridge/CLI local.")
        return

    if uploaded is None:
        st.caption("Cho phÃ©p microphone trong trÃ¬nh duyá»‡t rá»“i nÃ³i má»™t cÃ¢u. Audio chá»‰ Ä‘Æ°á»£c chuyá»ƒn vÃ o local voice bridge khi báº¡n báº¥m xá»­ lÃ½.")
        return

    if st.button("ðŸ§  Xá»­ lÃ½ báº±ng AI local", type="primary", use_container_width=True):
        st.session_state[state_key] = AvatarState.THINKING.value
        st.rerun()

    if st.session_state[state_key] == AvatarState.THINKING.value:
        try:
            from ai_kernel.teaching_voice import (
                FasterWhisperSTT,
                AIKernelTeachingBrain,
                TeachingAssistantVoiceBridge,
                TeachingVoiceConfig,
            )

            audio_path = _save_audio_upload(uploaded)
            tts_command = os.environ.get("MATHTEACHER_TTS_COMMAND", "").strip()
            tts = None
            if tts_command:
                from ai_kernel.teaching_voice import CommandTTSAdapter
                tts = CommandTTSAdapter(tts_command)

            bridge = TeachingAssistantVoiceBridge(
                config=TeachingVoiceConfig(mode="teacher"),
                stt=FasterWhisperSTT(
                    model_size=os.environ.get("MATHTEACHER_STT_MODEL", "small"),
                    device=os.environ.get("MATHTEACHER_STT_DEVICE", "cpu"),
                    compute_type=os.environ.get("MATHTEACHER_STT_COMPUTE", "int8"),
                ),
                brain=AIKernelTeachingBrain(),
                tts=tts,
            )
            turn = bridge.process_audio(audio_path, output_path=audio_path.with_name(audio_path.stem + "_reply.mp3") if tts else None)
            st.session_state[state_key] = AvatarState.SPEAKING.value
            st.success(f"AI trả lời: {turn.response_text}")
            st.session_state["ta_speech_text"] = turn.response_text
            if turn.synthesized_audio and turn.synthesized_audio.exists():
                audio_bytes = turn.synthesized_audio.read_bytes()
                st.session_state[audio_key] = "data:audio/mpeg;base64," + base64.b64encode(audio_bytes).decode("ascii")
                st.audio(audio_bytes, format="audio/mp3")
            st.caption("Voice surface chá»‰ tráº£ lá»i; khÃ´ng tá»± thá»±c thi Classroom Action.")
        except Exception as exc:
            st.session_state[state_key] = AvatarState.IDLE.value
            st.error(f"ChÆ°a thá»ƒ cháº¡y local voice: {exc}")


def render_livekit_realtime_panel(st: Any, *, identity: str = "teacher") -> None:
    """Optional self-hosted LiveKit panel; no API secret reaches the browser."""
    try:
        from ai_kernel.teaching_realtime_transport import LiveKitTransportConfig
        from ai_kernel.teaching_livekit import build_livekit_client_html, generate_livekit_access_token
    except Exception as exc:
        st.info(f"LiveKit chưa khả dụng: {exc}")
        return

    config = LiveKitTransportConfig.from_env()
    if not os.environ.get("LIVEKIT_API_KEY") or not os.environ.get("LIVEKIT_API_SECRET"):
        st.info("ChÆ°a cáº¥u hÃ¬nh LIVEKIT_API_KEY/LIVEKIT_API_SECRET á»Ÿ backend.")
        return
    try:
        participant = generate_livekit_access_token(
            room_name=config.room_name,
            identity=f"{config.identity_prefix}-{identity}".strip("-"),
            name="Giáo viên",
            ttl_seconds=min(config.token_ttl_seconds, 900),
            can_publish_audio=True,
            can_publish_video=False,
            can_subscribe_audio=True,
            can_subscribe_video=True,
        )
        client_js = os.environ.get("MATHTEACHER_LIVEKIT_CLIENT_JS_URL", "").strip() or None
        html_fragment = build_livekit_client_html(
            server_url=config.url,
            token=participant.token,
            display_name="AI Trá»£ giáº£ng â€“ Realtime",
            client_js_url=client_js,
        )
        import streamlit.components.v1 as components
        components.html(html_fragment, height=130, scrolling=False)
        st.caption(f"Room: {participant.room_name} Â· token hiá»‡u lá»±c {participant.ttl_seconds}s")
    except Exception as exc:
        st.error(f"KhÃ´ng táº¡o Ä‘Æ°á»£c phiÃªn LiveKit: {exc}")


__all__ = ["build_avatar_surface_html", "render_teaching_assistant_avatar_surface", "render_livekit_realtime_panel"]
