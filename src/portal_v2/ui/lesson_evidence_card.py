"""Teacher recorded evidence attached to multiple lesson activity sources."""

from datetime import datetime, timezone
from uuid import uuid4

from portal_v2.ui.lesson_classroom_tools import TOOL_LABELS

ACTIVITIES = {"MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"}
MANUAL = "TEACHER_OBSERVATION"


def available_sources(draft, activity):
    sources = {MANUAL: "Quan sát trực tiếp của giáo viên"}
    for card in draft.get("activity_cards", []):
        if card["activity"] == activity:
            sources[card["id"]] = ("Kiểm tra nhanh" if card["kind"] == "QUICK_CHECK" else "Giao nhiệm vụ") + " · " + card["title"]
    for tool in draft.get("classroom_tools", []):
        if tool["activity"] == activity:
            sources[tool["id"]] = TOOL_LABELS[tool["kind"]] + " · " + tool["title"]
    return sources


def validate_evidence_card(card, draft=None):
    if not isinstance(card, dict) or set(card) != {"id", "activity", "title", "source_ids", "entries"}:
        raise ValueError("Thẻ ghi nhận hoạt động không hợp lệ.")
    if card["activity"] not in ACTIVITIES or not isinstance(card["id"], str) or not 0 < len(card["id"]) <= 80:
        raise ValueError("Mã hoặc hoạt động của thẻ ghi nhận không hợp lệ.")
    if not isinstance(card["title"], str) or not 0 < len(card["title"].strip()) <= 180:
        raise ValueError("Thẻ ghi nhận cần tiêu đề hợp lệ.")
    sources = card["source_ids"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 12 or any(
        not isinstance(source, str) or not source or len(source) > 80 for source in sources
    ) or len(set(sources)) != len(sources):
        raise ValueError("Thẻ ghi nhận cần ít nhất một nguồn hợp lệ.")
    if draft is not None and not set(sources) <= set(available_sources(draft, card["activity"])):
        raise ValueError("Thẻ ghi nhận tham chiếu công cụ không còn thuộc hoạt động này.")
    entries = card["entries"]
    if not isinstance(entries, list) or len(entries) > 200:
        raise ValueError("Thẻ ghi nhận vượt quá 200 lần ghi.")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"source_id", "recorded_at", "participated", "completed", "needs_help", "note"}:
            raise ValueError("Bản ghi minh chứng không hợp lệ.")
        if entry["source_id"] not in sources:
            raise ValueError("Bản ghi minh chứng không thuộc nguồn đã chọn.")
        if not isinstance(entry["recorded_at"], str) or len(entry["recorded_at"]) > 40:
            raise ValueError("Thời điểm ghi nhận không hợp lệ.")
        try:
            if datetime.fromisoformat(entry["recorded_at"]).tzinfo is None:
                raise ValueError("Thiếu múi giờ.")
        except ValueError as exc:
            raise ValueError("Thời điểm ghi nhận không hợp lệ.") from exc
        for metric in ("participated", "completed", "needs_help"):
            if type(entry[metric]) is not int or not 0 <= entry[metric] <= 999:
                raise ValueError("Số lượng học sinh không hợp lệ.")
        if entry["completed"] > entry["participated"] or entry["needs_help"] > entry["participated"]:
            raise ValueError("Số học sinh hoàn thành/cần hỗ trợ vượt số tham gia.")
        if not isinstance(entry["note"], str) or len(entry["note"]) > 1000:
            raise ValueError("Ghi chú minh chứng không hợp lệ.")
    return card


def add_evidence_card(draft, *, activity, title, source_ids):
    cards = draft.setdefault("evidence_cards", [])
    if len(cards) >= 40:
        raise ValueError("Bài giảng chỉ nhận tối đa 40 thẻ ghi nhận.")
    card = {"id": str(uuid4()), "activity": activity, "title": title.strip(),
            "source_ids": list(source_ids), "entries": []}
    validate_evidence_card(card, draft)
    cards.append(card)
    return card


def record_evidence(card, *, source_id, participated, completed, needs_help, note):
    entry = {"source_id": source_id,
             "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "participated": participated, "completed": completed,
             "needs_help": needs_help, "note": note.strip()}
    candidate = dict(card, entries=[*card["entries"], entry])
    validate_evidence_card(candidate)
    card["entries"].append(entry)
    return entry


def render_evidence_authoring(st, draft, activity):
    with st.expander("Thẻ thu thập thông tin hoạt động học sinh", expanded=False):
        sources = available_sources(draft, activity)
        st.caption("Kết nối nhiều công cụ trong bài. Dữ liệu học sinh do giáo viên ghi nhận; sân khấu chưa đồng bộ lượt chơi tự động.")
        title = st.text_input("Tên thẻ ghi nhận", value="Minh chứng hoạt động học tập", max_chars=180,
                              key="lesson_evidence_new_title")
        selected = st.multiselect("Kết nối nguồn", list(sources), default=[MANUAL],
                                  format_func=sources.get, key="lesson_evidence_new_sources")
        if st.button("Thêm thẻ ghi nhận vào hoạt động", key="lesson_evidence_add"):
            try:
                add_evidence_card(draft, activity=activity, title=title, source_ids=selected)
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
    for card in list(draft.get("evidence_cards", [])):
        if card["activity"] != activity:
            continue
        with st.expander(card["title"] + f" · {len(card['entries'])} lần ghi", expanded=False):
            sources = available_sources(draft, activity)
            st.write("Nguồn kết nối: " + ", ".join(sources.get(s, "Nguồn đã gỡ") for s in card["source_ids"]))
            active_sources = [source for source in card["source_ids"] if source in sources]
            source_id = st.selectbox("Ghi nhận từ nguồn", active_sources,
                                     format_func=sources.get, disabled=not active_sources,
                                     key="lesson_evidence_source_" + card["id"])
            a, b, c = st.columns(3)
            participated = a.number_input("Tham gia", min_value=0, max_value=999, step=1,
                                          key="lesson_evidence_part_" + card["id"])
            completed = b.number_input("Hoàn thành", min_value=0, max_value=999, step=1,
                                       key="lesson_evidence_done_" + card["id"])
            needs_help = c.number_input("Cần hỗ trợ", min_value=0, max_value=999, step=1,
                                        key="lesson_evidence_help_" + card["id"])
            note = st.text_area("Quan sát / câu trả lời tiêu biểu (không nhập tên học sinh)",
                                max_chars=1000, key="lesson_evidence_note_" + card["id"])
            if st.button("Lưu lần ghi nhận", disabled=not active_sources,
                         key="lesson_evidence_record_" + card["id"]):
                try:
                    record_evidence(card, source_id=source_id, participated=int(participated),
                                    completed=int(completed), needs_help=int(needs_help), note=note)
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
            for entry in reversed(card["entries"][-10:]):
                st.caption(f"{entry['recorded_at']} · {sources.get(entry['source_id'], 'Nguồn đã gỡ')} · "
                           f"tham gia {entry['participated']}, hoàn thành {entry['completed']}, "
                           f"cần hỗ trợ {entry['needs_help']}")
                if entry["note"]:
                    st.write(entry["note"])
            if st.button("Bỏ thẻ ghi nhận", key="lesson_evidence_remove_" + card["id"]):
                draft["evidence_cards"].remove(card)
                st.rerun()
