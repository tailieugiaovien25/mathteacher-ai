"""Independent admin page: submitted Mathematics questions by grade and form."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from portal_v2.ui.assessment_exam_settings_streamlit import (
    SupabaseAssessmentExamSettingsCatalog,
)


QUESTION_FORMS = (
    ("I. CÂU HỎI TN NHIỀU LỰA CHỌN", ("MULTIPLE_CHOICE",)),
    ("II. CÂU HỎI TN ĐÚNG SAI", ("TRUE_FALSE",)),
    ("III. CÂU HỎI TRẢ LỜI NGẮN", ("SHORT_RESPONSE", "SHORT_ANSWER")),
    ("IV. CÂU HỎI TỰ LUẬN", ("ESSAY",)),
)
PAGE_SIZE = 20
QUERY_BATCH_SIZE = 500
MAX_QUEUE_SIZE = 10000


def _rows(result: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in (getattr(result, "data", None) or [])
            if isinstance(row, Mapping)]


def _parent(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else {}
    return dict(value) if isinstance(value, Mapping) else {}


def _questions(client: Any, grade: int, status: str) -> tuple[list[dict[str, Any]], bool]:
    """Fetch visible math questions by review status with stable server-side paging."""
    rows: list[dict[str, Any]] = []
    for offset in range(0, MAX_QUEUE_SIZE, QUERY_BATCH_SIZE):
        batch = _rows(client.table("assessment_question_versions").select(
            "question_version_id,prompt_text,question_type_code,cognitive_level_code,"
            "default_score,origin_type,created_at,assessment_question_items!inner("
            "question_code,owner_user_id,grade_level,subject_code)"
        ).eq("review_status", status)
            .eq("assessment_question_items.subject_code", "MATH")
            .eq("assessment_question_items.grade_level", grade)
            .order("created_at", desc=True)
            .order("question_version_id", desc=True)
            .range(offset, offset + QUERY_BATCH_SIZE - 1).execute())
        rows.extend(batch)
        if len(batch) < QUERY_BATCH_SIZE:
            return rows, False
    return rows, True


def _details(st: Any, client: Any, version_id: str) -> bool:
    try:
        for title, table, fields in (
            ("Phương án trả lời", "assessment_question_options", "option_code,option_text,is_correct"),
            ("Các ý đúng/sai", "assessment_question_statements", "statement_text,correct_value"),
            ("Đáp án", "assessment_question_answers", "exact_answer_text,answer_explanation"),
            ("Lời giải", "assessment_question_solutions", "solution_text"),
            ("Thang điểm", "assessment_question_scoring_steps", "step_description,step_score"),
            ("Yêu cầu cần đạt", "assessment_question_requirement_links", "requirement_code,link_role"),
            ("Năng lực", "assessment_question_competency_links", "competency_code,link_role"),
        ):
            data = _rows(client.table(table).select(fields)
                         .eq("question_version_id", version_id).execute())
            if data:
                st.markdown(f"**{title}**")
                st.dataframe(data, hide_index=True, use_container_width=True)
    except Exception as exc:
        st.error(f"Không thể đọc đủ nội dung câu hỏi: {exc}")
        return False
    return True


def _approved_section(st: Any, client: Any, grade: int, codes: tuple[str, ...],
                      approved: list[dict[str, Any]]) -> None:
    rows = [row for row in approved if row.get("question_type_code") in codes]
    st.markdown("#### Câu hỏi đã duyệt")
    st.caption(f"{len(rows)} câu · APPROVED")
    if not rows:
        st.info("Chưa có câu hỏi đã duyệt thuộc mục này.")
        return
    key = f"approved_math_{grade}_{codes[0]}"
    page = st.number_input("Trang câu hỏi đã duyệt", min_value=1,
                           max_value=(len(rows) - 1) // PAGE_SIZE + 1,
                           value=1, key=f"{key}_page")
    visible = rows[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
    st.dataframe([{
        "Mã câu": _parent(row.get("assessment_question_items")).get("question_code"),
        "Câu hỏi": row.get("prompt_text"),
        "Mức độ": row.get("cognitive_level_code"),
        "Điểm": row.get("default_score"),
        "Nguồn": row.get("origin_type"),
    } for row in visible], hide_index=True, use_container_width=True)
    approved_lookup = {str(row["question_version_id"]): row for row in visible}
    selected = st.selectbox("Xem câu đã duyệt và đáp án", list(approved_lookup),
                            key=f"{key}_selected",
                            format_func=lambda version_id: (
                                f"{_parent(approved_lookup[version_id].get('assessment_question_items')).get('question_code', '')}"
                                f" · {str(approved_lookup[version_id].get('prompt_text') or '')[:100]}"))
    with st.expander("Nội dung và đáp án câu đã duyệt", expanded=False):
        st.markdown(str(approved_lookup[selected].get("prompt_text") or ""))
        _details(st, client, selected)


def _label(row: dict[str, Any]) -> str:
    item = _parent(row.get("assessment_question_items"))
    code = str(item.get("question_code") or "").strip()
    prompt = str(row.get("prompt_text") or "").replace("\n", " ").strip()
    if len(prompt) > 105:
        prompt = prompt[:102].rstrip() + "…"
    return f"{code} · {prompt}"


def _eligible_for_admin(
    rows: list[dict[str, Any]], reviewer_user_id: str
) -> list[dict[str, Any]]:
    """Exclude questions owned by the reviewing ADMIN from approval actions."""
    return [
        row
        for row in rows
        if str(_parent(row.get("assessment_question_items")).get("owner_user_id") or "")
        != reviewer_user_id
    ]


def _approve_batch(
    st: Any,
    client: Any,
    reviewer_user_id: str,
    rows: list[dict[str, Any]],
    *,
    review_mode: str,
    success_message: str,
) -> None:
    """Approve one or many pending questions through the existing review table."""
    if not rows:
        st.warning("Chưa có câu hỏi đủ điều kiện để duyệt.")
        return

    payload = [
        {
            "question_version_id": str(row["question_version_id"]),
            "reviewer_user_id": reviewer_user_id,
            "decision": "APPROVED",
            "review_note": "ADMIN phê duyệt trên trang duyệt câu hỏi môn Toán.",
            "checklist": {
                "question_content_checked": True,
                "answer_and_scoring_checked": True,
                "review_mode": review_mode,
            },
        }
        for row in rows
    ]

    try:
        result = client.table("assessment_question_reviews").insert(payload).execute()
        inserted = _rows(result)
        if inserted and len(inserted) != len(payload):
            raise ValueError(
                f"Chỉ xác nhận được {len(inserted)}/{len(payload)} quyết định duyệt."
            )
    except Exception as exc:
        st.error(f"Không ghi được quyết định duyệt hàng loạt: {exc}")
    else:
        st.success(success_message)
        st.rerun()


def _bulk_selection(
    st: Any,
    *,
    eligible_subset: list[dict[str, Any]],
    eligible_visible: list[dict[str, Any]],
    key: str,
) -> list[str]:
    """Select individual questions, current page, or the whole pending form."""
    by_id = {
        str(row["question_version_id"]): row
        for row in eligible_subset
    }
    all_ids = list(by_id)
    visible_ids = [
        str(row["question_version_id"])
        for row in eligible_visible
    ]
    state_key = f"{key}_bulk_selected"

    # Keep only IDs that are still pending and eligible.
    existing = [
        str(value)
        for value in st.session_state.get(state_key, [])
        if str(value) in by_id
    ]
    st.session_state[state_key] = existing

    def choose_visible() -> None:
        current = [
            str(value)
            for value in st.session_state.get(state_key, [])
            if str(value) in by_id
        ]
        for version_id in visible_ids:
            if version_id not in current:
                current.append(version_id)
        st.session_state[state_key] = current

    def choose_all() -> None:
        st.session_state[state_key] = list(all_ids)

    def clear_all() -> None:
        st.session_state[state_key] = []

    controls = st.columns([1.25, 1.35, 1.0, 2.2])
    controls[0].button(
        f"Chọn trang này ({len(visible_ids)})",
        key=f"{key}_choose_page",
        use_container_width=True,
        disabled=not visible_ids,
        on_click=choose_visible,
    )
    controls[1].button(
        f"Chọn tất cả ({len(all_ids)})",
        key=f"{key}_choose_all",
        use_container_width=True,
        disabled=not all_ids,
        on_click=choose_all,
    )
    controls[2].button(
        "Bỏ chọn",
        key=f"{key}_clear",
        use_container_width=True,
        disabled=not existing,
        on_click=clear_all,
    )
    controls[3].caption(
        "Chỉ các câu không thuộc chính tài khoản ADMIN hiện tại mới được đưa vào thao tác duyệt."
    )

    selected = st.multiselect(
        "Chọn từng câu hoặc một nhóm câu",
        options=all_ids,
        key=state_key,
        format_func=lambda version_id: _label(by_id[version_id]),
        placeholder="Chọn câu hỏi cần duyệt…",
        help=(
            "Có thể chọn từng câu bằng danh sách này, hoặc dùng nút "
            "Chọn trang này / Chọn tất cả."
        ),
    )
    st.caption(
        f"Đã chọn **{len(selected)} / {len(all_ids)}** câu đủ điều kiện trong mục này."
    )
    return list(selected)


def _form(st: Any, client: Any, reviewer_user_id: str, grade: int,
          title: str, codes: tuple[str, ...], rows: list[dict[str, Any]],
          approved: list[dict[str, Any]]) -> None:
    st.markdown(f"### {title}")
    subset = [r for r in rows if r.get("question_type_code") in codes]
    st.caption(f"{len(subset)} câu đang chờ duyệt")
    if not subset:
        st.info("Chưa có câu hỏi USER gửi duyệt thuộc dạng này.")
        _approved_section(st, client, grade, codes, approved)
        return

    key = f"admin_math_{grade}_{codes[0]}"
    max_page = (len(subset) - 1) // PAGE_SIZE + 1
    page = st.number_input("Trang danh sách", 1, max_page, 1, key=f"{key}_page")
    visible = subset[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    table = []
    for row in visible:
        item = _parent(row.get("assessment_question_items"))
        table.append({
            "Mã câu": item.get("question_code"),
            "Câu hỏi": row.get("prompt_text"),
            "Mức độ": row.get("cognitive_level_code"),
            "Điểm": row.get("default_score"),
            "Nguồn": row.get("origin_type"),
            "Có thể duyệt": (
                "Không - câu của chính ADMIN"
                if str(item.get("owner_user_id") or "") == reviewer_user_id
                else "Có"
            ),
        })
    st.dataframe(table, hide_index=True, use_container_width=True)

    eligible_subset = _eligible_for_admin(subset, reviewer_user_id)
    eligible_visible = _eligible_for_admin(visible, reviewer_user_id)
    own_count = len(subset) - len(eligible_subset)
    if own_count:
        st.warning(
            f"Có {own_count} câu do chính tài khoản ADMIN này tạo; "
            "các câu đó chỉ được xem, không được đưa vào duyệt hàng loạt."
        )

    selected_ids = _bulk_selection(
        st,
        eligible_subset=eligible_subset,
        eligible_visible=eligible_visible,
        key=key,
    )
    eligible_lookup = {
        str(row["question_version_id"]): row
        for row in eligible_subset
    }
    selected_rows = [
        eligible_lookup[version_id]
        for version_id in selected_ids
        if version_id in eligible_lookup
    ]

    # Preview / single-review flow remains available exactly as before.
    lookup = {str(row["question_version_id"]): row for row in visible}
    selected = st.selectbox(
        "Kiểm tra và duyệt một câu trong danh sách trên",
        list(lookup),
        key=f"{key}_selected",
        format_func=lambda version_id: _label(lookup[version_id]),
    )
    row = lookup[selected]
    item = _parent(row.get("assessment_question_items"))

    st.markdown("**Nội dung đầy đủ**")
    st.markdown(str(row.get("prompt_text") or ""))

    detail_ok = _details(st, client, selected)
    if detail_ok:
        if str(item.get("owner_user_id") or "") == reviewer_user_id:
            st.warning(
                "ADMIN không thể duyệt câu hỏi do chính tài khoản mình tạo. "
                "Hãy dùng ADMIN khác."
            )
        else:
            labels = {
                "Chọn quyết định": None,
                "Phê duyệt": "APPROVED",
                "Yêu cầu sửa": "REVISION_REQUIRED",
                "Từ chối": "REJECTED",
            }
            label = st.selectbox(
                "Quyết định",
                tuple(labels),
                key=f"{key}_{selected}_decision",
            )
            note = st.text_area(
                "Nhận xét gửi giáo viên",
                key=f"{key}_{selected}_note",
            ).strip()
            checked = st.checkbox(
                "Tôi đã kiểm tra câu hỏi, đáp án, lời giải và thang điểm",
                key=f"{key}_{selected}_checked",
            )
            decision = labels[label]
            if st.button(
                "Ghi quyết định duyệt câu hỏi",
                type="primary",
                key=f"{key}_{selected}_submit",
                disabled=(
                    not checked
                    or not decision
                    or (decision != "APPROVED" and not note)
                ),
            ):
                try:
                    client.table("assessment_question_reviews").insert({
                        "question_version_id": selected,
                        "reviewer_user_id": reviewer_user_id,
                        "decision": decision,
                        "review_note": note,
                        "checklist": {
                            "question_content_checked": True,
                            "answer_and_scoring_checked": True,
                            "review_mode": "ADMIN_CONFIRMED_SINGLE",
                        },
                    }).execute()
                except Exception as exc:
                    st.error(f"Không ghi được quyết định duyệt: {exc}")
                else:
                    st.success(
                        "Đã ghi quyết định; câu hỏi rời khỏi danh sách chờ duyệt."
                    )
                    st.rerun()

    st.markdown("#### Duyệt nhanh theo nhóm")
    bulk_confirmed = st.checkbox(
        "Tôi đã kiểm tra các câu được chọn và đồng ý phê duyệt",
        key=f"{key}_bulk_confirmed",
    )
    b1, b2 = st.columns(2)

    if b1.button(
        f"Duyệt nhóm đã chọn ({len(selected_rows)})",
        type="primary",
        use_container_width=True,
        key=f"{key}_bulk_approve",
        disabled=not bulk_confirmed or not selected_rows,
    ):
        _approve_batch(
            st,
            client,
            reviewer_user_id,
            selected_rows,
            review_mode="ADMIN_CONFIRMED_GROUP",
            success_message=f"Đã phê duyệt {len(selected_rows)} câu được chọn.",
        )

    if b2.button(
        f"Duyệt tất cả đủ điều kiện ({len(eligible_subset)})",
        type="primary",
        use_container_width=True,
        key=f"{key}_approve_all",
        disabled=not bulk_confirmed or not eligible_subset,
    ):
        _approve_batch(
            st,
            client,
            reviewer_user_id,
            eligible_subset,
            review_mode="ADMIN_CONFIRMED_ALL_VISIBLE_FORM",
            success_message=(
                f"Đã phê duyệt toàn bộ {len(eligible_subset)} câu đủ điều kiện "
                f"trong mục {title}."
            ),
        )

    _approved_section(st, client, grade, codes, approved)


def render_admin_math_question_review(st: Any, *, client: Any,
                                       reviewer_user_id: str) -> None:
    st.title("Duyệt câu hỏi môn Toán")
    st.caption("Câu hỏi do USER gửi duyệt · phân theo lớp và dạng câu · duyệt từng câu, nhóm câu hoặc toàn bộ")
    if client is None:
        st.error("Chưa có kết nối dữ liệu.")
        return
    try:
        catalog = SupabaseAssessmentExamSettingsCatalog(client=client,
                                                        user_id=reviewer_user_id)
        if not catalog.is_admin():
            st.error("Chỉ tài khoản ADMIN được duyệt câu hỏi.")
            return
    except Exception as exc:
        st.error(f"Không xác minh được quyền ADMIN: {exc}")
        return
    tabs = st.tabs([f"Câu hỏi Toán {grade}" for grade in (6, 7, 8, 9)])
    known = set().union(*(codes for _, codes in QUESTION_FORMS))
    for grade, tab in zip((6, 7, 8, 9), tabs):
        with tab:
            try:
                rows, truncated = _questions(client, grade, "PENDING_REVIEW")
                approved, approved_truncated = _questions(client, grade, "APPROVED")
            except Exception as exc:
                st.error(f"Không tải được câu hỏi Toán {grade}: {exc}")
                continue
            st.info(f"Toán {grade}: {len(rows)} câu hỏi USER gửi đang chờ duyệt.")
            if truncated:
                st.error("Hàng đợi vượt 10.000 câu. Chưa tải hết; cần thu hẹp hoặc phân trang máy chủ.")
            if approved_truncated:
                st.warning("Có hơn 10.000 câu đã duyệt; danh sách này chưa tải hết.")
            unexpected = [r for r in rows if r.get("question_type_code") not in known]
            if unexpected:
                st.warning(f"Có {len(unexpected)} câu dùng mã dạng khác bốn mục trên; cần bổ sung ánh xạ trước khi duyệt.")
                st.dataframe([{"Mã câu": _parent(r.get("assessment_question_items")).get("question_code"),
                               "Dạng": r.get("question_type_code"), "Câu hỏi": r.get("prompt_text")}
                              for r in unexpected], hide_index=True, use_container_width=True)
            unexpected_approved = [r for r in approved if r.get("question_type_code") not in known]
            if unexpected_approved:
                st.warning(f"Có {len(unexpected_approved)} câu đã duyệt mang mã dạng khác bốn mục.")
                st.dataframe([{"Mã câu": _parent(r.get("assessment_question_items")).get("question_code"),
                               "Dạng": r.get("question_type_code"), "Câu hỏi": r.get("prompt_text")}
                              for r in unexpected_approved], hide_index=True, use_container_width=True)
            for title, codes in QUESTION_FORMS:
                _form(st, client, reviewer_user_id, grade, title, codes, rows, approved)
