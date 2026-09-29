"""First classroom presentation authoring surface (local draft and portable JSON)."""

from __future__ import annotations

from html import escape
from hashlib import sha256
from datetime import datetime, timezone
import json
from uuid import uuid4

from portal_v2.ui.lesson_activity_cards import validate_card
from portal_v2.ui.lesson_classroom_tools import validate_tool, render_classroom_tools, TOOL_LABELS
from portal_v2.ui.lesson_ai_presenter import (
    validate_presenter, render_presenter_authoring, avatar_data_uri, presenter_speech_script, ROLES,
)
from portal_v2.ui.lesson_evidence_card import (
    validate_evidence_card, render_evidence_authoring, MAX_DRAFT_PHOTO_BASE64,
)


ACTIVITIES = (
    ("MO_DAU", "1 · Mở đầu"),
    ("HINH_THANH_KIEN_THUC", "2 · Hình thành kiến thức mới"),
    ("LUYEN_TAP", "3 · Luyện tập"),
    ("VAN_DUNG", "4 · Vận dụng"),
)
BLOCK_KINDS = ("Nội dung", "Câu hỏi", "Gợi ý", "Kiến thức chốt")
ACTIVITY_MODES = {
    "MO_DAU": "Khởi động · ôn bài cũ",
    "HINH_THANH_KIEN_THUC": "Khám phá · làm việc nhóm",
    "LUYEN_TAP": "Luyện tập · củng cố",
    "VAN_DUNG": "Vận dụng · tìm tòi mở rộng",
}
TOOL_WORKFLOW = {
    "slide": "prepare",
    "approved_question": "prepare",
    "presenter_script": "prepare",
    "classroom_stage_setup": "prepare",
    "stage_play": "both",
    "presenter_speech": "both",
    "evidence_capture": "both",
    "phone_photo_inbox": "both",
}


def tool_workflow(kind: str) -> str:
    return TOOL_WORKFLOW[kind]


def _designer_style(st) -> None:
    """Page-local presentation styles; leave button colors and animations to the portal theme."""
    st.markdown('''<style>
        .lesson-designer-band{background:#08263e;color:#f4fbff;border-radius:12px;
            padding:10px 16px;margin:8px 0 12px;font-weight:700;letter-spacing:.01em}
        .lesson-designer-band small{display:block;color:#bbd5e7;font-weight:500;margin-top:2px}
        .lesson-designer-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:6px 0}
        .lesson-designer-grid article{background:#edf5fa;border:1px solid #bfd4e5;
            border-radius:10px;padding:9px 12px;color:#0b3550;box-shadow:0 2px 0 #a8c5d7}
        .lesson-designer-grid strong{display:block;font-size:.9rem}
        .lesson-designer-grid span{display:block;font-size:.75rem;margin-top:3px}
        @media(max-width:850px){.lesson-designer-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        div[data-testid="stButton"] > button,div[data-testid="stDownloadButton"] > button{
            min-height:2.6rem;border-radius:10px;box-shadow:0 2px 0 #55758a,0 3px 6px #071b3426}
        div[data-testid="stButton"] > button:active,div[data-testid="stDownloadButton"] > button:active{
            box-shadow:0 1px 0 #55758a;transform:translateY(1px)}
        label[data-testid="stWidgetLabel"]{color:#0b3550;font-weight:700}
        div[data-testid="stVerticalBlock"]{gap:.45rem}
    </style>''', unsafe_allow_html=True)


def _designer_band(st, title: str, subtitle: str = "") -> None:
    st.markdown('<div class="lesson-designer-band">' + escape(title)
                + ('<small>' + escape(subtitle) + '</small>' if subtitle else '') + '</div>',
                unsafe_allow_html=True)


