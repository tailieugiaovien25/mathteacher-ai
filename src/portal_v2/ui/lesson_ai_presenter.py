"""Teacher authored visual AI presenter cards for lesson activities."""

from base64 import b64encode
from functools import lru_cache
from pathlib import Path
from uuid import uuid4


ROLES = {"GUIDE": "AI hướng dẫn", "ASSISTANT": "AI trợ giảng", "MC": "AI MC"}
ACTIVITIES = {"MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"}
AVATAR = Path(__file__).parent / "assets" / "lesson_ai_companion.png"


@lru_cache(maxsize=1)
def avatar_data_uri() -> str:
    return "data:image/png;base64," + b64encode(AVATAR.read_bytes()).decode("ascii")


def validate_presenter(card):
    if not isinstance(card, dict) or set(card) != {"id", "activity", "role", "message"}:
        raise ValueError("Thẻ nhân vật AI không hợp lệ.")
    if card["activity"] not in ACTIVITIES or card["role"] not in ROLES:
        raise ValueError("Hoạt động hoặc vai trò AI không hợp lệ.")
    for field, limit in (("id", 80), ("message", 1000)):
        if not isinstance(card[field], str) or not card[field].strip() or len(card[field]) > limit:
            raise ValueError("Nội dung nhân vật AI không hợp lệ.")
    return card


def add_presenter(draft, *, activity, role, message):
    cards = draft.setdefault("ai_presenters", [])
    if len(cards) >= 40:
        raise ValueError("Bài giảng chỉ nhận tối đa 40 thẻ nhân vật AI.")
    card = validate_presenter({"id": str(uuid4()), "activity": activity,
                               "role": role, "message": message.strip()})
    cards.append(card)
    return card


def render_presenter_authoring(st, draft, activity):
    with st.expander("Thêm nhân vật AI dẫn dắt hoạt động", expanded=False):
        role = st.selectbox("Vai trò", list(ROLES), format_func=ROLES.get,
                            key="lesson_ai_presenter_role")
        message = st.text_area("Lời dẫn của nhân vật", max_chars=1000,
                               placeholder="Ví dụ: Chào các em! Hôm nay chúng ta cùng tìm hiểu cách ghi số tự nhiên.",
                               key="lesson_ai_presenter_message")
        st.caption("Giáo viên kiểm tra và viết lời dẫn trước khi trình chiếu.")
        if st.button("Thêm nhân vật vào hoạt động này", key="lesson_ai_presenter_add"):
            try:
                add_presenter(draft, activity=activity, role=role, message=message)
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
    for card in list(draft.get("ai_presenters", [])):
        if card["activity"] != activity:
            continue
        with st.expander(f"{ROLES[card['role']]} · {card['message'][:60]}", expanded=False):
            st.write(card["message"])
            if st.button("Bỏ nhân vật khỏi hoạt động", key="lesson_ai_presenter_remove_" + card["id"]):
                draft["ai_presenters"].remove(card)
                st.rerun()
