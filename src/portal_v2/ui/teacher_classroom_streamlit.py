"""Teacher-controlled classroom review using approved question versions only."""
from __future__ import annotations

from typing import Any
from html import escape
import json
import re
from portal_v2.ui.classroom_sound_layer import stage_audio_sources


def _rows(result: Any) -> list[dict]:
    return list(getattr(result, "data", None) or [])


def _question_bank(client: Any, user_id: str) -> list[dict]:
    items = _rows(client.table("assessment_question_items")
                  .select("question_id,question_code,grade_level,subject_code,lifecycle_status")
                  .eq("owner_user_id", user_id).limit(1000).execute())
    if not items:
        return []
    by_id = {str(item["question_id"]): item for item in items}
    versions = _rows(client.table("assessment_question_versions")
                    .select("question_id,question_version_id,prompt_text,question_type_code,cognitive_level_code,version_number")
                    .eq("review_status", "APPROVED")
                    .in_("question_id", list(by_id)).limit(1000).execute())
    return [{**version, "item": by_id[str(version["question_id"])]}
            for version in versions if str(version["question_id"]) in by_id]


def _detail(client: Any, version_id: str) -> dict:
    options = _rows(client.table("assessment_question_options")
                    .select("option_code,option_text,is_correct,sequence_number")
                    .eq("question_version_id", version_id).order("sequence_number").execute())
    statements = _rows(client.table("assessment_question_statements")
                       .select("statement_text,correct_value,sequence_number")
                       .eq("question_version_id", version_id).order("sequence_number").execute())
    answers = _rows(client.table("assessment_question_answers")
                    .select("exact_answer_text,answer_explanation")
                    .eq("question_version_id", version_id).limit(1).execute())
    solutions = _rows(client.table("assessment_question_solutions")
                      .select("solution_text,sequence_number")
                      .eq("question_version_id", version_id).order("sequence_number").limit(5).execute())
    return {"options": options, "statements": statements, "answers": answers, "solutions": solutions}


def _render_question(st: Any, client: Any, row: dict, *, show_answer: bool) -> None:
    st.markdown("#### CÂU HỎI")
    st.markdown(str(row["prompt_text"]))
    detail = _detail(client, str(row["question_version_id"]))
    kind = row["question_type_code"]
    if kind == "MULTIPLE_CHOICE":
        for option in detail["options"]:
            st.markdown(f"**{option['option_code']}.** {option['option_text']}")
    elif kind == "TRUE_FALSE":
        for index, statement in enumerate(detail["statements"], 1):
            st.markdown(f"**{index}.** {statement['statement_text']}")
    if show_answer:
        st.divider()
        st.markdown("#### ĐÁP ÁN VÀ LỜI GIẢI")
        if kind == "MULTIPLE_CHOICE":
            correct = [str(o["option_code"]) for o in detail["options"] if o["is_correct"]]
            st.success("Phương án đúng: " + ", ".join(correct))
        elif kind == "TRUE_FALSE":
            st.success("; ".join(f"{i}. {'Đúng' if o['correct_value'] else 'Sai'}"
                                 for i, o in enumerate(detail["statements"], 1)))
        for answer in detail["answers"]:
            if answer.get("exact_answer_text"):
                st.markdown(f"**Đáp án:** {answer['exact_answer_text']}")
            if answer.get("answer_explanation"):
                st.markdown(str(answer["answer_explanation"]))
        for solution in detail["solutions"]:
            st.markdown(str(solution["solution_text"]))


def _textbook_math_fragment(expr: str) -> str:
    """Render common THCS textbook math notation without changing its meaning.

    This lightweight renderer is self-contained for offline HTML. It converts
    common LaTeX-like tokens already stored in question text to textbook
    symbols/HTML while leaving the source database untouched.
    """
    value = escape(str(expr or "").strip(), quote=True)

    # Structural wrappers that do not carry mathematical meaning themselves.
    value = value.replace(r"\left", "").replace(r"\right", "")
    value = value.replace(r"\,", " ").replace(r"\;", " ").replace(r"\:", " ")
    value = value.replace(r"\{", "{").replace(r"\}", "}")

    symbols = (
        (r"\notin", "∉"), (r"\in", "∈"),
        (r"\leq", "≤"), (r"\le", "≤"),
        (r"\geq", "≥"), (r"\ge", "≥"),
        (r"\neq", "≠"), (r"\ne", "≠"),
        (r"\approx", "≈"), (r"\equiv", "≡"),
        (r"\times", "×"), (r"\cdot", "·"), (r"\div", "÷"),
        (r"\pm", "±"), (r"\mp", "∓"),
        (r"\cup", "∪"), (r"\cap", "∩"),
        (r"\subseteq", "⊆"), (r"\subset", "⊂"),
        (r"\supseteq", "⊇"), (r"\supset", "⊃"),
        (r"\emptyset", "∅"), (r"\varnothing", "∅"),
        (r"\infty", "∞"), (r"\parallel", "∥"), (r"\perp", "⊥"),
        (r"\angle", "∠"), (r"\degree", "°"),
        (r"\ldots", "…"), (r"\dots", "…"),
    )
    for source, target in symbols:
        value = value.replace(source, target)

    # Simple textbook fractions and radicals. Repeated passes cover common
    # non-nested forms used by THCS question-bank content.
    frac_re = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
    sqrt_re = re.compile(r"\\sqrt\{([^{}]+)\}")
    for _ in range(4):
        updated = frac_re.sub(
            r'<span class="math-frac"><span class="math-num">\1</span>'
            r'<span class="math-den">\2</span></span>',
            value,
        )
        updated = sqrt_re.sub(r'<span class="math-root">√<span>\1</span></span>', updated)
        if updated == value:
            break
        value = updated

    # Text wrappers frequently produced by AI/LaTeX generators.
    value = re.sub(r"\\(?:mathrm|mathbf|text)\{([^{}]*)\}", r"\1", value)

    # Superscripts/subscripts used for powers, indices and labels.
    value = re.sub(r"\^\{([^{}]+)\}", r"<sup>\1</sup>", value)
    value = re.sub(r"\^([A-Za-z0-9+\-]+)", r"<sup>\1</sup>", value)
    value = re.sub(r"_\{([^{}]+)\}", r"<sub>\1</sub>", value)
    value = re.sub(r"_([A-Za-z0-9]+)", r"<sub>\1</sub>", value)

    # Remove grouping braces that remain after recognized conversions.
    value = value.replace("{", "").replace("}", "")
    return value


def _textbook_math_html(value: Any) -> str:
    """Escape normal prose and render $...$ math as textbook-style notation."""
    source = str(value or "")
    parts = re.split(r"(\$[^$]*\$)", source)
    rendered: list[str] = []
    for part in parts:
        if len(part) >= 2 and part.startswith("$") and part.endswith("$"):
            rendered.append(
                '<span class="math-text">' + _textbook_math_fragment(part[1:-1]) + "</span>"
            )
        else:
            # Also normalize obvious LaTeX commands outside dollar delimiters,
            # but keep ordinary prose fully escaped.
            escaped = escape(part, quote=True)
            if "\\" in part or re.search(r"[A-Za-z0-9]\^[{A-Za-z0-9]", part):
                escaped = _textbook_math_fragment(part)
            rendered.append(escaped.replace("\n", "<br>"))
    return "".join(rendered)