def activity_overview_html(draft: dict) -> str:
    labels = dict(ACTIVITIES)
    cells = []
    for key, _ in ACTIVITIES:
        count = sum(item["activity"] == key for collection in
                    ("slides", "activity_cards", "classroom_tools", "ai_presenters", "evidence_cards")
                    for item in draft.get(collection, []))
        cells.append('<article><strong>' + escape(labels[key]) + '</strong><span>'
                     + escape(ACTIVITY_MODES[key]) + ' · ' + str(count) + ' nội dung</span></article>')
    return '<div class="lesson-designer-grid">' + ''.join(cells) + '</div>'


def new_draft() -> dict:
    return {"schema_version": 1, "subject": "Toán", "grade": 6,
            "lesson_title": "", "source_lesson_id": "", "slides": [],
            "activity_cards": [], "classroom_tools": [], "ai_presenters": [],
            "evidence_cards": []}


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
    presenters = draft.get("ai_presenters", [])
    if not isinstance(presenters, list) or len(presenters) > 40:
        raise ValueError("Bài giảng vượt quá 40 thẻ nhân vật AI.")
    for presenter in presenters:
        validate_presenter(presenter)
        if presenter["id"] in ids:
            raise ValueError("Mã thẻ nhân vật AI đã được sử dụng.")
        ids.add(presenter["id"])
    evidence_cards = draft.get("evidence_cards", [])
    if not isinstance(evidence_cards, list) or len(evidence_cards) > 40:
        raise ValueError("Bài giảng vượt quá 40 thẻ ghi nhận.")
    for evidence in evidence_cards:
        validate_evidence_card(evidence)
        if evidence["id"] in ids:
            raise ValueError("Mã thẻ ghi nhận đã được sử dụng.")
        ids.add(evidence["id"])
    if sum(len(photo["data_b64"]) for evidence in evidence_cards
           for photo in evidence.get("media", [])) > MAX_DRAFT_PHOTO_BASE64:
        raise ValueError("Tổng dung lượng ảnh minh chứng vượt giới hạn bản nháp.")
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


