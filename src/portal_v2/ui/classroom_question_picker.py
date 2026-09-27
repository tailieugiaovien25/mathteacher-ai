"""Visual question picker for teacher classroom sessions.

R21 scope:
- no database writes;
- consumes already-approved question rows supplied by teacher_classroom_streamlit;
- provides visual filtering, preview, selected-count progress and system suggestion;
- selection lives only in Streamlit session_state until the existing create-session RPC is called.
"""
from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any, Callable


_TYPE_LABELS = {
    "MULTIPLE_CHOICE": "◉ Trắc nghiệm",
    "TRUE_FALSE": "✓ Đúng / Sai",
    "SHORT_ANSWER": "✎ Trả lời ngắn",
    "ESSAY": "✎ Tự luận",
}
_LEVEL_LABELS = {
    "RECOGNITION": "Nhận biết",
    "KNOWLEDGE": "Nhận biết",
    "UNDERSTANDING": "Thông hiểu",
    "COMPREHENSION": "Thông hiểu",
    "APPLICATION": "Vận dụng",
    "HIGH_APPLICATION": "Vận dụng cao",
}


def _type_label(code: str) -> str:
    return _TYPE_LABELS.get(str(code or "").upper(), str(code or "Khác"))


def _level_label(code: str) -> str:
    raw = str(code or "").upper()
    return _LEVEL_LABELS.get(raw, raw.replace("_", " ").title() if raw else "Chưa gắn mức độ")


def _balanced_suggestion(rows: list[dict], count: int) -> list[str]:
    """Pick a stable, level-balanced set from the currently filtered rows."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[_level_label(row.get("cognitive_level_code"))].append(row)

    preferred = ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao", "Chưa gắn mức độ"]
    ordered_groups = [groups[name] for name in preferred if groups.get(name)]
    ordered_groups.extend(
        values for name, values in sorted(groups.items())
        if name not in preferred and values
    )

    chosen: list[str] = []
    cursor = 0
    while len(chosen) < count and ordered_groups:
        progressed = False
        for group in ordered_groups:
            if cursor < len(group):
                qid = str(group[cursor]["question_version_id"])
                if qid not in chosen:
                    chosen.append(qid)
                    progressed = True
                    if len(chosen) >= count:
                        break
        if not progressed:
            break
        cursor += 1
    return chosen[:count]


def render_question_picker(
    st: Any,
    questions: list[dict],
    *,
    key: str,
    target_count: int = 9,
    max_selected: int = 9,
    require_exact: bool = True,
    preview_renderer: Callable[[dict], None] | None = None,
) -> list[str]:
    """Render a visual card picker and return selected question_version_ids."""
    state_key = f"{key}_selected"
    preview_key = f"{key}_preview"

    valid_ids = {str(q["question_version_id"]) for q in questions}
    current = [str(x) for x in st.session_state.get(state_key, []) if str(x) in valid_ids]
    st.session_state[state_key] = current

    st.markdown("""
