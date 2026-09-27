# Offline classroom game-show stage for MathTeacherAI - R29 Gameshow Pro.
from __future__ import annotations

from html import escape
import json
from typing import Any

from portal_v2.ui.classroom_sound_layer import stage_audio_sources


def _h(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def _slide(row: dict, detail: dict, index: int) -> str:
    kind = str(row.get("question_type_code") or "")
    options = detail.get("options") or []
    statements = detail.get("statements") or []
    answers = detail.get("answers") or []
    solutions = detail.get("solutions") or []

    if kind == "MULTIPLE_CHOICE":
        body = "".join(
            '<button type="button" class="choice mcq" '
            f'data-correct="{str(bool(o.get("is_correct"))).lower()}">'
            f'<b>{_h(o.get("option_code"))}.</b> {_h(o.get("option_text"))}'
            "</button>"
            for o in options
        )
        summary = "Phương án đúng: " + ", ".join(
            str(o.get("option_code") or "")
            for o in options
            if o.get("is_correct")
        )
    elif kind == "TRUE_FALSE":
        body = "".join(
            '<div class="choice truth" '
            f'data-correct="{str(bool(s.get("correct_value"))).lower()}">'
            f'<b>{i}. {_h(s.get("statement_text"))}</b>'
            '<div class="truth-actions">'
            '<button type="button" data-value="true">Đúng</button>'
            '<button type="button" data-value="false">Sai</button>'
            "</div></div>"
            for i, s in enumerate(statements, 1)
        )
        summary = "; ".join(
            f"{i}. {'Đúng' if s.get('correct_value') else 'Sai'}"
            for i, s in enumerate(statements, 1)
        )
    else:
        body = (
            '<div class="open-answer">'
            '<div class="open-answer-title">Học sinh trình bày câu trả lời</div>'
            '<div class="open-answer-lines"></div>'
            "</div>"
        )
        summary = ""

    answer_text = "".join(
        f'<p>{_h(a.get("exact_answer_text"))}</p>'
        f'<p>{_h(a.get("answer_explanation"))}</p>'
        for a in answers
        if a.get("exact_answer_text") or a.get("answer_explanation")
    )
    solution_text = "".join(
        f'<p>{_h(s.get("solution_text"))}</p>'
        for s in solutions
        if s.get("solution_text")
    )
    item = row.get("item") or {}
    code = item.get("question_code") or ""
    return (
        f'<section class="question-slide" id="q-{index}" data-index="{index-1}" '
        f'data-kind="{_h(kind)}">'
        '<div class="question-topline">'
        f'<span class="question-number">CÂU {index}</span>'
        f'<span class="question-code">{_h(code)}</span>'
        "</div>"
        f'<h1>{_h(row.get("prompt_text"))}</h1>'
        f'<div class="choices">{body}</div>'
        '<div class="answer-panel" hidden>'
        '<div class="answer-title">ĐÁP ÁN &amp; LỜI GIẢI</div>'
        f'<div class="answer-summary">{_h(summary)}</div>'
        f'{answer_text}{solution_text}'
        "</div>"
        "</section>"
    )


def build_offline_gameshow(
    title: str,
    slides: list[tuple[dict, dict]],
    *,
    session_id: str = "",
) -> bytes:
    if not slides:
        raise ValueError("Gameshow chưa có câu hỏi.")

    content = "".join(
        _slide(row, detail, i)
        for i, (row, detail) in enumerate(slides, 1)
    )
    audio_json = json.dumps(stage_audio_sources(), ensure_ascii=False)
    storage_key = json.dumps(
        f"mathteacher-gameshow-r28:{session_id or title}",
        ensure_ascii=False,
    )
    title_html = _h(title)

    html = r'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · MathTeacherAI Gameshow</title>
<style>
:root{
  color-scheme:dark;
  font-family:"Segoe UI",Arial,sans-serif;
  --bg:#061427;--panel:#0c2340;--ink:#f8fbff;--muted:#b8d5ef;
  --cyan:#44e2e0;--blue:#45a9ff;--gold:#ffd166;--green:#52e39b;
  --red:#ff6b73;--purple:#a98cff;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:
  radial-gradient(circle at 15% 15%,#0d6da955,transparent 31%),
  radial-gradient(circle at 84% 82%,#673a9b55,transparent 33%),
  linear-gradient(145deg,#04101f,#09223e 58%,#050d19);color:var(--ink)}
body{min-height:100vh;overflow-x:hidden}
body:before{content:"";position:fixed;inset:0;pointer-events:none;
 background-image:linear-gradient(#ffffff07 1px,transparent 1px),
 linear-gradient(90deg,#ffffff07 1px,transparent 1px);
 background-size:42px 42px;mask-image:linear-gradient(to bottom,#0008,transparent 75%)}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;
 padding:10px 14px;background:#04101eea;border-bottom:1px solid #6ec8ff55;
 box-shadow:0 12px 30px #0009;backdrop-filter:blur(12px)}
.brand{font-weight:900;letter-spacing:.06em;margin-right:auto;max-width:34vw;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.progress{font-weight:900;color:#d8f5ff;background:#ffffff12;border:1px solid #ffffff25;
 border-radius:999px;padding:8px 12px}
.topbar button,.control button,.score-btn,.timer-btn{font:inherit;font-weight:800;border:1px solid #8fc7ee88;
 border-radius:10px;padding:9px 13px;background:#f5fbff;color:#0a2a48;cursor:pointer;
 box-shadow:0 4px 0 #3b6f90;transition:.16s ease}
.topbar button:hover,.control button:hover,.score-btn:hover,.timer-btn:hover{transform:translateY(-2px)}
.topbar button:active,.control button:active,.score-btn:active,.timer-btn:active{transform:translateY(2px);box-shadow:0 1px 0 #3b6f90}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:18px;padding:18px;max-width:1600px;margin:auto}
.stage{min-width:0}
.question-slide{display:none;position:relative;overflow:hidden;min-height:73vh;
 background:linear-gradient(155deg,#fff,#f3f8ff 78%);color:#112b47;border-radius:28px;
 border:1px solid #d6e8fa;box-shadow:0 16px 0 #2d5d7f,0 34px 80px #0008;
 padding:clamp(24px,4vw,62px)}
.question-slide.active{display:block;animation:enter .35s ease-out}
.question-slide:before{content:"";position:absolute;inset:0 0 auto;height:10px;
 background:linear-gradient(90deg,var(--cyan),var(--blue),var(--purple),var(--gold))}
.question-topline{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.question-number{font-weight:950;letter-spacing:.09em;background:#dff7ff;color:#0a6093;
 padding:7px 13px;border-radius:9px}
.question-code{color:#51718c;font-weight:800}
h1{font-family:"Times New Roman",serif;font-size:clamp(1.8rem,3vw,3rem);line-height:1.45;
 text-align:justify;margin:12px 0 26px;white-space:pre-wrap;overflow-wrap:anywhere}
.choice{display:block;width:100%;text-align:left;margin:12px 0;padding:14px 18px;border-radius:14px;
 border:2px solid #d7e5f1;background:#f8fbff;color:#122d48;font-family:"Times New Roman",serif;
 font-size:clamp(1.5rem,2vw,2rem);line-height:1.45;cursor:pointer;box-shadow:0 5px 0 #c3d4e1}
.choice:hover{transform:translateX(5px);border-color:#53aee1;background:#eaf8ff}
.choice.selected,.truth button.selected{background:#eadcff!important;border-color:#8259da!important;
 box-shadow:0 0 0 4px #a98cff55,0 5px 0 #6842b2!important}
.choice.correct,.truth button.correct{background:#d9f8e8!important;border-color:#209769!important;
 box-shadow:0 0 0 5px #52e39b55!important;color:#0c563c!important}
.choice.wrong,.truth button.wrong{background:#7f1d2d!important;border-color:#4b0c18!important;color:white!important}
.truth{display:flex;justify-content:space-between;align-items:center;gap:16px}
.truth-actions{display:flex;gap:8px;flex-shrink:0}
.truth button{font:inherit;font-weight:800;padding:9px 16px;border-radius:10px;border:1px solid #abc9df;background:white;color:#163c5b;cursor:pointer}
.open-answer{border:2px dashed #8db3d0;border-radius:18px;padding:18px 22px;background:#f8fbff}
.open-answer-title{font-size:1.25rem;font-weight:900;color:#315c7e}
.open-answer-lines{height:110px;background:repeating-linear-gradient(to bottom,transparent 0 34px,#b9cfe0 35px 36px)}
.answer-panel{margin-top:28px;border-radius:18px;border:2px solid #7ed4ad;background:#eaf9f1;
 padding:18px 22px;font-family:"Times New Roman",serif;font-size:1.35rem;line-height:1.5;color:#153f31}
.answer-title{font-family:"Segoe UI",Arial,sans-serif;font-weight:950;color:#14744d;letter-spacing:.04em}
.answer-summary{font-weight:900;margin:8px 0}
.side{display:flex;flex-direction:column;gap:14px}
.card{background:linear-gradient(155deg,#0c2645,#081a31);border:1px solid #7bc9ff3d;border-radius:20px;
 box-shadow:0 15px 34px #0007;padding:14px}
.card h2{margin:0 0 10px;font-size:1rem;letter-spacing:.07em;color:#bfe6ff;text-transform:uppercase}
.timer-display{font-size:3.4rem;font-weight:1000;text-align:center;font-variant-numeric:tabular-nums;
 color:#fff;text-shadow:0 0 22px #47bfff}
.timer-display.danger{color:#ffd6d9;animation:pulse .7s infinite alternate}
.timer-grid,.judge-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.timer-btn,.control button{padding:8px}
.scoreboard{display:flex;flex-direction:column;gap:8px}
.team{position:relative;border:1px solid #ffffff24;background:#ffffff0b;border-radius:15px;padding:10px;
 display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;cursor:pointer}
.team.active{border-color:var(--gold);box-shadow:0 0 0 3px #ffd1662e,0 0 28px #ffd16625}
.team.leader:after{content:"👑";position:absolute;right:8px;top:-12px;font-size:1.35rem}
.team-main{min-width:0}
.team-name{font-weight:950;font-size:1.08rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.team-meta{font-size:.78rem;color:var(--muted)}
.team-score{font-size:1.8rem;font-weight:1000;color:var(--gold);font-variant-numeric:tabular-nums}
.team-actions{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-top:6px;grid-column:1/-1}
.score-btn{padding:5px 7px;font-size:.78rem}
.score-btn.plus{background:#d8f8e8;color:#0b593b}
.score-btn.minus{background:#ffe3e6;color:#7e1e2d}
.judge-grid button{padding:12px 8px}
.judge-correct{background:#cbf8df!important;color:#0b5b3a!important}
.judge-wrong{background:#ffe0e3!important;color:#821d2b!important}
.combo-banner{min-height:36px;text-align:center;font-size:1.25rem;font-weight:1000;color:var(--gold);
 padding:7px;border-radius:12px;background:#ffffff0a}
.event-banner{display:none;position:fixed;z-index:60;left:50%;top:16%;transform:translateX(-50%);
 min-width:min(700px,86vw);text-align:center;padding:18px 26px;border:2px solid #ffd166;
 border-radius:18px;background:#091a30ee;color:#fff;font-size:clamp(1.4rem,3vw,2.8rem);font-weight:1000;
 box-shadow:0 24px 80px #000b,0 0 40px #ffd16655}
.event-banner.show{display:block;animation:banner .5s cubic-bezier(.2,.8,.2,1)}
.confetti{position:fixed;inset:0;pointer-events:none;z-index:55;overflow:hidden}
.confetti i{position:absolute;width:10px;height:18px;top:-30px;animation:fall 1.7s linear forwards}
.game-note{font-size:.8rem;color:#9cc6e5;line-height:1.4}
.pro-badge{font-size:.72rem;font-weight:1000;letter-spacing:.12em;color:#081d34;background:linear-gradient(90deg,#44e2e0,#ffd166);padding:5px 8px;border-radius:999px}
.card select{width:100%;border-radius:10px;padding:8px 10px;background:#f7fbff;color:#123856;font:inherit;font-weight:800;border:1px solid #9bc8e6}
.setup-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.setup-grid label{font-size:.78rem;color:#bfe6ff;font-weight:800}
.buzzer-btn{background:#fff1bb!important;color:#6b4b00!important}
.buzzer-btn.locked{background:#ffd166!important;color:#3b2700!important;box-shadow:0 0 0 3px #ffd1664d!important}
.buzzer-btn:disabled{opacity:.45;cursor:not-allowed}
.round-pill{font-weight:1000;color:#071b30;background:linear-gradient(90deg,#b7fbf4,#ffe59d);border-radius:999px;padding:6px 10px;text-align:center;margin:8px 0}
.event-state{min-height:32px;border-radius:10px;padding:7px 9px;background:#ffffff0c;color:#d5efff;font-weight:800;text-align:center}
.overlay{display:none;position:fixed;inset:0;z-index:80;background:
 radial-gradient(circle at 50% 30%,#195f9f66,transparent 38%),#030b16ee;
 color:white;align-items:center;justify-content:center;padding:24px;text-align:center}
.overlay.show{display:flex}
.overlay-card{width:min(900px,94vw);border:1px solid #7bc9ff66;border-radius:28px;background:linear-gradient(155deg,#0d294b,#07182d);
 box-shadow:0 35px 100px #000d;padding:clamp(28px,6vw,70px)}
.overlay-title{font-size:clamp(2rem,6vw,5.8rem);font-weight:1000;letter-spacing:.04em;text-shadow:0 0 35px #47bfff}
.overlay-sub{font-size:clamp(1rem,2vw,1.5rem);color:#ccecff;margin-top:10px}
.countdown{font-size:clamp(7rem,22vw,15rem);font-weight:1000;line-height:1;color:#ffd166;text-shadow:0 0 55px #ffd16688}
.rank-list{display:grid;gap:10px;margin:24px auto 0;max-width:650px;text-align:left}
.rank-row{display:grid;grid-template-columns:60px 1fr auto;gap:10px;align-items:center;padding:12px 16px;border-radius:14px;background:#ffffff10;border:1px solid #ffffff20}
.rank-pos{font-size:1.35rem;font-weight:1000;color:#ffd166}
.rank-name{font-size:1.15rem;font-weight:900}
.rank-score{font-size:1.4rem;font-weight:1000;color:#70e6ff}
.student-view .side{display:none!important}
.student-view .layout{grid-template-columns:1fr!important;max-width:1800px}
.student-view .topbar button:not(#studentView):not(#fullscreen){display:none!important}
.student-view .topbar .brand{max-width:none}
.student-view .question-slide{min-height:calc(100vh - 110px)}
@keyframes enter{from{opacity:.25;transform:translateY(16px) scale(.99)}to{opacity:1;transform:none}}
@keyframes pulse{from{transform:scale(1)}to{transform:scale(1.06);text-shadow:0 0 38px #ff5260}}
@keyframes banner{from{opacity:0;transform:translate(-50%,-20px) scale(.9)}to{opacity:1;transform:translate(-50%,0) scale(1)}}
@keyframes fall{to{transform:translateY(115vh) rotate(720deg);opacity:.9}}
body:fullscreen .layout{max-width:none;height:calc(100vh - 65px);padding:10px}
body:fullscreen .question-slide{min-height:calc(100vh - 85px)}
body:fullscreen h1{font-size:clamp(2.1rem,4vw,4.2rem)}
body:fullscreen .choice{font-size:clamp(1.7rem,2.7vw,2.8rem)}
@media(max-width:1050px){.layout{grid-template-columns:1fr}.side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){.topbar{align-items:stretch}.brand{max-width:none;flex-basis:100%}.layout{padding:8px}.side{grid-template-columns:1fr}.truth{display:block}.truth-actions{margin-top:10px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<nav class="topbar">
  <div class="brand">🎤 __TITLE__</div>
  <span class="pro-badge">GAMESHOW PRO</span>
  <div class="progress" id="progress"></div>
  <button id="intro">▶ Mở màn</button>
  <button id="ranking">🏁 Xếp hạng</button>
  <button id="studentView">🎬 Màn hình HS</button>
  <button id="prev">← Trước</button>
  <button id="reveal">Hiện đáp án</button>
  <button id="next">Tiếp →</button>
  <button id="sound">♪ Âm thanh</button>
  <button id="fullscreen">⛶ Toàn màn hình</button>
</nav>

<div class="layout">
  <main class="stage">__CONTENT__</main>

  <aside class="side">
    <section class="card">
      <h2>🎮 Thiết lập trận đấu</h2>
      <div class="setup-grid">
        <label>Số đội
          <select id="teamCount">
            <option value="2">2 đội</option><option value="3">3 đội</option>
            <option value="4" selected>4 đội</option><option value="5">5 đội</option>
            <option value="6">6 đội</option>
          </select>
        </label>
        <label>Vòng thi
          <select id="roundSelect">
            <option value="0">Khởi động · x1</option>
            <option value="1">Tăng tốc · x2</option>
            <option value="2">Về đích · x3</option>
          </select>
        </label>
      </div>
      <div class="round-pill" id="roundPill">KHỞI ĐỘNG · ĐIỂM x1</div>
      <div class="control" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <button id="openBuzzer">🔔 Mở Buzzer</button>
        <button id="randomEvent">🎁 Sự kiện</button>
      </div>
      <div class="event-state" id="eventState">Không có sự kiện đang chờ.</div>
    </section>

    <section class="card">
      <h2>⏱ Đồng hồ</h2>
      <div class="timer-display" id="timer">30</div>
      <div class="timer-grid">
        <button class="timer-btn" data-time="10">10s</button>
        <button class="timer-btn" data-time="20">20s</button>
        <button class="timer-btn" data-time="30">30s</button>
        <button class="timer-btn" data-time="45">45s</button>
        <button class="timer-btn" data-time="60">60s</button>
        <button class="timer-btn" id="timerStart">▶ / ⏸</button>
      </div>
      <div class="game-note">5 giây cuối phát tín hiệu ngắn. Hết giờ không tự hiện đáp án.</div>
    </section>

    <section class="card">
      <h2>🏆 Bảng điểm đội</h2>
      <div class="scoreboard" id="scoreboard"></div>
      <div class="game-note">Buzzer: nút 🔔 hoặc phím 1–6. Đội bấm đầu tiên được khóa quyền trả lời.</div>
    </section>

    <section class="card">
      <h2>🎯 Chấm nhanh</h2>
      <div class="judge-grid">
        <button class="judge-correct" id="judgeCorrect">✓ Đúng +10</button>
        <button class="judge-wrong" id="judgeWrong">✕ Sai</button>
        <button id="resetStreak">↺ Combo</button>
      </div>
      <div class="combo-banner" id="combo">Sẵn sàng!</div>
      <div class="game-note">Điểm chỉ thay đổi khi giáo viên bấm chấm hoặc nút +/- ở bảng điểm.</div>
    </section>

    <section class="card">
      <h2>✨ Điều khiển sân khấu</h2>
      <div class="control" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <button id="spotlight">🔦 Spotlight</button>
        <button id="celebrate">🎉 Ăn mừng</button>
        <button id="resetGame">↺ Reset điểm</button>
        <button id="renameTeams">✎ Đổi tên đội</button>
        <button id="showRanking">🏁 Bảng xếp hạng</button>
        <button id="finale">🏆 Chung kết</button>
      </div>
    </section>
  </aside>
</div>

<div class="event-banner" id="eventBanner"></div>
<div class="confetti" id="confetti"></div>

<div class="overlay" id="introOverlay">
  <div class="overlay-card">
    <div class="overlay-title">🎤 __TITLE__</div>
    <div class="overlay-sub">MathTeacherAI · Gameshow Pro</div>
    <div class="countdown" id="countdown">3</div>
    <div class="overlay-sub">Sẵn sàng chinh phục thử thách!</div>
  </div>
</div>

<div class="overlay" id="rankingOverlay">
  <div class="overlay-card">
    <div class="overlay-title" id="rankingTitle">🏁 BẢNG XẾP HẠNG</div>
    <div class="rank-list" id="rankList"></div>
    <div class="overlay-sub">Bấm ESC hoặc phím R để đóng.</div>
  </div>
</div>

<script>
const AUDIO=__AUDIO__;
const STORAGE_KEY=__STORAGE_KEY__;
const slides=[...document.querySelectorAll('.question-slide')];
const ROUND_DATA=[
  {name:'KHỞI ĐỘNG',multiplier:1},
  {name:'TĂNG TỐC',multiplier:2},
  {name:'VỀ ĐÍCH',multiplier:3}
];
let current=0;
let sound=false;
let timerDefault=30;
let timeLeft=30;
let timerId=null;
let timerRunning=false;
let lastBeepSecond=null;
let teams=[
  {name:'Đội 1',score:0,streak:0},
  {name:'Đội 2',score:0,streak:0},
  {name:'Đội 3',score:0,streak:0},
  {name:'Đội 4',score:0,streak:0}
];
let activeTeam=0;
let spotlight=false;
let roundIndex=0;
let buzzerOpen=true;
let lockedTeam=null;
let eventMultiplier=1;
let eventLabel='';
let studentView=false;

function save(){
  try{
    localStorage.setItem(STORAGE_KEY,JSON.stringify({
      current,teams,activeTeam,timerDefault,roundIndex,buzzerOpen,lockedTeam,
      eventMultiplier,eventLabel,studentView
    }))
  }catch(e){}
}
function load(){
  try{
    const raw=localStorage.getItem(STORAGE_KEY);
    if(!raw)return;
    const data=JSON.parse(raw);
    if(Number.isInteger(data.current)&&data.current>=0&&data.current<slides.length)current=data.current;
    if(Array.isArray(data.teams)&&data.teams.length>=2&&data.teams.length<=6)teams=data.teams;
    if(Number.isInteger(data.activeTeam)&&data.activeTeam>=0&&data.activeTeam<teams.length)activeTeam=data.activeTeam;
    if([10,20,30,45,60].includes(data.timerDefault))timerDefault=data.timerDefault;
    if(Number.isInteger(data.roundIndex)&&data.roundIndex>=0&&data.roundIndex<ROUND_DATA.length)roundIndex=data.roundIndex;
    if(typeof data.buzzerOpen==='boolean')buzzerOpen=data.buzzerOpen;
    if(data.lockedTeam===null||(Number.isInteger(data.lockedTeam)&&data.lockedTeam>=0&&data.lockedTeam<teams.length))lockedTeam=data.lockedTeam;
    if(data.eventMultiplier===2)eventMultiplier=2;
    if(typeof data.eventLabel==='string')eventLabel=data.eventLabel;
    if(typeof data.studentView==='boolean')studentView=data.studentView;
  }catch(e){}
}

const players={};
function play(role,volume=.55){
  if(!sound||!AUDIO[role])return;
  let p=players[role];
  if(!p){p=new Audio(AUDIO[role]);players[role]=p}
  try{p.pause();p.currentTime=0;p.volume=volume;p.play().catch(()=>{})}catch(e){}
}
function tone(freq=880,duration=.08){
  if(!sound)return;
  try{
    const C=window.AudioContext||window.webkitAudioContext;
    const ctx=tone.ctx||(tone.ctx=new C());
    const o=ctx.createOscillator(),g=ctx.createGain();
    o.frequency.value=freq;g.gain.value=.045;o.connect(g);g.connect(ctx.destination);
    o.start();g.gain.exponentialRampToValueAtTime(.0001,ctx.currentTime+duration);o.stop(ctx.currentTime+duration);
  }catch(e){}
}

function currentSlide(){return slides[current]}
function showQuestion(index){
  current=Math.max(0,Math.min(slides.length-1,index));
  slides.forEach((s,i)=>s.classList.toggle('active',i===current));
  document.querySelector('#progress').textContent=`${current+1}/${slides.length}`;
  document.querySelector('#reveal').textContent=currentSlide().querySelector('.answer-panel').hidden?'Hiện đáp án':'Ẩn đáp án';
  resetTimer(false);
  save();
}
function reveal(){
  const s=currentSlide(),answer=s.querySelector('.answer-panel');
  answer.hidden=!answer.hidden;
  if(!answer.hidden){
    s.querySelectorAll('.mcq').forEach(b=>{
      if(b.dataset.correct==='true')b.classList.add('correct');
      else if(b.classList.contains('selected'))b.classList.add('wrong');
    });
    s.querySelectorAll('.truth').forEach(t=>{
      t.querySelectorAll('button').forEach(b=>{
        if(b.dataset.value===t.dataset.correct)b.classList.add('correct');
        else if(b.classList.contains('selected'))b.classList.add('wrong');
      });
    });
    play('reveal',.45);setTimeout(()=>play('final',.55),650);
  }else{
    s.querySelectorAll('.correct,.wrong').forEach(x=>x.classList.remove('correct','wrong'));
  }
  document.querySelector('#reveal').textContent=answer.hidden?'Hiện đáp án':'Ẩn đáp án';
}
function renderScoreboard(){
  const board=document.querySelector('#scoreboard');
  board.innerHTML='';
  const max=Math.max(...teams.map(t=>t.score));
  teams.forEach((team,i)=>{
    const el=document.createElement('div');
    el.className='team'+(i===activeTeam?' active':'')+(team.score===max&&max>0?' leader':'');
    const buzzerLocked=lockedTeam!==null;
    el.innerHTML=`
      <div class="team-main">
        <div class="team-name" data-team="${i}">${escapeHtml(team.name)}</div>
        <div class="team-meta">Combo x${team.streak||0} · Phím ${i+1}</div>
      </div>
      <div class="team-score">${team.score}</div>
      <div class="team-actions">
        <button class="score-btn buzzer-btn ${lockedTeam===i?'locked':''}" data-buzz="${i}"
          ${(!buzzerOpen|| (buzzerLocked&&lockedTeam!==i))?'disabled':''}>
          ${lockedTeam===i?'🔒 ĐÃ GIÀNH':'🔔 BUZZ'}
        </button>
        <button class="score-btn plus" data-delta="10" data-team="${i}">+10</button>
        <button class="score-btn minus" data-delta="-5" data-team="${i}">−5</button>
      </div>`;
    el.onclick=(e)=>{
      const buzz=e.target.closest('[data-buzz]');
      if(buzz){e.stopPropagation();buzzTeam(Number(buzz.dataset.buzz));return}
      const btn=e.target.closest('.score-btn');
      if(btn){
        e.stopPropagation();
        activeTeam=Number(btn.dataset.team);
        teams[activeTeam].score+=Number(btn.dataset.delta);
        renderScoreboard();updateCombo();save();return;
      }
      activeTeam=i;renderScoreboard();updateCombo();save();
    };
    board.appendChild(el);
  });
}
function setTeamCount(count){
  count=Math.max(2,Math.min(6,Number(count)||4));
  while(teams.length<count)teams.push({name:`Đội ${teams.length+1}`,score:0,streak:0});
  if(teams.length>count)teams=teams.slice(0,count);
  if(activeTeam>=teams.length)activeTeam=0;
  if(lockedTeam!==null&&lockedTeam>=teams.length)lockedTeam=null;
  document.querySelector('#teamCount').value=String(teams.length);
  renderScoreboard();updateCombo();save();
}
function buzzTeam(index){
  if(!buzzerOpen||lockedTeam!==null||index<0||index>=teams.length)return;
  lockedTeam=index;activeTeam=index;buzzerOpen=false;
  tone(1080,.13);play('select',.5);
  banner(`🔔 ${teams[index].name} GIÀNH QUYỀN TRẢ LỜI!`,1700);
  renderScoreboard();updateCombo();save();
}
function openBuzzer(){
  lockedTeam=null;buzzerOpen=true;
  document.querySelector('#openBuzzer').textContent='🔔 Buzzer đang mở';
  setTimeout(()=>{document.querySelector('#openBuzzer').textContent='🔔 Mở Buzzer'},900);
  renderScoreboard();save();
}
function updateRound(){
  const round=ROUND_DATA[roundIndex];
  document.querySelector('#roundSelect').value=String(roundIndex);
  document.querySelector('#roundPill').textContent=`${round.name} · ĐIỂM x${round.multiplier}`;
  const base=10*round.multiplier*eventMultiplier;
  document.querySelector('#judgeCorrect').textContent=`✓ Đúng +${base}`;
  save();
}
function updateEventState(){
  const el=document.querySelector('#eventState');
  el.textContent=eventLabel||'Không có sự kiện đang chờ.';
}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function updateCombo(){
  const streak=teams[activeTeam]?.streak||0;
  const name=teams[activeTeam]?.name||'Đội';
  const box=document.querySelector('#combo');
  box.textContent=streak>=2?`🔥 ${name}: COMBO x${streak}`:`${name} · Combo x${streak}`;
}
function judge(correct){
  const team=teams[activeTeam];if(!team)return;
  const round=ROUND_DATA[roundIndex];
  if(correct){
    const gained=10*round.multiplier*eventMultiplier;
    team.score+=gained;
    team.streak=(team.streak||0)+1;
    play('win',.7);
    banner(`✅ ${team.name} +${gained} điểm!`,1200);
    if(team.streak>=2)setTimeout(()=>banner(`🔥 ${team.name} · COMBO x${team.streak}`,1300),500);
    confetti(team.streak>=3?70:38);
    eventMultiplier=1;eventLabel='';
    updateEventState();updateRound();
  }else{
    team.streak=0;play('lose',.6);banner(`💪 ${team.name} · Tiếp tục cố gắng!`,900);
  }
  lockedTeam=null;buzzerOpen=false;
  renderScoreboard();updateCombo();save();
}
function banner(text,ms=1500){
  const b=document.querySelector('#eventBanner');b.textContent=text;b.classList.add('show');
  clearTimeout(b._t);b._t=setTimeout(()=>b.classList.remove('show'),ms);
}
function confetti(count=55){
  const host=document.querySelector('#confetti');
  const palette=['#44e2e0','#45a9ff','#ffd166','#52e39b','#a98cff','#ff6b73'];
  for(let i=0;i<count;i++){
    const p=document.createElement('i');
    p.style.left=(Math.random()*100)+'vw';
    p.style.background=palette[Math.floor(Math.random()*palette.length)];
    p.style.animationDelay=(Math.random()*.45)+'s';
    p.style.transform=`rotate(${Math.random()*360}deg)`;
    host.appendChild(p);setTimeout(()=>p.remove(),2300);
  }
}
function updateTimer(){
  const el=document.querySelector('#timer');el.textContent=timeLeft;
  el.classList.toggle('danger',timeLeft<=5&&timeLeft>0);
}
function resetTimer(start=false){
  if(timerId){clearInterval(timerId);timerId=null}
  timerRunning=false;timeLeft=timerDefault;lastBeepSecond=null;updateTimer();
  if(start)toggleTimer();
}
function toggleTimer(){
  if(timerRunning){
    clearInterval(timerId);timerId=null;timerRunning=false;return;
  }
  if(timeLeft<=0)timeLeft=timerDefault;
  timerRunning=true;
  timerId=setInterval(()=>{
    timeLeft--;updateTimer();
    if(timeLeft<=5&&timeLeft>0&&lastBeepSecond!==timeLeft){tone(720+timeLeft*40,.08);lastBeepSecond=timeLeft}
    if(timeLeft<=0){
      clearInterval(timerId);timerId=null;timerRunning=false;tone(220,.35);play('lose',.35);banner('⏰ HẾT GIỜ!',1300);
    }
  },1000);
}
function randomEvent(){
  const events=[
    {
      label:'⚡ NHÂN ĐÔI ĐIỂM LƯỢT NÀY',
      apply:()=>{eventMultiplier=2;eventLabel='⚡ x2 điểm cho lần chấm đúng tiếp theo';updateRound()}
    },
    {
      label:'⏱ THÊM 10 GIÂY',
      apply:()=>{timeLeft+=10;eventLabel='⏱ Đã cộng 10 giây';updateTimer()}
    },
    {
      label:'🛟 QUYỀN TRỢ GIÚP',
      apply:()=>{eventLabel='🛟 Đội đang thi có quyền sử dụng 1 trợ giúp'}
    },
    {
      label:'🔄 CHUYỂN QUYỀN',
      apply:()=>{eventLabel='🔄 Mở lại Buzzer để đội khác giành quyền';openBuzzer()}
    },
    {
      label:'⭐ CÂU MAY MẮN',
      apply:()=>{eventLabel='⭐ Câu may mắn: giáo viên quyết định phần thưởng'}
    }
  ];
  const event=events[Math.floor(Math.random()*events.length)];
  event.apply();updateEventState();banner(event.label,1700);save();
}
function sortedTeams(){
  return teams.map((t,i)=>({...t,index:i})).sort((a,b)=>b.score-a.score||a.index-b.index);
}
function showRanking(finalMode=false){
  const overlay=document.querySelector('#rankingOverlay');
  const list=document.querySelector('#rankList');
  const ordered=sortedTeams();
  document.querySelector('#rankingTitle').textContent=finalMode?'🏆 KẾT QUẢ CHUNG CUỘC':'🏁 BẢNG XẾP HẠNG';
  list.innerHTML=ordered.map((t,i)=>`
    <div class="rank-row">
      <div class="rank-pos">${i===0?'🥇':i===1?'🥈':i===2?'🥉':'#'+(i+1)}</div>
      <div class="rank-name">${escapeHtml(t.name)}${t.streak>=2?` · 🔥 x${t.streak}`:''}</div>
      <div class="rank-score">${t.score}</div>
    </div>`).join('');
  overlay.classList.add('show');
  if(finalMode&&ordered.length){
    confetti(140);play('win',.8);
    setTimeout(()=>banner(`🏆 CHÚC MỪNG ${ordered[0].name.toUpperCase()}!`,2600),350);
  }
}
function closeOverlays(){
  document.querySelector('#introOverlay').classList.remove('show');
  document.querySelector('#rankingOverlay').classList.remove('show');
}
async function startIntro(){
  const overlay=document.querySelector('#introOverlay'),count=document.querySelector('#countdown');
  overlay.classList.add('show');play('question',.18);
  for(const value of ['3','2','1','BẮT ĐẦU!']){
    count.textContent=value;tone(value==='BẮT ĐẦU!'?1180:760,.12);
    await new Promise(resolve=>setTimeout(resolve,value==='BẮT ĐẦU!'?900:700));
  }
  overlay.classList.remove('show');confetti(55);banner('🎤 GAMESHOW BẮT ĐẦU!',1200);
}
function toggleStudentView(){
  studentView=!studentView;
  document.body.classList.toggle('student-view',studentView);
  document.querySelector('#studentView').textContent=studentView?'🎛 Trở lại MC':'🎬 Màn hình HS';
  save();
}
function renameTeams(){
  teams.forEach((t,i)=>{
    const name=prompt(`Tên đội ${i+1}:`,t.name);
    if(name&&name.trim())t.name=name.trim().slice(0,30);
  });
  renderScoreboard();updateCombo();save();
}
function resetGame(){
  if(!confirm('Đưa toàn bộ điểm, combo, vòng thi và Buzzer về trạng thái đầu?'))return;
  teams=teams.map(t=>({...t,score:0,streak:0}));
  activeTeam=0;roundIndex=0;lockedTeam=null;buzzerOpen=true;eventMultiplier=1;eventLabel='';
  renderScoreboard();updateCombo();updateEventState();updateRound();openBuzzer();save();
  banner('Đã reset Gameshow',900);
}

document.querySelectorAll('.mcq').forEach(b=>b.onclick=()=>{
  const s=b.closest('.question-slide');
  if(!s.querySelector('.answer-panel').hidden)return;
  s.querySelectorAll('.mcq').forEach(x=>x.classList.remove('selected'));
  b.classList.add('selected');play('select',.4);
});
document.querySelectorAll('.truth button').forEach(b=>b.onclick=()=>{
  const t=b.closest('.truth'),s=t.closest('.question-slide');
  if(!s.querySelector('.answer-panel').hidden)return;
  t.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));
  b.classList.add('selected');play('select',.4);
});

document.querySelector('#prev').onclick=()=>{if(current>0){showQuestion(current-1);play('question',.16)}};
document.querySelector('#next').onclick=()=>{if(current<slides.length-1){showQuestion(current+1);play('question',.16)}};
document.querySelector('#reveal').onclick=reveal;
document.querySelector('#sound').onclick=()=>{
  sound=!sound;
  document.querySelector('#sound').textContent=sound?'♫ Tắt âm':'♪ Âm thanh';
  if(sound)play('question',.14);
};
document.querySelector('#fullscreen').onclick=async()=>{
  try{if(document.fullscreenElement)await document.exitFullscreen();else await document.body.requestFullscreen()}
  catch(e){alert('Trình duyệt không cho phép. Có thể dùng F11.')}
};
document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{
  timerDefault=Number(b.dataset.time);resetTimer(false);save();
});
document.querySelector('#timerStart').onclick=toggleTimer;
document.querySelector('#judgeCorrect').onclick=()=>judge(true);
document.querySelector('#judgeWrong').onclick=()=>judge(false);
document.querySelector('#resetStreak').onclick=()=>{
  teams[activeTeam].streak=0;updateCombo();renderScoreboard();save();
};
document.querySelector('#celebrate').onclick=()=>{confetti(90);play('win',.75);banner('🎉 TUYỆT VỜI!',1500)};
document.querySelector('#spotlight').onclick=()=>{
  spotlight=!spotlight;
  document.querySelector('#spotlight').textContent=spotlight?'🔦 Spotlight: Bật':'🔦 Spotlight';
  if(spotlight){banner(`🔦 ${teams[activeTeam].name}`,900)}
};
document.querySelector('#resetGame').onclick=resetGame;
document.querySelector('#renameTeams').onclick=renameTeams;

document.querySelector('#teamCount').onchange=e=>setTeamCount(e.target.value);
document.querySelector('#roundSelect').onchange=e=>{
  roundIndex=Number(e.target.value)||0;updateRound();banner(`🎯 ${ROUND_DATA[roundIndex].name}`,950);
};
document.querySelector('#openBuzzer').onclick=openBuzzer;
document.querySelector('#randomEvent').onclick=randomEvent;
document.querySelector('#showRanking').onclick=()=>showRanking(false);
document.querySelector('#ranking').onclick=()=>showRanking(false);
document.querySelector('#finale').onclick=()=>{
  if(confirm('Công bố kết quả chung cuộc và đội chiến thắng?'))showRanking(true);
};
document.querySelector('#intro').onclick=startIntro;
document.querySelector('#studentView').onclick=toggleStudentView;
document.querySelector('#rankingOverlay').onclick=e=>{
  if(e.target===document.querySelector('#rankingOverlay'))closeOverlays();
};

document.addEventListener('keydown',e=>{
  if(e.target.matches('input,textarea,select'))return;
  if(e.key==='Escape'){closeOverlays();return}
  if(e.key==='ArrowRight')document.querySelector('#next').click();
  if(e.key==='ArrowLeft')document.querySelector('#prev').click();
  if(e.key===' '){e.preventDefault();document.querySelector('#reveal').click()}
  if(e.key.toLowerCase()==='t')toggleTimer();
  if(e.key.toLowerCase()==='c')judge(true);
  if(e.key.toLowerCase()==='x')judge(false);
  if(e.key.toLowerCase()==='f')document.querySelector('#fullscreen').click();
  if(e.key.toLowerCase()==='b')openBuzzer();
  if(e.key.toLowerCase()==='e')randomEvent();
  if(e.key.toLowerCase()==='r')document.querySelector('#rankingOverlay').classList.toggle('show');
  if(e.key.toLowerCase()==='m')toggleStudentView();
  if(/^[1-6]$/.test(e.key)){
    const index=Number(e.key)-1;
    if(index<teams.length)buzzTeam(index);
  }
});
document.addEventListener('fullscreenchange',()=>{
  document.querySelector('#fullscreen').textContent=document.fullscreenElement?'⤢ Thu nhỏ':'⛶ Toàn màn hình';
});

load();
timeLeft=timerDefault;
document.querySelector('#teamCount').value=String(teams.length);
document.body.classList.toggle('student-view',studentView);
document.querySelector('#studentView').textContent=studentView?'🎛 Trở lại MC':'🎬 Màn hình HS';
renderScoreboard();updateCombo();updateTimer();updateEventState();updateRound();showQuestion(current);
</script>
</body>
</html>'''

    html = html.replace("__TITLE__", title_html)
    html = html.replace("__CONTENT__", content)
    html = html.replace("__AUDIO__", audio_json)
    html = html.replace("__STORAGE_KEY__", storage_key)
    return html.encode("utf-8")


__all__ = ["build_offline_gameshow"]
