"""Teacher authored visual AI presenter cards for lesson activities."""

from base64 import b64encode
from functools import lru_cache
from pathlib import Path
from uuid import uuid4


ROLES = {"GUIDE": "AI hướng dẫn", "ASSISTANT": "AI trợ giảng", "MC": "AI MC"}
ACTIVITIES = {"MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"}
AVATAR = Path(__file__).parent / "assets" / "lesson_ai_companion.png"


@lru_cache(maxsize=1)
def avatar_data_uri() -> str:
    return "data:image/png;base64," + b64encode(AVATAR.read_bytes()).decode("ascii")


def validate_presenter(card):
    if not isinstance(card, dict) or set(card) != {"id", "activity", "role", "message"}:
        raise ValueError("Thẻ nhân vật AI không hợp lệ.")
    if card["activity"] not in ACTIVITIES or card["role"] not in ROLES:
        raise ValueError("Hoạt động hoặc vai trò AI không hợp lệ.")
    for field, limit in (("id", 80), ("message", 1000)):
        if not isinstance(card[field], str) or not card[field].strip() or len(card[field]) > limit:
            raise ValueError("Nội dung nhân vật AI không hợp lệ.")
    return card


def add_presenter(draft, *, activity, role, message):
    cards = draft.setdefault("ai_presenters", [])
    if len(cards) >= 40:
        raise ValueError("Bài giảng chỉ nhận tối đa 40 thẻ nhân vật AI.")
    card = validate_presenter({"id": str(uuid4()), "activity": activity,
                               "role": role, "message": message.strip()})
    cards.append(card)
    return card


def render_presenter_authoring(st, draft, activity):
    with st.expander("Thêm nhân vật AI dẫn dắt hoạt động", expanded=False):
        role = st.selectbox("Vai trò", list(ROLES), format_func=ROLES.get,
                            key="lesson_ai_presenter_role")
        message = st.text_area("Kịch bản lời nói (mỗi dòng là một lượt nói)", max_chars=1000,
                               placeholder="Ví dụ: Chào các em! Hôm nay chúng ta cùng tìm hiểu cách ghi số tự nhiên.",
                               key="lesson_ai_presenter_message")
        st.caption("Trên slide, giáo viên bấm Phát lời dẫn. Máy dùng giọng tiếng Việt sẵn có trong trình duyệt; không tự nói khi chuyển slide.")
        if st.button("Thêm nhân vật vào hoạt động này", key="lesson_ai_presenter_add"):
            try:
                add_presenter(draft, activity=activity, role=role, message=message)
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
    for card in list(draft.get("ai_presenters", [])):
        if card["activity"] != activity:
            continue
        with st.expander(f"{ROLES[card['role']]} · {card['message'][:60]}", expanded=False):
            st.write(card["message"])
            if st.button("Bỏ nhân vật khỏi hoạt động", key="lesson_ai_presenter_remove_" + card["id"]):
                draft["ai_presenters"].remove(card)
                st.rerun()


def presenter_speech_script() -> str:
    """Speech is opt-in and refuses a non-Vietnamese fallback voice."""
    return r'''<script>
(function(){
  const synth=window.speechSynthesis;
  let active=null;
  function status(slide,message){
    const node=slide.querySelector('.ai-voice-status');
    if(node) node.textContent=message;
  }
  function reset(){
    if(synth) synth.cancel();
    if(active){active.classList.remove('ai-speaking');status(active,'Đã dừng.');}
    active=null;
  }
  function vietnameseVoices(){
    return synth ? synth.getVoices().filter(v=>/^vi(?:-|$)/i.test(v.lang)) : [];
  }
  function refresh(){
    document.querySelectorAll('.ai-voice-select').forEach(select=>{
      const old=select.value, voices=vietnameseVoices();
      select.replaceChildren();
      if(!voices.length){
        const option=document.createElement('option');
        option.textContent='Chưa có giọng tiếng Việt';option.value='';select.append(option);
        return;
      }
      voices.forEach(voice=>{
        const option=document.createElement('option');
        option.value=voice.voiceURI;option.textContent=voice.name+' ('+voice.lang+')';
        select.append(option);
      });
      if(voices.some(v=>v.voiceURI===old)) select.value=old;
    });
  }
  if(synth){synth.addEventListener('voiceschanged',refresh);refresh();}
  document.addEventListener('click',event=>{
    const button=event.target.closest('.ai-voice-play,.ai-voice-stop');
    if(!button) return;
    event.preventDefault();event.stopPropagation();
    const slide=button.closest('.ai-presenter-slide');
    if(!slide) return;
    if(button.classList.contains('ai-voice-stop')){reset();return;}
    reset();
    if(!synth || typeof SpeechSynthesisUtterance==='undefined'){
      status(slide,'Trình duyệt không hỗ trợ đọc lời nói.');return;
    }
    const select=slide.querySelector('.ai-voice-select');
    const voice=vietnameseVoices().find(v=>v.voiceURI===select.value);
    if(!voice){status(slide,'Chưa có giọng tiếng Việt trên thiết bị này.');return;}
    const lines=[...slide.querySelectorAll('.ai-script-line')]
      .map(node=>node.textContent.trim()).filter(Boolean);
    if(!lines.length) return;
    active=slide;
    let index=0;
    function next(){
      if(active!==slide) return;
      if(index>=lines.length){
        slide.classList.remove('ai-speaking');active=null;
        status(slide,'Đã đọc xong kịch bản.');return;
      }
      const utterance=new SpeechSynthesisUtterance(lines[index]);
      utterance.lang='vi-VN';utterance.voice=voice;utterance.rate=1;
      status(slide,'Đang nói '+(index+1)+'/'+lines.length+'…');
      slide.classList.add('ai-speaking');index++;
      utterance.onend=next;
      utterance.onerror=()=>{
        if(active===slide){slide.classList.remove('ai-speaking');active=null;
          status(slide,'Giọng nói bị gián đoạn. Bấm Phát để thử lại.');}
      };
      synth.speak(utterance);
    }
    next();
  });
  if(window.Reveal){Reveal.on('slidechanged',reset);}
  window.addEventListener('pagehide',reset);
})();
</script>'''
