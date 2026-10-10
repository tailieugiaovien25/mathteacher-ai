"""Pure helpers for rendering AI Teaching Assistant classroom runtime state."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping


def build_runtime_overlay_html(
    runtime_state: Mapping[str, Any] | None,
    classroom_stages: Mapping[str, bytes] | None = None,
) -> str:
    """Build a safe, self-contained overlay consumed by the lesson presentation iframe.

    The overlay is presentation-only. It does not execute a classroom action and does not
    mutate the Streamlit session; the executor remains the sole writer of runtime state.
    """
    state = dict(runtime_state or {})
    stages = dict(classroom_stages or {})
    timer = state.get("timer") if isinstance(state.get("timer"), Mapping) else None
    quiz = state.get("quiz") if isinstance(state.get("quiz"), Mapping) else None
    stage = state.get("stage") if isinstance(state.get("stage"), Mapping) else None
    whiteboard = state.get("whiteboard") if isinstance(state.get("whiteboard"), Mapping) else None

    parts: list[str] = []
    script: list[str] = []

    if timer and str(timer.get("status", "")) == "running":
        seconds = max(0, int(timer.get("seconds", 0)))
        started_at = escape(str(timer.get("started_at", "")), quote=True)
        parts.append(
            '<div class="ta-runtime-card ta-timer-card" role="status" aria-live="polite">'
            '<div class="ta-runtime-label">⏱ Thời gian</div>'
            '<div id="ta-runtime-timer" class="ta-runtime-timer">'
            + str(seconds)
            + '</div></div>'
        )
        script.append(
            "(function(){const el=document.getElementById('ta-runtime-timer');"
            f"const started=Date.parse('{started_at}');const total={seconds};"
            "function tick(){if(!el)return;let elapsed=Math.max(0,Math.floor((Date.now()-started)/1000));"
            "let left=Math.max(0,total-elapsed);el.textContent=String(left);"
            "if(left<=0){el.classList.add('ta-runtime-expired');clearInterval(id);}}"
            "tick();const id=setInterval(tick,250);})();"
        )

    if quiz and str(quiz.get("question", "")).strip():
        parts.append(
            '<div class="ta-runtime-modal ta-quiz-card" role="dialog" aria-label="Câu hỏi AI Trợ giảng">'
            '<div class="ta-runtime-label">❓ Câu hỏi</div><div class="ta-runtime-content">'
            + escape(str(quiz.get("question", ""))).replace("\n", "<br>")
            + '</div></div>'
        )

    if whiteboard and (str(whiteboard.get("content", "")).strip() or str(whiteboard.get("title", "")).strip()):
        parts.append(
            '<div class="ta-runtime-modal ta-whiteboard-card" role="dialog" aria-label="Bảng của Trợ giảng">'
            '<div class="ta-runtime-label">✏ Bảng</div><div class="ta-whiteboard-title">'
            + escape(str(whiteboard.get("title", "")))
            + '</div><div class="ta-runtime-content">'
            + escape(str(whiteboard.get("content", ""))).replace("\n", "<br>")
            + '</div></div>'
        )

    if stage:
        content_id = str(stage.get("content_id", "")).strip()
        stage_bytes = stages.get(content_id)
        if stage_bytes is not None:
            srcdoc = escape(stage_bytes.decode("utf-8"), quote=True)
            parts.append(
                '<div class="ta-runtime-stage" role="dialog" aria-label="Sân khấu AI Trợ giảng">'
                '<div class="ta-runtime-stage-head"><span>🎬 '
                + escape(str(stage.get("title", "Sân khấu lớp học")))
                + '</span><button type="button" class="ta-stage-close" onclick="this.parentElement.parentElement.hidden=true">Ẩn</button></div>'
                '<iframe title="Sân khấu lớp học" sandbox="allow-scripts allow-same-origin" allow="fullscreen" '
                'allowfullscreen srcdoc="'
                + srcdoc
                + '"></iframe></div>'
            )

    if not parts:
        return ""

    return (
        '<div id="ta-runtime-overlay" class="ta-runtime-overlay">'
        + "".join(parts)
        + "</div>"
        '<style>'
        '.ta-runtime-overlay{position:fixed;inset:0;pointer-events:none;z-index:90;font-family:Segoe UI,Arial,sans-serif}'
        '.ta-runtime-card,.ta-runtime-modal,.ta-runtime-stage{position:absolute;pointer-events:auto;box-sizing:border-box}'
        '.ta-timer-card{top:14px;left:14px;min-width:150px;padding:10px 14px;border-radius:14px;background:#092b44dd;color:#fff;box-shadow:0 8px 24px #001a2a44;text-align:center}'
        '.ta-runtime-label{font-weight:800;font-size:.82rem;letter-spacing:.02em}.ta-runtime-timer{font-size:2.3rem;font-weight:900;line-height:1.05;font-variant-numeric:tabular-nums}'
        '.ta-runtime-expired{color:#ffcc66}.ta-quiz-card,.ta-whiteboard-card{left:8%;right:8%;bottom:6%;padding:18px 22px;border-radius:18px;background:#ffffffee;border:2px solid #66b9dd;color:#08304b;box-shadow:0 14px 36px #05243b44}'
        '.ta-whiteboard-card{bottom:auto;top:14%;left:auto;right:4%;width:min(38vw,460px);min-height:240px;background:#fffdf4;border-color:#d9c48c}'
        '.ta-whiteboard-title{font-weight:900;font-size:1.15rem;margin:.25rem 0 .65rem}.ta-runtime-content{font-size:1.05rem;line-height:1.45;white-space:normal}'
        '.ta-runtime-stage{inset:5% 4%;background:#071725;border-radius:16px;overflow:hidden;box-shadow:0 18px 55px #00142277;border:1px solid #78c8ef;display:flex;flex-direction:column}'
        '.ta-runtime-stage-head{height:48px;display:flex;align-items:center;justify-content:space-between;padding:0 14px;color:#fff;background:#0b3550;font-weight:800}'
        '.ta-stage-close{pointer-events:auto;border:1px solid #8acbed;border-radius:8px;background:#fff;color:#08304b;padding:6px 10px;cursor:pointer}.ta-runtime-stage iframe{flex:1;border:0;min-height:0}'
        '</style><script>'
        + "".join(script)
        + '</script>'
    )


__all__ = ["build_runtime_overlay_html"]