def _offline_slide(row: dict, detail: dict, index: int) -> str:
    """Render approved question data; answer content stays hidden until reveal."""
    def block(value: Any) -> str:
        return escape(str(value or ""), quote=True)

    def rich(value: Any) -> str:
        return _textbook_math_html(value)

    kind = row["question_type_code"]
    choices = ""
    answer = ""
    if kind == "MULTIPLE_CHOICE":
        choices = "".join(
            f'<button type="button" class="choice mcq" data-correct="{str(bool(o["is_correct"])).lower()}">'
            f'<b>{block(o["option_code"])}.</b> {rich(o["option_text"])}</button>'
            for o in detail["options"])
        answer = "Phương án đúng: " + ", ".join(
            str(o["option_code"]) for o in detail["options"] if o["is_correct"])
    elif kind == "TRUE_FALSE":
        choices = "".join(
            f'<div class="choice truth" data-correct="{str(bool(o["correct_value"])).lower()}">'
            f'<b>{i}. {rich(o["statement_text"])}</b>'
            f'<div class="truth-actions"><button type="button" data-value="true">Đúng</button>'
            f'<button type="button" data-value="false">Sai</button></div></div>'
            for i, o in enumerate(detail["statements"], 1))
        answer = "; ".join(
            f"{i}. {'Đúng' if o['correct_value'] else 'Sai'}"
            for i, o in enumerate(detail["statements"], 1))
    else:
        choices = '<label class="short-label">Câu trả lời của em<input type="text" autocomplete="off" placeholder="Nhập hoặc nêu câu trả lời…"></label>'
    answer_text = "".join(
        f'<p>{rich(a.get("exact_answer_text"))}</p><p>{rich(a.get("answer_explanation"))}</p>'
        for a in detail["answers"])
    explanations = "".join(f'<p>{rich(s["solution_text"])}</p>' for s in detail["solutions"])
    return (
        f'<section class="slide" id="slide-{index}" aria-label="Câu {index}">'
        f'<div class="eyebrow">CÂU {index} · {block(row["item"]["question_code"])}</div>'
        f'<h1>{rich(row["prompt_text"])}</h1>{choices}'
        f'<div class="answer" hidden><h2>Đáp án &amp; lời giải</h2>'
        f'<p><strong>{block(answer)}</strong></p>{answer_text}{explanations}</div></section>'
    )


def build_offline_presentation(title: str, slides: list[tuple[dict, dict]], *,
                               initial_index: int = 0, storage_key: str = "") -> bytes:
    """One self-contained HTML file: no API calls, CDN, fonts or external assets."""
    if not slides:
        raise ValueError("Buổi học chưa có câu hỏi để xuất.")
    content = "".join(_offline_slide(row, detail, i)
                      for i, (row, detail) in enumerate(slides, 1))
    html = '''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + escape(title, quote=True) + '''</title><style>
