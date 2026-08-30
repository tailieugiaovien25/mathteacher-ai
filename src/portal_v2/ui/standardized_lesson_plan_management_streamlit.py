from __future__ import annotations

from hashlib import sha256
from typing import Any, Callable

import streamlit as st

from lesson_planning_v2.services.lesson_plan_merge_service import (
    LessonPlanMergeError,
    LessonPlanMergeService,
    LessonPlanMergeSource,
)

_REGISTRY_KEY = "standardized_lesson_plan_management_records_v1"
_SELECTION_PREFIX = "standardized_lesson_plan_selected_v1_"
_PREVIEW_KEY = "standardized_lesson_plan_preview_record_v2"
_MERGE_ORDER_KEY = "standardized_lesson_plan_merge_order_v4"
_MERGE_RESULT_KEY = "standardized_lesson_plan_merge_result_v4"
_MERGE_PREVIEW_KEY = "standardized_lesson_plan_merge_preview_v4"


def _record_id(*, file_name: str, content: bytes) -> str:
    digest = sha256()
    digest.update(file_name.encode("utf-8", errors="replace"))
    digest.update(b"\0")
    digest.update(content)
    return digest.hexdigest()[:20]


def _selection_key(record_id: str) -> str:
    return _SELECTION_PREFIX + record_id


def _registry() -> list[dict[str, Any]]:
    value = st.session_state.get(_REGISTRY_KEY)
    if not isinstance(value, list):
        value = []
        st.session_state[_REGISTRY_KEY] = value
    return value


def _remember_current_artifact(*, file_name: str, content: bytes) -> str:
    record_id = _record_id(file_name=file_name, content=content)
    records = _registry()
    if not any(str(x.get("id", "")) == record_id for x in records if isinstance(x, dict)):
        records.append({"id": record_id, "file_name": file_name, "content": bytes(content)})
    return record_id


def _clear_merge_result() -> None:
    st.session_state.pop(_MERGE_RESULT_KEY, None)
    st.session_state.pop(_MERGE_PREVIEW_KEY, None)


def _remove_record(record_id: str) -> None:
    st.session_state[_REGISTRY_KEY] = [
        x for x in _registry() if str(x.get("id", "")) != record_id
    ]
    st.session_state.pop(_selection_key(record_id), None)
    if st.session_state.get(_PREVIEW_KEY) == record_id:
        st.session_state.pop(_PREVIEW_KEY, None)
    order = st.session_state.get(_MERGE_ORDER_KEY, [])
    if isinstance(order, list):
        st.session_state[_MERGE_ORDER_KEY] = [x for x in order if x != record_id]
    _clear_merge_result()


def selected_standardized_lesson_plan_records() -> tuple[dict[str, Any], ...]:
    return tuple(
        x for x in _registry()
        if st.session_state.get(_selection_key(str(x.get("id", ""))), False)
    )


def _ordered_selected_records() -> tuple[dict[str, Any], ...]:
    selected = selected_standardized_lesson_plan_records()
    ids = [str(x["id"]) for x in selected]
    selected_set = set(ids)
    order = st.session_state.get(_MERGE_ORDER_KEY, [])
    if not isinstance(order, list):
        order = []
    order = [x for x in order if x in selected_set]
    order.extend(x for x in ids if x not in order)
    st.session_state[_MERGE_ORDER_KEY] = order
    by_id = {str(x["id"]): x for x in selected}
    return tuple(by_id[x] for x in order if x in by_id)


def _move(record_id: str, delta: int) -> None:
    order = list(st.session_state.get(_MERGE_ORDER_KEY, []))
    if record_id not in order:
        return
    i = order.index(record_id)
    j = i + delta
    if 0 <= j < len(order):
        order[i], order[j] = order[j], order[i]
        st.session_state[_MERGE_ORDER_KEY] = order
        _clear_merge_result()


