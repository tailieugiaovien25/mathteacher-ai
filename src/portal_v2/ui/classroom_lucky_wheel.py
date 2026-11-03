"""Offline 9-question lucky-wheel mode for the MathTeacherAI classroom stage."""
from __future__ import annotations

import json
import re
import unicodedata
from html import escape
from pathlib import Path

from portal_v2.ui.classroom_sound_layer import stage_audio_sources


WHEEL_QUESTION_COUNT = 9
WHEEL_BUILD_VERSION = 7


def _normalize_answer_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text.replace("đ", "d").replace("Đ", "D").lower()).strip()


def _classify_multiple_choice(detail: dict, transcript: str) -> tuple[str, str]:
    """Match a spoken option code or option text against approved choices."""
    heard = _normalize_answer_text(transcript)
    tokens = heard.split()
    options = sorted(detail.get("options", []), key=lambda item: item.get("sequence_number", 0))
    by_code = {
        _normalize_answer_text(option.get("option_code")): option
        for option in options
        if _normalize_answer_text(option.get("option_code"))
    }

    code_hits = []
    for position, token in enumerate(tokens):
        option = by_code.get(token)
        if option is None:
            continue
        context = tokens[max(0, position - 3):position]
        anchored = any(
            marker in context
            for marker in ("chon", "dap", "phuong", "lua", "la")
        )
        code_hits.append((token, anchored))

    anchored_codes = list(dict.fromkeys(code for code, anchored in code_hits if anchored))
    if len(anchored_codes) == 1:
        selected_code = anchored_codes[0]
    elif not anchored_codes and len({code for code, _ in code_hits}) == 1:
        selected_code = code_hits[0][0]
    else:
        selected_code = ""

    selected = by_code.get(selected_code) if selected_code else None
    if selected is None:
        text_matches = []
        for option in options:
            option_text = _normalize_answer_text(option.get("option_text"))
            if not option_text:
                continue
            if f" {option_text} " in f" {heard} ":
                text_matches.append(option)
        unique_codes = {
            _normalize_answer_text(option.get("option_code")): option
            for option in text_matches
        }
        if len(unique_codes) == 1:
            selected = next(iter(unique_codes.values()))

    if selected is None:
        return "unclear", "Không nhận dạng chắc chắn được phương án học sinh chọn."

    code = str(selected.get("option_code", "")).strip()
    correct_options = [option for option in options if option.get("is_correct")]
    correct_codes = [str(option.get("option_code", "")).strip() for option in correct_options]
    if not correct_codes:
        return "teacher-check", f"Học sinh chọn phương án {code}; câu hỏi chưa có đáp án chuẩn đã duyệt."
    is_correct = bool(selected.get("is_correct"))
    reference = ", ".join(correct_codes)
    outcome = "ĐÚNG" if is_correct else "SAI"
    context = (
        f"Học sinh chọn phương án {code}. Đáp án chuẩn là {reference}. Kết quả đối chiếu: {outcome}. "
        "Nếu sai, không tiết lộ mã hoặc nội dung đáp án chuẩn; chỉ đưa một gợi ý ngắn."
    )
    return ("correct" if is_correct else "wrong"), context


def _classify_true_false_selection(
    detail: dict, statement_index: int, selected_value: str
) -> tuple[str, str]:
    statements = sorted(
        detail.get("statements", []), key=lambda item: item.get("sequence_number", 0)
    )
    if not 0 <= statement_index < len(statements) or selected_value not in {"true", "false"}:
        return "teacher-check", "Không xác định được nhận định Đúng/Sai đã chọn."
    statement = statements[statement_index]
    selected = selected_value == "true"
    expected = bool(statement.get("correct_value"))
    outcome = "ĐÚNG" if selected == expected else "SAI"
    selection_text = "Đúng" if selected else "Sai"
    expected_text = "Đúng" if expected else "Sai"
    context = (
        f"Người điều khiển ghi nhận nhận định {statement_index + 1} là {selection_text}. "
        f"Đáp án chuẩn là {expected_text}. Kết quả đối chiếu: {outcome}. "
        "Nếu học sinh sai, không tiết lộ đáp án chuẩn; chỉ đưa một gợi ý ngắn."
    )
    return ("correct" if selected == expected else "wrong"), context