def build_presentation_html(draft: dict, *, classroom_stages: dict[str, bytes] | None = None) -> str:
    """Escape all teacher text; presentation uses pinned reveal.js assets."""
    validate_draft(draft)
    classroom_stages = classroom_stages or {}
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
        for evidence in draft.get("evidence_cards", []):
            if evidence["activity"] == activity:
                recent = evidence["entries"][-1] if evidence["entries"] else None
                summary = (f"Lần ghi gần nhất: {recent['participated']} tham gia, "
                           f"{recent['completed']} hoàn thành, {recent['needs_help']} cần hỗ trợ."
                           if recent else "Chưa có số liệu học sinh. Giáo viên ghi nhận trong trình soạn bài.")
                photos = ''.join(
                    '<figure><img alt="Ảnh hoạt động học sinh từ ' + escape(photo["device"], quote=True)
                    + '" src="data:' + photo["mime"] + ';base64,' + photo["data_b64"]
                    + '"><figcaption>' + escape(photo["device"]) + '</figcaption></figure>'
                    for photo in evidence.get("media", []))
                sections.append('<section class="lesson-evidence-slide"><small>' + escape(label)
                                + '</small><h2>' + escape(evidence["title"]) + '</h2><p>'
                                + escape(summary) + '</p><p>'
                                + f"Đã ghi {len(evidence['entries'])} lần từ {len(evidence['source_ids'])} nguồn kết nối."
                                + '</p><div class="lesson-evidence-media">' + photos + '</div>'
                                + '</section>')
        for presenter in draft.get("ai_presenters", []):
            if presenter["activity"] == activity:
                script_lines = ''.join(
                    '<span class="ai-script-line">' + escape(line) + '</span>'
                    for line in presenter["message"].splitlines() if line.strip()
                )
                sections.append('<section class="ai-presenter-slide"><small>' + escape(label)
                                + '</small><div class="ai-presenter-layout">'
                                '<div class="ai-presenter-avatar" role="img" aria-label="Nhân vật AI"></div>'
                                '<div class="ai-presenter-dialog"><h2>'
                                + escape(ROLES[presenter["role"]]) + '</h2><div class="ai-script">'
                                + script_lines + '</div><div class="ai-voice-controls">'
                                '<select class="ai-voice-select" aria-label="Chọn giọng tiếng Việt"></select>'
                                '<button type="button" class="ai-voice-play">▶ Phát lời dẫn</button>'
                                '<button type="button" class="ai-voice-stop">■ Dừng</button></div>'
                                '<p class="ai-voice-status" role="status" aria-live="polite">'
                                'Bấm Phát để nhân vật đọc kịch bản.</p></div></div></section>')
        for tool in draft.get("classroom_tools", []):
            if tool["activity"] == activity:
                stage = classroom_stages.get(tool["id"])
                if stage is not None:
                    # Stage builders escape question content. srcdoc keeps the
                    # existing interactive stage inside this presentation slide.
                    frame = ('<div class="classroom-stage-shell">'
                             '<iframe title="' + escape(TOOL_LABELS[tool["kind"]], quote=True)
                             + '" sandbox="allow-scripts allow-same-origin" allow="fullscreen" allowfullscreen '
                             + 'srcdoc="' + escape(stage.decode("utf-8"), quote=True) + '"></iframe>'
                             '<button class="classroom-fullscreen" type="button" '
                             'aria-label="Toàn màn hình sân khấu">⛶ Toàn màn hình</button></div>')
                else:
                    frame = '<p>Chuẩn bị sân khấu tích hợp để trình chiếu tại slide này.</p>'
                sections.append('<section class="classroom-tool-slide"><small>' + escape(label)
                                + '</small><h2>' + escape(TOOL_LABELS[tool["kind"]])
                                + '</h2>' + frame + '</section>')
    if not sections:
        sections.append('<section><h2>Chưa có slide</h2><p>Thêm nội dung để xem trước.</p></section>')
    avatar_css = ('.ai-presenter-avatar{background-image:url("' + avatar_data_uri() + '")}'
                  if draft.get("ai_presenters") else '')
    return ('<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/reveal.css">'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/theme/white.css">'
            '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]],displayMath:[["$$","$$"]]},options:{skipHtmlTags:["script","style","textarea","pre","code"]}};</script>'
            '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
            '<style>.reveal .slides{text-align:left}.reveal small{color:#2563a6}'
            '.reveal .content{padding:.4em .7em;margin:.5em 0;background:#eef4fc;border-radius:.35em}'
            '.reveal .question-choices{font-size:.68em;line-height:1.5;list-style:none;padding-left:0}'
            '.reveal .lesson-evidence-media{display:flex;gap:12px;align-items:start;max-height:42vh}'
            '.reveal .lesson-evidence-media figure{max-width:30%;margin:0;font-size:.45em}'
            '.reveal .lesson-evidence-media img{display:block;max-width:100%;max-height:36vh;object-fit:contain}'
            '.reveal .content p{margin:.2em 0;font-size:.65em}'
            '.reveal .classroom-tool-slide h2{font-size:.9em;margin:.08em 0 .2em}'
            '.reveal .classroom-stage-shell{position:relative;width:100%;height:76vh;'
            'background:#061427;overflow:hidden;border-radius:12px}'
            '.classroom-stage-shell iframe{display:block;width:100%;height:100%;border:0}'
            '.classroom-stage-shell:fullscreen{width:100vw;height:100vh;border-radius:0}'
            '.classroom-fullscreen{position:absolute;right:12px;bottom:12px;z-index:5;'
            'padding:9px 13px;border:1px solid #a9daf9;border-radius:10px;'
            'background:#0b3550;color:#fff;font:700 16px Segoe UI,Arial,sans-serif;cursor:pointer;'
            'box-shadow:0 4px 14px #071b34aa}'
            '.classroom-fullscreen:focus-visible{outline:3px solid #ffc857}'
            '.lesson-presentation-fullscreen{position:fixed;top:12px;right:12px;z-index:100;'
            'padding:10px 16px;border:1px solid #a9daf9;border-radius:10px;'
            'background:#0b3550;color:#fff;font:700 16px Segoe UI,Arial,sans-serif;cursor:pointer;'
            'box-shadow:0 4px 14px #071b34aa}'
            '.lesson-presentation-fullscreen:focus-visible{outline:3px solid #ffc857}'
            'html:fullscreen,html:fullscreen body{width:100%;height:100%;margin:0;background:#fff}'
            'html:fullscreen .reveal{width:100vw;height:100vh}'
            '.reveal .ai-presenter-layout{display:grid;grid-template-columns:35% 1fr;gap:3%;'
            'align-items:center;min-height:60vh}'
            '.reveal .ai-presenter-avatar{height:58vh;background-position:center bottom;'
            'background-repeat:no-repeat;background-size:contain}'
            '.reveal .ai-presenter-dialog{background:#e9f7ff;border:2px solid #61bee4;'
            'border-radius:24px;padding:1em;color:#123453;box-shadow:0 12px 32px #12345322}'
            '.reveal .ai-presenter-dialog h2{color:#105b85;font-size:1.1em;margin:0 0 .4em}'
            '.reveal .ai-presenter-dialog p{font-size:.8em;line-height:1.5;margin:0}'
            '.reveal .ai-script{font-size:.72em;line-height:1.45;max-height:36vh;overflow:auto}'
            '.reveal .ai-script-line{display:block;margin:.3em 0}'
            '.reveal .ai-voice-controls{display:flex;gap:.35em;align-items:center;flex-wrap:wrap;margin-top:.7em}'
            '.reveal .ai-voice-controls select,.reveal .ai-voice-controls button{font:600 .42em Segoe UI,Arial;'
            'padding:.6em;border-radius:.6em;border:1px solid #267399;background:#fff;color:#123453}'
            '.reveal .ai-voice-controls button{cursor:pointer;background:#075987;color:#fff}'
            '.reveal .ai-voice-status{font-size:.48em!important;margin-top:.5em!important}'
            '.reveal .ai-speaking .ai-presenter-avatar{animation:ai-talk .7s ease-in-out infinite alternate;'
            'filter:drop-shadow(0 0 20px #35c6e6)}'
            '.reveal .ai-speaking .ai-presenter-dialog{border-color:#11aace;'
            'box-shadow:0 0 26px #11aace66}'
            '@keyframes ai-talk{to{transform:translateY(-10px) rotate(1.5deg)}}'
            '@media(prefers-reduced-motion:reduce){.reveal .ai-speaking .ai-presenter-avatar{animation:none}}'
            '@media(max-width:720px){.reveal .ai-presenter-layout{grid-template-columns:30% 1fr}}'
            + avatar_css +
            '</style></head><body>'
            '<button class="lesson-presentation-fullscreen" type="button" '
            'aria-label="Toàn màn hình bài giảng">⛶ Toàn màn hình bài giảng</button>'
            '<div class="reveal"><div class="slides">' + "".join(sections) + '</div></div>'
            '<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/reveal.js"></script>'
            '<script>if(window.Reveal){Reveal.initialize({hash:false,controls:true,progress:true,center:true});}'
            'document.querySelector(".lesson-presentation-fullscreen").addEventListener("click",function(){'
            'if(document.fullscreenElement===document.documentElement){document.exitFullscreen();return;}'
            'document.documentElement.requestFullscreen().catch(function(){'
            'this.textContent="Dùng F11 để mở toàn màn hình";'
            '}.bind(this));});'
            'document.addEventListener("fullscreenchange",function(){'
            'const button=document.querySelector(".lesson-presentation-fullscreen");'
            'button.textContent=document.fullscreenElement===document.documentElement'
            '?"⤢ Thoát toàn màn hình":"⛶ Toàn màn hình bài giảng";'
            'if(window.Reveal){Reveal.layout();}});'
            'document.addEventListener("click",function(event){'
            'const button=event.target.closest(".classroom-fullscreen");if(!button)return;'
            'event.preventDefault();event.stopPropagation();'
            'const shell=button.closest(".classroom-stage-shell");'
            'if(document.fullscreenElement===shell){document.exitFullscreen();return;}'
            'if(!shell.requestFullscreen){button.textContent="Trình duyệt không hỗ trợ";return;}'
            'shell.requestFullscreen().catch(function(){button.textContent="Không mở được toàn màn hình";});'
            '});document.addEventListener("fullscreenchange",function(){'
            'document.querySelectorAll(".classroom-fullscreen").forEach(function(button){'
            'button.textContent=document.fullscreenElement===button.parentElement'
            '?"⤢ Thoát toàn màn hình":"⛶ Toàn màn hình";});});</script>'
            + (presenter_speech_script() if draft.get("ai_presenters") else '') +
            '</body></html>')


