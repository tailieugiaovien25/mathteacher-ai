"""Shared AI MC bridge for interactive classroom stages.

The browser owns presentation and speech synthesis; Python owns AI responses.
This module never mutates question, score, timer, buzzer, or assessment state.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def build_gameshow_mc_html(html: bytes | str) -> bytes:
    """Add an optional MC panel to the existing Gameshow without changing game logic."""
    source = html.decode("utf-8") if isinstance(html, bytes) else str(html)
    if "mathteacher-gameshow-ai-mc" in source:
        return source.encode("utf-8")
    panel = r"""
<section id="mathteacher-gameshow-ai-mc" style="position:fixed;right:18px;bottom:18px;z-index:100;
width:min(390px,calc(100vw - 36px));padding:14px;border:1px solid #79c9ff;
border-radius:16px;background:#071b31f2;color:#f5fbff;font:14px/1.45 Segoe UI,Arial,sans-serif;
box-shadow:0 12px 38px #0009">
 <div style="display:flex;gap:8px;align-items:center;justify-content:space-between">
  <strong>🎤 AI TRỢ GIẢNG · MC GAMESHOW</strong>
  <button id="mt-mc-toggle" type="button" aria-pressed="false">Bật MC</button>
 </div>
 <div id="mt-mc-status" role="status" style="margin:8px 0;color:#c8eaff">MC đang tắt.</div>
 <div style="display:flex;gap:8px;flex-wrap:wrap">
  <button id="mt-mc-announce" type="button" disabled>Đọc câu hỏi</button>
  <button id="mt-mc-listen" type="button" disabled>🎙 Nghe học sinh</button>
  <button id="mt-mc-stop" type="button">Dừng giọng</button>
 </div>
 <div id="mt-mc-reply" style="margin-top:8px;max-height:100px;overflow:auto"></div>
</section>
"""
    script = r"""
