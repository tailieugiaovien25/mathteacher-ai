"""Offline 9-question lucky-wheel mode for the MathTeacherAI classroom stage."""
from __future__ import annotations

import json
from html import escape

from portal_v2.ui.classroom_sound_layer import stage_audio_sources


WHEEL_QUESTION_COUNT = 9


def build_offline_wheel(
    title: str,
    slides: list[tuple[dict, dict]],
    *,
    session_id: str,
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

  const panel = document.getElementById('wheel-panel');
  const disc = document.getElementById('wheel-disc');
  const spinButton = document.getElementById('wheel-spin');
  const stopButton = document.getElementById('wheel-stop');
  const revealButton = document.getElementById('reveal');
  const feedback = document.getElementById('wheel-feedback');
  const slotButtons = [...document.querySelectorAll('.slot-button')];

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
    stopTrack();
    stopAudio();
    spinning = false;
    settling = false;
    pending = null;
    disc.classList.remove('spinning');
    document.body.classList.remove('question-selected');
    panel.hidden = false;
    clearQuestionVisuals();
    active = null;
    if (revealButton) revealButton.disabled = true;
    feedback.textContent = remaining().length
      ? 'Sẵn sàng. Bấm QUAY, sau đó bấm DỪNG.'
      : 'Đã hoàn thành 9 câu. Chọn CHƠI LẠI để bắt đầu phiên mới.';
    render();
  }

  function openQuestion(slot) {
    if (pending !== slot || spinning || settling || used.includes(slot)) return;

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
    playAudio('question');
    render();

    requestAnimationFrame(() => {
      selectedSlide.scrollIntoView({block: 'start', inline: 'nearest'});
    });
  }

  document.body.classList.add('wheel-mode');
  requestAnimationFrame(layoutWheelLabels);
  addEventListener('resize', layoutWheelLabels);

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
        `Mũi tên đã chọn CÂU ${chosen + 1}. Bấm ô số ${chosen + 1} để mở câu hỏi.`;
      render();
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
    )
    return base.replace("</body>", script + "</body>", 1).encode("utf-8")