def build_offline_wheel(
    title: str,
    slides: list[tuple[dict, dict]],
    *,
    session_id: str,
    ai_bridge: bool = False,
) -> bytes:
    """Build the R15 lucky-wheel stage.

    The game intentionally uses exactly nine approved classroom-session slides:
    one fixed 40-degree wheel segment and one numbered tile per question.
    The wheel never writes to the database; local score/progress state stays in
    browser storage scoped to the classroom session.
    """
    if len(slides) != WHEEL_QUESTION_COUNT:
        raise ValueError(
            f"Vòng quay may mắn cần đúng {WHEEL_QUESTION_COUNT} câu đã duyệt "
            f"(hiện có {len(slides)} câu)."
        )

    from portal_v2.ui.teacher_classroom_streamlit import build_offline_presentation

    base = build_offline_presentation(title, slides).decode("utf-8")
    wheel_sound = json.dumps(stage_audio_sources(include_wheel=True)["wheel"])
    storage = json.dumps("mathteacher-wheel:r15:" + session_id).replace("<", "\\u003c")
    title_safe = escape(title, quote=True)

    css = r"""
body.wheel-mode main{max-width:1500px}
body.wheel-mode .slide{display:none!important}
body.wheel-mode .slide.wheel-active{display:block!important}
body.wheel-mode #prev,body.wheel-mode #next,body.wheel-mode #progress{display:none}

#wheel-panel{
  position:relative;overflow:hidden;
  background:
    radial-gradient(circle at 75% 10%,#ffffff 0 7%,transparent 8%),
    linear-gradient(135deg,#f7fbff 0%,#eef7ff 48%,#fdf8ff 100%);
  border:1px solid #d6e7f6;border-radius:30px;
  padding:clamp(18px,2.5vw,34px);
  box-shadow:0 14px 0 #b9d4e8,0 28px 60px #071b33aa;
  color:#102a47;min-height:72vh
}
#wheel-panel[hidden]{display:none!important}
body.question-selected #wheel-panel{
  min-height:0;padding:10px 18px;margin-bottom:20px;background:#f7fbff
}
body.question-selected #wheel-panel .wheel-stage,
body.question-selected #wheel-panel .score-zone{display:none}

.wheel-stage{
  display:grid;grid-template-columns:minmax(270px,390px) minmax(390px,620px) minmax(210px,300px);
  gap:clamp(18px,3vw,42px);align-items:center
}
.wheel-left h1{
  margin:.15em 0 .45em;font:950 clamp(34px,4vw,62px)/.92 'Segoe UI',Arial,sans-serif;
  letter-spacing:-.04em;color:#e62a2a;text-shadow:0 4px 0 #ffd35c,0 7px 18px #7f172844
}
.wheel-left .eyebrow{font-weight:900;letter-spacing:.12em;color:#24628e}
.wheel-title-sub{font-weight:750;color:#385b78;margin:0 0 18px}

.slot-board{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;max-width:360px}
.slot-button{
  aspect-ratio:1;border:3px solid #fff;border-radius:20px;background:linear-gradient(#9ade57,#83c83c);
  color:#062d70;font:950 clamp(28px,3vw,46px)/1 'Segoe UI',Arial,sans-serif;
  cursor:not-allowed;box-shadow:0 7px 0 #5f9f2a,0 12px 22px #2a5d2540;
  transition:transform .18s ease,box-shadow .18s ease,filter .18s ease,background .18s ease
}
.slot-button.pending{
  cursor:pointer;background:linear-gradient(#ffef5d,#ffc928);
  box-shadow:0 0 0 5px #fff,0 0 0 10px #ffb400,0 10px 26px #d879004f;
  animation:slot-pulse .85s ease-in-out infinite alternate
}
.slot-button.used{
  background:linear-gradient(#c8d4de,#9eafbc);color:#52616d;
  box-shadow:0 5px 0 #7f909c;filter:saturate(.55)
}
.slot-button.pending:hover{transform:translateY(-4px) scale(1.04)}
.slot-button:focus-visible{outline:5px solid #164f9e;outline-offset:3px}
.slot-button .slot-check{display:none;font-size:.48em;margin-left:.12em}
.slot-button.used .slot-check{display:inline}
@keyframes slot-pulse{to{transform:scale(1.045);filter:brightness(1.08)}}

.wheel-center{display:grid;place-items:center}
.wheel-frame{
  position:relative;display:grid;place-items:center;width:min(100%,570px);aspect-ratio:1
}
.wheel-disc{
  width:90%;aspect-ratio:1;border-radius:50%;border:12px solid #fff;
  box-shadow:0 10px 0 #55789d,0 24px 42px #0a2c5470;
  background:conic-gradient(
    #ff2da5 0deg 40deg,
    #13d538 40deg 80deg,
    #ffbe19 80deg 120deg,
    #5f9fd2 120deg 160deg,
    #fff11a 160deg 200deg,
    #08ae60 200deg 240deg,
    #ff1765 240deg 280deg,
    #1717e9 280deg 320deg,
    #d72bd8 320deg 360deg
  );
  position:relative;transition:transform 1.8s cubic-bezier(.12,.72,.2,1)
}
.wheel-disc::after{
  content:"";position:absolute;inset:0;border-radius:50%;
  background:repeating-conic-gradient(transparent 0deg 39deg,#fff 39deg 40deg);
  pointer-events:none
}
.wheel-disc.spinning{animation:wheel-spin .7s linear infinite}
.wheel-label{position:absolute;left:50%;top:50%;width:0;height:0;pointer-events:none;z-index:2}
.wheel-label-text{
  position:absolute;left:0;top:0;width:58px;height:58px;display:grid;place-items:center;
  border-radius:50%;background:#ffffffea;color:#102a47;
  font:950 clamp(22px,2.5vw,34px)/1 'Segoe UI',Arial,sans-serif;
  box-shadow:0 4px 12px #102a4750
}
.wheel-hub{
  position:absolute;z-index:4;left:50%;top:50%;display:grid;place-items:center;
  width:25%;aspect-ratio:1;border-radius:50%;border:7px solid #fff;
  background:radial-gradient(circle,#ffb53b 0 44%,#ff8d2b 45% 56%,#123f7a 57% 70%,#fff 71%);
  box-shadow:0 5px 18px #102d5388;transform:translate(-50%,-50%)!important;
  pointer-events:none
}
.wheel-pointer{
  position:absolute;z-index:8;top:-3px;left:50%;transform:translate(-50%,-28%);
  width:0;height:0;border-left:25px solid transparent;border-right:25px solid transparent;
  border-top:56px solid #e32636;filter:drop-shadow(0 5px 2px #172b5066)
}

.wheel-controls{text-align:center}
.wheel-meta{font-weight:800;color:#21446c;font-size:1.08rem;line-height:1.5}
.wheel-action,.wheel-score button{
  border:0;border-radius:16px;padding:15px 22px;background:#1167ab;color:#fff;
  font:900 1.1rem 'Segoe UI',Arial,sans-serif;cursor:pointer;margin:6px;
  box-shadow:0 6px 0 #0a4677;transition:transform .15s ease,filter .15s ease
}
.wheel-action.primary{background:#ff1260;box-shadow:0 6px 0 #ae0c43}
.wheel-action.stop{background:#d61919;box-shadow:0 6px 0 #8b1111}
.wheel-action:disabled{opacity:.42;cursor:not-allowed;box-shadow:none}
.wheel-action:hover:not(:disabled){filter:brightness(1.08);transform:translateY(-2px)}
#wheel-feedback{
  min-height:3.4em;font-weight:850;color:#0d5688;line-height:1.35;margin:14px 0 0
}
.wheel-ai-status{display:inline-block;max-width:min(100%,560px);color:#f2fbff;background:#123b60;
  border:1px solid #59c5ff;border-radius:10px;padding:7px 11px;font-size:.94rem;font-weight:800;
  line-height:1.35;white-space:normal;text-align:left;box-shadow:0 2px 8px #06182b66}
.wheel-voice-panel{flex:1 1 100%;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  padding:12px 14px;background:#eff8ff;color:#123b60;border:1px solid #8fc5e8;border-radius:14px}
.wheel-voice-panel[hidden]{display:none!important}
.wheel-voice-panel label{display:grid;gap:5px;font-size:.88rem;font-weight:800}
.wheel-voice-panel select{min-width:210px;max-width:100%;padding:8px 10px;border:1px solid #8eb6d1;border-radius:8px;
  background:#fff;color:#143b58;font:inherit}
.wheel-voice-panel input[type=range]{min-width:150px;accent-color:#1477bb}
.wheel-voice-panel output,.wheel-voice-status{font-size:.88rem;font-weight:700;color:#174c70}
.wheel-voice-status{flex:1 1 220px}
.wheel-ai-button{border:1px solid #9cc5e3!important;background:#eef8ff!important;color:#12476e!important;
  box-shadow:0 4px 0 #9cc5e3!important;font-size:.88rem!important;padding:8px 10px!important}
.wheel-ai-button:disabled{opacity:.5;cursor:not-allowed}
.toolbar .wheel-ai-status{flex-basis:100%;text-align:right;max-width:none;min-height:1.3em}

.score-zone{margin-top:20px;padding-top:18px;border-top:1px solid #c6ddeb}
.score-zone h2{margin:.2em 0 .5em}
.wheel-score{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.wheel-score input{border:2px solid #a4c9e5;border-radius:10px;font:inherit;padding:10px;max-width:190px}
.wheel-score input[type=number]{max-width:90px}
#score-list{font-size:1.05rem;line-height:1.65;margin-top:8px}

@keyframes wheel-spin{to{transform:rotate(360deg)}}
@media(max-width:1120px){
  .wheel-stage{grid-template-columns:minmax(250px,350px) 1fr}
  .wheel-controls{grid-column:1/-1}
}
@media(max-width:760px){
  .wheel-stage{grid-template-columns:1fr}
  .wheel-left{text-align:center}.slot-board{margin:auto}
  .wheel-frame{max-width:420px;margin:auto}
}
@media(prefers-reduced-motion:reduce){
  .wheel-disc.spinning{animation:none!important}.wheel-disc{transition:none!important}
  .slot-button.pending{animation:none!important}
}
body:fullscreen #wheel-panel{min-height:calc(100vh - 110px)}
"""

    toolbar = (
        '<button type="button" id="wheel-home" title="Trở lại vòng quay">'
        '🎡 Vòng quay</button>'
        '<button type="button" class="wheel-ai-button" id="wheel-ai-toggle" aria-pressed="true">'
        '🔊 MC: ĐANG BẬT · bấm để tắt</button>'
        '<button type="button" class="wheel-ai-button" id="wheel-voice-settings" '
        'aria-expanded="false" aria-controls="wheel-voice-panel">🎙 Tùy chọn giọng đọc</button>'
        '<button type="button" class="wheel-ai-button" id="wheel-ai-listen" disabled>'
        '🎙 Nghe câu trả lời</button>'
        '<div class="wheel-voice-panel" id="wheel-voice-panel" hidden>'
        '<label for="wheel-voice-select">Giọng tiếng Việt'
        '<select id="wheel-voice-select"><option value="">Đang tìm giọng đọc…</option></select></label>'
        '<label for="wheel-voice-rate">Tốc độ đọc <output id="wheel-voice-rate-value">0,96×</output>'
        '<input id="wheel-voice-rate" type="range" min="0.7" max="1.3" step="0.05" value="0.96"></label>'
        '<button type="button" class="wheel-ai-button" id="wheel-voice-test">▶ Nghe thử</button>'
        '<span class="wheel-voice-status" id="wheel-voice-status" role="status" aria-live="polite">'
        'Các giọng hiển thị tùy theo giọng đã cài trên thiết bị.</span></div>'
        '<span class="wheel-ai-status" id="wheel-ai-status" role="status" aria-live="polite">'
        'MC sẽ tự đọc câu được chọn.</span>'
    )

    slot_buttons = "".join(
        f'<button type="button" class="slot-button" data-slot="{i - 1}" '
        f'aria-label="Câu {i}" disabled>{i}<span class="slot-check">✓</span></button>'
        for i in range(1, WHEEL_QUESTION_COUNT + 1)
    )

    wheel_labels = "".join(
        f'<span class="wheel-label" data-wheel-slot="{i}" aria-hidden="true">'
        f'<span class="wheel-label-text">{i + 1}</span></span>'
        for i in range(WHEEL_QUESTION_COUNT)
    )

    panel = f"""<section id="wheel-panel" aria-label="Vòng quay may mắn">
      <div class="wheel-stage">
        <div class="wheel-left">
          <div class="eyebrow">TRÒ CHƠI LỚP HỌC</div>
          <h1>VÒNG QUAY<br>MAY MẮN</h1>
          <p class="wheel-title-sub">{title_safe}</p>
          <div class="slot-board" id="slot-board">{slot_buttons}</div>
        </div>

        <div class="wheel-center">
          <div class="wheel-frame">
            <span class="wheel-pointer" aria-hidden="true"></span>
            <div class="wheel-disc" id="wheel-disc">{wheel_labels}</div>
            <div class="wheel-hub" aria-hidden="true"></div>
          </div>
        </div>

        <div class="wheel-controls">
          <p class="wheel-meta" id="wheel-remaining"></p>
          <button type="button" class="wheel-action primary" id="wheel-spin">▶ QUAY</button>
          <button type="button" class="wheel-action stop" id="wheel-stop" disabled>■ DỪNG</button>
          <button type="button" class="wheel-action" id="wheel-reset">↺ CHƠI LẠI</button>
          <p id="wheel-feedback" role="status" aria-live="polite"></p>
        </div>
      </div>

      <div class="score-zone">
        <h2>🏆 Bảng điểm</h2>
        <div class="wheel-score">
          <label>Tên học sinh / nhóm
            <input id="score-name" maxlength="60" autocomplete="off">
          </label>
          <label>Điểm
            <input type="number" id="score-points" min="1" max="100" value="10">
          </label>
          <button type="button" id="score-award">+ Cộng điểm</button>
          <button type="button" id="score-export">⬇ Tải điểm CSV</button>
        </div>
        <div id="score-list"></div>
      </div>
    </section>"""

    base = base.replace("</style>", css + "</style>", 1)
    base = base.replace(
        '<button type="button" id="fullscreen"',
        toolbar + '<button type="button" id="fullscreen"',
        1,
    )
    base = base.replace("<main>", "<main>" + panel, 1)

    script = r"""
<script>
(() => {
  'use strict';

  const QUESTION_COUNT = 9;
  const SLICE = 360 / QUESTION_COUNT;
  const key = __STORAGE__;
  const wheelAudioSrc = __WHEEL_AUDIO__;
  const aiBridgeEnabled = __AI_BRIDGE__;

  const panel = document.getElementById('wheel-panel');
  const disc = document.getElementById('wheel-disc');
  const spinButton = document.getElementById('wheel-spin');
  const stopButton = document.getElementById('wheel-stop');
  const revealButton = document.getElementById('reveal');
  const feedback = document.getElementById('wheel-feedback');
  const slotButtons = [...document.querySelectorAll('.slot-button')];
  const aiToggle = document.getElementById('wheel-ai-toggle');
  const aiListen = document.getElementById('wheel-ai-listen');
  const aiStatus = document.getElementById('wheel-ai-status');
  const voiceSettingsButton = document.getElementById('wheel-voice-settings');
  const voicePanel = document.getElementById('wheel-voice-panel');
  const voiceSelect = document.getElementById('wheel-voice-select');
  const voiceRate = document.getElementById('wheel-voice-rate');
  const voiceRateValue = document.getElementById('wheel-voice-rate-value');
  const voicePreview = document.getElementById('wheel-voice-status');
  const voiceTest = document.getElementById('wheel-voice-test');
  const voicePrefsKey = 'mathteacher-ai:voice-settings:v1';

  let aiEnabled = true;
  let recognition = null;
  let speechGeneration = 0;
  let aiResponseTimeout = null;
  let autoRevealTimer = null;
  const speechPrefs = {voiceURI:'', rate:0.96, pitch:1.04};
  try {
    const savedPrefs = JSON.parse(localStorage.getItem(voicePrefsKey) || '{}');
    if (typeof savedPrefs.voiceURI === 'string') speechPrefs.voiceURI = savedPrefs.voiceURI;
    if (Number.isFinite(savedPrefs.rate)) speechPrefs.rate = Math.max(0.7, Math.min(1.3, savedPrefs.rate));
    if (Number.isFinite(savedPrefs.pitch)) speechPrefs.pitch = Math.max(0.7, Math.min(1.3, savedPrefs.pitch));
  } catch (error) {}
  voiceRate.value = String(speechPrefs.rate);
  voiceRateValue.textContent = `${speechPrefs.rate.toFixed(2).replace('.', ',')}×`;

  function saveSpeechPrefs() {
    try { localStorage.setItem(voicePrefsKey, JSON.stringify(speechPrefs)); } catch (error) {}
  }

  function vietnameseVoices() {
    if (!('speechSynthesis' in window)) return [];
    return window.speechSynthesis.getVoices().filter(voice => /^vi(?:[-_]|$)/i.test(voice.lang || ''));
  }

  function refreshVoiceOptions() {
    const voices = vietnameseVoices();
    voiceSelect.replaceChildren();
    if (!voices.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Chưa tìm thấy giọng tiếng Việt';
      voiceSelect.appendChild(option);
      voiceSelect.disabled = true;
      voiceTest.disabled = true;
      voicePreview.textContent = 'Cài giọng Tiếng Việt trong Windows rồi khởi động lại Chrome.';
      return;
    }
    voiceSelect.disabled = false;
    voiceTest.disabled = false;
    voices.forEach(voice => {
      const option = document.createElement('option');
      option.value = voice.voiceURI;
      option.textContent = `${voice.name} (${voice.lang})`;
      voiceSelect.appendChild(option);
    });
    const savedVoice = voices.find(voice => voice.voiceURI === speechPrefs.voiceURI);
    const preferredVoice = savedVoice || voices.find(voice => /\bAn\b/i.test(voice.name)) || voices[0];
    voiceSelect.value = preferredVoice.voiceURI;
    speechPrefs.voiceURI = preferredVoice.voiceURI;
    saveSpeechPrefs();
    voicePreview.textContent = `${voices.length} giọng tiếng Việt khả dụng trên thiết bị.`;
  }

  refreshVoiceOptions();
  if ('speechSynthesis' in window) {
    window.speechSynthesis.addEventListener?.('voiceschanged', refreshVoiceOptions);
  }
  voiceSettingsButton.addEventListener('click', () => {
    voicePanel.hidden = !voicePanel.hidden;
    voiceSettingsButton.setAttribute('aria-expanded', String(!voicePanel.hidden));
    if (!voicePanel.hidden) refreshVoiceOptions();
  });
  voiceSelect.addEventListener('change', () => {
    speechPrefs.voiceURI = voiceSelect.value;
    saveSpeechPrefs();
    const voice = vietnameseVoices().find(item => item.voiceURI === speechPrefs.voiceURI);
    voicePreview.textContent = voice ? `Đã chọn giọng ${voice.name}.` : 'Chưa chọn được giọng đọc.';
  });
  voiceRate.addEventListener('input', () => {
    speechPrefs.rate = Number(voiceRate.value);
    voiceRateValue.textContent = `${speechPrefs.rate.toFixed(2).replace('.', ',')}×`;
    saveSpeechPrefs();
  });
  voiceTest.addEventListener('click', () => {
    if (!vietnameseVoice()) {
      refreshVoiceOptions();
      return;
    }
    voicePreview.textContent = 'Đang phát thử giọng đã chọn…';
    say('Xin chào! Đây là giọng đọc MC trợ giảng trong trò chơi Vòng quay may mắn.');
  });

  function stopSpeech() {
    speechGeneration += 1;
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }

  function vietnameseVoice() {
    const voices = vietnameseVoices();
    return voices.find(voice => voice.voiceURI === speechPrefs.voiceURI) || voices[0] || null;
  }

  function waitForVietnameseVoice(timeoutMs = 2500) {
    return new Promise(resolve => {
      const ready = vietnameseVoice();
      if (ready) return resolve(ready);
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        window.speechSynthesis.removeEventListener?.('voiceschanged', finish);
        resolve(vietnameseVoice());
      };
      const timer = setTimeout(finish, timeoutMs);
      window.speechSynthesis.addEventListener?.('voiceschanged', finish, {once:true});
    });
  }

  async function say(text, onend) {
    if (!aiEnabled || !('speechSynthesis' in window) ||
        typeof SpeechSynthesisUtterance === 'undefined' || !text) {
      if (onend) onend();
      return;
    }
    const request = ++speechGeneration;
    window.speechSynthesis.cancel();
    const voice = await waitForVietnameseVoice();
    if (request !== speechGeneration) return;
    if (!voice) {
      const notice = 'Thiết bị chưa có giọng đọc tiếng Việt.';
      if (!aiStatus.textContent.includes(notice)) aiStatus.textContent += ` (${notice})`;
      if (onend) onend();
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = voice;
    utterance.lang = voice.lang || 'vi-VN';
    utterance.rate = speechPrefs.rate;
    utterance.pitch = speechPrefs.pitch;
    if (onend) utterance.onend = onend;
    utterance.onerror = () => {
      if (request === speechGeneration) {
        const notice = 'Không phát được giọng tiếng Việt.';
        if (!aiStatus.textContent.includes(notice)) aiStatus.textContent += ` (${notice})`;
        if (onend) onend();
      }
    };
    window.speechSynthesis.speak(utterance);
  }

  function cleanSpeech(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase()
      .replace(/[^a-z0-9+.,-]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function assessSpokenAnswer(slide, transcript) {
    const heard = cleanSpeech(transcript);
    const choices = [...slide.querySelectorAll('.mcq')];
    if (choices.length) {
      const matched = choices.find(choice => {
        const code = cleanSpeech(choice.querySelector('b')?.textContent).replace(/\.$/, '');
        const text = cleanSpeech(choice.textContent);
        return (code && new RegExp(`(?:^|\\s)(?:dap an )?${code}(?:$|\\s)`).test(heard)) ||
          (text.length > 8 && heard.includes(text.slice(text.indexOf(' ') + 1)));
      });
      return matched ? (matched.dataset.correct === 'true' ? 'correct' : 'wrong') : 'unclear';
    }

    const truths = [...slide.querySelectorAll('.truth')];
    if (truths.length === 1) {
      if (/\b(dung|dung a|true)\b/.test(heard))
        return truths[0].dataset.correct === 'true' ? 'correct' : 'wrong';
      if (/\b(sai|false)\b/.test(heard))
        return truths[0].dataset.correct === 'false' ? 'correct' : 'wrong';
      return 'unclear';
    }

    const shortAnswer = slide.querySelector('.answer p:not(:has(strong))');
    const expected = cleanSpeech(shortAnswer?.textContent);
    if (expected && heard && (heard === expected || heard.includes(expected))) return 'correct';
    return 'teacher-check';
  }

  function respondToStudent(transcript) {
    if (active === null) return;
    if (aiBridgeEnabled) {
      const eventId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      aiStatus.textContent = 'Trợ giảng đang nghe và chuẩn bị phản hồi…';
      clearTimeout(aiResponseTimeout);
      aiResponseTimeout = setTimeout(() => {
        aiStatus.textContent = 'Chưa nhận được phản hồi từ máy chủ AI. Hãy thử lại hoặc kiểm tra kết nối AI của ứng dụng.';
      }, 30000);
      window.parent.postMessage({mathteacherWheel: {
        event_id: eventId, action: 'student_answer', question_index: active,
        transcript: String(transcript || '').slice(0, 1000)
      }}, '*');
      return;
    }
    const slide = slides[active];
    const result = assessSpokenAnswer(slide, transcript);
    const messages = {
      correct: `Câu trả lời của đội là: ${transcript}. Chính xác! Xin chúc mừng cả đội.`,
      wrong: `Câu trả lời của đội là: ${transcript}. Chưa chính xác, các đội hãy thử suy nghĩ thêm nhé.`,
      unclear: `MC nghe được: ${transcript}. Câu trả lời chưa rõ để chấm tự động; thầy cô hãy xác nhận giúp nhé.`,
      'teacher-check': `MC đã ghi nhận câu trả lời: ${transcript}. Mời thầy cô xác nhận đáp án và điểm số.`
    };
    aiStatus.textContent = messages[result];
    say(messages[result]);
  }

  function sendOperatorAnswer(selection) {
    if (!aiBridgeEnabled || !aiEnabled || active === null) return;
    const eventId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    aiStatus.textContent = 'Đã nhận câu trả lời. Trợ giảng đang kiểm tra…';
    clearTimeout(aiResponseTimeout);
    aiResponseTimeout = setTimeout(() => {
      aiStatus.textContent = 'Chưa nhận được phản hồi từ trợ giảng. Hãy kiểm tra kết nối AI của ứng dụng.';
    }, 30000);
    window.parent.postMessage({mathteacherWheel: {
      event_id: eventId, action: 'operator_answer', question_index: active, selection
    }}, '*');
  }

  function scheduleAutomaticReveal(message) {
    if (autoRevealTimer !== null) clearTimeout(autoRevealTimer);
    aiStatus.textContent = 'Đã ghi nhận lựa chọn. Sau 3 giây MC sẽ đọc kết quả và tự hiện đáp án.';
    autoRevealTimer = setTimeout(() => {
      autoRevealTimer = null;
      if (active === null || !aiEnabled) return;

      const soundButton = document.getElementById('sound');
      if (typeof sound !== 'undefined' && !sound) {
        sound = true;
        if (soundButton) {
          soundButton.textContent = '♫ Tắt âm thanh';
          soundButton.setAttribute('aria-pressed', 'true');
        }
      }

      const answer = slides[active]?.querySelector('.answer');
      if (answer?.hidden && revealButton) revealButton.click();
      else if (typeof playAudio === 'function') playAudio('final');

      aiStatus.textContent = message;
      say(message);
    }, 3000);
  }

  document.addEventListener('click', event => {
    if (active === null || !aiEnabled) return;
    const slide = event.target.closest?.('.slide');
    if (!slide || slide !== slides[active]) return;

    const option = event.target.closest?.('.mcq');
    if (option) {
      const code = option.querySelector('b')?.textContent?.replace(/[.．。]\s*$/, '').trim();
      if (code) {
        const correct = option.dataset.correct === 'true';
        const message = correct
          ? `Chính xác! Người điều khiển đã chọn phương án ${code}. Chúc mừng cả đội!`
          : `Phương án ${code} chưa chính xác. Các em hãy xem lại dữ kiện và thử suy nghĩ thêm nhé.`;
        scheduleAutomaticReveal(message);
      }
      return;
    }

    const truthButton = event.target.closest?.('.truth-actions button');
    if (truthButton) {
      const statement = truthButton.closest('.truth');
      const statementIndex = [...slide.querySelectorAll('.truth')].indexOf(statement);
      if (statementIndex >= 0) {
        const value = truthButton.dataset.value;
        const correct = value === statement.dataset.correct;
        const selectedText = value === 'true' ? 'Đúng' : 'Sai';
        const message = correct
          ? `Chính xác! Nhận định ${statementIndex + 1} được chọn là ${selectedText}.`
          : `Lựa chọn ${selectedText} cho nhận định ${statementIndex + 1} chưa chính xác. Hãy xem lại nhận định nhé.`;
        scheduleAutomaticReveal(message);
      }
    }
  });

  function submitTypedAnswer(input) {
    const value = input.value.trim();
    if (!value || input.dataset.mcSubmittedValue === value) return;
    input.dataset.mcSubmittedValue = value;
    const slide = input.closest('.slide');
    if (slide && active !== null && slide === slides[active]) {
      const result = assessSpokenAnswer(slide, value);
      if (result === 'correct') {
        const message = 'Chính xác! Câu trả lời đã khớp với đáp án chuẩn. Chúc mừng em!';
        scheduleAutomaticReveal(message);
        return;
      }
    }
    sendOperatorAnswer({kind:'typed_answer', answer_text:value.slice(0, 1000)});
  }

  const typedAnswerTimers = new WeakMap();
  document.addEventListener('input', event => {
    const input = event.target.closest?.('.short-label input');
    if (!input) return;
    clearTimeout(typedAnswerTimers.get(input));
    typedAnswerTimers.set(input, setTimeout(() => submitTypedAnswer(input), 900));
  });
  document.addEventListener('change', event => {
    const input = event.target.closest?.('.short-label input');
    if (input) submitTypedAnswer(input);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    const input = event.target.closest?.('.short-label input');
    if (input) {
      event.preventDefault();
      submitTypedAnswer(input);
      input.blur();
    }
  });

  function askQuestion(slot) {
    const slide = slides[slot];
    const prompt = slide?.querySelector('h1')?.innerText?.trim() || `Câu hỏi số ${slot + 1}`;
    const options = [...slide.querySelectorAll('.mcq')].map(option => option.innerText.trim());
    const statements = [...slide.querySelectorAll('.truth b')].map(item => item.innerText.trim());
    const choices = options.length ? ` Các phương án là: ${options.join('. ')}.`
      : statements.length ? ` Các nhận định là: ${statements.join('. ')}.` : '';
    aiStatus.textContent = `Câu ${slot + 1} đang được đọc. Sau khi chọn hoặc nhập đáp án, MC sẽ chốt kết quả sau 3 giây.`;
    say(`Vòng quay đã chọn câu ${slot + 1}. Mời các đội lắng nghe câu hỏi. ${prompt}${choices}`);
    aiListen.disabled = false;
  }

  aiToggle.addEventListener('click', () => {
    aiEnabled = !aiEnabled;
    aiToggle.setAttribute('aria-pressed', String(aiEnabled));
    aiToggle.textContent = aiEnabled ? '🔊 MC: ĐANG BẬT · bấm để tắt' : '🔇 MC: ĐANG TẮT · bấm để bật';
    if (!aiEnabled) {
      if (autoRevealTimer !== null) clearTimeout(autoRevealTimer);
      autoRevealTimer = null;
      stopSpeech();
      aiStatus.textContent = 'MC đang tắt. Bấm nút này để bật MC tiếng Việt.';
      if (pending !== null && active === null) openQuestion(pending);
    }
    if (aiEnabled && active !== null) askQuestion(active);
    else if (aiEnabled) aiStatus.textContent = 'MC đã bật. Bấm QUAY rồi DỪNG để chọn câu hỏi.';
  });

  aiListen.addEventListener('click', () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      aiStatus.textContent = 'Trình duyệt chưa hỗ trợ nhận dạng giọng nói. Thầy cô có thể xác nhận đáp án trực tiếp.';
      return;
    }
    if (recognition) recognition.abort();
    recognition = new SpeechRecognition();
    const currentRecognition = recognition;
    recognition.lang = 'vi-VN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => { aiStatus.textContent = 'MC đang nghe câu trả lời…'; };
    recognition.onresult = event => {
      const transcript = event.results[0][0].transcript;
      aiStatus.textContent = `MC đã nghe: “${transcript}”. Đang gửi cho trợ giảng phản hồi…`;
      respondToStudent(transcript);
    };
    recognition.onerror = event => {
      if (recognition !== currentRecognition) return;
      aiStatus.textContent = event.error === 'not-allowed'
        ? 'Trình duyệt chưa được cấp quyền dùng micro.'
        : 'MC chưa nghe rõ. Hãy bấm nghe và thử lại.';
    };
    try {
      recognition.start();
    } catch (error) {
      aiStatus.textContent = 'Không khởi động được micro. Hãy tải lại trang và kiểm tra quyền micro của Chrome.';
    }
  });

  let used = [];
  let scores = {};
  let active = null;
  let pending = null;
  let spinning = false;
  let settling = false;
  let track = null;
  let lastAngle = 0;

  try {
    const saved = JSON.parse(localStorage.getItem(key) || '{}');
    if (Array.isArray(saved.used)) {
      used = saved.used.filter(
        x => Number.isInteger(x) && x >= 0 && x < QUESTION_COUNT
      );
    }
    if (saved.scores && typeof saved.scores === 'object' && !Array.isArray(saved.scores)) {
      for (const [name, points] of Object.entries(saved.scores)) {
        if (name.length <= 60 && Number.isSafeInteger(points) && points >= 0) {
          scores[name] = points;
        }
      }
    }
  } catch (e) {
    used = [];
    scores = {};
  }
  used = [...new Set(used)];

  function save() {
    try {
      localStorage.setItem(key, JSON.stringify({used, scores}));
    } catch (e) {}
  }

  function remaining() {
    return [...Array(QUESTION_COUNT).keys()].filter(i => !used.includes(i));
  }

  function stopTrack() {
    if (track) {
      track.pause();
      track.currentTime = 0;
      track = null;
    }
  }

  function randomIndex(n) {
    if (window.crypto && crypto.getRandomValues) {
      const a = new Uint32Array(1);
      const limit = Math.floor(4294967296 / n) * n;
      do { crypto.getRandomValues(a); } while (a[0] >= limit);
      return a[0] % n;
    }
    return Math.floor(Math.random() * n);
  }

  function layoutWheelLabels() {
    const radius = disc.getBoundingClientRect().width * .34;
    disc.querySelectorAll('.wheel-label').forEach((anchor, slot) => {
      const angle = (slot + .5) * SLICE;
      anchor.style.transform = `rotate(${angle}deg)`;
      const label = anchor.querySelector('.wheel-label-text');
      label.dataset.angle = String(angle);
      label.dataset.radius = String(radius);
      label.style.transform =
        `translate(-50%,-50%) translateY(-${radius}px) rotate(-${angle + lastAngle}deg)`;
    });
  }

  function straightenLabels(stopAngle) {
    disc.querySelectorAll('.wheel-label-text').forEach(label => {
      const angle = Number(label.dataset.angle);
      const radius = Number(label.dataset.radius);
      label.style.transform =
        `translate(-50%,-50%) translateY(-${radius}px) rotate(-${angle + stopAngle}deg)`;
    });
  }

  function renderSlots() {
    slotButtons.forEach((button, slot) => {
      const isUsed = used.includes(slot);
      const isPending = pending === slot;
      button.classList.toggle('used', isUsed);
      button.classList.toggle('pending', isPending);
      button.disabled = !isPending || spinning || settling;
      button.setAttribute(
        'aria-label',
        isUsed ? `Câu ${slot + 1}, đã chơi`
          : isPending ? `Câu ${slot + 1}, được chọn, bấm để mở`
          : `Câu ${slot + 1}, chưa được chọn`
      );
    });
  }

  function render() {
    const n = remaining().length;
    document.getElementById('wheel-remaining').textContent =
      `Còn ${n} / ${QUESTION_COUNT} câu chưa chơi`;

    spinButton.disabled = n === 0 || spinning || settling || pending !== null;
    stopButton.disabled = !spinning || settling;

    renderSlots();

    const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    const list = document.getElementById('score-list');
    list.replaceChildren();

    if (!entries.length) {
      list.textContent = 'Chưa có điểm.';
      return;
    }
    for (const [name, points] of entries) {
      const row = document.createElement('div');
      row.textContent = `${name}: ${points} điểm`;
      list.appendChild(row);
    }
  }

  function clearQuestionVisuals() {
    slides.forEach(slide => {
      slide.classList.remove('wheel-active');
      slide.hidden = false;
      slide.style.removeProperty('display');
      const answer = slide.querySelector('.answer');
      if (answer) answer.hidden = true;
      slide.querySelectorAll('.correct,.incorrect,.selected').forEach(node =>
        node.classList.remove('correct', 'incorrect', 'selected')
      );
    });
  }

  function home() {
    if (autoRevealTimer !== null) clearTimeout(autoRevealTimer);
    autoRevealTimer = null;
    stopTrack();
    stopAudio();
    stopSpeech();
    const activeRecognition = recognition;
    recognition = null;
    if (activeRecognition) activeRecognition.abort();
    spinning = false;
    settling = false;
    pending = null;
    disc.classList.remove('spinning');
    document.body.classList.remove('question-selected');
    panel.hidden = false;
    clearQuestionVisuals();
    active = null;
    aiListen.disabled = true;
    aiStatus.textContent = 'MC sẽ tự đọc câu được chọn.';
    if (revealButton) revealButton.disabled = true;
    feedback.textContent = remaining().length
      ? 'Sẵn sàng. Bấm QUAY, sau đó bấm DỪNG.'
      : 'Đã hoàn thành 9 câu. Chọn CHƠI LẠI để bắt đầu phiên mới.';
    render();
  }

  function openQuestion(slot) {
    if (pending !== slot || spinning || settling || used.includes(slot)) return;

    if (autoRevealTimer !== null) clearTimeout(autoRevealTimer);
    autoRevealTimer = null;

    active = slot;
    pending = null;
    clearQuestionVisuals();

    // Sync the base classroom stage first.
    show(slot);

    // R15.3: the base stage writes a normal inline display value, while wheel
    // mode hides every slide with !important. Explicitly promote only the
    // selected approved-question slide with an important inline display.
    slides.forEach((slide, i) => {
      const selected = i === slot;
      slide.classList.toggle('wheel-active', selected);
      slide.hidden = !selected;
      slide.style.setProperty('display', selected ? 'block' : 'none', 'important');
    });

    const selectedSlide = slides[slot];
    if (!selectedSlide) {
      feedback.textContent = 'Không tìm thấy nội dung câu hỏi đã chọn.';
      return;
    }

    panel.hidden = true;
    document.body.classList.add('question-selected');

    used.push(slot);
    used = [...new Set(used)];
    save();

    if (revealButton) revealButton.disabled = false;
    if (aiEnabled) askQuestion(slot);
    else playAudio('question');
    render();

    requestAnimationFrame(() => {
      selectedSlide.scrollIntoView({block: 'start', inline: 'nearest'});
    });
  }

  document.body.classList.add('wheel-mode');
  requestAnimationFrame(layoutWheelLabels);
  addEventListener('resize', layoutWheelLabels);

  window.addEventListener('message', event => {
    if (event.source !== window.parent || !event.data?.mathteacherAssistantResponse) return;
    const response = event.data.mathteacherAssistantResponse;
    if (!response.event_id || response.event_id === window.__lastMathteacherResponse) return;
    clearTimeout(aiResponseTimeout);
    aiResponseTimeout = null;
    window.__lastMathteacherResponse = response.event_id;
    const message = String(response.text || 'Trợ giảng chưa thể phản hồi lúc này.').slice(0, 1200);
    scheduleAutomaticReveal(message);
  });

  document.getElementById('sound').onclick = () => {
    sound = !sound;
    const button = document.getElementById('sound');
    button.textContent = sound ? '♫ Tắt âm thanh' : '♪ Bật âm thanh';
    button.setAttribute('aria-pressed', String(sound));
    if (!sound) {
      stopAudio();
      stopTrack();
      effectLayer.stop();
    } else if (active !== null) {
      const answer = slides[active].querySelector('.answer');
      playAudio(answer && answer.hidden ? 'question' : 'final');
    }
  };

  document.getElementById('wheel-home').onclick = home;

  slotButtons.forEach((button, slot) => {
    button.addEventListener('click', () => openQuestion(slot));
  });

  spinButton.onclick = () => {
    if (!remaining().length || spinning || settling || pending !== null) return;

    stopAudio();
    panel.hidden = false;
    spinning = true;
    disc.classList.add('spinning');
    feedback.textContent = 'Đang quay… bấm DỪNG để chọn ngẫu nhiên một câu chưa chơi.';
    render();

    if (sound) {
      track = new Audio(wheelAudioSrc);
      track.loop = true;
      track.volume = .38;
      track.play().catch(() => {
        stopTrack();
        feedback.textContent = 'Âm quay bị chặn; vòng quay vẫn hoạt động.';
      });
    }
  };

  stopButton.onclick = () => {
    if (!spinning || settling) return;

    const pool = remaining();
    if (!pool.length) {
      home();
      return;
    }

    const chosen = pool[randomIndex(pool.length)];
    spinning = false;
    settling = true;
    stopTrack();

    const center = (chosen + .5) * SLICE;
    const target = (360 - center) % 360;
    const turns = 4 + randomIndex(3);
    const finalAngle = turns * 360 + target;

    disc.classList.remove('spinning');
    lastAngle = target;
    straightenLabels(target);
    disc.style.transform = `rotate(${finalAngle}deg)`;

    feedback.textContent = 'Đang dừng bánh xe…';
    render();

    const delay = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1850;
    setTimeout(() => {
      settling = false;
      pending = chosen;
      feedback.textContent =
        `Mũi tên đã chọn CÂU ${chosen + 1}. MC đang mở câu hỏi…`;
      render();
      say(`Vòng quay dừng ở câu số ${chosen + 1}.`, () => openQuestion(chosen));
    }, delay);
  };

  document.getElementById('wheel-reset').onclick = () => {
    if (!confirm(
      'Bắt đầu lại? Danh sách câu đã chơi và bảng điểm trong buổi này sẽ bị xóa.'
    )) return;

    used = [];
    scores = {};
    pending = null;
    lastAngle = 0;
    disc.style.transform = 'rotate(0deg)';
    save();
    home();
    requestAnimationFrame(layoutWheelLabels);
  };

  document.getElementById('score-award').onclick = () => {
    const name = document.getElementById('score-name').value.trim();
    const value = Number(document.getElementById('score-points').value);

    if (active === null) {
      feedback.textContent = 'Hãy mở một câu hỏi trước khi cộng điểm.';
      return;
    }
    if (!name || name.length > 60 || !Number.isInteger(value) || value < 1 || value > 100) {
      alert('Nhập tên nhóm và điểm nguyên từ 1 đến 100.');
      return;
    }

    scores[name] = (scores[name] || 0) + value;
    save();
    render();
  };

  document.getElementById('score-export').onclick = () => {
    const safe = [
      '"Tên học sinh / nhóm","Điểm"',
      ...Object.entries(scores).map(([name, points]) => {
        const safeName = /^[=+@\-\t\r]/.test(name) ? "'" + name : name;
        return `"${safeName.replace(/"/g, '""')}","${points}"`;
      })
    ];

    const blob = new Blob(
      ['\ufeff' + safe.join('\r\n')],
      {type: 'text/csv;charset=utf-8'}
    );
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'bang-diem-vong-quay.csv';
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  };

  home();
})();
</script>
"""

    script = (
        script.replace("__STORAGE__", storage)
        .replace("__WHEEL_AUDIO__", wheel_sound)
        .replace("__AI_BRIDGE__", "true" if ai_bridge else "false")
    )
    return base.replace("</body>", script + "</body>", 1).encode("utf-8")