def _render_merge_workspace(preview_html_builder: Callable[[bytes], str] | None) -> None:
    ordered = _ordered_selected_records()
    st.markdown("---")
    st.subheader("Gộp giáo án")

    if len(ordered) < 2:
        st.info("Hãy lựa chọn ít nhất 2 giáo án để gộp.")
        _clear_merge_result()
        return

    st.caption(f"Đã chọn {len(ordered)} giáo án. Thứ tự dưới đây là thứ tự trong file gộp.")

    for index, item in enumerate(ordered):
        rid = str(item["id"])
        row = st.columns([0.7, 5.0, 0.8, 0.8])
        row[0].markdown(f"**{index + 1}.**")
        row[1].write(str(item["file_name"]))
        if row[2].button("↑", key=f"standardized_merge_up_v4_{rid}", disabled=index == 0):
            _move(rid, -1)
            st.rerun()
        if row[3].button("↓", key=f"standardized_merge_down_v4_{rid}", disabled=index == len(ordered) - 1):
            _move(rid, 1)
            st.rerun()

    if st.button("GỘP FILE", key="standardized_lesson_plan_merge_v4", type="primary", width="stretch"):
        try:
            result = LessonPlanMergeService().merge([
                LessonPlanMergeSource(
                    source_id=str(x["id"]),
                    file_name=str(x["file_name"]),
                    content=bytes(x["content"]),
                )
                for x in ordered
            ])
            st.session_state[_MERGE_RESULT_KEY] = {
                "file_name": f"giao-an-gop-{len(ordered)}-bai.docx",
                "content": result.content,
                "source_ids": result.source_ids,
                "source_file_names": result.source_file_names,
            }
            st.session_state[_MERGE_PREVIEW_KEY] = False
            st.success("Đã gộp giáo án theo đúng thứ tự đã chọn.")
        except LessonPlanMergeError as error:
            st.error("Không thể gộp giáo án: " + str(error))
        except Exception as error:
            st.error("Có lỗi khi gộp giáo án: " + str(error))

    merged = st.session_state.get(_MERGE_RESULT_KEY)
    if not isinstance(merged, dict):
        return
    if tuple(merged.get("source_ids", ())) != tuple(str(x["id"]) for x in ordered):
        _clear_merge_result()
        return

    st.markdown("#### File giáo án đã gộp")
    actions = st.columns([1.2, 1.3, 1.3])
    if actions[0].button(
        "Xem trước", key="standardized_merge_preview_button_v4",
        disabled=preview_html_builder is None,
    ):
        st.session_state[_MERGE_PREVIEW_KEY] = not bool(
            st.session_state.get(_MERGE_PREVIEW_KEY, False)
        )

    actions[1].button(
        "Lưu hệ thống",
        key="standardized_merge_save_disabled_v4",
        disabled=True,
        help="Sẽ bật sau khi lớp lưu provenance của file gộp được hoàn thiện.",
    )
    actions[2].download_button(
        "Tải file Word",
        data=bytes(merged["content"]),
        file_name=str(merged["file_name"]),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="standardized_merge_download_v4",
    )
    st.caption("Nguồn gộp: " + " → ".join(str(x) for x in merged.get("source_file_names", ())))

    if st.session_state.get(_MERGE_PREVIEW_KEY, False) and preview_html_builder is not None:
        try:
            st.components.v1.html(
                preview_html_builder(bytes(merged["content"])),
                height=820, scrolling=True,
            )
        except Exception as error:
            st.warning("Không thể xem trước file gộp: " + str(error))


def render_standardized_lesson_plan_management(
    *,
    current_file_name: str,
    current_content: bytes,
    preview_html_builder: Callable[[bytes], str] | None = None,
    save_handler: Callable[..., None] | None = None,
) -> None:
    if not current_file_name or not current_content:
        return

    _remember_current_artifact(file_name=current_file_name, content=current_content)
    st.markdown("---")
    st.subheader("Danh sách giáo án đã chuẩn hóa")
    st.caption(
        "Danh sách làm việc phục vụ lựa chọn nhiều giáo án. "
        "Xóa tại đây chỉ xóa khỏi danh sách làm việc, không xóa giáo án đã lưu trên hệ thống."
    )

    records = list(_registry())
    if not records:
        st.info("Chưa có giáo án đã chuẩn hóa trong danh sách.")
        return

    toolbar = st.columns([1, 1, 3])
    if toolbar[0].button("Chọn tất cả", key="standardized_lesson_plan_select_all_v1"):
        for item in records:
            st.session_state[_selection_key(str(item["id"]))] = True
        _clear_merge_result()
        st.rerun()
    if toolbar[1].button("Bỏ chọn", key="standardized_lesson_plan_clear_all_v1"):
        for item in records:
            st.session_state[_selection_key(str(item["id"]))] = False
        _clear_merge_result()
        st.rerun()
    toolbar[2].caption(f"{len(records)} giáo án trong danh sách làm việc.")

    for index, item in enumerate(records, start=1):
        rid = str(item["id"])
        file_name = str(item["file_name"])
        content = bytes(item["content"])
        row = st.columns([0.75, 3.3, 1.1, 1.25, 0.9, 1.25])
        row[0].checkbox("Lựa chọn", key=_selection_key(rid))
        row[1].markdown(f"**{index}. {file_name}**")

        if row[2].button("Xem trước", key=f"standardized_lesson_plan_preview_v2_{rid}"):
            current = st.session_state.get(_PREVIEW_KEY)
            st.session_state[_PREVIEW_KEY] = None if current == rid else rid

        if row[3].button(
            "Lưu hệ thống", key=f"standardized_lesson_plan_save_v2_{rid}",
            disabled=save_handler is None,
        ):
            if save_handler is not None:
                save_handler(artifact_file_name=file_name, artifact_content=content)

        if row[4].button("Xóa", key=f"standardized_lesson_plan_remove_v1_{rid}"):
            _remove_record(rid)
            st.rerun()

        row[5].download_button(
            "Tải xuống", data=content, file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"standardized_lesson_plan_download_v1_{rid}",
        )

        if st.session_state.get(_PREVIEW_KEY) == rid:
            if preview_html_builder is None:
                st.warning("Chức năng xem trước chưa sẵn sàng.")
            else:
                try:
                    st.components.v1.html(preview_html_builder(content), height=720, scrolling=True)
                except Exception as error:
                    st.warning("Không thể xem trước giáo án này: " + str(error))

    selected_count = len(selected_standardized_lesson_plan_records())
    if selected_count:
        st.success(f"Đã lựa chọn {selected_count} giáo án.")
    else:
        st.caption("Chưa lựa chọn giáo án nào để chuẩn bị gộp.")

    _render_merge_workspace(preview_html_builder)
