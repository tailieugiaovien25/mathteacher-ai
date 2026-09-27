from __future__ import annotations

from typing import Any, Callable, Sequence


def render_review_selection_controls(
    st: Any,
    *,
    item_ids: Sequence[str],
    label_for_id: Callable[[str], str],
    key_prefix: str,
    noun: str,
) -> list[str]:
    """Reusable single/group/all selection control for ADMIN review pages."""
    ids = [str(value) for value in item_ids]
    selected_key = f"{key_prefix}_selected"
    select_all_key = f"{key_prefix}_select_all"

    current = [
        str(value)
        for value in st.session_state.get(selected_key, [])
        if str(value) in ids
    ]
    st.session_state[selected_key] = current
    st.session_state.setdefault(select_all_key, False)

    def _select_all() -> None:
        st.session_state[selected_key] = list(ids)
        st.session_state[select_all_key] = True

    def _clear_all() -> None:
        st.session_state[selected_key] = []
        st.session_state[select_all_key] = False

    def _sync_checkbox() -> None:
        if st.session_state.get(select_all_key):
            st.session_state[selected_key] = list(ids)

    top = st.columns([1.15, 1.15, 2.7])
    top[0].button(
        "Chọn tất cả",
        key=f"{key_prefix}_select_all_button",
        use_container_width=True,
        on_click=_select_all,
    )
    top[1].button(
        "Bỏ chọn",
        key=f"{key_prefix}_clear_button",
        use_container_width=True,
        on_click=_clear_all,
    )
    top[2].checkbox(
        f"Chọn tất cả {noun} đang hiển thị",
        key=select_all_key,
        on_change=_sync_checkbox,
    )

    selected = st.multiselect(
        f"Chọn từng {noun} hoặc một nhóm {noun}",
        options=ids,
        format_func=label_for_id,
        key=selected_key,
        placeholder=f"Chọn {noun} cần duyệt…",
    )

    if len(selected) != len(ids):
        st.session_state[select_all_key] = False

    st.caption(f"Đã chọn {len(selected)} / {len(ids)} {noun}.")
    return list(selected)


def clear_review_selection(st: Any, *, key_prefix: str) -> None:
    st.session_state[f"{key_prefix}_selected"] = []
    st.session_state[f"{key_prefix}_select_all"] = False