<style>
.qp-head{display:flex;justify-content:space-between;align-items:center;gap:12px;
padding:14px 18px;border:1px solid #c8deee;border-radius:16px;background:linear-gradient(135deg,#f7fbff,#eef7ff);
margin:4px 0 14px}
.qp-title{font-weight:850;color:#153f61;font-size:1.05rem}
.qp-count{font-weight:850;color:#fff;background:#155a8f;border-radius:999px;padding:7px 13px}
.qp-card{border:1px solid #c9ddec;border-radius:17px;background:#fff;padding:14px 15px 12px;
box-shadow:0 5px 0 #dbe8f1,0 12px 24px #153e5d12;min-height:190px}
.qp-card-selected{border-color:#6b46b8;background:#f5efff;box-shadow:0 5px 0 #b9a2e2,0 12px 24px #4d2d7a18}
.qp-code{font-size:.82rem;font-weight:850;color:#275879;letter-spacing:.04em}
.qp-prompt{font-family:"Times New Roman",Times,serif;font-size:1.08rem;line-height:1.45;color:#182d41;
margin:9px 0 12px;min-height:74px}
.qp-tags{display:flex;flex-wrap:wrap;gap:6px}
.qp-tag{display:inline-block;border-radius:999px;padding:4px 9px;background:#eaf4fb;color:#1e5278;font-size:.76rem;font-weight:750}
.qp-tag-level{background:#fff0c6;color:#805600}
.qp-selected-strip{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0 13px}
.qp-slot{width:34px;height:34px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;
font-weight:850;background:#edf3f7;color:#6b8091;border:1px solid #d4e1ea}
.qp-slot-on{background:#6b46b8;color:#fff;border-color:#57389a;box-shadow:0 3px 0 #452d7d}
</style>
""", unsafe_allow_html=True)

    count = len(current)
    exact_text = f"{count} / {target_count}" if require_exact else f"{count} đã chọn"
    st.markdown(
        f'<div class="qp-head"><div><div class="qp-title">Thư viện chọn câu hỏi</div>'
        f'<div style="color:#5e7385;font-size:.9rem">Lọc · xem trước · chọn trực quan</div></div>'
        f'<div class="qp-count">{escape(exact_text)}</div></div>',
        unsafe_allow_html=True,
    )

    slots = "".join(
        f'<span class="qp-slot {"qp-slot-on" if i <= count else ""}">{i}</span>'
        for i in range(1, target_count + 1)
    )
    st.markdown(f'<div class="qp-selected-strip">{slots}</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.7, 1, 1])
    with f1:
        search = st.text_input(
            "Tìm trong câu hỏi",
            key=f"{key}_search",
            placeholder="Nhập mã câu hoặc từ khóa nội dung…",
        ).strip().lower()
    type_options = sorted({_type_label(q.get("question_type_code")) for q in questions})
    with f2:
        selected_type = st.selectbox("Loại câu", ["Tất cả"] + type_options, key=f"{key}_type")
    level_options = sorted({_level_label(q.get("cognitive_level_code")) for q in questions})
    with f3:
        selected_level = st.selectbox("Mức độ", ["Tất cả"] + level_options, key=f"{key}_level")

    filtered: list[dict] = []
    for q in questions:
        code = str(q.get("item", {}).get("question_code", ""))
        prompt = str(q.get("prompt_text", ""))
        if search and search not in f"{code} {prompt}".lower():
            continue
        if selected_type != "Tất cả" and _type_label(q.get("question_type_code")) != selected_type:
            continue
        if selected_level != "Tất cả" and _level_label(q.get("cognitive_level_code")) != selected_level:
            continue
        filtered.append(q)

    a, b, c = st.columns([1.2, 1.2, 2.2])
    with a:
        if st.button(
            f"✨ Gợi ý {target_count} câu",
            key=f"{key}_suggest",
            disabled=len(filtered) < target_count,
            use_container_width=True,
        ):
            st.session_state[state_key] = _balanced_suggestion(filtered, target_count)
            st.rerun()
    with b:
        if st.button("↺ Xóa lựa chọn", key=f"{key}_clear", disabled=not current, use_container_width=True):
            st.session_state[state_key] = []
            st.session_state.pop(preview_key, None)
            st.rerun()
    with c:
        st.caption(
            f"Đang hiển thị {len(filtered)} / {len(questions)} câu đã duyệt. "
            + (f"Cần chọn đúng {target_count} câu." if require_exact else f"Tối đa {max_selected} câu.")
        )

    if not filtered:
        st.info("Không có câu hỏi phù hợp với bộ lọc hiện tại.")
        return list(st.session_state[state_key])

    for start in range(0, len(filtered), 3):
        cols = st.columns(3)
        for col, q in zip(cols, filtered[start:start + 3]):
            qid = str(q["question_version_id"])
            selected_now = qid in st.session_state[state_key]
            code = str(q.get("item", {}).get("question_code", qid[:8]))
            prompt = str(q.get("prompt_text", "")).strip()
            short_prompt = prompt if len(prompt) <= 180 else prompt[:177].rstrip() + "…"
            qtype = _type_label(q.get("question_type_code"))
            level = _level_label(q.get("cognitive_level_code"))
            with col:
                css_class = "qp-card qp-card-selected" if selected_now else "qp-card"
                st.markdown(
                    f'<div class="{css_class}"><div class="qp-code">{escape(code)}</div>'
                    f'<div class="qp-prompt">{escape(short_prompt)}</div>'
                    f'<div class="qp-tags"><span class="qp-tag">{escape(qtype)}</span>'
                    f'<span class="qp-tag qp-tag-level">{escape(level)}</span></div></div>',
                    unsafe_allow_html=True,
                )
                x, y = st.columns(2)
                with x:
                    if st.button(
                        "✓ Đã chọn" if selected_now else "＋ Chọn",
                        key=f"{key}_pick_{qid}",
                        type="primary" if selected_now else "secondary",
                        use_container_width=True,
                    ):
                        selected_ids = list(st.session_state[state_key])
                        if selected_now:
                            selected_ids.remove(qid)
                        elif len(selected_ids) < max_selected:
                            selected_ids.append(qid)
                        else:
                            st.warning(f"Đã đạt giới hạn {max_selected} câu.")
                        st.session_state[state_key] = selected_ids
                        st.rerun()
                with y:
                    if st.button("👁 Xem", key=f"{key}_preview_{qid}", use_container_width=True):
                        st.session_state[preview_key] = qid
                        st.rerun()

    preview_id = st.session_state.get(preview_key)
    if preview_id and preview_id in valid_ids:
        preview_row = next((q for q in questions if str(q["question_version_id"]) == preview_id), None)
        if preview_row:
            st.divider()
            st.markdown("### 👁 Xem trước câu hỏi")
            if preview_renderer:
                preview_renderer(preview_row)
            else:
                st.markdown(str(preview_row.get("prompt_text", "")))
            if st.button("Đóng xem trước", key=f"{key}_close_preview"):
                st.session_state.pop(preview_key, None)
                st.rerun()

    return list(st.session_state[state_key])