<script>
(()=> {
 const root=document.getElementById('mathteacher-gameshow-ai-mc');
 if(!root || root.dataset.ready==='1')return;
 root.dataset.ready='1';
 const toggle=root.querySelector('#mt-mc-toggle'), announce=root.querySelector('#mt-mc-announce');
 const listen=root.querySelector('#mt-mc-listen'), stop=root.querySelector('#mt-mc-stop');
 const status=root.querySelector('#mt-mc-status'), reply=root.querySelector('#mt-mc-reply');
 let enabled=false, requestId=0, recognition=null;
 const speech=window.speechSynthesis;
 function say(value){
  if(!enabled || !speech || !value)return;
  speech.cancel();
  const u=new SpeechSynthesisUtterance(String(value).slice(0,1200));
  u.lang='vi-VN'; u.rate=0.96;
  const voices=speech.getVoices();
  u.voice=voices.find(v=>/^vi(-|_)/i.test(v.lang))||null;
  speech.speak(u);
 }
 function questionContext(){
  const slide=document.querySelector('.question-slide.active') || [...document.querySelectorAll('.slide')].find(x=>getComputedStyle(x).display!=='none');
  if(!slide)return null;
  const allSlides=[...document.querySelectorAll('.question-slide, .slide')];
  return {
   index:Math.max(0,allSlides.indexOf(slide)),
   question:slide.querySelector('h1')?.innerText?.trim().slice(0,3000)||'',
   options:[...slide.querySelectorAll('.mcq')].map(x=>x.innerText.trim().slice(0,500)),
   statements:[...slide.querySelectorAll('.truth')].map(x=>x.innerText.trim().slice(0,500))
  };
 }
 function send(action, transcript=''){
  const q=questionContext();
  if(!q){status.textContent='Chưa có câu hỏi đang hiển thị.';return}
  const eventId=Date.now()+'-'+(++requestId);
  status.textContent=action==='announce'?'MC đang chuẩn bị giới thiệu câu hỏi…':'MC đang nghe và phản hồi…';
  parent.postMessage({mathteacherGameshow:{event_id:eventId,action,question_index:q.index,
    question:q.question,options:q.options,statements:q.statements,transcript:String(transcript).slice(0,1000)}},'*');
 }
 toggle.addEventListener('click',()=>{
  enabled=!enabled;toggle.setAttribute('aria-pressed',String(enabled));
  toggle.textContent=enabled?'Tắt MC':'Bật MC';
  announce.disabled=!enabled;listen.disabled=!enabled;
  status.textContent=enabled?'MC đã bật. Có thể yêu cầu đọc câu hỏi hoặc bật micro.':'MC đang tắt.';
  if(!enabled){speech?.cancel();if(recognition)recognition.abort()}
 });
 announce.addEventListener('click',()=>send('announce'));
 listen.addEventListener('click',()=>{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){status.textContent='Trình duyệt chưa hỗ trợ nhận dạng giọng nói. Hãy dùng phần trả lời của giáo viên.';return}
  if(recognition)recognition.abort();
  recognition=new SR();recognition.lang='vi-VN';recognition.interimResults=false;recognition.maxAlternatives=1;
  recognition.onstart=()=>status.textContent='MC đang nghe học sinh…';
  recognition.onresult=e=>send('student_answer',e.results?.[0]?.[0]?.transcript||'');
  recognition.onerror=e=>status.textContent=e.error==='not-allowed'?'Chưa được cấp quyền micro.':'MC chưa nghe rõ, hãy thử lại.';
  try{recognition.start()}catch(e){status.textContent='Không khởi động được micro.'}
 });
 stop.addEventListener('click',()=>speech?.cancel());
 window.addEventListener('message',event=>{
  const data=event.data?.mathteacherAssistantResponse;
  if(!data || !data.event_id || !data.text)return;
  status.textContent='MC đã phản hồi.';
  reply.textContent=data.text;
  say(data.text);
 });
 // Re-introduce the current question when the teacher advances the slide.
 document.addEventListener('click',e=>{
  if(!enabled)return;
  if(e.target.closest('#next'))setTimeout(()=>send('announce'),100);
 });
})();
</script>
"""
    # Insert before the original game script, so the overlay is available from load.
    source = source.replace("</body>", panel + script + "</body>", 1)
    return source.encode("utf-8")


def _render_ai_integrated_stage(st: Any, html: bytes, slides: list[tuple[dict, dict]], *, session_id: str, surface: str) -> None:
    """Render a classroom stage in a bidirectional component and answer MC events."""
    import streamlit.components.v1 as components

    component_dir = Path(__file__).with_name("classroom_lucky_wheel_component")
    component = components.declare_component(f"mathteacher_{surface}_ai_mc_v1", path=str(component_dir))
    event = component(
        html=html.decode("utf-8"),
        ai_response=st.session_state.get(f"{surface}_ai_response:{session_id}"),
        key=f"classroom_{surface}_ai_component_{session_id}",
        default=None,
    )
    if not isinstance(event, dict) or event.get("action") not in {"announce", "student_answer"}:
        return
    event_id = str(event.get("event_id", ""))[:100]
    processed_key = f"{surface}_ai_processed:{session_id}"
    if not event_id or st.session_state.get(processed_key) == event_id:
        return
    st.session_state[processed_key] = event_id
    try:
        index = int(event.get("question_index", -1))
        if not 0 <= index < len(slides):
            raise ValueError("Không nhận được câu hỏi hiện tại hợp lệ.")
        row, detail = slides[index]
        question = str(row.get("prompt_text", event.get("question", "")))[:3000]
        transcript = str(event.get("transcript", "")).strip()[:1000]
        options = [str(x.get("option_code", "")) + ". " + str(x.get("option_text", ""))
                   for x in detail.get("options", [])]
        statements = [str(x.get("statement_text", "")) for x in detail.get("statements", [])]
        if event.get("action") == "announce":
            prompt = (
                "Hãy dẫn chương trình Gameshow Toán bằng tiếng Việt. Giới thiệu ngắn gọn câu hỏi "
                "đang hiển thị, tạo không khí hào hứng, mời các đội suy nghĩ và trả lời. "
                "Không đọc đáp án hoặc lời giải. Tối đa 3 câu.\n"
                f"Câu hỏi: {question}\nPhương án: {'; '.join(options)}\n"
                f"Nhận định: {'; '.join(statements)}"
            )
            fallback = f"Chúng ta cùng đến với câu hỏi số {index + 1}. {question} Các đội hãy suy nghĩ và sẵn sàng trả lời nhé!"
        else:
            if not transcript:
                raise ValueError("Chưa nhận được nội dung học sinh trả lời.")
            prompt = (
                "Bạn là MC kiêm trợ giảng trong Gameshow Toán. Phản hồi tự nhiên, thân thiện, "
                "ngắn gọn bằng tiếng Việt. Ghi nhận chính xác câu trả lời của học sinh; "
                "không tự kết luận đúng sai, không tiết lộ đáp án, không cộng/trừ điểm. "
                "Mời giáo viên hoặc người điều khiển xác nhận kết quả. Tối đa 2 câu.\n"
                f"Câu hỏi: {question}\nPhương án: {'; '.join(options)}\n"
                f"Nhận định: {'; '.join(statements)}\n"
                f"Câu trả lời vừa nghe: {transcript}"
            )
            fallback = f"MC đã nghe câu trả lời: {transcript}. Cảm ơn đội chơi! Mời giáo viên xác nhận kết quả."
        try:
            from ai_kernel.teaching_voice import AIKernelTeachingBrain
            response = AIKernelTeachingBrain().respond(
                transcript=prompt,
                system_prompt=(
                    "Bạn là MC trợ giảng MathTeacher AI. Chỉ dẫn dắt và giao tiếp; "
                    "không thay đổi trạng thái trò chơi, không chấm điểm và không tự công bố đáp án."
                ),
                mode="student",
                channel="chat",
            )
            text = str(response or "").strip()[:1200] or fallback
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Gameshow AI MC response failed")
            text = fallback
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Gameshow AI MC event rejected")
        text = "MC chưa xử lý được yêu cầu này. Mời giáo viên tiếp tục điều khiển Gameshow."
    st.session_state[f"{surface}_ai_response:{session_id}"] = {"event_id": event_id, "text": text}
    st.rerun()


def render_ai_integrated_gameshow(st: Any, html: bytes, slides: list[tuple[dict, dict]], *, session_id: str) -> None:
    _render_ai_integrated_stage(st, html, slides, session_id=session_id, surface="gameshow")


def render_ai_integrated_presentation(st: Any, html: bytes, slides: list[tuple[dict, dict]], *, session_id: str) -> None:
    _render_ai_integrated_stage(st, html, slides, session_id=session_id, surface="presentation")