def render_ai_integrated_wheel(st, html: bytes, slides: list[tuple[dict, dict]], *, session_id: str) -> None:
    """Render the wheel as a bidirectional Streamlit component and route answers to AI."""
    import streamlit.components.v1 as components

    component_dir = Path(__file__).with_name("classroom_lucky_wheel_component")
    component = components.declare_component(
        "mathteacher_lucky_wheel_ai_mc_v1",
        path=str(component_dir),
    )
    event = component(
        html=html.decode("utf-8"),
        ai_response=st.session_state.get(f"wheel_ai_response:{session_id}"),
        key=f"classroom_wheel_ai_component_{session_id}",
        default=None,
    )
    if not isinstance(event, dict) or event.get("action") not in {"student_answer", "operator_answer"}:
        return
    event_id = str(event.get("event_id", ""))[:100]
    processed_key = f"wheel_ai_processed:{session_id}"
    if not event_id or st.session_state.get(processed_key) == event_id:
        return
    st.session_state[processed_key] = event_id

    try:
        index = int(event.get("question_index", -1))
        transcript = str(event.get("transcript", "")).strip()[:1000]
        if not 0 <= index < len(slides):
            raise ValueError("Không nhận được câu hỏi hợp lệ.")
        row, detail = slides[index]
        kind = str(row.get("question_type_code", ""))
        classification = "teacher-check"
        assessment = ""
        if event.get("action") == "operator_answer":
            selection = event.get("selection")
            if not isinstance(selection, dict):
                raise ValueError("Không nhận được lựa chọn của người điều khiển.")
            selection_kind = str(selection.get("kind", ""))
            if selection_kind == "multiple_choice" and kind == "MULTIPLE_CHOICE":
                code = str(selection.get("option_code", "")).strip()
                approved_codes = {
                    str(option.get("option_code", "")).strip()
                    for option in detail.get("options", [])
                }
                if not code or code not in approved_codes:
                    raise ValueError("Phương án được chọn không thuộc câu hỏi hiện tại.")
                transcript = f"Người điều khiển chọn phương án {code}."
                classification, assessment = _classify_multiple_choice(detail, f"em chọn {code}")
            elif selection_kind == "true_false" and kind == "TRUE_FALSE":
                statement_index = int(selection.get("statement_index", -1))
                selected_value = str(selection.get("value", ""))
                classification, assessment = _classify_true_false_selection(
                    detail, statement_index, selected_value
                )
                transcript = (
                    f"Người điều khiển chọn nhận định {statement_index + 1} là "
                    f"{'Đúng' if selected_value == 'true' else 'Sai'}."
                )
            elif selection_kind == "typed_answer":
                transcript = str(selection.get("answer_text", "")).strip()[:1000]
                if transcript:
                    assessment = (
                        "Người điều khiển đã ghi nhận câu trả lời tự luận của học sinh; "
                        "hãy so sánh nội dung với đáp án chuẩn, chỉ kết luận khi đủ căn cứ."
                    )
            else:
                raise ValueError("Kiểu lựa chọn không khớp với câu hỏi hiện tại.")
        if not transcript:
            raise ValueError("Không nhận được câu trả lời hợp lệ.")
        answers = [
            str(answer.get("exact_answer_text", "")).strip()
            for answer in detail.get("answers", [])
            if str(answer.get("exact_answer_text", "")).strip()
        ]
        if kind == "MULTIPLE_CHOICE":
            classification, assessment = _classify_multiple_choice(detail, transcript)
            answers = [
                "Phương án " + ", ".join(
                    str(option.get("option_code", ""))
                    for option in detail.get("options", [])
                    if option.get("is_correct")
                )
            ]
        elif kind == "TRUE_FALSE":
            answers = [
                "; ".join(
                    f"{position}. {'Đúng' if statement.get('correct_value') else 'Sai'}"
                    for position, statement in enumerate(detail.get("statements", []), 1)
                )
            ]

        if classification == "unclear":
            text = "MC chưa nhận ra em chọn phương án nào. Em hãy nói rõ mã phương án, ví dụ: ‘Em chọn A’."
        else:
            if not assessment:
                assessment = (
                    "Hãy tự đối chiếu câu trả lời với đáp án chuẩn. Nếu chưa đủ dữ liệu để chấm, "
                    "mời giáo viên xác nhận; không đoán."
                )

            fallback_feedback = {
                "correct": "Chính xác! Em đã chọn đúng đáp án. Cả lớp hãy chúc mừng bạn nhé!",
                "wrong": "Chưa chính xác. Em hãy đọc lại dữ kiện và thử suy nghĩ thêm một bước nhé!",
                "teacher-check": "MC đã ghi nhận câu trả lời. Mời thầy cô xác nhận đáp án và tiếp tục trò chơi nhé.",
            }

            from ai_kernel.teaching_voice import AIKernelTeachingBrain

            prompt = (
                "Bạn là MC kiêm trợ giảng Toán 6 trong trò chơi Vòng quay may mắn. "
                "Hãy phản hồi trực tiếp, tự nhiên, tối đa 2 câu, bằng tiếng Việt. "
                "Ưu tiên kết luận đối chiếu bên dưới, kết luận này là chuẩn và không được thay đổi. "
                "Nếu đúng, khen ngắn gọn. Nếu sai, động viên và cho một gợi ý nhỏ, không tiết lộ đáp án. "
                "Nếu chưa đủ dữ liệu, mời giáo viên xác nhận. Không cộng điểm.\n\n"
                f"Câu hỏi: {row.get('prompt_text', '')}\n"
                f"Đáp án chuẩn dành riêng cho trợ giảng: {'; '.join(answers) or 'Chưa có đáp án.'}\n"
                f"Kết luận đối chiếu: {assessment}\n"
                f"Câu học sinh vừa nói: {transcript}"
            )
            try:
                response = AIKernelTeachingBrain().respond(
                    transcript=prompt,
                    system_prompt=(
                        "Bạn là MC trợ giảng Toán thân thiện cho học sinh lớp 6. "
                        "Kết luận chấm máy đã cung cấp là bắt buộc và chính xác. "
                        "Không bịa, không đổi đúng thành sai hoặc sai thành đúng, "
                        "không tiết lộ đáp án khi học sinh sai."
                    ),
                    mode="student",
                    channel="chat",
                )
                text = str(response or "").strip()[:1200]
                if not text:
                    raise RuntimeError("AI chưa tạo được phản hồi.")
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Lucky wheel AI response failed")
                text = fallback_feedback[classification]
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Lucky wheel AI response failed")
        text = "MC chưa thể chấm câu này do thiếu dữ liệu đáp án. Mời thầy cô xác nhận giúp nhé."
    st.session_state[f"wheel_ai_response:{session_id}"] = {
        "event_id": event_id,
        "text": text,
    }
    st.rerun()
