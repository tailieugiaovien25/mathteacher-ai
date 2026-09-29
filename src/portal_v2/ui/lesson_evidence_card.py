"""Teacher recorded evidence attached to multiple lesson activity sources."""

from datetime import datetime, timezone
from uuid import uuid4
from base64 import b64decode, b64encode
from binascii import Error as Base64Error
import os

from portal_v2.ui.lesson_classroom_tools import TOOL_LABELS

ACTIVITIES = {"MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"}
MANUAL = "TEACHER_OBSERVATION"
DEVICE_TYPES = ("Máy tính", "Điện thoại", "iPad", "Máy ảnh", "Máy quay")
PHOTO_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 450_000
MAX_DRAFT_PHOTO_BASE64 = 1_400_000


def image_mime(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Ảnh phải là JPEG, PNG hoặc WebP hợp lệ.")


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
    required = {"id", "activity", "title", "source_ids", "entries"}
    if not isinstance(card, dict) or not required <= set(card) or set(card) - required - {"media"}:
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
    media = card.get("media", [])
    if not isinstance(media, list) or len(media) > 3:
        raise ValueError("Một thẻ chỉ lưu tối đa 3 ảnh minh chứng.")
    for photo in media:
        if not isinstance(photo, dict) or set(photo) != {"id", "source_id", "device", "captured_at", "mime", "data_b64"}:
            raise ValueError("Ảnh minh chứng không hợp lệ.")
        if not isinstance(photo["id"], str) or not 0 < len(photo["id"]) <= 80 or photo["source_id"] not in sources or photo["device"] not in DEVICE_TYPES:
            raise ValueError("Nguồn ảnh minh chứng không hợp lệ.")
        if not isinstance(photo["captured_at"], str) or len(photo["captured_at"]) > 40:
            raise ValueError("Ngày chụp ảnh không hợp lệ.")
        try:
            if datetime.fromisoformat(photo["captured_at"]).tzinfo is None:
                raise ValueError("Thiếu múi giờ.")
        except ValueError as exc:
            raise ValueError("Ngày chụp ảnh không hợp lệ.") from exc
        if not isinstance(photo["mime"], str) or photo["mime"] not in PHOTO_MIMES or not isinstance(photo["data_b64"], str) or len(photo["data_b64"]) > 600_000:
            raise ValueError("Định dạng hoặc kích thước ảnh không hợp lệ.")
        try:
            raw = b64decode(photo["data_b64"], validate=True)
            if len(raw) > MAX_PHOTO_BYTES or image_mime(raw) != photo["mime"]:
                raise ValueError("Nội dung ảnh không khớp định dạng.")
        except (ValueError, Base64Error) as exc:
            raise ValueError("Ảnh minh chứng không hợp lệ.") from exc
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


def attach_photo(draft, card, *, source_id, device, data):
    if source_id not in card["source_ids"] or device not in DEVICE_TYPES or not isinstance(data, bytes):
        raise ValueError("Nguồn thiết bị không hợp lệ.")
    if not data or len(data) > MAX_PHOTO_BYTES:
        raise ValueError("Ảnh minh chứng phải nhỏ hơn 450 KB. Hãy chọn ảnh dung lượng thấp hơn.")
    mime = image_mime(data)
    encoded = b64encode(data).decode("ascii")
    if any(p["data_b64"] == encoded for c in draft.get("evidence_cards", [])
           for p in c.get("media", [])):
        raise ValueError("Ảnh này đã được lưu trong bài giảng.")
    used = sum(len(p["data_b64"]) for c in draft.get("evidence_cards", []) for p in c.get("media", []))
    if used + len(encoded) > MAX_DRAFT_PHOTO_BASE64:
        raise ValueError("Bài giảng đã đạt giới hạn ảnh. Hãy dùng ảnh dung lượng thấp hơn hoặc bỏ ảnh cũ.")
    photo = {"id": str(uuid4()), "source_id": source_id, "device": device,
             "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "mime": mime, "data_b64": encoded}
    validate_evidence_card(dict(card, media=[*card.get("media", []), photo]))
    card.setdefault("media", []).append(photo)
    return photo


def render_evidence_authoring(st, draft, activity, *, owner_id=None, lesson_key=None,
                              mode="design"):
    if mode not in ("design", "presentation"):
        raise ValueError("Chế độ thẻ ghi nhận không hợp lệ.")
    suffix = "_" + mode
    if mode == "design":
        with st.container():
            sources = available_sources(draft, activity)
            st.caption("Chọn nguồn trước khi dạy. Dữ liệu học sinh do giáo viên ghi nhận; sân khấu chưa đồng bộ lượt chơi tự động.")
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
                                     key="lesson_evidence_source_" + card["id"] + suffix)
            a, b, c = st.columns(3)
            participated = a.number_input("Tham gia", min_value=0, max_value=999, step=1,
                                          key="lesson_evidence_part_" + card["id"] + suffix)
            completed = b.number_input("Hoàn thành", min_value=0, max_value=999, step=1,
                                       key="lesson_evidence_done_" + card["id"] + suffix)
            needs_help = c.number_input("Cần hỗ trợ", min_value=0, max_value=999, step=1,
                                        key="lesson_evidence_help_" + card["id"] + suffix)
            note = st.text_area("Quan sát / câu trả lời tiêu biểu (không nhập tên học sinh)",
                                max_chars=1000, key="lesson_evidence_note_" + card["id"] + suffix)
            if st.button("Lưu lần ghi nhận", disabled=not active_sources,
                         key="lesson_evidence_record_" + card["id"] + suffix):
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
            with st.expander("Thiết bị · ảnh và video hoạt động học sinh", expanded=False):
                device = st.selectbox("Thiết bị tạo nội dung", DEVICE_TYPES,
                                      key="lesson_evidence_device_" + card["id"] + suffix)
                st.caption("Máy tính, điện thoại và iPad có thể chụp ảnh hoặc chọn tệp; máy ảnh, máy quay dùng tệp đã chép sang thiết bị đang mở ứng dụng.")
                captured = st.camera_input("Chụp ảnh hoạt động", key="lesson_evidence_camera_" + card["id"] + suffix)
                image_file = st.file_uploader("Chọn ảnh từ thiết bị", type=["jpg", "jpeg", "png", "webp"],
                                              key="lesson_evidence_image_" + card["id"] + suffix)
                chosen_photo = captured or image_file
                if chosen_photo is not None:
                    photo_bytes = chosen_photo.getvalue()
                    already_saved = any(p["data_b64"] == b64encode(photo_bytes).decode("ascii")
                                        for c in draft.get("evidence_cards", []) for p in c.get("media", []))
                    st.image(chosen_photo, caption="Ảnh đã lưu" if already_saved else "Ảnh vừa chọn · chưa lưu vào bản nháp")
                    if st.button("Lưu ảnh vào thẻ", disabled=not active_sources or already_saved,
                                 key="lesson_evidence_save_photo_" + card["id"] + suffix):
                        try:
                            attach_photo(draft, card, source_id=source_id, device=device,
                                         data=photo_bytes)
                            st.rerun()
                        except ValueError as exc:
                            st.warning(str(exc))
                for photo in reversed(card.get("media", [])):
                    st.image(b64decode(photo["data_b64"]),
                             caption=f"{photo['device']} · {photo['captured_at']} · ảnh đã lưu")
                    if mode == "design" and st.button("Bỏ ảnh này", key="lesson_evidence_remove_photo_" + photo["id"]):
                        card["media"].remove(photo)
                        st.rerun()
                video = st.file_uploader("Chọn video từ điện thoại, iPad hoặc máy quay (MP4/WebM)",
                                         type=["mp4", "webm"],
                                         key="lesson_evidence_video_" + card["id"] + suffix)
                if video is not None:
                    if video.size > 25_000_000:
                        st.warning("Video vượt 25 MB; hãy chọn đoạn ngắn hơn.")
                    else:
                        st.video(video)
                        st.caption(f"{device} · {video.name} · {video.size / 1_000_000:.1f} MB. "
                                   "Video chỉ xem trước trong phiên này, chưa lưu hoặc chuyển tới thiết bị khác.")
            if owner_id and lesson_key and os.getenv("MATHTEACHER_LOCAL_PHONE_INBOX") == "1":
                from portal_v2.ui.lesson_phone_inbox import (
                    current_inbox, local_ip, start_inbox, stop_inbox,
                )
                with st.expander("Nhận ảnh từ điện thoại / iPad giáo viên qua hotspot", expanded=False):
                    inbox = current_inbox(owner_id, lesson_key)
                    if inbox is None:
                        if st.button("Bật hộp nhận ảnh nội bộ", key="lesson_phone_start_" + card["id"] + suffix):
                            try:
                                start_inbox(owner_id, lesson_key)
                                st.rerun()
                            except (ValueError, OSError) as exc:
                                st.error(f"Chưa bật được hộp nhận: {exc}")
                    else:
                        st.write("Điện thoại kết nối cùng hotspot với máy tính rồi mở:")
                        st.code(f"http://{local_ip()}:{inbox.port}/", language=None)
                        st.write("Mã ghép cặp (hết hạn sau 20 phút):")
                        st.code(inbox.code, language=None)
                        if st.button("Tạo mã ghép cặp mới", key="lesson_phone_rotate_" + card["id"] + suffix):
                            inbox.rotate_code()
                            st.rerun()
                        st.caption("Ảnh vào hộp chờ trên máy tính; chỉ ảnh được duyệt mới lên slide. Dừng hộp nhận sau tiết học.")
                        if st.button("Làm mới hộp chờ", key="lesson_phone_refresh_" + card["id"] + suffix):
                            st.rerun()
                        for pending in inbox.list_pending():
                            st.image(pending["data"], caption=pending["device"] + " · " + pending["at"])
                            if st.button("Duyệt và đưa ảnh vào thẻ", disabled=not active_sources,
                                         key="lesson_phone_approve_" + card["id"] + pending["id"] + suffix):
                                try:
                                    attach_photo(draft, card, source_id=source_id,
                                                 device=pending["device"], data=pending["data"])
                                    inbox.remove(pending["id"])
                                    st.rerun()
                                except ValueError as exc:
                                    st.warning(str(exc))
                            if st.button("Bỏ ảnh chờ", key="lesson_phone_discard_" + card["id"] + pending["id"] + suffix):
                                inbox.remove(pending["id"])
                                st.rerun()
                        if st.button("Dừng hộp nhận ảnh", key="lesson_phone_stop_" + card["id"] + suffix):
                            stop_inbox(owner_id, lesson_key)
                            st.rerun()
            if mode == "design" and st.button("Bỏ thẻ ghi nhận", key="lesson_evidence_remove_" + card["id"]):
                draft["evidence_cards"].remove(card)
                if owner_id and not draft["evidence_cards"]:
                    from portal_v2.ui.lesson_phone_inbox import stop_owner_inbox
                    stop_owner_inbox(owner_id)
                st.rerun()