:root{color-scheme:light;font-family:Arial,"Segoe UI",sans-serif;background:#e9f1fa;color:#0b2038}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 82% 10%,#79c9f266,transparent 27%),linear-gradient(135deg,#e8f1fb,#f8fbff)}
.toolbar{position:sticky;top:0;background:linear-gradient(100deg,#071a30,#0d3962);color:white;
padding:12px 22px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
.toolbar strong{margin-right:auto}.toolbar button{border:1px solid #9dbce0;border-radius:9px;
padding:10px 16px;background:#fff;color:#092642;font-weight:700;cursor:pointer}
.toolbar button:hover{background:#cde9ff;transform:translateY(-2px)}
body:before{content:"";position:fixed;inset:0 0 auto;height:4px;background:#1d9adc;z-index:3;transform:scaleX(var(--slide-progress,.05));transform-origin:left}
main{margin:3vh auto;max-width:1120px;padding:24px}.slide{display:none;background:white;border:1px solid #ccdcec;
border-radius:20px;min-height:70vh;padding:clamp(24px,5vw,68px);box-shadow:0 12px 32px #142e4a16}
.slide{position:relative;overflow:hidden}.slide:after{content:"";position:absolute;right:-45px;bottom:-55px;width:190px;height:190px;border-radius:50%;background:#d2edff70;pointer-events:none}
.slide:first-child{display:block}.eyebrow{font-size:1.05rem;color:#125291;font-weight:800;letter-spacing:.06em}
h1{font-size:clamp(1.45rem,3vw,2.55rem);line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}
.choice{display:block;width:100%;text-align:left;color:#0b2038;background:#f7fbff;font-family:inherit;font-size:clamp(1.18rem,2vw,1.9rem);line-height:1.55;border:1px solid #d9e5f0;
border-radius:12px;padding:12px 18px;margin:11px 0;white-space:pre-wrap;overflow-wrap:anywhere}
.mcq{cursor:pointer}.mcq:hover{background:#e3f4ff;border-color:#53a7d9;transform:translateX(5px)}
.mcq.selected,.truth button.selected{background:#cfeeff;border-color:#1477bb;box-shadow:0 0 0 3px #86cbff66}
.mcq.correct,.truth button.correct{background:#d3f6e7;border-color:#16895a;box-shadow:0 0 0 3px #5bd39a88}
.mcq.incorrect,.truth button.incorrect{background:#ffe7e6;border-color:#c54e53}
.truth{display:flex;justify-content:space-between;gap:20px;align-items:center}.truth-actions{display:flex;gap:8px;flex-shrink:0}
.truth-actions button{border:1px solid #b8d2e6;border-radius:9px;background:white;padding:8px 14px;font-weight:700;cursor:pointer}
.short-label{display:block;font-weight:700;font-size:1.2rem;margin:28px 0}.short-label input{display:block;width:100%;font:inherit;margin-top:10px;border:2px solid #b6d8eb;border-radius:12px;padding:14px}
.flash{animation:glow .65s ease-out} @keyframes glow{0%{box-shadow:inset 0 0 0 14px #5cbfff99}100%{box-shadow:inset 0 0 0 0 transparent}}
.answer{margin-top:28px;border-top:3px solid #1d689e;padding-top:12px;background:#e9f7f2;
border-radius:10px;padding:18px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:1.15rem;line-height:1.5}
body:fullscreen{background:linear-gradient(130deg,#041a30,#113c60);color:#0b2038}
body:fullscreen main{max-width:none;margin:0;padding:12px 2vw}
body:fullscreen .slide{height:calc(100vh - 89px);min-height:0;overflow:auto;border-radius:16px;padding:clamp(25px,4vw,75px)}
body:fullscreen h1{font-size:clamp(2rem,4vw,4rem)}body:fullscreen .choice{font-size:clamp(1.5rem,2.6vw,2.7rem)}
button:focus-visible{outline:4px solid #f4a539} @media(prefers-reduced-motion:no-preference){.slide{animation:appear .3s ease-out}@keyframes appear{from{opacity:.2;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
@media(max-width:650px){.truth{display:block}.truth-actions{margin-top:10px}}
@media print{.toolbar{display:none}.slide{display:block!important;page-break-after:always;min-height:0}.answer[hidden]{display:none}}
/* Classroom stage R11: projector-friendly contrast, type hierarchy and depth. */
:root{font-family:"Segoe UI",Arial,sans-serif;color:#10263e;background:#071b35}
body{background:radial-gradient(circle at 14% 12%,#1282c852,transparent 32%),radial-gradient(circle at 90% 80%,#735dca42,transparent 36%),linear-gradient(145deg,#071a32,#102f52 60%,#071728)}
body:before{background:linear-gradient(90deg,#3ce0dc,#6ebfff,#f5bc69);box-shadow:0 0 15px #57b7e9}
.toolbar{background:linear-gradient(105deg,#05172c,#123e6a);border-bottom:1px solid #70aada77;box-shadow:0 10px 34px #03152d88;gap:10px;padding:14px clamp(14px,2.5vw,32px)}
.toolbar strong{font-size:clamp(1.05rem,1.5vw,1.35rem);letter-spacing:.02em;color:#fff;max-width:36ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#progress{font-size:1rem;font-weight:850;color:#d9f5ff;background:#ffffff20;border:1px solid #a0d3f170;border-radius:100px;padding:9px 14px;font-variant-numeric:tabular-nums}
.toolbar button{font-family:inherit;font-size:clamp(.97rem,1.2vw,1.1rem);font-weight:750;color:#113453;background:#fff;border:1px solid #bdd7ee;box-shadow:0 4px 0 #8baec6,0 10px 17px #01132470;min-height:44px;transition:transform .18s ease,box-shadow .18s ease,background .18s ease}
.toolbar button:hover{background:#e4f7ff;transform:translateY(-3px);box-shadow:0 7px 0 #76a8ca,0 14px 22px #01132480}
.toolbar button:active{transform:translateY(3px);box-shadow:0 1px 0 #76a8ca}
#next{background:#1460a5;color:#fff;border-color:#70c6fc;box-shadow:0 4px 0 #083767,0 12px 21px #01132490}
#next:hover{background:#1b75c2;box-shadow:0 7px 0 #083767,0 14px 22px #01132490}
main{max-width:1380px;margin:clamp(12px,2vh,30px) auto;padding:clamp(12px,2vw,30px);perspective:1400px}
.slide{isolation:isolate;background:linear-gradient(155deg,#fff,#f5faff 85%);border:1px solid #ddedff;border-radius:28px;box-shadow:0 14px 0 #7faac7,0 32px 75px #021226aa,inset 0 2px 0 #fff;min-height:72vh;padding:clamp(25px,4vw,68px);transform-style:preserve-3d}
.slide:before{content:"";position:absolute;inset:0 0 auto;height:9px;background:linear-gradient(90deg,#138eca,#4cced4,#c197e8);border-radius:28px 28px 0 0;pointer-events:none}
.slide:after{width:230px;height:230px;background:radial-gradient(circle,#89d6f34a,transparent 70%);right:-60px;bottom:-70px}
.eyebrow{display:inline-flex;align-items:center;min-height:38px;padding:6px 15px;border-radius:9px;background:#dfedfc;color:#114b79;font-size:clamp(.95rem,1.3vw,1.15rem);letter-spacing:.07em}
h1{font-family:"Segoe UI",Arial,sans-serif;color:#102c49;font-weight:800;font-size:clamp(1.85rem,3.3vw,3.5rem);line-height:1.37;margin:clamp(18px,3vh,34px) 0;max-width:32ch;text-wrap:pretty}
.choice{position:relative;font-family:"Segoe UI",Arial,sans-serif;font-size:clamp(1.35rem,2.2vw,2.18rem);font-weight:600;color:#15334e;line-height:1.48;border:2px solid #c5ddec;border-radius:18px;background:#fff;padding:clamp(14px,1.7vw,23px) clamp(18px,2vw,30px);margin:clamp(10px,1.5vh,20px) 0;box-shadow:0 6px 0 #a9c5d8,0 13px 22px #092d5019;transition:transform .22s ease,box-shadow .22s ease,background .22s ease,border-color .22s ease;transform-style:preserve-3d}
.choice b{display:inline-grid;place-items:center;min-width:2.1em;min-height:2.1em;padding:.1em .25em;border-radius:12px;background:#e6f2ff;color:#125492;margin-right:10px;font-weight:850;box-shadow:inset 0 0 0 1px #b8d8f4}
.mcq:hover{background:#f0faff;transform:translate3d(0,-5px,14px) rotateX(1.5deg);box-shadow:0 10px 0 #91bad5,0 24px 34px #092d5033}
.mcq:active{transform:translateY(3px);box-shadow:0 2px 0 #91bad5}
.mcq.selected,.truth:has(button.selected){background:#e2f4ff;border-color:#157ac2;box-shadow:0 5px 0 #268ac4,0 13px 24px #0b538438}
.mcq.correct,.truth:has(button.correct){background:#def8eb;border-color:#139568;box-shadow:0 5px 0 #189667,0 13px 24px #084a3233}
.mcq.incorrect,.truth:has(button.incorrect){background:#ffebea;border-color:#bb3c45;box-shadow:0 5px 0 #bc5159,0 13px 24px #70202833}
.truth button.selected,.truth button.correct,.truth button.incorrect{color:#11283d;border-width:2px}
.truth-actions button{font-size:clamp(1rem,1.4vw,1.3rem);min-width:76px;min-height:48px}
.answer{font-size:clamp(1.18rem,1.75vw,1.65rem);line-height:1.6;color:#123c32;background:linear-gradient(125deg,#e6f9f0,#f6fffb);border:2px solid #9bd8b7;border-left:9px solid #149661;box-shadow:0 8px 0 #b3dac4,0 22px 34px #0d46361a;padding:clamp(18px,3vw,32px);border-radius:17px;margin-top:clamp(24px,4vh,46px)}
.answer h2{font-size:clamp(1.4rem,2vw,2rem);margin:0 0 14px;color:#0b6645}.answer p{margin:.7em 0}
.short-label{font-size:clamp(1.2rem,1.8vw,1.7rem);color:#183f5c}.short-label input{font-size:clamp(1.3rem,2vw,2rem);background:white;color:#10263e}
body:fullscreen{background:radial-gradient(circle at 85% 0%,#2077ac88,transparent 40%),#061628}
body:fullscreen main{padding:16px 2vw}body:fullscreen .slide{height:calc(100vh - 112px);border-radius:24px}body:fullscreen h1{font-size:clamp(2rem,4vw,4.2rem)}body:fullscreen .choice{font-size:clamp(1.55rem,2.7vw,2.9rem)}
@media(max-width:760px){.toolbar strong{flex-basis:100%;max-width:none}.toolbar button{flex:1 1 auto}.slide{min-height:65vh}.choice b{margin-right:5px}.truth-actions{justify-content:flex-start}}
@media(prefers-reduced-motion:no-preference){.slide{animation:stage-enter .42s cubic-bezier(.22,.7,.25,1)}@keyframes stage-enter{from{opacity:.35;transform:translateY(18px) rotateX(3deg)}to{opacity:1;transform:translateY(0) rotateX(0)}}.flash{animation:glow .65s ease-out}}
/* One-shot light cues: blue for choice, green for right, coral for wrong. */
@media(prefers-reduced-motion:no-preference){
body{background-size:130% 130%;animation:ambient-shift 18s ease-in-out infinite alternate}
@keyframes ambient-shift{from{background-position:0% 0%}to{background-position:100% 100%}}
.slide.flash{animation:slide-light .6s ease-out}
@keyframes slide-light{0%{filter:brightness(1);box-shadow:0 14px 0 #7faac7,0 32px 75px #021226aa}45%{filter:brightness(1.09);box-shadow:0 14px 0 #7faac7,0 32px 75px #021226aa,0 0 48px #6ec8ffb0}100%{filter:brightness(1);box-shadow:0 14px 0 #7faac7,0 32px 75px #021226aa}}
.mcq.selected,.truth button.selected{animation:choice-light .55s ease-out}
@keyframes choice-light{0%{filter:brightness(1);box-shadow:0 0 0 0 #44bcffbb}45%{filter:brightness(1.2);box-shadow:0 0 0 10px #44bcff66}100%{filter:brightness(1);box-shadow:0 0 0 0 #44bcff00}}
.mcq.correct,.truth button.correct{animation:correct-light .9s ease-out}
@keyframes correct-light{0%,100%{filter:brightness(1)}35%{filter:brightness(1.3);box-shadow:0 0 0 12px #30d99a80}70%{filter:brightness(1.06);box-shadow:0 0 0 20px #30d99a00}}
.mcq.incorrect,.truth button.incorrect{animation:incorrect-light .68s ease-out}
@keyframes incorrect-light{0%,100%{filter:brightness(1)}45%{filter:brightness(1.17);box-shadow:0 0 0 9px #f4767880}}
.answer:not([hidden]){animation:answer-enter .48s cubic-bezier(.18,.68,.3,1)}
@keyframes answer-enter{from{opacity:.25;transform:translateY(13px);border-color:#41be8d}to{opacity:1;transform:translateY(0);border-color:#9bd8b7}}
}
@media(prefers-reduced-motion:reduce){body{animation:none!important}.slide.flash,.mcq.selected,.truth button.selected,.mcq.correct,.truth button.correct,.mcq.incorrect,.truth button.incorrect,.answer:not([hidden]){animation:none!important}}
/* R16: correct-answer cue after the teacher reveals the answer. */
@media(prefers-reduced-motion:no-preference){
.mcq.correct.answer-correct-flash,
.truth button.correct.answer-correct-flash{
  animation:answer-correct-flash 1.8s ease-in-out 1!important;
  transform-origin:center;
}
@keyframes answer-correct-flash{
  0%{filter:brightness(1);transform:scale(1)}
  12%{filter:brightness(1.28);transform:scale(1.018);background:#c8f7df;box-shadow:0 0 0 6px #29c98266,0 0 34px #29c9828f}
  25%{filter:brightness(1);transform:scale(1);background:#def8eb}
  40%{filter:brightness(1.22);transform:scale(1.012);background:#fff0a8;box-shadow:0 0 0 8px #ffc93666,0 0 38px #ffc93688}
  55%{filter:brightness(1);transform:scale(1);background:#def8eb}
  70%{filter:brightness(1.24);transform:scale(1.014);background:#c8f7df;box-shadow:0 0 0 7px #29c9825f,0 0 36px #29c98280}
  100%{filter:brightness(1);transform:scale(1);background:#def8eb}
}
}
@media(prefers-reduced-motion:reduce){
.mcq.correct.answer-correct-flash,
.truth button.correct.answer-correct-flash{
  outline:6px solid #21a86f;outline-offset:3px;
}
}
@media(prefers-reduced-motion:reduce){.toolbar button,.choice{transition:none!important}}
@media print{body{background:#fff}.slide{box-shadow:none;border:1px solid #aaa}.choice{box-shadow:none}.answer{box-shadow:none}}

/* Classroom stage R17: Times New Roman typography and fixed projector sizes.
   Mathematical expressions remain text-identical; only presentation font changes. */
:root,
body,
button,
input,
label,
.slide,
.slide h1,
.slide .choice,
.slide .choice b,
.slide .truth,
.slide .truth button,
.slide .short-label,
.slide .short-label input,
.slide .answer,
.slide .answer h2,
.slide .answer p{
  font-family:"Times New Roman",Times,serif!important;
}
.slide h1{
  font-size:28px!important;
  line-height:1.42!important;
  font-weight:700!important;
  letter-spacing:0!important;
}
.slide .choice,
.slide .truth{
  font-size:26px!important;
  line-height:1.42!important;
}
.slide .choice b{
  font-size:26px!important;
  line-height:1.2!important;
}
.slide .truth button{
  font-size:26px!important;
  line-height:1.2!important;
}
.slide .short-label,
.slide .short-label input{
  font-size:26px!important;
  line-height:1.42!important;
}
.slide .answer{
  font-size:26px!important;
  line-height:1.45!important;
}
.slide .answer h2{
  font-size:28px!important;
  line-height:1.3!important;
}
.slide .answer p{
  font-size:26px!important;
  line-height:1.45!important;
}
body:fullscreen .slide h1{font-size:28px!important}
body:fullscreen .slide .choice,
body:fullscreen .slide .truth,
body:fullscreen .slide .truth button,
body:fullscreen .slide .short-label,
body:fullscreen .slide .short-label input,
body:fullscreen .slide .answer,
body:fullscreen .slide .answer p{font-size:26px!important}
/* Preserve every math token verbatim. Inline mathematical notation inherits the same Times New Roman face. */
.slide h1 *,
.slide .choice *,
.slide .answer *{
  font-family:"Times New Roman",Times,serif!important;
}



/* Classroom stage R20: locked-choice purple cue + dark-red wrong answers. */
.mcq.selected,
.truth:has(button.selected),
.truth button.selected{
  background:#eadcff!important;
  border-color:#7b3fc3!important;
  color:#2b1745!important;
  box-shadow:0 5px 0 #6730a8,0 13px 24px #4d247033,0 0 0 3px #b58be766!important;
}
@media(prefers-reduced-motion:no-preference){
.mcq.selected,
.truth button.selected{
  animation:choice-lock-purple .62s ease-out 1!important;
}
@keyframes choice-lock-purple{
  0%{
    background:#fff;
    box-shadow:0 0 0 0 #8d55cf00;
    transform:scale(1)
  }
  45%{
    background:#d9c0ff;
    box-shadow:0 0 0 10px #8d55cf55,0 0 28px #8d55cf66;
    transform:scale(1.016)
  }
  100%{
    background:#eadcff;
    box-shadow:0 5px 0 #6730a8,0 13px 24px #4d247033,0 0 0 3px #b58be766;
    transform:scale(1)
  }
}
}

/* Final wrong-answer state: deep red, visually distinct but not harsh. */
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  background:#7f1d2d!important;
  border-color:#5f1020!important;
  color:#fff!important;
  box-shadow:0 5px 0 #4d0c18,0 13px 24px #3a071244!important;
}
.mcq.answer-wrong-settle b,
.truth button.answer-wrong-settle b{
  color:#fff!important;
}
@media(prefers-reduced-motion:no-preference){
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  animation:answer-wrong-deep-settle .62s ease-out 1 forwards!important;
}
@keyframes answer-wrong-deep-settle{
  0%{
    background:#fff;
    border-color:#c5ddec;
    color:#15334e;
    box-shadow:0 0 0 0 #7f1d2d00;
    filter:brightness(1)
  }
  52%{
    background:#a83245;
    border-color:#7f1d2d;
    color:#fff;
    box-shadow:0 0 0 8px #a8324550,0 0 32px #7f1d2d55;
    filter:brightness(1.08)
  }
  100%{
    background:#7f1d2d;
    border-color:#5f1020;
    color:#fff;
    box-shadow:0 5px 0 #4d0c18,0 13px 24px #3a071244;
    filter:brightness(1)
  }
}
}
@media(prefers-reduced-motion:reduce){
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  background:#7f1d2d!important;
  border-color:#5f1020!important;
  color:#fff!important;
}
}
/* Classroom stage R19: two-phase answer reveal synchronized with result audio. */
@media(prefers-reduced-motion:no-preference){
.mcq.answer-correct-settle,
.truth button.answer-correct-settle{
  animation:answer-correct-settle 1.05s ease-in-out 1 forwards!important;
}
@keyframes answer-correct-settle{
  0%{
    background:#d9edff;
    border-color:#3f94da;
    box-shadow:0 0 0 7px #3f94da55,0 0 30px #3f94da70;
    filter:brightness(1.12);
    transform:scale(1.012)
  }
  48%{
    background:#fff0a8;
    border-color:#e1ad18;
    box-shadow:0 0 0 8px #ffc93655,0 0 34px #ffc93675;
    filter:brightness(1.13);
    transform:scale(1.018)
  }
  100%{
    background:#def8eb;
    border-color:#139568;
    box-shadow:0 5px 0 #189667,0 13px 24px #084a3233;
    filter:brightness(1);
    transform:scale(1)
  }
}
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  animation:answer-wrong-settle .55s ease-out 1 forwards!important;
}
@keyframes answer-wrong-settle{
  0%{
    background:#fff;
    border-color:#c5ddec;
    filter:brightness(1)
  }
  55%{
    background:#ffd2d2;
    border-color:#df6268;
    box-shadow:0 0 0 7px #ef6b7160;
    filter:brightness(1.07)
  }
  100%{
    background:#ffe7e6;
    border-color:#bb3c45;
    box-shadow:0 5px 0 #bc5159,0 13px 24px #70202833;
    filter:brightness(1)
  }
}
}
.mcq.answer-correct-settle,
.truth button.answer-correct-settle{
  background:#def8eb;
  border-color:#139568;
}
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  background:#ffe7e6;
  border-color:#bb3c45;
}
@media(prefers-reduced-motion:reduce){
.mcq.answer-correct-settle,
.truth button.answer-correct-settle{
  background:#def8eb!important;
  border-color:#139568!important;
  outline:5px solid #21a86f;
  outline-offset:2px;
}
.mcq.answer-wrong-settle,
.truth button.answer-wrong-settle{
  background:#ffe7e6!important;
  border-color:#bb3c45!important;
}
}
/* Classroom stage R18: textbook math notation and balanced question header. */
.slide h1{
  width:100%!important;
  max-width:none!important;
  text-align:justify!important;
  text-align-last:left!important;
  text-justify:inter-word;
  hyphens:none;
  margin:18px 0 28px!important;
}
.math-text{
  font-family:"Times New Roman",Times,serif!important;
  font-style:normal;
  white-space:nowrap;
  letter-spacing:0;
}
.math-text sup,.math-text sub{
  font-family:"Times New Roman",Times,serif!important;
  font-size:.72em;
  line-height:0;
}
.math-frac{
  display:inline-flex;
  flex-direction:column;
  vertical-align:-.42em;
  text-align:center;
  line-height:1.02;
  margin:0 .12em;
  min-width:1.2em;
}
.math-frac .math-num{
  display:block;
  padding:0 .12em .06em;
  border-bottom:1.3px solid currentColor;
}
.math-frac .math-den{
  display:block;
  padding:.06em .12em 0;
}
.math-root{
  display:inline-flex;
  align-items:flex-start;
  white-space:nowrap;
}
.math-root>span{
  display:inline-block;
  border-top:1.3px solid currentColor;
  padding:0 .08em 0 .05em;
  margin-top:.12em;
}
</style></head><body><nav class="toolbar"><strong>''' + escape(title, quote=True) + '''</strong>
<span id="progress"></span><button type="button" id="prev">← Trước</button>
<button type="button" id="reveal">Hiện đáp án</button><button type="button" id="next">Tiếp →</button>
<button type="button" id="sound" aria-pressed="false" title="Âm thanh chỉ phát sau thao tác của giáo viên">♪ Bật âm thanh</button>
<button type="button" id="effects" aria-pressed="true" title="Bật hoặc tắt riêng âm khi chọn và hiện đáp án">✨ Hiệu ứng: Bật</button>
<button type="button" id="fullscreen" title="Phím F; Escape để thoát">⛶ Toàn màn hình</button></nav>
<main>''' + content + '''</main><script>
const pptAudioSources=__AUDIO_SOURCES__;
const slides=[...document.querySelectorAll('.slide')];let current=0,sound=false,ctx;
const audioPlayers={};let activeAudio=null,resultTimer=null,answerEffectTimer=null;
const effectLayer=(()=>{let enabled=true;const players={};
return{play(role){if(!sound||!enabled)return;let player=players[role];
if(!player){player=new Audio(pptAudioSources[role]);players[role]=player}
player.pause();player.currentTime=0;player.volume=.42;
player.play().catch(()=>{})},setEnabled(value){enabled=value;
if(!enabled)Object.values(players).forEach(p=>{p.pause();p.currentTime=0})},
stop(){Object.values(players).forEach(p=>{p.pause();p.currentTime=0})}}})();
function stopAudio(){if(resultTimer){clearTimeout(resultTimer);resultTimer=null}
if(answerEffectTimer){clearTimeout(answerEffectTimer);answerEffectTimer=null}
if(activeAudio){activeAudio.pause();activeAudio.currentTime=0;activeAudio=null}}
function playAudio(role){if(!sound)return;stopAudio();let player=audioPlayers[role];
if(!player){player=new Audio(pptAudioSources[role]);audioPlayers[role]=player}
player.loop=role==='question';player.volume=role==='question'?.12:.65;player.currentTime=0;
activeAudio=player;player.play().catch(()=>{sound=false;stopAudio();
document.querySelector('#sound').textContent='♪ Bật âm thanh';
document.querySelector('#sound').setAttribute('aria-pressed','false')})}
function resultFor(s){const picked=s.querySelector('.mcq.selected');
if(picked)return picked.dataset.correct==='true'?'win':'lose';
const truths=[...s.querySelectorAll('.truth')];
if(truths.length&&truths.every(t=>t.querySelector('button.selected')))
return truths.every(t=>t.querySelector('button.selected').dataset.value===t.dataset.correct)?'win':'lose';
return null}
function glow(){let s=slides[current];s.classList.remove('flash');void s.offsetWidth;s.classList.add('flash')}
function show(i){current=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,k)=>s.style.display=k===current?'block':'none');
document.querySelector('#progress').textContent=`${current+1}/${slides.length}`;
document.body.style.setProperty('--slide-progress',(current+1)/slides.length);
document.querySelector('#reveal').textContent=slides[current].querySelector('.answer').hidden?'Hiện đáp án':'Ẩn đáp án';}
document.querySelector('#prev').onclick=()=>{if(current>0){show(current-1);glow();playAudio('question')}};
document.querySelector('#next').onclick=()=>{if(current<slides.length-1){show(current+1);glow();playAudio('question')}};
document.querySelector('#reveal').onclick=()=>{let s=slides[current],a=s.querySelector('.answer');a.hidden=!a.hidden;
if(!a.hidden){
if(answerEffectTimer){clearTimeout(answerEffectTimer);answerEffectTimer=null}
s.querySelectorAll('.answer-correct-flash,.answer-correct-settle,.answer-wrong-settle').forEach(b=>b.classList.remove('answer-correct-flash','answer-correct-settle','answer-wrong-settle'));
s.querySelectorAll('.mcq').forEach(b=>{if(b.dataset.correct==='true')b.classList.add('correct');else if(b.classList.contains('selected'))b.classList.add('incorrect')});
s.querySelectorAll('.truth').forEach(t=>t.querySelectorAll('button').forEach(b=>{if(b.dataset.value===t.dataset.correct)b.classList.add('correct');else if(b.classList.contains('selected'))b.classList.add('incorrect')}));
const correctTargets=[...s.querySelectorAll('.mcq.correct,.truth button.correct')];
correctTargets.forEach(b=>{void b.offsetWidth;b.classList.add('answer-correct-flash')});
glow();effectLayer.play('reveal');playAudio('final');const outcome=resultFor(s);
answerEffectTimer=setTimeout(()=>{
answerEffectTimer=null;
correctTargets.forEach(b=>{b.classList.remove('answer-correct-flash');void b.offsetWidth;b.classList.add('answer-correct-settle')});
s.querySelectorAll('.mcq').forEach(b=>{if(b.dataset.correct!=='true')b.classList.add('answer-wrong-settle')});
s.querySelectorAll('.truth').forEach(t=>t.querySelectorAll('button').forEach(b=>{if(b.dataset.value!==t.dataset.correct)b.classList.add('answer-wrong-settle')}));
if(outcome&&sound){resultTimer=setTimeout(()=>playAudio(outcome),0)}
},1500)}
else{stopAudio();s.querySelectorAll('.correct,.incorrect,.answer-correct-flash,.answer-correct-settle,.answer-wrong-settle').forEach(b=>b.classList.remove('correct','incorrect','answer-correct-flash','answer-correct-settle','answer-wrong-settle'));playAudio('question')}show(current)};
document.querySelector('#sound').onclick=()=>{sound=!sound;document.querySelector('#sound').textContent=sound?'♫ Tắt âm thanh':'♪ Bật âm thanh';document.querySelector('#sound').setAttribute('aria-pressed',String(sound));if(sound)playAudio(slides[current].querySelector('.answer').hidden?'question':'final');else{stopAudio();effectLayer.stop()}};
document.querySelector('#effects').onclick=()=>{const b=document.querySelector('#effects');const on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(on));b.textContent=on?'✨ Hiệu ứng: Bật':'✨ Hiệu ứng: Tắt';effectLayer.setEnabled(on)};
document.querySelectorAll('.mcq').forEach(b=>b.onclick=()=>{let s=b.closest('.slide');if(!s.querySelector('.answer').hidden)return;s.querySelectorAll('.mcq').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');effectLayer.play('select')});
document.querySelectorAll('.truth button').forEach(b=>b.onclick=()=>{let t=b.closest('.truth');if(!t.closest('.slide').querySelector('.answer').hidden)return;t.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');effectLayer.play('select')});
document.querySelector('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement){await document.exitFullscreen()}else{await document.body.requestFullscreen()}}catch(e){alert('Trình duyệt không cho phép chế độ này; nhấn F11 để mở toàn màn hình.')}};
document.addEventListener('fullscreenchange',()=>{document.querySelector('#fullscreen').textContent=document.fullscreenElement?'⤢ Thu nhỏ':'⛶ Toàn màn hình'});
document.addEventListener('keydown',e=>{if(e.target.matches('input'))return;
if(e.key==='ArrowRight')document.querySelector('#next').click();if(e.key==='ArrowLeft')document.querySelector('#prev').click();
if(e.key===' '){e.preventDefault();document.querySelector('#reveal').click()}
if(e.key.toLowerCase()==='f'&&!e.repeat)document.querySelector('#fullscreen').click()});show(0);
</script></body></html>'''
    # The embedded stage contains the whole session. Its controls retain the
    # position in this browser without requiring an authenticated API call.
    html = html.replace("const slides=[...document.querySelectorAll('.slide')];let current=0,sound=false,ctx;",
                        "const slides=[...document.querySelectorAll('.slide')];"
                        f"const storageKey={json.dumps(storage_key)};"
                        f"let current={max(0, min(initial_index, len(slides) - 1))},sound=false,ctx;"
                        "if(storageKey){try{const saved=Number(localStorage.getItem(storageKey));"
                        "if(Number.isInteger(saved)&&saved>=0&&saved<slides.length)current=saved}catch(e){}}")
    html = html.replace("document.body.style.setProperty('--slide-progress',(current+1)/slides.length);",
                        "document.body.style.setProperty('--slide-progress',(current+1)/slides.length);"
                        "if(storageKey){try{localStorage.setItem(storageKey,String(current))}catch(e){}}")
    html = html.replace("});show(0);", "});show(current);")
    html = html.replace("__AUDIO_SOURCES__", json.dumps(stage_audio_sources()), 1)
    return html.encode("utf-8")


def render_teacher_classroom(st: Any, client: Any, user_id: str) -> None:
    """Only authenticated teachers can access this page via teacher portal."""
    st.markdown("""<style>
div.st-key-classroom_question{background:linear-gradient(165deg,#ffffff,#f5faff);border:1px solid #c5def0;
border-radius:22px;padding:clamp(18px,4vw,48px);box-shadow:0 18px 48px #0a315222}
div.st-key-classroom_question h4{color:#0e4a79;font-size:1rem;letter-spacing:.12em;font-weight:850}
div.st-key-classroom_question p{font-size:clamp(1.2rem,2.2vw,1.85rem);line-height:1.6}
div.st-key-classroom_question [data-testid="stAlert"] p{font-size:1.25rem}
.classroom-hero{border-radius:22px;padding:28px 34px;margin:0 0 24px;background:radial-gradient(circle at 86% 20%,#3da7de88,transparent 34%),linear-gradient(120deg,#061c34,#114673);color:white;box-shadow:0 20px 38px #071e3640;position:relative;overflow:hidden}
.classroom-hero::after{content:"";position:absolute;right:-50px;bottom:-110px;border:32px solid #95dcff33;border-radius:50%;width:220px;height:220px;pointer-events:none}
.classroom-kicker{font-size:.82rem;letter-spacing:.16em;color:#a7ddff;font-weight:800}
.classroom-hero h2{color:#fff!important;font-size:clamp(1.6rem,3vw,2.5rem);margin:10px 0;font-family:Arial,sans-serif}
.classroom-hero p{color:#dceeff;margin:0;font-size:1rem}
.classroom-session{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:14px 20px;margin:14px 0 20px;background:#eaf4fd;border:1px solid #cde2f3;border-radius:12px;color:#123452}
.classroom-pill{background:#0e4975;color:#fff;padding:6px 12px;border-radius:100px;font-size:.8rem;font-weight:750}
div.st-key-classroom_create_button button:disabled{background:#d7e3f0!important;color:#233e5b!important;border:1px solid #8ca6bd!important;opacity:1!important}
div.st-key-classroom_create_button button:disabled p{color:#233e5b!important}
@media(prefers-reduced-motion:no-preference){.classroom-hero{animation:classroom-in .5s ease-out}@keyframes classroom-in{from{opacity:.4;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}}
@media(prefers-reduced-motion:reduce){.classroom-hero{animation:none}}
.classroom-hero{font-family:"Segoe UI",Arial,sans-serif;background:radial-gradient(circle at 84% 14%,#39b7d683,transparent 32%),linear-gradient(115deg,#071b34,#155586);border:1px solid #508cb5;border-radius:24px;box-shadow:0 10px 0 #a7cadb,0 24px 42px #051c3552}
.classroom-kicker{color:#bcefff;font-size:.9rem}.classroom-hero h2{font-family:"Segoe UI",Arial,sans-serif!important;font-weight:800!important;line-height:1.2;font-size:clamp(2rem,3.3vw,3.1rem)}
.classroom-hero p{font-size:clamp(1rem,1.35vw,1.24rem);line-height:1.6;max-width:64ch}
.classroom-session{background:#fff;color:#123856;box-shadow:0 5px 0 #afcadb;border:1px solid #b1d2e7;font-family:"Segoe UI",Arial,sans-serif;font-size:1.08rem;padding:18px 22px}
.classroom-pill{background:#125a91;font-size:.9rem}
div.st-key-classroom_question{border-width:2px;border-radius:23px;box-shadow:0 8px 0 #bdd5e5,0 24px 36px #06284b22}
div.st-key-classroom_question p{color:#142f4b;font-family:"Segoe UI",Arial,sans-serif}
</style><div class="classroom-hero"><div class="classroom-kicker">MATHTEACHER AI · KHÔNG GIAN DẠY HỌC</div>
<h2>Lớp học ôn tập</h2><p>Chọn câu hỏi đã duyệt, trình chiếu trên lớp và mang theo bản dùng khi mất mạng.</p></div>""", unsafe_allow_html=True)
    try:
        bank = _question_bank(client, user_id)
        sessions = _rows(client.table("teacher_classroom_sessions")
                         .select("session_id,title,status,current_position,show_answer,class_id,created_at")
                         .eq("teacher_user_id", user_id).order("created_at", desc=True).limit(30).execute())
    except Exception as exc:
        st.error(f"Không tải được lớp học. Kiểm tra migration lớp học và quyền truy cập: {exc}")
        return
    if not bank:
        st.info("Tài khoản này chưa có câu hỏi đã duyệt trong ngân hàng.")
    with st.expander("Tạo buổi ôn tập", expanded=not sessions):
        title = st.text_input("Tên buổi học", value="Ôn tập Toán", key="classroom_title")
        class_id = st.text_input("Mã lớp (bắt buộc)", placeholder="Nhập lớp của buổi học, ví dụ: 7A2").strip()
        grade = st.selectbox("Khối", [6, 7, 8, 9])
        available = [q for q in bank if int(q["item"]["grade_level"]) == grade]
        if not available:
            st.info(f"Khối {grade} chưa có câu hỏi đã duyệt mà tài khoản này có quyền sử dụng. "
                    "Bạn vẫn có thể nhập mã lớp; cần bổ sung câu hỏi đã duyệt của khối này để tạo buổi học.")
        lookup = {str(q["question_version_id"]): q for q in available}
        wheel_pack = st.toggle(
            "Chuẩn bị bộ 9 câu cho Vòng quay may mắn",
            value=True,
            key="classroom_visual_picker_wheel_pack",
            help="Bật: chọn đúng 9 câu để dùng trực tiếp với Vòng quay. Tắt: có thể chọn 1–30 câu cho trình chiếu thông thường.",
        )
        from portal_v2.ui.classroom_question_picker import render_question_picker
        selected = render_question_picker(
            st,
            available,
            key=f"classroom_picker_g{grade}_{'wheel' if wheel_pack else 'stage'}",
            target_count=9,
            max_selected=9 if wheel_pack else 30,
            require_exact=wheel_pack,
            preview_renderer=lambda row: _render_question(st, client, row, show_answer=False),
        )
        missing = []
        if not title.strip():
            missing.append("tên buổi học")
        if not class_id:
            missing.append("mã lớp (ví dụ: 7A2)")
        if wheel_pack and len(selected) != 9:
            missing.append(f"đúng 9 câu cho Vòng quay (hiện có {len(selected)})")
        elif not wheel_pack and not selected:
            missing.append("ít nhất một câu hỏi đã duyệt")
        if missing:
            st.info("Để tạo buổi học, hãy nhập/chọn: " + ", ".join(missing) + ".")
        if st.button("Tạo buổi học", disabled=bool(missing),
                     type="primary", key="classroom_create_button"):
            try:
                client.rpc("create_teacher_classroom_session", {
                    "target_class_id": class_id, "target_title": title.strip(),
                    "selected_versions": selected,
                }).execute()
            except Exception as exc:
                st.error(f"Không tạo được buổi học: {exc}")
            else:
                st.success("Đã lưu buổi học và danh sách câu.")
                st.rerun()
    if not sessions:
        return
    session_by_id = {str(s["session_id"]): s for s in sessions}
    selected_id = st.selectbox("Buổi học", list(session_by_id),
        format_func=lambda k: f"{session_by_id[k]['title']} · {session_by_id[k]['status']} · {session_by_id[k]['created_at'][:10]}")
    session = session_by_id[selected_id]
    st.markdown(
        f'<div class="classroom-session"><strong>{escape(str(session["title"]))}</strong>'
        f'<span class="classroom-pill">{escape(str(session["status"]))}</span>'
        f'<span>Lớp {escape(str(session["class_id"]))}</span></div>', unsafe_allow_html=True)
    try:
        queue = _rows(client.table("teacher_classroom_questions")
                      .select("position,question_version_id")
                      .eq("session_id", selected_id).order("position").limit(100).execute())
    except Exception as exc:
        st.error(f"Không đọc được danh sách câu: {exc}")
        return
    by_version = {str(q["question_version_id"]): q for q in bank}
    if queue:
        stage_mode = st.radio(
            "Chế độ sân khấu", ("Trình chiếu câu hỏi", "🎡 Vòng quay may mắn", "🎤 Gameshow"),
            horizontal=True, key=f"classroom_stage_mode_{selected_id}")
        if stage_mode == "🎤 Gameshow":
            st.caption(
                "Gameshow lớp học: bảng điểm đội, đồng hồ, combo, hiệu ứng ăn mừng "
                "và chấm nhanh do giáo viên kiểm soát. Trạng thái game lưu trong trình duyệt."
            )
            if st.button("🎤 Chuẩn bị Gameshow", key=f"prepare_gameshow_{selected_id}"):
                try:
                    from portal_v2.ui.classroom_gameshow_core import build_offline_gameshow
                    slides = []
                    for entry in queue:
                        row = by_version.get(str(entry["question_version_id"]))
                        if (
                            not row
                            or int(row["item"]["grade_level"]) not in (6, 7, 8, 9)
                            or row["item"].get("subject_code") != "MATH"
                            or row["item"].get("lifecycle_status") != "ACTIVE"
                        ):
                            raise ValueError(
                                "Một câu không còn được duyệt hoặc nằm ngoài khối Toán 6–9."
                            )
                        slides.append(
                            (
                                row,
                                _detail(client, str(entry["question_version_id"])),
                            )
                        )
                    st.session_state["prepared_classroom_gameshow"] = (
                        selected_id,
                        build_offline_gameshow(
                            session["title"],
                            slides,
                            session_id=selected_id,
                        ),
                    )
                except Exception as exc:
                    st.error(f"Không chuẩn bị được Gameshow: {exc}")

            prepared_gameshow = st.session_state.get("prepared_classroom_gameshow")
            if prepared_gameshow and prepared_gameshow[0] == selected_id:
                st.download_button(
                    "⬇ Tải Gameshow HTML ngoại tuyến",
                    prepared_gameshow[1],
                    file_name=f"gameshow-{selected_id[:8]}.html",
                    mime="text/html",
                    key=f"download_gameshow_{selected_id}",
                    use_container_width=True,
                )
                from streamlit.components.v1 import html as component_html
                component_html(
                    prepared_gameshow[1].decode("utf-8"),
                    height=920,
                    scrolling=True,
                )
                st.caption(
                    "Phím nhanh: ←/→ chuyển câu · Space hiện đáp án · "
                    "T chạy/dừng giờ · C chấm đúng · X chấm sai · F toàn màn hình."
                )
            from portal_v2.ui.classroom_arena_teacher_streamlit import (
                render_classroom_arena_teacher,
            )
            render_classroom_arena_teacher(
                st,
                client=client,
                classroom_session_id=selected_id,
                default_team_count=4,
            )
            return
        if stage_mode == "🎡 Vòng quay may mắn":
            st.caption("Quay/Dừng với câu Toán đã duyệt trong buổi học. "
                       "Điểm và câu đã chơi được lưu trong trình duyệt này.")
            if st.button("🎡 Chuẩn bị vòng quay", key=f"prepare_wheel_{selected_id}"):
                try:
                    from portal_v2.ui.classroom_lucky_wheel import build_offline_wheel
                    slides = []
                    for entry in queue:
                        row = by_version.get(str(entry["question_version_id"]))
                        if (not row or int(row["item"]["grade_level"]) not in (6, 7, 8, 9)
                                or row["item"].get("subject_code") != "MATH"
                                or row["item"].get("lifecycle_status") != "ACTIVE"):
                            raise ValueError("Một câu không còn được duyệt hoặc nằm ngoài khối Toán 6–9.")
                        slides.append((row, _detail(client, str(entry["question_version_id"]))))
                    st.session_state["prepared_classroom_wheel"] = (
                        selected_id, build_offline_wheel(session["title"], slides,
                                                         session_id=selected_id))
                except Exception as exc:
                    st.error(f"Không chuẩn bị được vòng quay: {exc}")
            prepared_wheel = st.session_state.get("prepared_classroom_wheel")
            if prepared_wheel and prepared_wheel[0] == selected_id:
                st.download_button("⬇ Tải vòng quay HTML ngoại tuyến", prepared_wheel[1],
                    file_name=f"vong-quay-{selected_id[:8]}.html", mime="text/html",
                    key=f"download_wheel_{selected_id}", use_container_width=True)
                from streamlit.components.v1 import html as component_html
                component_html(prepared_wheel[1].decode("utf-8"), height=820, scrolling=True)
                st.caption("Mở tệp HTML đã tải để trình chiếu toàn màn hình. "
                           "Điểm trong bản tải về lưu riêng ở trình duyệt, không đồng bộ lên máy chủ.")
            return
    if queue:
        with st.expander("Sân khấu trình chiếu · dùng trực tiếp hoặc tải về", expanded=False):
            st.caption("Tạo sân khấu từ các câu đã duyệt. Bấm Toàn màn hình trong sân khấu; nếu trình duyệt chặn khung nhúng, tải HTML và mở riêng.")
            if st.button("✨ Chuẩn bị sân khấu", key=f"prepare_offline_{selected_id}"):
                try:
                    slides = []
                    for entry in queue:
                        row = by_version.get(str(entry["question_version_id"]))
                        if not row:
                            raise ValueError("Một câu không còn ở trạng thái đã duyệt hoặc không thuộc tài khoản này.")
                        slides.append((row, _detail(client, str(entry["question_version_id"]))))
                    st.session_state["offline_presentation"] = (
                        selected_id, build_offline_presentation(session["title"], slides))
                except Exception as exc:
                    st.error(f"Không thể chuẩn bị đầy đủ tệp trình chiếu: {exc}")
            prepared = st.session_state.get("offline_presentation")
            if prepared and prepared[0] == selected_id:
                st.download_button("⬇ Tải bản toàn màn hình ngoại tuyến (.html)", prepared[1],
                    file_name=f"lop-hoc-{selected_id[:8]}.html", mime="text/html",
                    key=f"download_offline_{selected_id}", use_container_width=True)
                if session["status"] != "LIVE" and st.toggle("▶ Xem thử sân khấu", key=f"inline_stage_{selected_id}"):
                    from streamlit.components.v1 import html as component_html
                    component_html(prepared[1].decode("utf-8"), height=740, scrolling=True)
                    st.caption("Nút Toàn màn hình có thể bị chặn trong khung nhúng Streamlit. Khi đó hãy mở tệp HTML đã tải và bấm nút Toàn màn hình ở đó (hoặc F11).")
    if session["status"] == "PREPARING":
        st.info(f"Đã sẵn sàng {len(queue)} câu hỏi. Bạn có thể tải bản trình chiếu toàn màn hình trước khi bắt đầu.")
        if st.button("Bắt đầu buổi học", disabled=not queue):
            client.table("teacher_classroom_sessions").update(
                {"status": "LIVE", "current_position": 1, "show_answer": False}
            ).eq("session_id", selected_id).eq("teacher_user_id", user_id).execute()
            st.rerun()
    elif session["status"] == "LIVE":
        pos = int(session["current_position"])
        st.markdown(f"### Sân khấu trực tiếp · {len(queue)} câu")
        st.caption("Dùng Trước / Tiếp ngay trong sân khấu để chuyển câu. Trình duyệt ghi nhớ câu đang chiếu trong buổi này. Để chiếu toàn màn hình, thử nút ⛶ hoặc tải HTML rồi mở riêng.")
        current = next((q for q in queue if q["position"] == pos), None)
        if current:
            question = by_version.get(str(current["question_version_id"]))
            if question:
                try:
                    slides = []
                    for entry in queue:
                        row = by_version.get(str(entry["question_version_id"]))
                        if not row:
                            raise ValueError("Một câu trong buổi học không còn được phép hiển thị.")
                        slides.append((row, _detail(client, str(entry["question_version_id"]))))
                    stage = build_offline_presentation(
                        session["title"], slides, initial_index=pos - 1,
                        storage_key=f"classroom-stage:{selected_id}").decode("utf-8")
                    from streamlit.components.v1 import html as component_html
                    component_html(stage, height=760, scrolling=True)
                except Exception as exc:
                    st.error(f"Không dựng được sân khấu; đang hiển thị câu dạng văn bản: {exc}")
                    _render_question(st, client, question, show_answer=False)
            else:
                st.error("Không còn quyền đọc câu đã chọn; dừng buổi học và kiểm tra ngân hàng.")
                return
        if st.button("Kết thúc", use_container_width=True):
            client.table("teacher_classroom_sessions").update({"status": "FINISHED"})\
                .eq("session_id", selected_id).eq("teacher_user_id", user_id).execute()
            st.rerun()
    else:
        st.success("Buổi học đã kết thúc. Danh sách câu vẫn được lưu để xem lại.")
