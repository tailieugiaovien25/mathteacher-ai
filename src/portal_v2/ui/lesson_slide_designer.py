"""First classroom presentation authoring surface (local draft and portable JSON)."""

from __future__ import annotations

from html import escape
from hashlib import sha256
from datetime import datetime, timezone
import json
from uuid import uuid4

from portal_v2.ui.lesson_activity_cards import validate_card
from portal_v2.ui.lesson_classroom_tools import validate_tool, render_classroom_tools, TOOL_LABELS


ACTIVITIES = (
    ("MO_DAU", "1 · Mở đầu"),
    ("HINH_THANH_KIEN_THUC", "2 · Hình thành kiến thức mới"),
    ("LUYEN_TAP", "3 · Luyện tập"),
    ("VAN_DUNG", "4 · Vận dụng"),
)
BLOCK_KINDS = ("Nội dung", "Câu hỏi", "Gợi ý", "Kiến thức chốt")


def new_draft() -> dict:
    return {"schema_version": 1, "subject": "Toán", "grade": 6,
            "lesson_title": "", "source_lesson_id": "", "slides": [],
            "activity_cards": [], "classroom_tools": []}


def save_teacher_draft(client, user_id: str, draft_id: str, draft: dict) -> None:
    """Save a validated draft with the signed-in user's RLS-scoped client."""
    validate_draft(draft)
    if len(json.dumps(draft, ensure_ascii=False).encode("utf-8")) > 2_000_000:
        raise ValueError("Bản nháp vượt quá 2 MB.")
    client.table("teacher_lesson_drafts").upsert({
        "draft_id": draft_id, "owner_user_id": user_id,
        "title": draft["lesson_title"], "draft_json": draft,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="draft_id").execute()


def list_teacher_drafts(client, user_id: str) -> list[dict]:
    rows = (client.table("teacher_lesson_drafts")
            .select("draft_id,title,updated_at").eq("owner_user_id", user_id)
            .order("updated_at", desc=True).limit(50).execute().data)
    return rows or []


def open_teacher_draft(client, user_id: str, draft_id: str) -> dict:
    rows = (client.table("teacher_lesson_drafts")
            .select("draft_json").eq("owner_user_id", user_id)
            .eq("draft_id", draft_id).limit(1).execute().data)
    if not rows:
        raise ValueError("Không tìm thấy bản nháp của tài khoản này.")
    return validate_draft(rows[0]["draft_json"])


def _draft_digest(draft: dict) -> str:
    return sha256(json.dumps(draft, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def validate_draft(draft: object) -> dict:
    """Validate imported JSON before it reaches session state or a presentation."""
    if not isinstance(draft, dict) or draft.get("schema_version") != 1:
        raise ValueError("File bài giảng không đúng phiên bản.")
    if draft.get("subject") not in ("Toán", "Tiếng Anh") or type(draft.get("grade")) is not int or draft["grade"] not in (6, 7, 8, 9):
        raise ValueError("Môn học hoặc lớp không hợp lệ.")
    for name in ("lesson_title", "source_lesson_id"):
        if not isinstance(draft.get(name), str) or len(draft[name]) > 250:
            raise ValueError("Thông tin bài học không hợp lệ.")
    slides = draft.get("slides")
    if not isinstance(slides, list) or len(slides) > 80:
        raise ValueError("Bài giảng vượt quá 80 slide.")
    ids = set()
    for slide in slides:
        if not isinstance(slide, dict) or slide.get("activity") not in dict(ACTIVITIES):
            raise ValueError("Slide có hoạt động không hợp lệ.")
        slide_id = slide.get("id")
        if not isinstance(slide_id, str) or len(slide_id) > 80 or slide_id in ids:
            raise ValueError("Mã slide trùng hoặc không hợp lệ.")
        ids.add(slide_id)
        if not isinstance(slide.get("title"), str) or len(slide["title"]) > 200:
            raise ValueError("Tiêu đề slide không hợp lệ.")
        blocks = slide.get("blocks")
        if not isinstance(blocks, list) or len(blocks) > 30:
            raise ValueError("Slide vượt quá 30 khối nội dung.")
        for block in blocks:
            if not isinstance(block, dict) or block.get("kind") not in BLOCK_KINDS or not isinstance(block.get("text"), str) or len(block["text"]) > 5000 or type(block.get("reveal_later")) is not bool:
                raise ValueError("Khối nội dung không hợp lệ.")
    cards = draft.get("activity_cards", [])  # Previously exported drafts have no cards.
    if not isinstance(cards, list) or len(cards) > 80:
        raise ValueError("Bài giảng vượt quá 80 thẻ hoạt động.")
    for card in cards:
        validate_card(card)
        if card["review_status"] != "TEACHER_APPROVED" or card["id"] in ids:
            raise ValueError("Chỉ lưu thẻ giáo viên đã duyệt và có mã riêng.")
        ids.add(card["id"])
    classroom_tools = draft.get("classroom_tools", [])
    if not isinstance(classroom_tools, list) or len(classroom_tools) > 40:
        raise ValueError("Bài giảng vượt quá 40 thẻ công cụ.")
    for tool in classroom_tools:
        validate_tool(tool)
        if tool["id"] in ids:
            raise ValueError("Mã thẻ công cụ đã được sử dụng.")
        ids.add(tool["id"])
    evidence = draft.get("source_evidence", {})
    if not isinstance(evidence, dict) or len(evidence) > 80 or any(
        not isinstance(key, str) or not key.startswith("teacher_excerpt:") or
        len(key) > 80 or not isinstance(value, str) or len(value) > 4000
        for key, value in evidence.items()
    ):
        raise ValueError("Nguồn kiến thức giáo viên lưu không hợp lệ.")
    verified_source = draft.get("verified_source")
    if verified_source is not None:
        if not isinstance(verified_source, dict) or not all(
            isinstance(verified_source.get(key), str) and
            0 < len(verified_source[key]) <= 250
            for key in ("textbook_id", "lesson_id")
        ):
            raise ValueError("Bài SGK đã xác thực không hợp lệ.")
        if any("lesson:" + verified_source["lesson_id"] not in card["source_refs"]
               for card in cards):
            raise ValueError("Thẻ đang tham chiếu sang bài SGK khác.")
    return draft


def build_presentation_html(draft: dict) -> str:
    """Escape all teacher text; presentation uses pinned reveal.js assets."""
    validate_draft(draft)
    sections = []
    for activity, label in ACTIVITIES:
        activity_slides = [slide for slide in draft["slides"] if slide["activity"] == activity]
        for slide in activity_slides:
            blocks = []
            for block in slide["blocks"]:
                classes = "content fragment" if block["reveal_later"] else "content"
                blocks.append(f'<div class="{classes}"><strong>{escape(block["kind"])}</strong>'
                              f'<p>{escape(block["text"]).replace(chr(10), "<br>")}</p></div>')
            sections.append(f'<section><small>{escape(label)}</small><h2>{escape(slide["title"])}</h2>'
                            + "".join(blocks) + "</section>")
        for card in draft.get("activity_cards", []):
            if card["activity"] == activity:
                choices = "".join(
                    '<li><b>' + escape(row["label"]) + '.</b> ' + escape(row["text"]) + '</li>'
                    for row in card.get("question_display", []))
                sections.append(f'<section><small>{escape(label)}</small>'
                                f'<h2>{escape(card["title"])}</h2>'
                                f'<p>{escape(card["instruction"]).replace(chr(10), "<br>")}</p>'
                                + ('<ol class="question-choices">' + choices + '</ol>' if choices else '')
                                + '</section>')
        for tool in draft.get("classroom_tools", []):
            if tool["activity"] == activity:
                sections.append('<section><small>' + escape(label) + '</small><h2>'
                                + escape(TOOL_LABELS[tool["kind"]]) + '</h2><p>'
                                + escape(tool["title"]) + '</p><p>Mở sân khấu từ thẻ công cụ trong trình soạn bài.</p></section>')
    if not sections:
        sections.append('<section><h2>Chưa có slide</h2><p>Thêm nội dung để xem trước.</p></section>')
    return ('<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/reveal.css">'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/theme/white.css">'
            '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]],displayMath:[["$$","$$"]]},options:{skipHtmlTags:["script","style","textarea","pre","code"]}};</script>'
            '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
            '<style>.reveal .slides{text-align:left}.reveal small{color:#2563a6}'
            '.reveal .content{padding:.4em .7em;margin:.5em 0;background:#eef4fc;border-radius:.35em}'
            '.reveal .question-choices{font-size:.68em;line-height:1.5;list-style:none;padding-left:0}'
            '.reveal .content p{margin:.2em 0;font-size:.65em}</style></head><body>'
            '<div class="reveal"><div class="slides">' + "".join(sections) + '</div></div>'
            '<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/reveal.js"></script>'
            '<script>if(window.Reveal){Reveal.initialize({hash:false,controls:true,progress:true,center:true});}</script>'
            '</body></html>')


def render_lesson_slide_designer(st, *, client=None, user_id: str | None = None) -> None:
    st.title("Thiết kế bài giảng")
    st.caption("Bản nháp của giáo viên; chưa công bố cho học sinh. Tải JSON để lưu và mở lại khi cần.")
    if "lesson_slide_draft" not in st.session_state:
        st.session_state["lesson_slide_draft"] = new_draft()
    if "lesson_slide_revision" not in st.session_state:
        st.session_state["lesson_slide_revision"] = str(uuid4())
    draft = st.session_state["lesson_slide_draft"]
    if client is not None and user_id:
        with st.expander("Bản nháp đã lưu của tôi", expanded=True):
            try:
                saved = list_teacher_drafts(client, user_id)
                if saved:
                    selected = st.selectbox("Chọn bản nháp", saved,
                        format_func=lambda row: (row["title"] or "Bài chưa đặt tên") + " · " + str(row["updated_at"]),
                        key="slide_saved_draft_selection")
                    if st.button("Mở bản nháp đã chọn", key="slide_open_saved"):
                        loaded = open_teacher_draft(client, user_id, selected["draft_id"])
                        st.session_state["lesson_slide_draft"] = loaded
                        st.session_state["lesson_slide_saved_id"] = selected["draft_id"]
                        st.session_state["lesson_slide_saved_digest"] = _draft_digest(loaded)
                        st.session_state["lesson_slide_revision"] = str(uuid4())
                        st.session_state.pop("lesson_slide_selected", None)
                        st.rerun()
                else:
                    st.caption("Chưa có bản nháp đã lưu trên tài khoản này.")
            except Exception as exc:
                st.warning(f"Chưa đọc được bản nháp đã lưu: {exc}")
            if st.button("Lưu bản nháp lên tài khoản", key="slide_save_cloud"):
                try:
                    draft_id = st.session_state.get("lesson_slide_saved_id") or str(uuid4())
                    save_teacher_draft(client, user_id, draft_id, draft)
                    st.session_state["lesson_slide_saved_id"] = draft_id
                    st.session_state["lesson_slide_saved_digest"] = _draft_digest(draft)
                    st.success("Đã lưu bản nháp. Các chỉnh sửa tiếp theo sẽ được tự lưu.")
                except Exception as exc:
                    st.error(f"Chưa lưu được bản nháp: {exc}")
            if st.button("Tạo bài giảng mới", key="slide_new_cloud"):
                st.session_state["lesson_slide_draft"] = new_draft()
                st.session_state["lesson_slide_revision"] = str(uuid4())
                for key in ("lesson_slide_saved_id", "lesson_slide_saved_digest", "lesson_slide_selected"):
                    st.session_state.pop(key, None)
                st.rerun()
    st.caption("Nếu bắt đầu bài mới, chọn môn và lớp rồi mở Xưởng thẻ để lấy bài SGK. Chỉ dùng Tải JSON khi đã có bản nháp trước đó.")
    uploaded = st.file_uploader("Mở bản nháp JSON", type=["json"], key="slide_import")
    st.caption("File JSON tải lên giới hạn 2 MB; giới hạn 200 MB ở khung tải lên là mặc định của Streamlit.")
    if uploaded is not None and st.button("Nạp bản nháp", key="slide_import_button"):
        try:
            if uploaded.size > 2_000_000:
                raise ValueError("File bản nháp vượt quá 2 MB.")
            imported = validate_draft(json.load(uploaded))
            st.session_state["lesson_slide_draft"] = imported
            st.session_state["lesson_slide_revision"] = str(uuid4())
            st.session_state.pop("lesson_slide_saved_id", None)
            st.session_state.pop("lesson_slide_saved_digest", None)
            st.session_state.pop("lesson_slide_selected", None)
            st.rerun()
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            st.error(f"Không mở được bài giảng: {exc}")
    left, right = st.columns(2)
    revision = st.session_state["lesson_slide_revision"]
    draft["subject"] = left.selectbox("Môn học", ("Toán", "Tiếng Anh"),
                                         index=("Toán", "Tiếng Anh").index(draft["subject"]),
                                         key="slide_subject_" + revision)
    draft["grade"] = right.selectbox("Lớp", (6, 7, 8, 9), index=(6, 7, 8, 9).index(draft["grade"]),
                                      key="slide_grade_" + revision)
    if client is not None and user_id:
        from portal_v2.ui.lesson_activity_card_authoring import render_card_authoring
        render_card_authoring(st, draft=draft, client=client, user_id=user_id,
                              revision=revision)
    draft["lesson_title"] = st.text_input("Tên bài học", value=draft["lesson_title"], max_chars=250,
                                           key="slide_lesson_title_" + revision)
    draft["source_lesson_id"] = st.text_input("Mã bài SGK tham khảo (chưa xác thực với lịch báo giảng)",
                                               value=draft["source_lesson_id"], max_chars=250,
                                               key="slide_source_lesson_" + revision)
    activity = st.selectbox("Hoạt động", [key for key, _ in ACTIVITIES],
                            format_func=dict(ACTIVITIES).get)
    if client is not None and user_id and draft["subject"] == "Toán":
        render_classroom_tools(st, draft, client, user_id, activity)
    slides = [slide for slide in draft["slides"] if slide["activity"] == activity]
    if st.button("Thêm slide vào hoạt động này"):
        slide = {"id": str(uuid4()), "activity": activity, "title": "Slide mới", "blocks": []}
        draft["slides"].append(slide)
        st.session_state["lesson_slide_selected"] = slide["id"]
        st.rerun()
    if slides:
        slide_ids = [slide["id"] for slide in slides]
        chosen = st.session_state.get("lesson_slide_selected")
        slide_id = st.selectbox("Slide", slide_ids, index=slide_ids.index(chosen) if chosen in slide_ids else 0,
                                format_func=lambda value: next(s["title"] for s in slides if s["id"] == value))
        slide = next(s for s in slides if s["id"] == slide_id)
        st.session_state["lesson_slide_selected"] = slide_id
        slide["title"] = st.text_input("Tiêu đề slide", value=slide["title"], max_chars=200,
                                       key="slide_title_" + revision + slide_id)
        for index, block in enumerate(slide["blocks"]):
            with st.expander(f"{index+1}. {block['kind']}", expanded=True):
                block["kind"] = st.selectbox("Loại khối", BLOCK_KINDS, index=BLOCK_KINDS.index(block["kind"]),
                                              key=f"slide_kind_{revision}_{slide_id}_{index}")
                block["text"] = st.text_area("Nội dung", value=block["text"], max_chars=5000,
                                              key=f"slide_text_{revision}_{slide_id}_{index}")
                block["reveal_later"] = st.checkbox("Giáo viên bấm mới hiện", value=block["reveal_later"],
                                                    key=f"slide_reveal_{revision}_{slide_id}_{index}")
                if st.button("Xóa khối", key=f"slide_remove_block_{slide_id}_{index}"):
                    slide["blocks"].pop(index)
                    st.rerun()
        if st.button("Thêm khối nội dung"):
            slide["blocks"].append({"kind": "Nội dung", "text": "", "reveal_later": False})
            st.rerun()
        if st.button("Xóa slide đang chọn"):
            draft["slides"].remove(slide)
            st.session_state.pop("lesson_slide_selected", None)
            st.rerun()
    validate_draft(draft)
    if client is not None and user_id and st.session_state.get("lesson_slide_saved_id"):
        current_digest = _draft_digest(draft)
        if current_digest != st.session_state.get("lesson_slide_saved_digest"):
            try:
                save_teacher_draft(client, user_id, st.session_state["lesson_slide_saved_id"], draft)
                st.session_state["lesson_slide_saved_digest"] = current_digest
                st.caption("Đã tự lưu thay đổi vào tài khoản.")
            except Exception as exc:
                st.error(f"Chưa tự lưu được thay đổi: {exc}. Hãy tải bản nháp JSON để giữ nội dung.")
    st.download_button("Tải bản nháp JSON", json.dumps(draft, ensure_ascii=False, indent=2),
                       file_name="bai_giang_nhap.json", mime="application/json")
    with st.expander("Xem trước và trình chiếu", expanded=False):
        st.caption("Bản xem trước dùng reveal.js qua mạng; các khối đánh dấu sẽ hiện khi chuyển bước.")
        st.components.v1.html(build_presentation_html(draft), height=620, scrolling=False)