def render_lesson_slide_designer(st, *, client=None, user_id: str | None = None) -> None:
    _designer_style(st)
    _designer_band(st, "THIẾT KẾ BÀI GIẢNG", "Soạn hoạt động · chuẩn bị công cụ · trình chiếu trên lớp")
    st.caption("Bản nháp của giáo viên; chưa công bố cho học sinh.")
    if "lesson_slide_draft" not in st.session_state:
        st.session_state["lesson_slide_draft"] = new_draft()
    if "lesson_slide_revision" not in st.session_state:
        st.session_state["lesson_slide_revision"] = str(uuid4())
    draft = st.session_state["lesson_slide_draft"]
    _designer_band(st, "BẢN NHÁP", "Chọn, lưu hoặc mở bản nháp JSON")
    col_select, col_open, col_save, col_new, col_json = st.columns([2.2, 1.2, 1.2, 1.2, 1.8], gap="small")
    if client is not None and user_id:
        try:
            saved = list_teacher_drafts(client, user_id)
        except Exception as exc:
            saved = []
            st.warning(f"Chưa đọc được bản nháp đã lưu: {exc}")
        with col_select:
            selected = st.selectbox("Chọn bản nháp", saved,
                format_func=lambda row: (row["title"] or "Bài chưa đặt tên") + " · " + str(row["updated_at"]),
                key="slide_saved_draft_selection", disabled=not saved,
                placeholder="Chưa có bản nháp" if not saved else None)
        with col_open:
            st.caption("Mở")
            if st.button("Mở bản nháp đã chọn", key="slide_open_saved", disabled=not saved,
                         use_container_width=True):
                loaded = open_teacher_draft(client, user_id, selected["draft_id"])
                from portal_v2.ui.lesson_phone_inbox import stop_owner_inbox
                stop_owner_inbox(user_id)
                st.session_state["lesson_slide_draft"] = loaded
                st.session_state["lesson_slide_saved_id"] = selected["draft_id"]
                st.session_state["lesson_slide_saved_digest"] = _draft_digest(loaded)
                st.session_state["lesson_slide_revision"] = str(uuid4())
                st.session_state.pop("lesson_slide_selected", None)
                st.rerun()
        with col_save:
            st.caption("Lưu")
            if st.button("Lưu bản nháp", key="slide_save_cloud", use_container_width=True):
                try:
                    draft_id = st.session_state.get("lesson_slide_saved_id") or str(uuid4())
                    save_teacher_draft(client, user_id, draft_id, draft)
                    st.session_state["lesson_slide_saved_id"] = draft_id
                    st.session_state["lesson_slide_saved_digest"] = _draft_digest(draft)
                    st.success("Đã lưu bản nháp. Các chỉnh sửa tiếp theo sẽ được tự lưu.")
                except Exception as exc:
                    st.error(f"Chưa lưu được bản nháp: {exc}")
        with col_new:
            st.caption("Tạo mới")
            if st.button("Tạo bài giảng mới", key="slide_new_cloud", use_container_width=True):
                from portal_v2.ui.lesson_phone_inbox import stop_owner_inbox
                stop_owner_inbox(user_id)
                st.session_state["lesson_slide_draft"] = new_draft()
                st.session_state["lesson_slide_revision"] = str(uuid4())
                for key in ("lesson_slide_saved_id", "lesson_slide_saved_digest", "lesson_slide_selected"):
                    st.session_state.pop(key, None)
                st.session_state.pop("lesson_integrated_stages", None)
                st.rerun()
    else:
        with col_select:
            st.selectbox("Chọn bản nháp", [], disabled=True, placeholder="Đăng nhập để chọn")
        for column, label in ((col_open, "Mở bản nháp đã chọn"), (col_save, "Lưu bản nháp"),
                              (col_new, "Tạo bài giảng mới")):
            with column:
                st.caption(label)
                st.button(label, disabled=True, use_container_width=True)
    with col_json:
        uploaded = st.file_uploader("Mở bản nháp JSON", type=["json"], key="slide_import")
        import_clicked = st.button("Nạp JSON", key="slide_import_button", disabled=uploaded is None,
                                   use_container_width=True)
    if uploaded is not None and import_clicked:
        try:
            if uploaded.size > 2_000_000:
                raise ValueError("File bản nháp vượt quá 2 MB.")
            imported = validate_draft(json.load(uploaded))
            if user_id:
                from portal_v2.ui.lesson_phone_inbox import stop_owner_inbox
                stop_owner_inbox(user_id)
            st.session_state["lesson_slide_draft"] = imported
            st.session_state["lesson_slide_revision"] = str(uuid4())
            st.session_state.pop("lesson_slide_saved_id", None)
            st.session_state.pop("lesson_slide_saved_digest", None)
            st.session_state.pop("lesson_slide_selected", None)
            st.session_state.pop("lesson_integrated_stages", None)
            st.rerun()
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            st.error(f"Không mở được bài giảng: {exc}")
    st.caption("JSON tối đa 2 MB. Bắt đầu bài mới bằng cách chọn môn và lớp, sau đó chọn bài trong Xưởng thẻ.")
    _designer_band(st, "THÔNG TIN BÀI HỌC", "Môn · lớp · bài · yêu cầu cần đạt · sách giáo khoa")
    subject_col, grade_col, lesson_col, requirement_col, book_col = st.columns([1.1, .65, 2, 1.5, 1.5], gap="small")
    revision = st.session_state["lesson_slide_revision"]
    draft["subject"] = subject_col.selectbox("Môn học", ("Toán", "Tiếng Anh"),
                                         index=("Toán", "Tiếng Anh").index(draft["subject"]),
                                         key="slide_subject_" + revision)
    draft["grade"] = grade_col.selectbox("Lớp", (6, 7, 8, 9), index=(6, 7, 8, 9).index(draft["grade"]),
                                      key="slide_grade_" + revision)
    draft["lesson_title"] = lesson_col.text_input("Bài", value=draft["lesson_title"], max_chars=250,
                                                  key="slide_lesson_title_" + revision)
    requirement_codes = st.session_state.get("card_requirements_" + draft.get("source_lesson_id", ""), [])
    requirement_col.text_input("Yêu cầu cần đạt", value=", ".join(requirement_codes) if requirement_codes
                               else "Chọn trong Xưởng thẻ", disabled=True)
    selected_book = st.session_state.get(f"card_book_{draft['subject']}_{draft['grade']}")
    book_col.text_input("Sách giáo khoa", value=selected_book.get("title", "")
                        if isinstance(selected_book, dict) else "Chọn trong Xưởng thẻ", disabled=True)
    if client is not None and user_id:
        from portal_v2.ui.lesson_activity_card_authoring import render_card_authoring
        render_card_authoring(st, draft=draft, client=client, user_id=user_id,
                              revision=revision)
    with st.expander("Mã bài SGK tham khảo", expanded=False):
        draft["source_lesson_id"] = st.text_input("Mã bài SGK tham khảo (chưa xác thực với lịch báo giảng)",
                                                   value=draft["source_lesson_id"], max_chars=250,
                                                   key="slide_source_lesson_" + revision)
    _designer_band(st, "KHÔNG GIAN THIẾT KẾ", "Chọn hoạt động rồi lắp thẻ, công cụ và slide")
    st.markdown(activity_overview_html(draft), unsafe_allow_html=True)
    activity = st.radio("Hoạt động đang thiết kế", [key for key, _ in ACTIVITIES],
                        format_func=dict(ACTIVITIES).get, horizontal=True)
    st.caption("Hình thức gợi ý: " + ACTIVITY_MODES[activity]
               + ". Có thể dùng công cụ bên dưới cho hoạt động này.")
    _designer_band(st, "1 · CHUẨN BỊ TRƯỚC TIẾT HỌC", "Viết kịch bản AI, chọn sân khấu, tạo thẻ và slide")
    st.caption("Các nội dung chuẩn bị được lưu cùng bản nháp; giáo viên kiểm tra trước khi trình chiếu.")
    render_presenter_authoring(st, draft, activity)
    if client is not None and user_id and draft["subject"] == "Toán":
        render_classroom_tools(st, draft, client, user_id, activity)
        if draft.get("classroom_tools") and st.button("Chuẩn bị sân khấu tích hợp",
                                                      key="lesson_integrated_prepare"):
            from portal_v2.ui.lesson_classroom_tools import build_owned_stage
            prepared = {}
            failures = []
            for tool in draft["classroom_tools"]:
                try:
                    prepared[tool["id"]] = build_owned_stage(client, user_id, tool)
                except Exception as exc:
                    failures.append(f"{tool['title']} ({TOOL_LABELS[tool['kind']]}): {exc}")
            st.session_state["lesson_integrated_stages"] = prepared
            for failure in failures:
                st.warning(failure)
            if prepared:
                st.success(f"Đã đưa {len(prepared)} sân khấu vào các slide hoạt động.")
    _designer_band(st, "2 · CÔNG CỤ SỬ DỤNG TRỰC TIẾP", "Thử khi soạn · dùng khi dạy")
    st.caption("Ghi nhận, nhận ảnh điện thoại và mở sân khấu có thể thử ngay ở đây. "
               "Trên slide, giáo viên điều khiển sân khấu và lời dẫn AI.")
    render_evidence_authoring(st, draft, activity, owner_id=user_id,
                              lesson_key=revision, mode="design")
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
    _designer_band(st, "TRÌNH CHIẾU", "Xem trước, bật toàn màn hình và tổ chức hoạt động học")
    with st.expander("Xem trước và trình chiếu", expanded=False):
        st.caption("Sân khấu đã chuẩn bị xuất hiện trong slide tương ứng. Chuẩn bị lại ở vùng thiết kế nếu bộ câu hỏi thay đổi.")
        st.markdown("**Điều khiển trực tiếp trong chế độ trình chiếu**")
        st.caption("Sân khấu và lời dẫn AI chạy trong slide. Ghi nhận học sinh và duyệt ảnh ở khung "
                   "bên dưới; thoát toàn màn hình để thao tác khung này.")
        render_evidence_authoring(st, draft, activity, owner_id=user_id,
                                  lesson_key=revision, mode="presentation")
        known_ids = {tool["id"] for tool in draft.get("classroom_tools", [])}
        staged = {key: value for key, value in st.session_state.get("lesson_integrated_stages", {}).items()
                  if key in known_ids}
        st.components.v1.html(build_presentation_html(draft, classroom_stages=staged),
                              height=780, scrolling=False)
    _designer_band(st, "MATH TEACHER AI · THIẾT KẾ BÀI GIẢNG")
