"""First classroom presentation authoring surface (local draft and portable JSON)."""

from __future__ import annotations

from html import escape
from hashlib import sha256
from datetime import datetime, timezone
import json
from uuid import uuid4
from pathlib import Path
import tempfile
import re
from copy import deepcopy

from portal_v2.ui.lesson_tool_buttons import tool_button, tool_download_button
from portal_v2.ui.lesson_activity_cards import validate_card
from portal_v2.ui.lesson_classroom_tools import validate_tool, render_classroom_tools, TOOL_LABELS
from portal_v2.ui.lesson_ai_presenter import (
    validate_presenter, render_presenter_authoring, avatar_data_uri, presenter_speech_script, ROLES,
)
from portal_v2.ui.lesson_evidence_card import (
    validate_evidence_card, render_evidence_authoring, MAX_DRAFT_PHOTO_BASE64,
)
from ai_kernel.teaching_classroom_surface import build_runtime_overlay_html


ACTIVITIES = (
    ("MO_DAU", "1 · Mở đầu"),
    ("HINH_THANH_KIEN_THUC", "2 · Hình thành kiến thức mới"),
    ("LUYEN_TAP", "3 · Luyện tập"),
    ("VAN_DUNG", "4 · Vận dụng"),
)
BLOCK_KINDS = ("Nội dung", "Câu hỏi", "Gợi ý", "Kiến thức chốt", "Hộp văn bản", "Công thức Toán", "Hình học")
TEXT_FONTS = ("Arial", "Times New Roman", "Calibri", "Segoe UI", "Verdana")
TEXT_STYLE_DEFAULT = {"width": 100, "min_height": 80, "font_size": 32, "font_family": "Arial", "color": "#123453", "background": "#EEF4FC", "bold": False, "italic": False, "underline": False, "align": "left", "depth": 0, "auto_size": False, "positioned": False, "x": 5, "y": 25}
DESIGN_TOOL_TABS = ("Bản nháp", "Thông tin", "SGK · AI", "Trợ giảng", "Sân khấu", "Ghi nhận", "Chèn", "Định dạng", "Slide")
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
            border-radius:10px;padding:9px 12px;color:#08263e;box-shadow:0 1px 0 #a8c5d7}
        .lesson-designer-grid strong{display:block;font-size:.9rem}
        .lesson-designer-grid span{display:block;font-size:.75rem;margin-top:3px}
        @media(max-width:850px){.lesson-designer-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        div[data-testid="stButton"] > button,div[data-testid="stDownloadButton"] > button{
            min-height:40px;border-radius:10px;box-shadow:0 1px 0 #55758a,0 2px 3px #071b3426}
        div[data-testid="stButton"] > button:active,div[data-testid="stDownloadButton"] > button:active{
            box-shadow:0 .5px 0 #55758a;transform:translateY(1px)}
        [data-testid="stWidgetLabel"],.lesson-control-label{
            display:flex;align-items:center;width:170px;max-width:100%;height:34px;box-sizing:border-box;
            margin:0 0 5px;padding:0 9px;border-radius:7px;background:#031629;
            color:#fff!important;font-weight:700;font-size:.8rem;white-space:nowrap;overflow:hidden}
        [data-testid="stWidgetLabel"] p{color:#fff!important;font-size:.8rem;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        [data-testid="stExpander"] summary{min-height:42px;background:#08263e!important;
            color:#fff!important;font-weight:700}
        [data-testid="stExpander"] summary p{color:#fff!important}
        [data-testid="stFileUploaderDropzone"]{min-height:40px!important;height:40px!important;
            padding:0 5px!important;display:flex;align-items:center;justify-content:center}
        [data-testid="stFileUploaderDropzoneInstructions"]{display:none!important}
        [data-testid="stPopover"] button{width:100%;min-height:40px}
        [data-testid="stTabs"]{width:100%;max-width:100%;box-sizing:border-box;
            border-radius:12px;background:#f6f9fc;
            box-shadow:0 13px 28px #08263e38,0 3px 7px #08263e25}
        [data-testid="stTabs"] [role="tablist"]{position:sticky;top:2.75rem;z-index:10;
            background:#f6f9fc;border-radius:9px;padding:3px 6px}
        [data-testid="stTabs"] :is([role="tabpanel"],[data-baseweb="tab-panel"]){
            min-height:780px;height:auto;overflow:visible!important;
            background:#f6f9fc;border:1px solid #bdd1df;border-radius:0 0 10px 10px;
            padding:8px 12px}
        [data-testid="stTabs"] :is([data-testid="stButton"],[data-testid="stDownloadButton"],
            [data-testid="stFormSubmitButton"]) > button{
            width:96px!important;min-width:96px!important;height:96px!important;min-height:96px!important;
            box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;align-items:center;
            gap:5px;padding:6px!important;white-space:normal!important;text-align:center;
            background:linear-gradient(155deg,#fff 0%,#e5f4ff 100%)!important;
            border:1px solid #8bb9d6!important;border-radius:12px!important;color:#063653!important;
            box-shadow:0 3px 6px #092a4533!important}
        [data-testid="stTabs"] :is([data-testid="stButton"],[data-testid="stDownloadButton"],
            [data-testid="stFormSubmitButton"]) > button p{
            color:inherit!important;font-size:.72rem!important;line-height:1.12!important;
            white-space:normal!important;overflow:hidden;display:-webkit-box;
            -webkit-box-orient:vertical;-webkit-line-clamp:3}
        [data-testid="stTabs"] :is([data-testid="stButton"],[data-testid="stDownloadButton"],
            [data-testid="stFormSubmitButton"]) > button [data-testid="stIconMaterial"]{
            font-size:25px!important;line-height:1!important}
        [data-testid="stTabs"] :is([data-testid="stButton"],[data-testid="stDownloadButton"],
            [data-testid="stFormSubmitButton"]) > button:hover:not(:disabled){
            background:linear-gradient(155deg,#e8f7ff,#b7e0ff)!important;
            border-color:#3080b7!important;color:#033150!important}
        [data-testid="stTabs"] :is([data-testid="stButton"],[data-testid="stDownloadButton"],
            [data-testid="stFormSubmitButton"]) > button:active:not(:disabled){
            background:#83c9ef!important;transform:translateY(2px)!important;
            box-shadow:0 1px 2px #092a4533!important}
        [data-testid="stCaptionContainer"] p{color:#38536b!important}
        div[data-testid="stVerticalBlock"]{gap:.45rem}
    </style>''', unsafe_allow_html=True)


def _designer_band(st, title: str, subtitle: str = "") -> None:
    st.markdown('<div class="lesson-designer-band">' + escape(title)
                + ('<small>' + escape(subtitle) + '</small>' if subtitle else '') + '</div>',
                unsafe_allow_html=True)


def _control_label(st, title: str) -> None:
    st.markdown('<div class="lesson-control-label">' + escape(title) + '</div>',
                unsafe_allow_html=True)


def lesson_requirement_summary(session_state, draft: dict) -> tuple[str, str]:
    """Show requirements for the committed lesson, refreshing the read-only widget on edits."""
    lesson_id = draft.get("source_lesson_id", "")
    selected = session_state.get("card_requirements_" + lesson_id, []) if lesson_id else []
    codes = tuple(str(code) for code in selected) if isinstance(selected, list) else ()
    summary = ", ".join(codes) if codes else "Chọn trong Xưởng thẻ"
    identity = sha256(repr((lesson_id, codes)).encode("utf-8")).hexdigest()[:16]
    return summary, identity


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



def validate_text_style(value: object) -> dict:
    if not isinstance(value, dict) or set(value) - set(TEXT_STYLE_DEFAULT):
        raise ValueError("Định dạng hộp văn bản không hợp lệ.")
    style = {**TEXT_STYLE_DEFAULT, **value}
    for name, low, high in (("width", 20, 100), ("min_height", 40, 500), ("font_size", 12, 96), ("depth", 0, 3)):
        if type(style[name]) is not int or not low <= style[name] <= high:
            raise ValueError("Kích thước hộp văn bản ngoài phạm vi.")
    for name in ("x", "y"):
        if type(style[name]) not in (int, float) or not 0 <= style[name] <= 100:
            raise ValueError("Vị trí hộp văn bản ngoài slide.")
    if style["font_family"] not in TEXT_FONTS or style["align"] not in ("left", "center", "right"):
        raise ValueError("Font hoặc căn chữ không hợp lệ.")
    for name in ("color", "background"):
        if not isinstance(style[name], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", style[name]):
            raise ValueError("Màu hộp văn bản không hợp lệ.")
    for name in ("bold", "italic", "underline", "positioned", "auto_size"):
        if type(style[name]) is not bool:
            raise ValueError("Kiểu chữ không hợp lệ.")
    return style


def text_box_css(value: dict) -> tuple[str, str]:
    style = validate_text_style(value)
    depth = style["depth"]
    box = (f"width:{style['width']}%;min-height:{style['min_height']}px;box-sizing:border-box;"
           f"background-color:{style['background']};color:{style['color']};text-align:{style['align']};")
    if style["auto_size"]:
        box += "width:max-content;max-width:none;min-width:1em;min-height:0;height:auto;"
    if style["positioned"]:
        box += f"position:absolute;left:{style['x']}%;top:{style['y']}%;margin:0;z-index:2;"
    if depth:
        box += (f"background-image:linear-gradient(145deg,#ffffff55,#ffffff00 48%,#00000022);"
                f"border:1px solid #ffffff88;box-shadow:inset 2px 2px 3px #ffffff66,"
                f"inset -2px -2px 4px #00000022,0 {depth*4}px {depth*8}px #00000033;")
    text = (f"font-family:'{style['font_family']}',sans-serif;font-size:{style['font_size']}px;"
            f"font-weight:{700 if style['bold'] else 400};font-style:{'italic' if style['italic'] else 'normal'};"
            f"text-decoration:{'underline' if style['underline'] else 'none'};line-height:1.35;white-space:pre;overflow-wrap:normal;word-break:normal;")
    return box, text


def render_text_box_format(st, block: dict, key: str) -> None:
    fmt = validate_text_style({"auto_size": block["kind"] == "Hộp văn bản", **block.get("style", {})})
    fmt["auto_size"] = st.checkbox("Tự co giãn theo nội dung", fmt["auto_size"], key=key+"auto_size")
    left, right = st.columns(2)
    with left:
        fmt["width"] = st.slider("Chiều rộng hộp (%)", 20, 100, fmt["width"], key=key+"width", disabled=fmt["auto_size"])
        fmt["min_height"] = st.slider("Chiều cao tối thiểu (px)", 40, 500, fmt["min_height"], key=key+"height", disabled=fmt["auto_size"])
        fmt["font_size"] = st.slider("Cỡ chữ (px)", 12, 96, fmt["font_size"], key=key+"size")
        fmt["font_family"] = st.selectbox("Font chữ", TEXT_FONTS, index=TEXT_FONTS.index(fmt["font_family"]), key=key+"font")
        fmt["align"] = st.selectbox("Căn chữ", ("left", "center", "right"), index=("left", "center", "right").index(fmt["align"]), format_func={"left":"Trái", "center":"Giữa", "right":"Phải"}.get, key=key+"align")
    with right:
        fmt["color"] = st.color_picker("Màu chữ", fmt["color"], key=key+"color")
        fmt["background"] = st.color_picker("Màu nền", fmt["background"], key=key+"background")
        fmt["bold"] = st.checkbox("Đậm", fmt["bold"], key=key+"bold")
        fmt["italic"] = st.checkbox("Nghiêng", fmt["italic"], key=key+"italic")
        fmt["underline"] = st.checkbox("Gạch chân", fmt["underline"], key=key+"underline")
        fmt["depth"] = st.select_slider("Độ nổi 3D của nền", options=(0, 1, 2, 3), value=fmt["depth"], key=key+"depth")
    fmt["positioned"] = st.checkbox("Đặt tại vị trí trên slide", fmt["positioned"], key=key+"positioned")
    if fmt["positioned"]:
        fmt["x"] = st.slider("Vị trí ngang (%)", 0.0, 100.0, float(fmt["x"]), step=0.1, key=key+"x")
        fmt["y"] = st.slider("Vị trí dọc (%)", 0.0, 100.0, float(fmt["y"]), step=0.1, key=key+"y")
    block["style"] = fmt


GEOMETRY_TYPES = {
    'point': 'Điểm', 'line': 'Đường thẳng', 'segment': 'Đoạn thẳng', 'ray': 'Tia',
    'triangle': 'Tam giác', 'right_triangle': 'Tam giác vuông',
    'isosceles_triangle': 'Tam giác cân', 'equilateral_triangle': 'Tam giác đều',
    'quadrilateral': 'Tứ giác', 'trapezoid': 'Hình thang',
    'isosceles_trapezoid': 'Hình thang cân', 'parallelogram': 'Hình bình hành',
    'rectangle': 'Hình chữ nhật', 'square': 'Hình vuông', 'rhombus': 'Hình thoi',
    'circle': 'Đường tròn', 'cuboid': 'Hình hộp chữ nhật', 'cube': 'Hình lập phương',
    'prism': 'Hình lăng trụ', 'right_prism': 'Lăng trụ đứng',
    'pyramid': 'Hình chóp', 'cylinder': 'Hình trụ', 'cone': 'Hình nón', 'sphere': 'Hình cầu',
}


def validate_geometry(value):
    if not isinstance(value, dict) or set(value) != {'type', 'width', 'height', 'stroke', 'fill', 'line_width'}:
        raise ValueError('Thông số hình học không hợp lệ.')
    if value['type'] not in GEOMETRY_TYPES:
        raise ValueError('Loại hình học không hợp lệ.')
    for key, low, high in (('width', 40, 800), ('height', 40, 600), ('line_width', 1, 12)):
        if type(value[key]) is not int or not low <= value[key] <= high:
            raise ValueError('Kích thước hình học không hợp lệ.')
    for key in ('stroke', 'fill'):
        if not isinstance(value[key], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value[key]):
            raise ValueError('Màu hình học không hợp lệ.')
    return value


def geometry_svg(value):
    g = validate_geometry(value)
    k = g['type']
    polygons = {
        'triangle': '20,155 95,15 190,155',
        'right_triangle': '25,20 25,155 185,155',
        'isosceles_triangle': '100,15 20,155 180,155',
        'equilateral_triangle': '100,16 20,155 180,155',
        'quadrilateral': '40,20 175,45 190,150 20,150',
        'trapezoid': '55,35 150,35 190,145 20,145',
        'isosceles_trapezoid': '55,35 145,35 180,145 20,145',
        'parallelogram': '60,35 185,35 145,145 20,145',
        'rectangle': '20,40 180,40 180,140 20,140',
        'square': '40,25 170,25 170,155 40,155',
        'rhombus': '100,15 185,90 100,165 15,90',
    }
    if k in polygons:
        body = f'<polygon points="{polygons[k]}"/>'
        if k == 'right_triangle':
            body += '<path fill="none" d="M25 135 H45 V155"/>'
    elif k == 'point':
        body = '<circle cx="100" cy="90" r="5"/>'
    elif k in ('line', 'segment', 'ray'):
        body = '<path fill="none" d="M15 90 H185"/>'
        if k != 'line':
            body += '<circle cx="15" cy="90" r="3"/>'
        if k == 'segment':
            body += '<circle cx="185" cy="90" r="3"/>'
        if k in ('line', 'ray'):
            body += '<path fill="none" d="M175 83 L185 90 L175 97"/>'
        if k == 'line':
            body += '<path fill="none" d="M25 83 L15 90 L25 97"/>'
    elif k == 'circle':
        body = '<circle cx="100" cy="90" r="70"/>'
    elif k in ('cuboid', 'cube'):
        right = 140 if k == 'cube' else 160
        body = f'<path d="M20 55 H{right} V155 H20 Z M20 55 L55 20 H{right+35} V120 L{right} 155 M{right} 55 L{right+35} 20"/><path fill="none" stroke-dasharray="5 5" d="M55 20 V120 H{right+35} M55 120 L20 155"/>'
    elif k in ('prism', 'right_prism'):
        body = '<path d="M25 75 L80 20 L130 75 Z M25 75 V155 L80 100 L130 155 V75 M80 20 V100 M25 155 H130"/>'
        body += '<path fill="none" stroke-dasharray="5 5" d="M25 155 L80 100 L130 155"/>'
        if k == 'prism':
            body = '<path d="M55 75 L110 20 L160 75 Z M55 75 L25 155 L80 100 L130 155 L160 75 M110 20 L80 100 M25 155 H130"/>'
    elif k == 'pyramid':
        body = '<path d="M100 15 L20 135 L90 170 L185 130 Z M100 15 L90 170 M20 135 L90 170 L185 130"/><path fill="none" stroke-dasharray="5 5" d="M20 135 L110 105 L185 130 M100 15 L110 105"/>'
    elif k == 'cylinder':
        body = '<path d="M35 40 V140 A65 20 0 0 0 165 140 V40"/><ellipse cx="100" cy="40" rx="65" ry="20"/><path fill="none" stroke-dasharray="5 5" d="M35 140 A65 20 0 0 1 165 140"/>'
    elif k == 'cone':
        body = '<path d="M100 15 L25 145 A75 20 0 0 0 175 145 Z"/><path fill="none" stroke-dasharray="5 5" d="M25 145 A75 20 0 0 1 175 145"/>'
    else:
        body = '<circle cx="100" cy="90" r="70"/><ellipse fill="none" cx="100" cy="90" rx="70" ry="20"/><ellipse fill="none" cx="100" cy="90" rx="25" ry="70"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 180" width="{g["width"]}" height="{g["height"]}" role="img" aria-label="{escape(GEOMETRY_TYPES[k])}" style="display:block;max-width:none" preserveAspectRatio="xMidYMid meet">'
            f'<g stroke="{g["stroke"]}" fill="{g["fill"]}" fill-opacity="0.18" stroke-width="{g["line_width"]}" stroke-linejoin="round">{body}</g></svg>')


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
            if block["kind"] == "Hình học":
                validate_geometry(block.get("geometry"))
            if "style" in block:
                validate_text_style(block["style"])
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


def build_presentation_html(draft: dict, *, classroom_stages: dict[str, bytes] | None = None,
                            selected_slide_id: str | None = None, shared_editor: bool = False, surface_index: int | None = None, insert_armed: bool = False, edit_block_index: int | None = None, dirty: bool = True, cloud_save: bool = False, classroom_runtime_state: dict | None = None) -> str:
    """Escape all teacher text; presentation uses pinned reveal.js assets."""
    validate_draft(draft)
    classroom_stages = classroom_stages or {}
    sections = []
    initial_slide = 0
    for activity, label in ACTIVITIES:
        activity_slides = [slide for slide in draft["slides"] if slide["activity"] == activity]
        for slide in activity_slides:
            if slide["id"] == selected_slide_id:
                initial_slide = len(sections)
            blocks = []
            for block_index, block in enumerate(slide["blocks"]):
                classes = "content fragment" if block["reveal_later"] else "content"
                if block["kind"] in ("Hộp văn bản", "Công thức Toán", "Hình học"):
                    classes += " lesson-text-box"
                    effective_style = {"auto_size": True, **block.get("style", {})}
                    box_css, text_css = text_box_css(effective_style)
                else:
                    box_css, text_css = text_box_css(block["style"]) if "style" in block else ("", "")
                heading = "" if block["kind"] in ("Hộp văn bản", "Công thức Toán", "Hình học") else f'<strong>{escape(block["kind"])}</strong>'
                handle = (f'<button type="button" class="text-box-drag" data-block-index="{block_index}" aria-label="Kéo để di chuyển" title="Kéo để di chuyển">✥</button>' if shared_editor else "")
                if handle and "position:absolute" not in box_css:
                    box_css += "position:relative;"
                attrs = ""
                content = escape(block["text"]).replace(chr(10), "<br>")
                hidden = ""
                if block["kind"] == "Hình học":
                    attrs = f' data-geometry-index="{block_index}" data-geometry="{escape(json.dumps(block["geometry"]), quote=True)}"'
                    content = ""
                    hidden = " hidden"
                    heading += geometry_svg(block["geometry"])
                if block["kind"] == "Công thức Toán":
                    attrs += ' data-formula="true"'
                blocks.append(f'<div class="{classes}" style="{escape(box_css, quote=True)}"{attrs} data-delete-kind="block" data-delete-index="{block_index}" data-text-format="{escape(json.dumps({"auto_size": block["kind"] in ("Hộp văn bản", "Hình học", "Công thức Toán"), **block.get("style", {})}), quote=True)}">{handle}{heading}'
                              f'<p{hidden} style="{escape(text_css, quote=True)}" data-edit-block="{block_index}" data-raw-text="{escape(block["text"], quote=True)}">{content}</p></div>')
            sections.append(f'<section data-slide-id="{escape(slide["id"], quote=True)}"><small>{escape(label)}</small><h2 data-delete-kind="title" data-edit-title data-raw-text="{escape(slide["title"], quote=True)}">{escape(slide["title"])}</h2>'
                            + "".join(blocks) + "</section>")
        for card in draft.get("activity_cards", []):
            if card["activity"] == activity:
                choices = "".join(
                    '<li><b>' + escape(row["label"]) + '.</b> ' + escape(row["text"]) + '</li>'
                    for row in card.get("question_display", []))
                sections.append(f'<section data-delete-kind="activity_cards" data-delete-id="{escape(card["id"], quote=True)}"><small>{escape(label)}</small>'
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
                sections.append('<section class="lesson-evidence-slide" data-delete-kind="evidence_cards" data-delete-id="' + escape(evidence["id"], quote=True) + '"><small>' + escape(label)
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
                sections.append('<section class="ai-presenter-slide" data-delete-kind="ai_presenters" data-delete-id="' + escape(presenter["id"], quote=True) + '"><small>' + escape(label)
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
                sections.append('<section class="classroom-tool-slide" data-delete-kind="classroom_tools" data-delete-id="' + escape(tool["id"], quote=True) + '"><small>' + escape(label)
                                + '</small><h2>' + escape(TOOL_LABELS[tool["kind"]])
                                + '</h2>' + frame + '</section>')
    if not sections:
        sections.append('<section><h2>Chưa có slide</h2><p>Thêm nội dung để xem trước.</p></section>')
    avatar_css = ('.ai-presenter-avatar{background-image:url("' + avatar_data_uri() + '")}'
                  if draft.get("ai_presenters") else '')
    runtime_overlay = build_runtime_overlay_html(classroom_runtime_state, classroom_stages)
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
            '<div class="reveal"><div class="slides">' + "".join(sections) + '</div></div>' + runtime_overlay +
            '<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.2.1/dist/reveal.js"></script>'
            '<script>if(window.Reveal){Reveal.initialize({hash:false,controls:true,progress:true,center:true,'
            + 'initialSlide:' + str(surface_index if surface_index is not None and 0 <= surface_index < len(sections) else initial_slide) + '});}'
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
            + (presenter_speech_script() if draft.get("ai_presenters") else '')
            + (_shared_editor_script(insert_armed=insert_armed, edit_block_index=edit_block_index, draft=draft, dirty=dirty, cloud_save=cloud_save) if shared_editor else '') + '</body></html>')



def _shared_editor_script(*, insert_armed: bool = False, edit_block_index: int | None = None, draft=None, dirty=True, cloud_save=False) -> str:
    # Commit plain text explicitly; no DOM edits are treated as trusted HTML.
    configuration = json.dumps({"armed": bool(insert_armed), "editBlock": edit_block_index, "draft": draft, "geometryTypes": GEOMETRY_TYPES, "dirty": dirty, "cloudSave": cloud_save}).replace("<", "\\u003c")
    return '<script>window.lessonInsertConfig=' + configuration + ';</script>' + r'''<style>
    .lesson-edit-toolbar{position:fixed;top:12px;left:12px;z-index:101;display:flex;flex-wrap:wrap;max-width:calc(100vw - 210px);gap:6px;align-items:center;font:16px Segoe UI;background:#edf5ff;padding:8px;border-radius:8px}
    .lesson-edit-toolbar button{padding:8px;cursor:pointer}
    .lesson-edit-toolbar .format-icon{min-width:36px;height:36px;border:1px solid #a4c8df;border-radius:6px;background:#fff;color:#16425e}
    .lesson-edit-toolbar .format-icon[aria-pressed=true]{background:#176c9a;color:white}
    .lesson-edit-toolbar select,.lesson-edit-toolbar input{font:14px Segoe UI;height:32px;max-width:140px}
    .lesson-edit-toolbar input[type=number]{width:54px}
    .lesson-edit-toolbar input[type=color]{width:30px;padding:0;border:0}
    .lesson-edit-toolbar label{display:flex;align-items:center;gap:3px}
    .lesson-edit-toolbar #lesson-edit-status{font-size:13px;flex-basis:100%}
    .lesson-format-selected{outline:2px solid #2494c7!important}
    [contenteditable=true]{outline:2px dashed #2680bb;white-space:pre-wrap}
    html:fullscreen .lesson-edit-toolbar{display:none}
    .reveal .slides section[data-slide-id]{height:640px!important;min-height:640px!important;box-sizing:border-box;top:0!important;transform:none!important}
    .text-box-drag{position:absolute;right:3px;top:3px;min-width:36px;min-height:32px;z-index:20;border:1px solid #91bbdf;border-radius:5px;background:#fff;color:#175889;cursor:grab;touch-action:none;font:22px Segoe UI;padding:2px 6px}
    html:fullscreen .text-box-drag{display:none}
    .text-box-drag:active{cursor:grabbing}
    .reveal .lesson-text-box p{white-space:pre!important;overflow-wrap:normal!important;word-break:normal!important;min-width:1em}
    .reveal .lesson-text-box{padding-right:44px}
    .lesson-tool-tabs{display:flex;gap:4px;flex-basis:100%;overflow-x:auto}
    .lesson-tool-tabs button{display:flex;flex-direction:column;justify-content:center;align-items:center;width:72px;height:64px;flex-shrink:0;border:1px solid #9ec5df;border-radius:8px;background:linear-gradient(#fff,#e4f4ff);color:#123e59;font-size:11px}
    .lesson-tool-tabs button:hover,.lesson-tool-tabs button:active{background:#91d0ef}
    .lesson-tool-tabs .tool-symbol{font-size:24px;line-height:28px}
    .lesson-edit-toolbar{max-width:calc(100vw - 24px);right:12px}
    .lesson-edit-toolbar>button{min-width:40px;min-height:36px;background:#fff;border:1px solid #9ec5df;border-radius:6px;color:#16425e}
    .lesson-tool-tabs{padding-right:210px;box-sizing:border-box}
.lesson-presentation-fullscreen{z-index:102;top:20px;right:20px;max-width:190px;min-height:44px}
@media(max-width:420px){.lesson-tool-tabs{padding-right:150px}.lesson-presentation-fullscreen{max-width:140px;font-size:13px}}

    .lesson-surface-heading{position:fixed;top:0;left:0;right:0;min-height:76px;box-sizing:border-box;padding:14px 230px 14px 16px;background:#09283e;color:white;font:700 16px Segoe UI;z-index:101;border-radius:10px}
    .lesson-surface-heading small{display:block;font:13px Segoe UI;color:#9dc5df;margin-top:7px}
    .lesson-presentation-fullscreen{z-index:102;top:14px;right:14px;max-width:200px;min-height:46px}
    .lesson-edit-toolbar{top:84px;max-width:calc(100vw - 24px)}
    .lesson-tool-tabs{padding-right:0!important;box-sizing:border-box}
    .lesson-tool-tabs button{width:auto;height:38px;flex-direction:row;gap:5px;padding:4px 9px;font-size:13px}
    .lesson-tool-tabs button[aria-selected=true]{background:#176c9a;color:white}
    .lesson-tab-panel{display:flex;flex-wrap:wrap;gap:6px;align-items:center;flex-basis:100%}
    .lesson-tab-panel[hidden]{display:none}
    .lesson-tab-panel button{min-height:36px;background:white;border:1px solid #9ec5df;border-radius:6px;color:#16425e}
    html:fullscreen .lesson-surface-heading{display:none}
    @media(max-width:420px){.lesson-surface-heading{padding-right:160px;font-size:14px}.lesson-presentation-fullscreen{max-width:140px;font-size:13px}}

    /* lesson-icon-tools-r151 */
    .lesson-tab-panel[hidden]{display:none!important}
    .lesson-tool-tabs{padding-right:0!important}
    .lesson-tool-tabs button{min-width:42px;width:42px;height:40px;font-size:23px}
    .lesson-tab-panel button,.lesson-edit-toolbar>button{min-width:40px;min-height:38px;font-size:21px}
    .lesson-presentation-fullscreen{width:48px!important;max-width:48px!important;height:48px!important;box-sizing:border-box;padding:0!important;display:flex;align-items:center;justify-content:center;font-size:25px!important}
    .lesson-surface-heading{padding-right:80px!important}


    /* lesson-header-slide-nav-r181 */
    header.lesson-surface-heading{padding-right:198px!important}
    .lesson-header-slide-menu{
        position:fixed;top:70px;right:130px;z-index:120;
        width:280px;max-width:calc(100vw - 24px);
        max-height:320px;overflow:auto;padding:8px;
        border:1px solid #9cbad1;border-radius:10px;
        background:white;box-shadow:0 8px 24px #12345340;
        font:15px Segoe UI
    }
    .lesson-header-slide-menu[hidden]{display:none!important}
    .lesson-header-slide-menu button{
        display:block;width:100%;text-align:left;padding:10px;
        border:0;border-radius:6px;background:white;
        color:#123453;cursor:pointer
    }
    .lesson-header-slide-menu button:hover,
    .lesson-header-slide-menu button[aria-current=true]{
        background:#e2f0ff
    }
    html:fullscreen .lesson-header-slide-menu{display:none!important}
    /* lesson-publish-delete-scroll-r18 */
    .lesson-slide-viewport{width:100%;overflow-x:scroll;overflow-y:hidden;scrollbar-color:#789bb8 #e7eef5;scrollbar-width:auto;padding-bottom:8px}
    html:not(:fullscreen) .lesson-slide-viewport .reveal{width:100%!important;min-width:960px!important}
    html:fullscreen .lesson-slide-viewport{overflow:visible;padding:0}
    html:fullscreen .lesson-slide-viewport .reveal{min-width:0!important;width:100vw!important}
    .lesson-delete-object{position:absolute;right:2px;top:2px;z-index:30;width:28px;height:28px;border:1px solid #d8a9a9;border-radius:6px;background:#fff;color:#a32626;cursor:pointer;font:18px Segoe UI}
    [data-delete-kind]{position:relative}
    html:fullscreen .lesson-delete-object{display:none!important}
    .lesson-publish-button{position:fixed;top:14px;right:72px;z-index:102;width:48px;height:48px;box-sizing:border-box;border:1px solid #a9daf9;border-radius:10px;background:#0b3550;color:white;font:25px Segoe UI;cursor:pointer;box-shadow:0 4px 14px #071b34aa}
    html:fullscreen .lesson-publish-button{display:none}
    .lesson-surface-heading{padding-right:140px!important}
    /* lesson-tools-layout-r163 */
    html:not(:fullscreen),html:not(:fullscreen) body{
        height:auto!important;min-height:100%;
        overflow-y:auto!important
    }
    html:not(:fullscreen) .lesson-edit-toolbar{
        position:relative!important;
        top:auto!important;left:auto!important;right:auto!important;
        margin:84px 12px 0!important;max-width:none!important;
        border:1px solid #9cbad1;border-radius:12px;
        background:linear-gradient(180deg,#f7fbff,#e7f1fc);
        box-shadow:0 6px 16px #12345326,inset 0 1px 0 #ffffff;
        padding:10px;box-sizing:border-box
    }
    .lesson-tool-tabs button{
        box-shadow:0 2px 4px #12345320,inset 0 1px 0 white
    }
    .lesson-tool-tabs button[aria-selected=true]{
        box-shadow:inset 0 1px 3px #09283e55;
        border-color:#0d5e8a
    }
    html:not(:fullscreen) .reveal{
        position:relative!important;height:640px!important;
        margin-top:18px!important;border-top:1px solid #cad8e4;
        box-sizing:border-box
    }
    html:fullscreen .reveal{
        margin-top:0!important;border:0;height:100vh!important
    }
</style><header class="lesson-surface-heading">THI?T K? B?I GI?NG<small>So?n ho?t ??ng ? chu?n b? c?ng c? ? tr?nh chi?u tr?n l?p</small></header><div class="lesson-edit-toolbar"><nav class="lesson-tool-tabs" aria-label="Nhóm công cụ bài giảng"></nav><button id="lesson-insert-text">＋ Hộp text</button><button id="lesson-edit-toggle">Sửa slide</button><button id="lesson-edit-apply" hidden>Áp dụng vào bản nháp</button><button class="format-icon" data-format="bold" title="Đậm" aria-label="Đậm"><b>B</b></button><button class="format-icon" data-format="italic" title="Nghiêng" aria-label="Nghiêng"><i>I</i></button><button class="format-icon" data-format="underline" title="Gạch chân" aria-label="Gạch chân"><u>U</u></button>
    <select id="format-font" title="Font chữ" aria-label="Font chữ"><option>Arial</option><option>Times New Roman</option><option>Calibri</option><option>Segoe UI</option><option>Verdana</option></select>
    <label title="Cỡ chữ">A↕ <input id="format-size" aria-label="Cỡ chữ" type="number" min="12" max="96" value="32"></label>
    <label title="Màu chữ">A <input id="format-color" aria-label="Màu chữ" type="color" value="#123453"></label>
    <label title="Màu nền">▨ <input id="format-background" aria-label="Màu nền" type="color" value="#eef4fc"></label>
    <select id="format-depth" aria-label="Nền 3D" title="Độ nổi nền 3D"><option value="0">3D: Tắt</option><option value="1">3D: Nhẹ</option><option value="2">3D: Vừa</option><option value="3">3D: Mạnh</option></select>
    <span id="lesson-edit-status" role="status"></span></div>
    <script>(function(){
    const edit=document.getElementById('lesson-edit-toggle'),apply=document.getElementById('lesson-edit-apply'),status=document.getElementById('lesson-edit-status');
    let editing=false;
    const toolGroups=[['Bản nháp','▣'],['Thông tin','ⓘ'],['SGK · AI','✦'],['Trợ giảng','♙'],['Sân khấu','▶'],['Ghi nhận','▧'],['Chèn','＋'],['Định dạng','Aa'],['Slide','▤']];
    const toolTabs=document.querySelector('.lesson-tool-tabs');

    toolTabs.setAttribute('role','tablist');
    const toolbar=document.querySelector('.lesson-edit-toolbar');
    // Keep the toolbar before the slide canvas.
    const slideCanvas=document.querySelector('.reveal');
    slideCanvas.before(document.querySelector('.lesson-surface-heading'),toolbar);
    let layoutFrame;
    function layoutLessonSurface(){
        cancelAnimationFrame(layoutFrame);
        layoutFrame=requestAnimationFrame(()=>{
            if(window.Reveal&&Reveal.isReady())Reveal.layout();
        });
    }
    const surfaceSizeObserver=new ResizeObserver(layoutLessonSurface);
    surfaceSizeObserver.observe(toolbar);
    window.addEventListener('resize',layoutLessonSurface);
    document.addEventListener('fullscreenchange',layoutLessonSurface);
    layoutLessonSurface();

    const children=Array.from(toolbar.children).filter(
        e=>e!==toolTabs&&e!==status
    );
    const panels=new Map();

    function openTool(label){
        if(editing){
            status.textContent='?p d?ng ho?c h?y n?i dung ?ang s?a tr??c khi m? c?ng c?';
            return;
        }
        parent.postMessage({
            lessonSurface:true,
            action:'open_tool',
            tool_group:label,
            slide_id:Reveal.getCurrentSlide()?.dataset.slideId,
            index:Reveal.getIndices().h,
            updates:[],
            event_id:Date.now().toString()+'-'+Math.random()
        },'*');
    }

    function selectTab(label){
        panels.forEach((panel,name)=>panel.hidden=name!==label);
        toolTabs.querySelectorAll('button').forEach(button=>{
            const active=button.dataset.tab===label;
            button.setAttribute('aria-selected',String(active));
            button.tabIndex=active?0:-1;
        });
    }

    toolGroups.forEach(([label,symbol],index)=>{
        const button=document.createElement('button');
        button.type='button';
        button.dataset.tab=label;
        button.id='lesson-tab-'+index;
        button.setAttribute('role','tab');
        button.textContent=symbol+' '+label;

        const panel=document.createElement('div');
        panel.className='lesson-tab-panel';
        panel.id='lesson-panel-'+index;
        panel.setAttribute('role','tabpanel');
        panel.setAttribute('aria-labelledby',button.id);
        button.setAttribute('aria-controls',panel.id);
        panels.set(label,panel);
        toolbar.insertBefore(panel,status);

        const setup=document.createElement('button');
        setup.type='button';
        setup.textContent=symbol+' '+(
            label==='Ch?n'?'Ch?n n?i dung kh?c':
            label==='??nh d?ng'?'Thi?t l?p h?p text':
            'M? c?ng c? '+label
        );
        setup.title='Thi?t l?p v? s? d?ng c?ng c? '+label;
        setup.onclick=()=>openTool(label);
        panel.append(setup);

        button.onclick=()=>selectTab(label);
        button.onkeydown=event=>{
            if(event.key!=='ArrowRight'&&event.key!=='ArrowLeft')return;
            event.preventDefault();
            const next=(
                index+(event.key==='ArrowRight'?1:-1)+toolGroups.length
            )%toolGroups.length;
            selectTab(toolGroups[next][0]);
            toolTabs.children[next].focus();
        };
        toolTabs.append(button);
    });


    // R152: use existing group names, avoiding encoded label mismatches.
    children.forEach(control=>{
        let index=7;
        if(control.id==='lesson-insert-text')index=6;
        if(control.id==='lesson-edit-toggle'||control.id==='lesson-edit-apply'){
            index=8;
        }
        const panel=panels.get(toolGroups[index][0]);
        if(panel)panel.append(control);
    });
    toolbar.insertBefore(apply,status);
    selectTab(toolGroups[6][0]);

    const heading=document.querySelector('.lesson-surface-heading');
    heading.replaceChildren();
    heading.append(document.createTextNode(
        'THI\u1ebeT K\u1ebe B\u00c0I GI\u1ea2NG'
    ));
    const subtitle=document.createElement('small');
    subtitle.textContent=
        'So\u1ea1n ho\u1ea1t \u0111\u1ed9ng \u00b7 chu\u1ea9n b\u1ecb c\u00f4ng c\u1ee5 \u00b7 tr\u00ecnh chi\u1ebfu tr\u00ean l\u1edbp';
    heading.append(subtitle);

    const icons=[
        '\u25a3','\u24d8','\u2726','\u2659','\u25b6',
        '\u25a7','\uff0b','Aa','\u25a4'
    ];
    function setIcon(button,icon,label){
        if(!button)return;
        button.title=label;
        button.setAttribute('aria-label',label);
        if(button.textContent!==icon)button.textContent=icon;
    }
    function refreshIcons(){
        toolTabs.querySelectorAll('button').forEach((button,i)=>{
            if(i<toolGroups.length)setIcon(button,icons[i],toolGroups[i][0]);
        });
        panels.forEach((panel,label)=>{
            const index=toolGroups.findIndex(group=>group[0]===label);
            const setup=panel.querySelector('button');
            if(index>=0&&setup&&!setup.id&&!setup.hasAttribute('data-format')){
                setIcon(setup,icons[index],label);
            }
        });
        setIcon(document.getElementById('lesson-insert-text'),
            'T+','Ch\u00e8n / h\u1ee7y ch\u00e8n h\u1ed9p text');
        setIcon(edit,'\u270e','S\u1eeda / h\u1ee7y s\u1eeda slide');
        setIcon(apply,'\u2713','\u00c1p d\u1ee5ng');
        setIcon(document.querySelector('.lesson-presentation-fullscreen'),
            document.fullscreenElement?'\u2922':'\u26f6',
            document.fullscreenElement?
            'Tho\u00e1t to\u00e0n m\u00e0n h\u00ecnh':
            'To\u00e0n m\u00e0n h\u00ecnh');
    }
    refreshIcons();
    const iconObserver=new MutationObserver(refreshIcons);
    iconObserver.observe(toolbar,
        {childList:true,subtree:true,characterData:true});
    iconObserver.observe(document.querySelector('.lesson-presentation-fullscreen'),
        {childList:true,subtree:true,characterData:true});
    document.addEventListener('fullscreenchange',refreshIcons);

    let objectPlacement=null, selectedGeometry=null;
    const mathPanel=document.createElement('div'),geometryPanel=document.createElement('div');
    [mathPanel,geometryPanel].forEach(p=>{p.className='lesson-tab-panel';p.hidden=true;toolbar.insertBefore(p,status);});
    function addTab(label,icon,panel){panels.set(label,panel);const b=document.createElement('button');b.type='button';b.dataset.tab=label;b.title=label;b.setAttribute('aria-label',label);b.setAttribute('role','tab');b.textContent=icon;b.onclick=()=>selectTab(label);toolTabs.append(b);}
    addTab('Công thức Toán','∑',mathPanel);addTab('Hình học','△',geometryPanel);
    function button(panel,icon,title,callback){const b=document.createElement('button');b.type='button';b.textContent=icon;b.title=title;b.setAttribute('aria-label',title);b.onclick=callback;panel.append(b);return b;}
    function postAction(action,extra){const slide=Reveal.getCurrentSlide();const updates=editing?currentUpdates():[];if(editing){fields().forEach(e=>e.dataset.rawText=e.innerText);setEditing(false);}parent.postMessage(Object.assign({lessonSurface:true,action,slide_id:slide?.dataset.slideId,index:Reveal.getIndices().h,updates,event_id:Date.now().toString()+'-'+Math.random()},extra||{}),'*');}
    function armObject(value){if(!Reveal.getCurrentSlide()?.dataset.slideId){status.textContent='Thêm hoặc chọn slide nội dung trước.';return;}objectPlacement=value;status.textContent='Bấm vị trí trên slide để chèn; Esc để hủy.';document.querySelector('.slides').style.cursor='crosshair';}
    const formula=document.createElement('textarea');formula.rows=2;formula.placeholder='Nhập LaTeX, ví dụ: \\frac{a}{b}';formula.title='Công thức LaTeX';formula.setAttribute('aria-label','Công thức LaTeX');formula.style.cssText='width:320px;max-width:100%;font:16px Segoe UI';mathPanel.append(formula);
    [['a/b','\\frac{a}{b}'],['√','\\sqrt{x}'],['x²','x^{2}'],['x₁','x_{1}'],['≤','\\leq'],['π','\\pi'],['∑','\\sum_{i=1}^{n} i']].forEach(([icon,value])=>button(mathPanel,icon,'Mẫu '+value,()=>{formula.value+=value;formula.focus();}));
    button(mathPanel,'∑+','Chèn công thức tại vị trí chọn',()=>{if(!formula.value.trim()){status.textContent='Nhập công thức trước.';return;}armObject({action:'insert_formula',formula:formula.value});});
    button(mathPanel,'✎','Sửa công thức đang chọn',()=>{if(!formatTarget||!formatTarget.matches('[data-formula]')){status.textContent='Bấm vào công thức cần sửa trước.';return;}if(!editing)edit.click();const field=formatTarget.querySelector('[data-edit-block]');field.focus();status.textContent='Sửa LaTeX trong hộp công thức rồi bấm ✓.';});

    // lesson-formula-preview-r162
    const mathPreview=document.createElement('div');
    mathPreview.style.cssText='flex-basis:100%;min-height:58px;padding:12px;background:white;border:1px solid #bdd5ed;border-radius:8px;font-size:24px;overflow:auto';
    mathPanel.append(mathPreview);
    let previewTimer, previewQueue=Promise.resolve();
    function previewFormula(){
        clearTimeout(previewTimer);
        previewTimer=setTimeout(()=>{
            previewQueue=previewQueue.catch(()=>{}).then(async()=>{
                if(window.MathJax&&MathJax.startup)await MathJax.startup.promise;
                if(window.MathJax&&MathJax.typesetClear)MathJax.typesetClear([mathPreview]);
                mathPreview.textContent=formula.value.trim()?'\\('+formula.value.trim()+'\\)':'...';
                if(window.MathJax&&MathJax.typesetPromise)await MathJax.typesetPromise([mathPreview]);
            });
        },150);
    }
    formula.addEventListener('input',previewFormula);
    mathPanel.addEventListener('click',previewFormula);
    formula.placeholder='a^{2}+b^{2}=c^{2}';
    button(mathPanel,'=','Xem cong thuc',previewFormula);
    previewFormula();
    const shapeSelect=document.createElement('select');shapeSelect.title='Loại hình';shapeSelect.setAttribute('aria-label','Loại hình');Object.entries(window.lessonInsertConfig.geometryTypes).forEach(([value,label])=>{const o=document.createElement('option');o.value=value;o.textContent=label;shapeSelect.append(o);});geometryPanel.append(shapeSelect);
    function input(panel,type,value,title,min,max){const label=document.createElement('label');label.title=title;label.textContent=title+' ';const e=document.createElement('input');e.type=type;e.value=value;e.setAttribute('aria-label',title);if(min!==undefined){e.min=min;e.max=max;}label.append(e);panel.append(label);return e;}
    const shapeW=input(geometryPanel,'number',240,'Rộng',40,800),shapeH=input(geometryPanel,'number',210,'Cao',40,600),shapeStroke=input(geometryPanel,'color','#123453','Nét'),shapeFill=input(geometryPanel,'color','#DDEEFF','Nền'),shapeLine=input(geometryPanel,'number',3,'Độ dày',1,12);
    function geometryValue(){return {type:shapeSelect.value,width:Number(shapeW.value),height:Number(shapeH.value),stroke:shapeStroke.value,fill:shapeFill.value,line_width:Number(shapeLine.value)};}
    button(geometryPanel,'△+','Chèn hình tại vị trí chọn',()=>armObject({action:'insert_geometry',geometry:geometryValue()}));
    button(geometryPanel,'✓','Áp dụng kích thước và màu cho hình đã chọn',()=>{if(!selectedGeometry||selectedGeometry.closest('section')!==Reveal.getCurrentSlide()){status.textContent='Bấm vào hình trên slide hiện tại trước.';return;}postAction('update_geometry',{block_index:Number(selectedGeometry.dataset.geometryIndex),geometry:geometryValue()});});
    document.addEventListener('pointerdown',event=>{const box=event.target.closest('[data-geometry-index]');if(!box)return;selectedGeometry=box;const g=JSON.parse(box.dataset.geometry);shapeSelect.value=g.type;shapeW.value=g.width;shapeH.value=g.height;shapeStroke.value=g.stroke;shapeFill.value=g.fill;shapeLine.value=g.line_width;});
    document.querySelector('.slides').addEventListener('click',event=>{if(!objectPlacement)return;event.preventDefault();event.stopImmediatePropagation();const section=Reveal.getCurrentSlide(),rect=section.getBoundingClientRect();if(!section.dataset.slideId)return;const scale=rect.width/section.offsetWidth;const item=objectPlacement;objectPlacement=null;document.querySelector('.slides').style.cursor='';postAction(item.action,Object.assign(item,{x:Math.max(0,Math.min(100,(event.clientX-rect.left)/rect.width*100)),y:Math.max(0,Math.min(100,(event.clientY-rect.top)/(640*scale)*100))}));},true);
    document.addEventListener('keydown',event=>{if(event.key==='Escape'){objectPlacement=null;document.querySelector('.slides').style.cursor='';status.textContent='';}});

    // lesson-publish-controls-r18
    const viewport=document.createElement('div');viewport.className='lesson-slide-viewport';
    slideCanvas.before(viewport);viewport.append(slideCanvas);
    const publishButton=document.createElement('button');publishButton.type='button';
    publishButton.className='lesson-publish-button';publishButton.textContent='\u21e7';
    publishButton.title='Xu\u1ea5t b\u1ea3n b\u00e0i gi\u1ea3ng';publishButton.setAttribute('aria-label',publishButton.title);
    document.body.append(publishButton);publishButton.onclick=()=>postAction('publish_lesson');
    document.querySelectorAll('[data-delete-kind]').forEach(object=>{
        const b=document.createElement('button');b.type='button';b.className='lesson-delete-object';b.textContent='\u00d7';
        b.title='X\u00f3a th\u00e0nh ph\u1ea7n';b.setAttribute('aria-label',b.title);
        b.addEventListener('pointerdown',e=>{e.preventDefault();e.stopImmediatePropagation();},true);
        b.addEventListener('click',e=>{
            e.preventDefault();e.stopImmediatePropagation();
            if(object.closest('section')!==Reveal.getCurrentSlide()||document.fullscreenElement)return;
            if(!window.confirm('X\u00f3a th\u00e0nh ph\u1ea7n n\u00e0y?'))return;
            postAction('delete_component',{component_kind:object.dataset.deleteKind,component_id:object.dataset.deleteId,block_index:Number(object.dataset.deleteIndex)});
        });
        if(object.dataset.deleteKind==='title'){object.after(b);}else{object.append(b);}
    });
    const slidePanel=panels.get(toolGroups[8][0]);
    button(slidePanel,'＋','Thêm slide sau slide hiện tại',()=>postAction('add_slide'));
    button(slidePanel,'◀','Slide trước',()=>{if(editing){status.textContent='Áp dụng hoặc hủy sửa trước khi chuyển slide.';return;}Reveal.prev();});
    button(slidePanel,'▶','Slide sau',()=>{if(editing){status.textContent='Áp dụng hoặc hủy sửa trước khi chuyển slide.';return;}Reveal.next();});
    const slidePicker=document.createElement('select');slidePicker.title='Chọn slide';slidePicker.setAttribute('aria-label','Chọn slide');slidePanel.append(slidePicker);

    // lesson-header-slide-nav-r181
    const slideNav=document.createElement('button');
    slideNav.type='button';
    slideNav.className='lesson-publish-button lesson-slide-nav';
    slideNav.style.right='130px';
    slideNav.textContent='\u21c4';
    slideNav.title='Chuy\u1ec3n slide';
    slideNav.setAttribute('aria-label',slideNav.title);
    slideNav.setAttribute('aria-expanded','false');

    const slideMenu=document.createElement('div');
    slideMenu.className='lesson-header-slide-menu';
    slideMenu.hidden=true;
    document.body.append(slideNav,slideMenu);

    function closeSlideMenu(){
        slideMenu.hidden=true;
        slideNav.setAttribute('aria-expanded','false');
    }
    slideNav.onclick=()=>{
        if(!slideMenu.hidden){closeSlideMenu();return;}
        syncPicker();
        slideMenu.replaceChildren();
        Array.from(slidePicker.options).forEach(option=>{
            const b=document.createElement('button');
            b.type='button';
            b.textContent=option.textContent;
            b.setAttribute('aria-current',
                String(option.value===slidePicker.value));
            b.onclick=()=>{
                slidePicker.value=option.value;
                slidePicker.onchange();
                closeSlideMenu();
            };
            slideMenu.append(b);
        });
        slideMenu.hidden=false;
        slideNav.setAttribute('aria-expanded','true');
    };
    document.addEventListener('pointerdown',e=>{
        if(!slideMenu.contains(e.target)&&!slideNav.contains(e.target))
            closeSlideMenu();
    });
    document.addEventListener('keydown',e=>{
        if(e.key==='Escape')closeSlideMenu();
    });
    document.addEventListener('fullscreenchange',closeSlideMenu);
    function syncPicker(){slidePicker.replaceChildren();document.querySelectorAll('.slides>section').forEach((section,index)=>{const o=document.createElement('option');o.value=index;o.textContent=(index+1)+'. '+(section.querySelector('h2')?.textContent||'Slide');slidePicker.append(o);});slidePicker.value=Reveal.getIndices().h;}
    slidePicker.onchange=()=>{if(editing){status.textContent='Áp dụng hoặc hủy sửa trước khi chuyển slide.';syncPicker();return;}Reveal.slide(Number(slidePicker.value));};
    Reveal.on('ready',syncPicker);Reveal.on('slidechanged',syncPicker);if(Reveal.isReady())syncPicker();
    button(slidePanel,'⌫','Xóa slide hiện tại',()=>{if(window.confirm('Xóa slide hiện tại và nội dung của slide này?'))postAction('delete_slide');});
    const saveButton=button(toolbar,'💾','Lưu bản nháp',()=>{
        const snapshot=JSON.parse(JSON.stringify(window.lessonInsertConfig.draft));const updates=editing?currentUpdates():[];
        updates.forEach(row=>{const slide=snapshot.slides.find(s=>s.id===row.id);if(slide){slide.title=row.title;slide.blocks.forEach((b,i)=>{b.text=row.blocks[i];if(row.styles)b.style=row.styles[i];});}});
        if(!window.lessonInsertConfig.cloudSave){const blob=new Blob([JSON.stringify(snapshot,null,2)],{type:'application/json'});const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download='bai_giang_nhap.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
        postAction('save_draft');
    });toolbar.insertBefore(saveButton,status);
    status.textContent=window.lessonInsertConfig.dirty?'Có thay đổi chưa lưu — bấm 💾 để lưu.':'Bấm 💾 để lưu bản nháp.';


    function fields(){return Reveal.getCurrentSlide().querySelectorAll('[data-edit-title],[data-edit-block]');}
    function setEditing(value){editing=value;fields().forEach(e=>e.contentEditable=value?'true':'false');apply.hidden=!value;edit.textContent=value?'Hủy sửa':'Sửa slide';if(window.Reveal){Reveal.configure({keyboard:!value,touch:!value});Reveal.sync();}}
    function send(updates){const indices=window.Reveal?Reveal.getIndices():{h:0};const current=window.Reveal?Reveal.getCurrentSlide():null;parent.postMessage({lessonSurface:true,slide_id:current?current.dataset.slideId:null,index:indices.h,updates:updates||[],event_id:Date.now().toString()+'-'+Math.random()},'*');}
    function currentUpdates(){return Array.from(document.querySelectorAll('section[data-slide-id]')).filter(section=>section===Reveal.getCurrentSlide()).map(section=>({id:section.dataset.slideId,title:section.querySelector('[data-edit-title]').innerText,blocks:Array.from(section.querySelectorAll('[data-edit-block]')).map(e=>e.innerText),styles:Array.from(section.querySelectorAll('[data-text-format]')).map(e=>JSON.parse(e.dataset.textFormat))}));}
    let dragging=null;
    document.addEventListener('pointerdown',function(event){const handle=event.target.closest('.text-box-drag');if(!handle||document.fullscreenElement||placing)return;event.preventDefault();event.stopPropagation();const box=handle.parentElement,section=box.closest('section'),rect=section.getBoundingClientRect(),boxRect=box.getBoundingClientRect();dragging={handle:handle,box:box,section:section,index:Number(handle.dataset.blockIndex),pointer:event.pointerId,dx:event.clientX-boxRect.left,dy:event.clientY-boxRect.top,original:box.style.cssText};Reveal.configure({touch:false});try{handle.setPointerCapture(event.pointerId);}catch(error){}status.textContent='Đang di chuyển hộp text';},true);
    document.addEventListener('pointermove',function(event){if(!dragging||event.pointerId!==dragging.pointer)return;event.preventDefault();const d=dragging,rect=d.section.getBoundingClientRect(),br=d.box.getBoundingClientRect(),canvasHeight=640*(rect.width/d.section.offsetWidth);d.x=Math.round(Math.max(0,Math.min(Math.max(0,rect.width-br.width),event.clientX-rect.left-d.dx))/rect.width*100);d.y=Math.round(Math.max(0,Math.min(Math.max(0,canvasHeight-br.height),event.clientY-rect.top-d.dy))/canvasHeight*100);Object.assign(d.box.style,{position:'absolute',left:d.x+'%',top:d.y+'%',margin:'0'});},true);
    document.addEventListener('pointerup',function(event){if(!dragging||event.pointerId!==dragging.pointer)return;const d=dragging;dragging=null;try{d.handle.releasePointerCapture(event.pointerId);}catch(error){}Reveal.configure({touch:!editing});if(d.x===undefined)return;d.box.dataset.textFormat=JSON.stringify(Object.assign(JSON.parse(d.box.dataset.textFormat),{positioned:true,x:d.x,y:d.y}));parent.postMessage({lessonSurface:true,action:'move_text',slide_id:d.section.dataset.slideId,block_index:d.index,x:d.x,y:d.y,index:Reveal.getIndices().h,updates:editing?currentUpdates():[],event_id:Date.now().toString()+'-'+Math.random()},'*');},true);
    document.addEventListener('pointercancel',function(){if(dragging){dragging.box.style.cssText=dragging.original;dragging=null;Reveal.configure({touch:!editing});}},true);
    const originalFormats=new Map();const originals=new Map();let placing=window.lessonInsertConfig.armed;
    const insert=document.getElementById('lesson-insert-text');
    function placingStatus(){insert.textContent=placing?'Hủy chèn':'＋ Hộp text';status.textContent=placing?'Kích vào vị trí trên slide để đặt hộp text':'';document.querySelector('.slides').style.cursor=placing?'crosshair':'';}
    placingStatus();
    insert.onclick=function(){if(editing){status.textContent='Áp dụng hoặc hủy sửa trước khi chèn';return;}const current=Reveal.getCurrentSlide();if(!current.dataset.slideId){status.textContent='Chọn slide nội dung để chèn hộp text';return;}placing=!placing;insert.textContent=placing?'Hủy chèn':'＋ Hộp text';placingStatus();};
    document.querySelector('.slides').addEventListener('click',function(event){if(!placing)return;const current=Reveal.getCurrentSlide();if(!current.dataset.slideId)return;event.preventDefault();event.stopImmediatePropagation();const rect=current.getBoundingClientRect(),scale=rect.width/current.offsetWidth,canvasHeight=640*scale;const x=Math.round(Math.max(0,Math.min(100,(event.clientX-rect.left)/rect.width*100))*100)/100;const y=Math.round(Math.max(0,Math.min(100,(event.clientY-rect.top)/canvasHeight*100))*100)/100;placing=false;placingStatus();parent.postMessage({lessonSurface:true,action:'insert_text',slide_id:current.dataset.slideId,index:Reveal.getIndices().h,x:x,y:y,updates:[],event_id:Date.now().toString()+'-'+Math.random()},'*');},true);
    edit.onclick=function(){if(editing){originals.forEach((text,e)=>e.textContent=text);originalFormats.forEach((saved,box)=>{box.dataset.textFormat=saved.data;box.style.cssText=saved.box;box.querySelector('[data-edit-block]').style.cssText=saved.text;});setEditing(false);status.textContent='Đã hủy sửa';return;}const current=Reveal.getCurrentSlide();if(!current.dataset.slideId){status.textContent='Thẻ này được sửa trong tab công cụ tương ứng';return;}originalFormats.clear();document.querySelectorAll('[data-text-format]').forEach(box=>originalFormats.set(box,{data:box.dataset.textFormat,box:box.style.cssText,text:box.querySelector('[data-edit-block]').style.cssText}));originals.clear();fields().forEach(e=>{originals.set(e,e.dataset.rawText);e.textContent=e.dataset.rawText;});setEditing(true);status.textContent='Sửa rồi bấm Áp dụng';};
    let formatTarget=null;
    const formatControls=Array.from(document.querySelectorAll('[data-format],#format-font,#format-size,#format-color,#format-background,#format-depth'));
    function chooseFormat(field){document.querySelectorAll('.lesson-format-selected').forEach(e=>e.classList.remove('lesson-format-selected'));formatTarget=field.parentElement;formatTarget.classList.add('lesson-format-selected');const fmt=Object.assign({font_family:'Arial',font_size:32,color:'#123453',background:'#eef4fc',depth:0,bold:false,italic:false,underline:false},JSON.parse(formatTarget.dataset.textFormat));formatControls.forEach(e=>e.disabled=false);document.getElementById('format-font').value=fmt.font_family;document.getElementById('format-size').value=fmt.font_size;document.getElementById('format-color').value=fmt.color;document.getElementById('format-background').value=fmt.background;document.getElementById('format-depth').value=fmt.depth;document.querySelectorAll('[data-format]').forEach(e=>e.setAttribute('aria-pressed',String(Boolean(fmt[e.dataset.format]))));}
    formatControls.forEach(e=>e.disabled=true);
    Reveal.on('slidechanged',()=>{
        formatTarget=null;selectedGeometry=null;objectPlacement=null;placing=false;
        document.querySelector('.slides').style.cursor='';
        document.querySelectorAll('.lesson-format-selected').forEach(e=>e.classList.remove('lesson-format-selected'));
        formatControls.forEach(e=>e.disabled=true);
    });
    document.addEventListener('click',event=>{const field=event.target.closest('[data-edit-block]');if(field&&!placing&&!document.fullscreenElement){chooseFormat(field);status.textContent='Đã chọn hộp text — chọn định dạng rồi Áp dụng';}});
    document.addEventListener('focusin',event=>{if(event.target.matches('[data-edit-block]'))chooseFormat(event.target);});
    function updateFormat(name,value){if(!formatTarget)return;if(!editing)edit.click();const fmt=Object.assign({font_family:'Arial',font_size:32,color:'#123453',background:'#eef4fc',depth:0},JSON.parse(formatTarget.dataset.textFormat));fmt[name]=value;formatTarget.dataset.textFormat=JSON.stringify(fmt);const field=formatTarget.querySelector('[data-edit-block]');Object.assign(field.style,{fontFamily:fmt.font_family,fontSize:fmt.font_size+'px',fontWeight:fmt.bold?'700':'400',fontStyle:fmt.italic?'italic':'normal',textDecoration:fmt.underline?'underline':'none',whiteSpace:'pre'});formatTarget.style.color=fmt.color;formatTarget.style.backgroundColor=fmt.background;formatTarget.style.backgroundImage=fmt.depth?'linear-gradient(145deg,#ffffff55,#ffffff00 48%,#00000022)':'none';formatTarget.style.boxShadow=fmt.depth?'inset 2px 2px 3px #ffffff66,inset -2px -2px 4px #00000022,0 '+(fmt.depth*4)+'px '+(fmt.depth*8)+'px #00000033':'none';document.querySelectorAll('[data-format]').forEach(e=>e.setAttribute('aria-pressed',String(Boolean(fmt[e.dataset.format]))));status.textContent='Định dạng đã hiển thị — bấm Áp dụng để lưu';}
    document.querySelectorAll('[data-format]').forEach(button=>button.onclick=()=>updateFormat(button.dataset.format,!(formatTarget&&JSON.parse(formatTarget.dataset.textFormat)[button.dataset.format])));
    document.getElementById('format-font').onchange=event=>updateFormat('font_family',event.target.value);
    document.getElementById('format-size').onchange=event=>{const size=Number(event.target.value);if(Number.isInteger(size)&&size>=12&&size<=96)updateFormat('font_size',size);};
    document.getElementById('format-color').oninput=event=>updateFormat('color',event.target.value);
    document.getElementById('format-background').oninput=event=>updateFormat('background',event.target.value);
    document.getElementById('format-depth').onchange=event=>updateFormat('depth',Number(event.target.value));
    function focusInserted(){const index=window.lessonInsertConfig.editBlock;if(index===null)return;const current=Reveal.getCurrentSlide();const field=current&&current.querySelector('[data-edit-block="'+index+'"]');if(!field)return;edit.click();field.focus();const range=document.createRange();range.selectNodeContents(field);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);status.textContent='Nhập chữ tại hộp mới, rồi Áp dụng vào bản nháp';}
    if(window.Reveal){Reveal.on('ready',focusInserted);if(Reveal.isReady()){focusInserted();}}

    // lesson-direct-edit-r161
    const directSlides=document.querySelector('.slides');
    directSlides.addEventListener('pointerdown',event=>{
        if(event.button!==0||document.fullscreenElement||placing||objectPlacement||dragging)return;
        if(event.target.closest('.text-box-drag,.lesson-delete-object'))return;
        const current=Reveal.getCurrentSlide();
        const section=event.target.closest('section[data-slide-id]');
        if(!section||section!==current)return;
        const geometry=event.target.closest('[data-geometry-index]');
        if(geometry){
            selectedGeometry=geometry;
            const g=JSON.parse(geometry.dataset.geometry);
            shapeSelect.value=g.type;shapeW.value=g.width;shapeH.value=g.height;
            shapeStroke.value=g.stroke;shapeFill.value=g.fill;shapeLine.value=g.line_width;
            selectTab('H??nh h???c');
            document.querySelectorAll('.lesson-format-selected').forEach(e=>e.classList.remove('lesson-format-selected'));
            geometry.classList.add('lesson-format-selected');
            status.textContent='Ch???nh k??ch th?????c, m??u r???i b???m ???.';
            return;
        }
        const field=event.target.closest('[data-edit-title],[data-edit-block]');
        if(field){
            const wasEditing=editing;
            if(!editing)edit.click();
            if(field.matches('[data-edit-block]'))chooseFormat(field);
            if(field.parentElement.matches('[data-formula]')){
                selectTab('C??ng th???c To??n');
            }else if(field.matches('[data-edit-block]')){
                selectTab(toolGroups[7][0]);
            }
            if(!wasEditing){
                event.preventDefault();field.focus();
                const range=document.caretRangeFromPoint?document.caretRangeFromPoint(event.clientX,event.clientY):null;
                const selection=window.getSelection();
                if(range&&field.contains(range.startContainer)){
                    selection.removeAllRanges();selection.addRange(range);
                }else{
                    const fallback=document.createRange();fallback.selectNodeContents(field);fallback.collapse(false);
                    selection.removeAllRanges();selection.addRange(fallback);
                }
            }
            status.textContent='Nh???p n???i dung; b???m ???? khi mu???n l??u.';
        }
    },true);
    directSlides.addEventListener('click',event=>{
        if(document.fullscreenElement||placing||objectPlacement||dragging)return;
        const section=event.target.closest('section[data-slide-id]');
        if(!section||section!==Reveal.getCurrentSlide())return;
        if(event.target.closest('[data-edit-title],[data-edit-block],[data-geometry-index],.content,button,a,small'))return;
        event.preventDefault();event.stopImmediatePropagation();
        const rect=section.getBoundingClientRect(),scale=rect.width/section.offsetWidth;
        const x=Math.max(0,Math.min(100,(event.clientX-rect.left)/rect.width*100));
        const y=Math.max(0,Math.min(100,(event.clientY-rect.top)/(640*scale)*100));
        postAction('insert_text',{x,y,direct:true});
    },true);

    document.addEventListener('dblclick',function(event){const field=event.target.closest('[data-edit-block]');if(!field||document.fullscreenElement||placing||dragging)return;event.preventDefault();event.stopPropagation();if(!editing){edit.click();}field.focus();const selection=window.getSelection(),range=document.createRange();range.selectNodeContents(field);range.collapse(false);selection.removeAllRanges();selection.addRange(range);status.textContent='Sửa chữ rồi bấm Áp dụng vào bản nháp';});
    apply.onclick=function(){const updates=currentUpdates();fields().forEach(e=>e.dataset.rawText=e.innerText);setEditing(false);send(updates);status.textContent='Đang cập nhật bản nháp…';};
    document.querySelector('.lesson-presentation-fullscreen').addEventListener('click',function(event){if(editing){event.stopImmediatePropagation();status.textContent='Áp dụng hoặc hủy sửa trước khi trình chiếu';}},true);
    document.addEventListener('fullscreenchange',function(){if(!document.fullscreenElement){send();}});
    if(window.Reveal){Reveal.on('slidechanged',function(){if(!document.fullscreenElement&&!editing){send();}});}
    })();</script>'''


def apply_surface_event(draft: dict, event: object) -> dict:
    """Validate all edits atomically before touching the teacher draft."""
    if isinstance(event, dict) and event.get("action") in ("insert_text", "insert_formula", "insert_geometry", "delete_component") and event.get("updates"):
        draft = apply_surface_event(draft, {"action": "edit", "updates": event["updates"]})
        event = {**event, "updates": []}
    if not isinstance(event, dict) or not isinstance(event.get("updates", []), list):
        raise ValueError("Dữ liệu chỉnh sửa slide không hợp lệ.")
    if event.get("action") == "open_tool" and event.get("tool_group") not in DESIGN_TOOL_TABS:
        raise ValueError("Nhóm công cụ không hợp lệ.")
    candidate = deepcopy(draft)
    by_id = {slide["id"]: slide for slide in candidate["slides"]}
    action = event.get('action')
    if action == 'delete_component':
        kind = event.get('component_kind')
        if kind in ('block', 'title'):
            current = by_id.get(event.get('slide_id'))
            if current is None:
                raise ValueError('Không tìm thấy slide hiện tại.')
            if kind == 'title':
                current['title'] = ''
            else:
                index = event.get('block_index')
                if type(index) is not int or not 0 <= index < len(current['blocks']):
                    raise ValueError('Thành phần đã thay đổi. Mở lại slide.')
                current['blocks'].pop(index)
        elif kind in ('activity_cards', 'evidence_cards', 'ai_presenters', 'classroom_tools'):
            rows = candidate.get(kind, [])
            item = next((row for row in rows if row['id'] == event.get('component_id')), None)
            if item is None:
                raise ValueError('Không tìm thấy thành phần cần xóa.')
            rows.remove(item)
        else:
            raise ValueError('Loại thành phần không hợp lệ.')
    elif action == 'add_slide':
        if len(candidate['slides']) >= 80:
            raise ValueError('Bài giảng tối đa 80 slide.')
        current = by_id.get(event.get('slide_id'))
        activity = current['activity'] if current else ACTIVITIES[0][0]
        new_slide = {'id': str(uuid4()), 'activity': activity, 'title': 'Slide mới', 'blocks': []}
        position = candidate['slides'].index(current) + 1 if current else len(candidate['slides'])
        candidate['slides'].insert(position, new_slide)
    elif action == 'delete_slide':
        current = by_id.get(event.get('slide_id'))
        if current is None:
            raise ValueError('Chọn slide nội dung để xóa.')
        candidate['slides'].remove(current)
    elif action in ('insert_formula', 'insert_geometry', 'update_geometry'):
        current = by_id.get(event.get('slide_id'))
        if current is None:
            raise ValueError('Chọn slide nội dung trước.')
        if action == 'update_geometry':
            index = event.get('block_index')
            if type(index) is not int or not 0 <= index < len(current['blocks']) or current['blocks'][index]['kind'] != 'Hình học':
                raise ValueError('Chọn hình học để sửa.')
            current['blocks'][index]['geometry'] = validate_geometry(event.get('geometry'))
        else:
            if len(current['blocks']) >= 30:
                raise ValueError('Mỗi slide tối đa 30 khối.')
            style = validate_text_style({**TEXT_STYLE_DEFAULT, 'auto_size': True, 'positioned': True,
                                        'x': event.get('x'), 'y': event.get('y'), 'background': '#FFFFFF'})
            if action == 'insert_formula':
                formula = event.get('formula')
                if not isinstance(formula, str) or not formula.strip() or len(formula) > 4000:
                    raise ValueError('Công thức không hợp lệ.')
                block = {'kind': 'Công thức Toán', 'text': r'\(' + formula + r'\)', 'style': style, 'reveal_later': False}
            else:
                block = {'kind': 'Hình học', 'text': '', 'geometry': validate_geometry(event.get('geometry')),
                         'style': style, 'reveal_later': False}
            current['blocks'].append(block)
    if event.get("action") == "insert_text":
        slide = by_id.get(event.get("slide_id"))
        if slide is None or len(slide["blocks"]) >= 30:
            raise ValueError("Chọn slide nội dung có ít hơn 30 khối để chèn hộp text.")
        fmt = validate_text_style({**TEXT_STYLE_DEFAULT, "positioned": True, "auto_size": True, "width": 35,
                                   "x": event.get("x"), "y": event.get("y")})
        slide["blocks"].append({"kind": "Hộp văn bản", "text": "Nhập nội dung…", "reveal_later": False, "style": fmt})
    if event.get("action") == "move_text":
        slide = by_id.get(event.get("slide_id"))
        index = event.get("block_index")
        if slide is None or type(index) is not int or not 0 <= index < len(slide["blocks"]):
            raise ValueError("Không tìm thấy hộp text cần di chuyển.")
        block = slide["blocks"][index]
        block["style"] = validate_text_style({**block.get("style", {}), "positioned": True,
                                              "x": event.get("x"), "y": event.get("y")})
    for row in event.get("updates", []):
        if not isinstance(row, dict) or row.get("id") not in by_id:
            raise ValueError("Không tìm thấy slide cần sửa.")
        slide = by_id[row["id"]]
        texts = row.get("blocks")
        if not isinstance(texts, list) or len(texts) != len(slide["blocks"]):
            raise ValueError("Cấu trúc slide đã thay đổi. Hãy mở lại slide.")
        styles = row.get("styles")
        if styles is not None:
            if not isinstance(styles, list) or len(styles) != len(slide["blocks"]):
                raise ValueError("Định dạng không khớp với các hộp text.")
            for block, style in zip(slide["blocks"], styles):
                block["style"] = validate_text_style(style)
        slide["title"] = row.get("title")
        for block, text in zip(slide["blocks"], texts):
            block["text"] = text
    validate_draft(candidate)
    return candidate


def render_shared_surface(st, draft, staged, revision, *, cloud_save=False):
    """A bidirectional component, with a stable frame during fullscreen use."""
    import streamlit.components.v1 as components
    root = Path(tempfile.gettempdir()) / "mathteacher_lesson_surface_r16"
    root.mkdir(exist_ok=True)
    wrapper = r'''<!doctype html><html><body style="margin:0"><iframe id="surface" allow="fullscreen" allowfullscreen style="width:100%;height:780px;border:0"></iframe><script>
    const frame=document.getElementById('surface');let previous='';
    function send(type,extra){parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},extra||{}),'*');}
    window.addEventListener('message',event=>{if(event.source===parent&&event.data.type==='streamlit:render'){const html=event.data.args.html;if(html!==previous){previous=html;frame.srcdoc=html;}send('streamlit:setFrameHeight',{height:780});}else if(event.source===frame.contentWindow&&event.data.lessonSurface){send('streamlit:setComponentValue',{value:event.data,dataType:'json'});}});
    send('streamlit:componentReady',{apiVersion:1});send('streamlit:setFrameHeight',{height:780});
    </script></body></html>'''
    (root / "index.html").write_text(wrapper, encoding="utf-8")
    component = components.declare_component("mathteacher_shared_lesson_surface_r16", path=str(root))
    event = component(html=build_presentation_html(draft, classroom_stages=staged,
                      selected_slide_id=st.session_state.get("lesson_slide_selected"), shared_editor=True, surface_index=st.session_state.get("lesson_surface_index"),
                      insert_armed=st.session_state.get("lesson_insert_armed", False),
                      edit_block_index=st.session_state.get("lesson_insert_edit_index"),
                      dirty=_draft_digest(draft) != st.session_state.get("lesson_slide_saved_digest"), cloud_save=cloud_save,
                      classroom_runtime_state=st.session_state.get("ta_classroom_runtime_state_v13k") or st.session_state.get("ta_classroom_runtime_state_v13j", {})),
                      key="lesson_shared_surface_" + revision, default=None)
    if isinstance(event, dict) and event.get("event_id") != st.session_state.get("lesson_surface_event_id"):
        st.session_state["lesson_surface_pending"] = event
        st.session_state["lesson_surface_event_id"] = event.get("event_id")
        st.rerun()



def create_catalog_lesson(draft, *, subject, grade, book, lesson, requirements):
    """Commit catalog information to the local draft without persisting it."""
    if not book.get("textbook_id") or not lesson.get("textbook_unit_id"):
        raise ValueError("Chọn SGK và bài học trước.")
    previous = draft.get("verified_source") or {}
    if draft.get("activity_cards") and (
        previous.get("textbook_id") != str(book["textbook_id"]) or
        previous.get("lesson_id") != str(lesson["textbook_unit_id"]) or
        subject != draft["subject"] or grade != draft["grade"]
    ):
        raise ValueError("Bài đang có thẻ của nguồn SGK khác. Tạo bản nháp riêng trước khi đổi bài.")
    candidate = deepcopy(draft)
    candidate.update(subject=subject, grade=grade, lesson_title=str(lesson["title"]),
                     source_lesson_id=str(lesson["textbook_unit_id"]))
    candidate["catalog_selection"] = {
        "textbook_id": str(book["textbook_id"]), "textbook_title": str(book["title"]),
        "lesson_id": str(lesson["textbook_unit_id"]),
        "requirements": [{"requirement_code": str(row["requirement_code"]),
                          "requirement_text": str(row["requirement_text"])} for row in requirements],
    }
    if not candidate["slides"]:
        candidate = apply_surface_event(candidate, {"action": "add_slide"})
    validate_draft(candidate)
    return candidate


def render_lesson_information(st, draft, *, client, user_id, revision):
    # lesson-information-catalog-r17
    if client is None or not user_id:
        st.info("Đăng nhập để chọn Bài và YCCĐ từ dữ liệu hệ thống.")
        return
    from portal_v2.ui.lesson_activity_card_authoring import load_lesson_catalog, load_reviewed_requirements, _rows
    subject_col, grade_col = st.columns(2)
    subject = subject_col.selectbox("Môn", ("Toán", "Tiếng Anh"),
        index=("Toán", "Tiếng Anh").index(draft["subject"]), key="info_subject_" + revision)
    grade = grade_col.selectbox("Lớp", (6, 7, 8, 9),
        index=(6, 7, 8, 9).index(draft["grade"]), key="info_grade_" + revision)
    scope = f"{revision}_{subject}_{grade}"
    saved = draft.get("catalog_selection") or {}
    try:
        books = load_lesson_catalog(client, grade=grade, subject=subject)
        if not books:
            st.info("Chưa có SGK ACTIVE theo Môn và Lớp đã chọn.")
            return
        book_ids = [str(row["textbook_id"]) for row in books]
        book_id = st.selectbox("SGK", book_ids,
            index=book_ids.index(saved["textbook_id"]) if saved.get("textbook_id") in book_ids else 0,
            format_func=lambda value: next(row["title"] for row in books if str(row["textbook_id"]) == value),
            key="info_book_" + scope)
        book = next(row for row in books if str(row["textbook_id"]) == book_id)
        lessons = _rows(client.table("textbook_units").select("textbook_unit_id,title,unit_type")
            .eq("textbook_id", book_id).eq("status", "ACTIVE").eq("unit_type", "LESSON")
            .order("display_order").limit(501))
        if len(lessons) >= 501:
            raise ValueError("Danh mục bài học vượt giới hạn hiển thị.")
        if not lessons:
            st.info("SGK này chưa có bài học ACTIVE.")
            return
        lesson_ids = [str(row["textbook_unit_id"]) for row in lessons]
        selected_id = draft.get("source_lesson_id")
        lesson_id = st.selectbox("Bài", lesson_ids,
            index=lesson_ids.index(selected_id) if selected_id in lesson_ids else 0,
            format_func=lambda value: next(row["title"] for row in lessons if str(row["textbook_unit_id"]) == value),
            key="info_lesson_" + scope + "_" + book_id)
        lesson = next(row for row in lessons if str(row["textbook_unit_id"]) == lesson_id)
        requirements = load_reviewed_requirements(client, lesson_id)
        codes = [str(row["requirement_code"]) for row in requirements]
        saved_codes = [row["requirement_code"] for row in saved.get("requirements", [])] if saved.get("lesson_id") == lesson_id else []
        previous_codes = st.session_state.get("card_requirements_" + lesson_id, saved_codes)
        chosen = st.multiselect("YCCĐ", codes, default=[code for code in previous_codes if code in codes],
            format_func=lambda code: code + " · " + next(row["requirement_text"] for row in requirements if str(row["requirement_code"]) == code),
            key="info_requirements_" + scope + "_" + lesson_id)
        if not requirements:
            st.warning("Bài này chưa có YCCĐ ACTIVE đã liên kết. Có thể tạo bài giảng và bổ sung sau.")
    except Exception as exc:
        st.error(f"Chưa đọc được dữ liệu Bài / YCCĐ: {exc}")
        return
    st.caption("Tạo bài giảng xác nhận thông tin vào bản nháp. Bấm nút Lưu khi muốn lưu bài.")
    if st.button("Tạo bài giảng", icon=":material/add_circle:", key="info_create_" + revision):
        try:
            candidate = create_catalog_lesson(draft, subject=subject, grade=grade, book=book, lesson=lesson,
                requirements=[row for row in requirements if str(row["requirement_code"]) in chosen])
        except ValueError as exc:
            st.error(str(exc))
            return
        st.session_state["lesson_slide_draft"] = candidate
        st.session_state[f"card_book_{subject}_{grade}"] = book
        st.session_state["card_lesson_" + book_id] = lesson
        st.session_state["card_requirements_" + lesson_id] = chosen
        st.session_state["slide_source_lesson_" + revision] = lesson_id
        st.session_state["slide_lesson_title_" + revision] = candidate["lesson_title"]
        st.session_state["card_proposals"] = []
        st.session_state.pop("card_proposal_identity", None)
        st.session_state.setdefault("lesson_slide_selected", candidate["slides"][0]["id"])
        st.rerun(scope="app")


def render_design_tool_dialog(st, draft, *, group, client=None, user_id=None):
    save_requested = False
    save_status = None
    activity = st.selectbox("Hoạt động", [key for key, _ in ACTIVITIES],
                            format_func=dict(ACTIVITIES).get, key="lesson_tool_activity")
    revision = st.session_state["lesson_slide_revision"]
    if group == 'Bản nháp':
        col_select, col_open, col_save, col_new, col_json = st.columns(5, gap="small")
        if client is not None and user_id:
            try:
                saved = list_teacher_drafts(client, user_id)
            except Exception as exc:
                saved = []
                st.warning(f"Chưa đọc được bản nháp đã lưu: {exc}")
            with col_select:
                selected = st.selectbox("Bản nháp", saved,
                    format_func=lambda row: (row["title"] or "Bài chưa đặt tên") + " · " + str(row["updated_at"]),
                    key="slide_saved_draft_selection", disabled=not saved,
                    placeholder="Chưa có bản nháp" if not saved else None)
            with col_open:
                _control_label(st, "Mở")
                if tool_button(st, "Mở", key="slide_open_saved", disabled=not saved,
                             help="Mở bản nháp đã chọn",
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
                _control_label(st, "Lưu")
                if tool_button(st, "Lưu", key="slide_save_cloud", help="Lưu bản nháp lên tài khoản",
                             use_container_width=True):
                    save_requested = True
                save_status = st.empty()
            with col_new:
                _control_label(st, "Bài mới")
                if tool_button(st, "Bài mới", key="slide_new_cloud", help="Tạo bài giảng mới",
                             use_container_width=True):
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
                st.selectbox("Bản nháp", [], disabled=True, placeholder="Đăng nhập để chọn")
            for column, label in ((col_open, "Mở"), (col_save, "Lưu"),
                                  (col_new, "Bài mới")):
                with column:
                    _control_label(st, label)
                    tool_button(st, label, disabled=True, use_container_width=True)
        with col_json:
            _control_label(st, "JSON")
            with st.popover("JSON", use_container_width=True):
                uploaded = st.file_uploader("Mở bản nháp JSON", type=["json"], key="slide_import")
                import_clicked = tool_button(st, "Nạp", key="slide_import_button", disabled=uploaded is None,
                                           help="Mở bản nháp JSON đã tải lên", use_container_width=True)
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
    if group == 'Thông tin':
        render_lesson_information(st, draft, client=client, user_id=user_id,
                                  revision=st.session_state["lesson_slide_revision"])
    if group == 'SGK · AI':
        if client is not None and user_id:
            from portal_v2.ui.lesson_activity_card_authoring import render_card_authoring
            render_card_authoring(st, draft=draft, client=client, user_id=user_id,
                                  revision=revision)
        else:
            st.info("Đăng nhập để chọn SGK, bài học và tạo thẻ cùng AI.")
        with st.expander("Mã bài SGK tham khảo", expanded=False):
            draft["source_lesson_id"] = st.text_input("Mã bài SGK tham khảo (chưa xác thực với lịch báo giảng)",
                                                       value=draft["source_lesson_id"], max_chars=250,
                                                       key="slide_source_lesson_" + revision)
    if group == 'Trợ giảng':
        render_presenter_authoring(st, draft, activity)
    if group == 'Sân khấu':
        if client is not None and user_id and draft["subject"] == "Toán":
            render_classroom_tools(st, draft, client, user_id, activity)
            if draft.get("classroom_tools") and tool_button(st, "Chuẩn bị sân khấu tích hợp",
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
        else:
            st.info("Chọn Toán và đăng nhập để chuẩn bị sân khấu lớp học.")
    if group == 'Ghi nhận':
        render_evidence_authoring(st, draft, activity, owner_id=user_id,
                                  lesson_key=revision, mode="design")
        render_evidence_authoring(st, draft, activity, owner_id=user_id,
                                  lesson_key=revision, mode="presentation")
    if group == 'Chèn':
        st.caption("Hộp text")
        if st.button("▣", key="lesson_insert_text_icon", help="Chèn hộp text: bấm nút rồi kích vào vị trí trên vùng bài giảng"):
            available = [row for row in draft["slides"] if row["activity"] == activity]
            chosen = next((row for row in available if row["id"] == st.session_state.get("lesson_slide_selected")), None)
            if chosen is None:
                chosen = available[0] if available else {"id": str(uuid4()), "activity": activity, "title": "Slide mới", "blocks": []}
                if not available:
                    if len(draft["slides"]) >= 80:
                        st.warning("Bài giảng tối đa 80 slide.")
                        return
                    draft["slides"].append(chosen)
            st.session_state["lesson_slide_selected"] = chosen["id"]
            st.session_state.pop("lesson_surface_index", None)
            st.session_state.pop("lesson_insert_edit_index", None)
            st.session_state["lesson_insert_armed"] = True
        if st.session_state.get("lesson_insert_armed"):
            st.info("Kích vào vị trí trong vùng Bài giảng bên dưới để chèn hộp text.")
    if group == 'Slide':
        slides = [slide for slide in draft["slides"] if slide["activity"] == activity]
        if tool_button(st, "Thêm slide vào hoạt động này"):
            slide = {"id": str(uuid4()), "activity": activity, "title": "Slide mới", "blocks": []}
            draft["slides"].append(slide)
            st.session_state["lesson_slide_selected"] = slide["id"]
            st.rerun()
        if slides:
            slide = next((row for row in slides if row["id"] == st.session_state.get("lesson_slide_selected")), slides[0])
            slide_id = slide["id"]
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
                    render_text_box_format(st, block, f"text_format_{revision}_{slide_id}_{index}_")
                    if tool_button(st, "Xóa khối", key=f"slide_remove_block_{slide_id}_{index}"):
                        slide["blocks"].pop(index)
                        for widget_key in list(st.session_state):
                            if widget_key.startswith((f"text_format_{revision}_{slide_id}_", f"slide_kind_{revision}_{slide_id}_", f"slide_text_{revision}_{slide_id}_", f"slide_reveal_{revision}_{slide_id}_")):
                                del st.session_state[widget_key]
                        st.rerun()
            if st.button("＋ Hộp văn bản", key="lesson_add_text_box"):
                if len(slide["blocks"]) >= 30:
                    st.warning("Mỗi slide tối đa 30 khối nội dung.")
                else:
                    slide["blocks"].append({"kind": "Hộp văn bản", "text": "Nhập nội dung…", "reveal_later": False, "style": {**TEXT_STYLE_DEFAULT, "auto_size": True}})
                    st.rerun()
            if tool_button(st, "Thêm khối nội dung"):
                slide["blocks"].append({"kind": "Nội dung", "text": "", "reveal_later": False})
                st.rerun()
            if tool_button(st, "Xóa slide đang chọn"):
                draft["slides"].remove(slide)
                st.session_state.pop("lesson_slide_selected", None)
                st.rerun()
        validate_draft(draft)
        tool_download_button(st, "Tải bản nháp JSON", json.dumps(draft, ensure_ascii=False, indent=2),
                           file_name="bai_giang_nhap.json", mime="application/json")
    if group == 'Định dạng':
        selected_slide = next((row for row in draft["slides"] if row["id"] == st.session_state.get("lesson_slide_selected")), None)
        if selected_slide and selected_slide["blocks"]:
            block_index = st.selectbox("Hộp text cần định dạng", list(range(len(selected_slide["blocks"]))),
                format_func=lambda i: f"{i+1} · {selected_slide['blocks'][i]['text'][:50] or 'Hộp trống'}",
                key="lesson_format_block_" + revision + selected_slide["id"])
            render_text_box_format(st, selected_slide["blocks"][block_index],
                                  f"text_format_{revision}_{selected_slide['id']}_{block_index}_")
        else:
            st.info("Chọn hoặc chèn hộp text để định dạng. Các nút định dạng trực tiếp nằm trên vùng slide.")
    if save_requested:
        try:
            draft_id = st.session_state.get("lesson_slide_saved_id") or str(uuid4())
            save_teacher_draft(client, user_id, draft_id, draft)
            st.session_state["lesson_slide_saved_id"] = draft_id
            st.session_state["lesson_slide_saved_digest"] = _draft_digest(draft)
            save_status.success("Đã lưu bản nháp. Bấm Lưu để lưu các thay đổi tiếp theo.")
        except Exception as exc:
            save_status.error(f"Chưa lưu được bản nháp: {exc}")


def render_lesson_slide_designer(st, *, client=None, user_id: str | None = None) -> None:
    _designer_style(st)
    with st.container(border=True):
        if "lesson_slide_draft" not in st.session_state:
            st.session_state["lesson_slide_draft"] = new_draft()
        if "lesson_slide_revision" not in st.session_state:
            st.session_state["lesson_slide_revision"] = str(uuid4())
        draft = st.session_state["lesson_slide_draft"]
        # lesson-current-slide-r164
        if not draft["slides"]:
            draft = apply_surface_event(draft, {"action": "add_slide"})
            st.session_state["lesson_slide_draft"] = draft
            st.session_state["lesson_slide_selected"] = draft["slides"][0]["id"]
            st.session_state.pop("lesson_surface_index", None)
        if st.session_state.get("lesson_surface_revision") != st.session_state["lesson_slide_revision"]:
            st.session_state.pop("lesson_surface_index", None)
            st.session_state.pop("lesson_surface_pending", None)
            st.session_state.pop("lesson_insert_armed", None)
            st.session_state.pop("lesson_insert_edit_index", None)
            st.session_state["lesson_surface_revision"] = st.session_state["lesson_slide_revision"]
        pending = st.session_state.pop("lesson_surface_pending", None)
        if pending is not None:
            try:
                draft = apply_surface_event(draft, pending)
                action = pending.get("action")
                if action == "save_draft":
                    if client is not None and user_id:
                        draft_id = st.session_state.get("lesson_slide_saved_id") or str(uuid4())
                        try:
                            save_teacher_draft(client, user_id, draft_id, draft)
                        except Exception as exc:
                            st.error(f"Chưa lưu được bản nháp: {exc}")
                        else:
                            st.session_state["lesson_slide_saved_id"] = draft_id
                            st.session_state["lesson_slide_saved_digest"] = _draft_digest(draft)
                            st.success("Đã lưu bản nháp vào tài khoản.")
                    else:
                        st.session_state["lesson_slide_saved_digest"] = _draft_digest(draft)
                        st.info("Đã yêu cầu tải bản nháp JSON. Giữ tệp này để mở lại bài giảng.")
                if action == "add_slide":
                    previous_ids = {row["id"] for row in st.session_state["lesson_slide_draft"]["slides"]}
                    added = next(row for row in draft["slides"] if row["id"] not in previous_ids)
                    pending["slide_id"] = added["id"]
                    pending.pop("index", None)
                    st.session_state.pop("lesson_surface_index", None)
                elif action == "delete_slide":
                    pending["slide_id"] = draft["slides"][0]["id"] if draft["slides"] else None
                    pending.pop("index", None)
                    st.session_state.pop("lesson_surface_index", None)
                    st.session_state.pop("lesson_slide_selected", None)
                st.session_state["lesson_slide_draft"] = draft
                selected = next((row for row in draft["slides"] if row["id"] == pending.get("slide_id")), None)
                if type(pending.get("index")) is int:
                    st.session_state["lesson_surface_index"] = pending["index"]
                st.session_state["lesson_insert_armed"] = False
                st.session_state.pop("lesson_insert_edit_index", None)
                if pending.get("action") == "insert_text" and selected:
                    st.session_state["lesson_insert_edit_index"] = len(selected["blocks"]) - 1
                if selected:
                    st.session_state["lesson_slide_selected"] = selected["id"]
                    st.session_state["lesson_tool_activity"] = selected["activity"]
                # Clear stale widget values before those widgets are instantiated.
                if pending.get("updates") or pending.get("action") == "move_text":
                    for widget_key in list(st.session_state):
                        if widget_key.startswith(("slide_title_", "slide_text_", "text_format_")):
                            del st.session_state[widget_key]
            except ValueError as exc:
                st.error(str(exc))
        revision = st.session_state["lesson_slide_revision"]
        st.session_state["lesson_slide_ids"] = tuple(str(row["id"]) for row in draft.get("slides", []))
        activity = st.session_state.get("lesson_tool_activity", "MO_DAU")
        if pending and pending.get("action") == "open_tool":
            group = pending.get("tool_group")
            if group in DESIGN_TOOL_TABS:
                @st.dialog(group, width="large")
                def tool_dialog():
                    render_design_tool_dialog(st, draft, group=group, client=client, user_id=user_id)
                    if group != "Thông tin" and st.button("Áp dụng và về slide", icon=":material/check:"):
                        st.rerun(scope="app")
                tool_dialog()

        known_ids = {tool["id"] for tool in draft.get("classroom_tools", [])}
        staged = {key: value for key, value in st.session_state.get("lesson_integrated_stages", {}).items()
                  if key in known_ids}
        if pending and pending.get("action") == "publish_lesson":
            @st.dialog("Xuất bản bài giảng", width="large")
            def publish_dialog():
                st.caption("Tải bài giảng HTML để mở bằng trình duyệt. Cần Internet để tải thư viện trình chiếu và công thức Toán.")
                html = build_presentation_html(draft, classroom_stages=staged, shared_editor=False, classroom_runtime_state=st.session_state.get("ta_classroom_runtime_state_v13k") or {})
                st.download_button("Xuất bản · Tải HTML", html, file_name="bai_giang.html", mime="text/html",
                                   icon=":material/publish:")
            publish_dialog()
        render_shared_surface(st, draft, staged, revision, cloud_save=client is not None and bool(user_id))
        _designer_band(st, "MATH TEACHER AI · THIẾT KẾ BÀI GIẢNG")
