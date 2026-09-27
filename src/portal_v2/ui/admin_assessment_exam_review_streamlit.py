from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from portal_v2.ui.admin_review_selection_controls import (
    clear_review_selection,
    render_review_selection_controls,
)
from portal_v2.ui.assessment_exam_settings_streamlit import (
    SupabaseAssessmentExamSettingsCatalog,
)


GRADES = (6, 7, 8, 9)


def _rows(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    return [dict(row) for row in data or [] if isinstance(row, Mapping)]


def _exam(row: dict[str, Any]) -> Mapping[str, Any]:
    relation = row.get("assessment_exams")
    exam = relation[0] if isinstance(relation, list) else relation
    if not isinstance(exam, Mapping):
        raise ValueError("Không xác định được đề kiểm tra gốc.")
    return exam


def _pending_exams(client: Any, reviewer_user_id: str) -> tuple[list[dict[str, Any]], int]:
    rows = _rows(
        client.table("assessment_exam_versions")
        .select(
            "exam_version_id,version_number,exam_title,exam_code_label,"
            "academic_year,semester_number,total_score,duration_minutes,"
            "origin_type,created_at,"
            "assessment_exams!inner("
            "exam_code,owner_user_id,subject_code,grade_level,lifecycle_status)"
        )
        .eq("assembly_status", "PENDING_REVIEW")
        .eq("assessment_exams.subject_code", "MATH")
        .in_("assessment_exams.grade_level", list(GRADES))
        .order("created_at")
        .execute()
    )
    visible: list[dict[str, Any]] = []
    excluded_own = 0
    for row in rows:
        if str(_exam(row).get("owner_user_id") or "") == reviewer_user_id:
            excluded_own += 1
            continue
        visible.append(row)
    return visible, excluded_own


def _grade(row: dict[str, Any]) -> int:
    return int(_exam(row).get("grade_level") or 0)


def _code(row: dict[str, Any]) -> str:
    return str(_exam(row).get("exam_code") or "").strip()


def _label(row: dict[str, Any]) -> str:
    return (
        f"{_code(row)} · {row.get('exam_title', '')} · "
        f"Lớp {_grade(row)} · {row.get('duration_minutes', '')} phút"
    )


def _approve(
    st: Any,
    *,
    client: Any,
    exams: list[dict[str, Any]],
    reviewer_user_id: str,
    review_mode: str,
    selection_key_prefix: str,
) -> None:
    if not exams:
        st.warning("Chưa chọn đề kiểm tra để duyệt.")
        return
    payload = [
        {
            "exam_version_id": row["exam_version_id"],
            "reviewer_user_id": reviewer_user_id,
            "decision": "APPROVED",
            "review_note": "ADMIN duyệt trên trang duyệt đề kiểm tra.",
            "checklist": {
                "review_mode": review_mode,
                "blueprint_and_assembly_checked": True,
                "question_availability_checked": True,
            },
        }
        for row in exams
    ]
    try:
        result = client.table("assessment_exam_reviews").insert(payload).execute()
        if len(_rows(result)) != len(payload):
            raise ValueError(
                f"Chưa xác nhận được kết quả duyệt đủ {len(payload)} đề."
            )
    except Exception as error:
        st.error(f"Không thể duyệt đề kiểm tra: {error}")
    else:
        clear_review_selection(st, key_prefix=selection_key_prefix)
        st.success(f"Đã duyệt {len(payload)} đề kiểm tra.")
        st.rerun()


def _render_grade(
    st: Any,
    *,
    client: Any,
    reviewer_user_id: str,
    exams: list[dict[str, Any]],
    grade: int,
) -> None:
    rows = [row for row in exams if _grade(row) == grade]
    st.info(f"Toán {grade}: {len(rows)} đề kiểm tra đang chờ duyệt.")
    if not rows:
        return

    by_id = {str(row["exam_version_id"]): row for row in rows}
    key_prefix = f"admin_math_exam_review_g{grade}"

    selected_ids = render_review_selection_controls(
        st,
        item_ids=list(by_id),
        label_for_id=lambda exam_id: _label(by_id[exam_id]),
        key_prefix=key_prefix,
        noun="đề",
    )

    st.dataframe(
        [
            {
                "Mã đề": _code(row),
                "Tên đề": row.get("exam_title"),
                "Phiên bản": row.get("version_number"),
                "Học kỳ": row.get("semester_number"),
                "Thời lượng": row.get("duration_minutes"),
                "Tổng điểm": row.get("total_score"),
                "Nguồn": row.get("origin_type"),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )

    preview_id = st.selectbox(
        "Kiểm tra một đề trong danh sách",
        options=list(by_id),
        format_func=lambda exam_id: _label(by_id[exam_id]),
        key=f"{key_prefix}_preview",
    )
    preview = by_id[preview_id]
    st.write(
        {
            "Mã đề": _code(preview),
            "Tên đề": preview.get("exam_title"),
            "Phiên bản": preview.get("version_number"),
            "Năm học": preview.get("academic_year"),
            "Học kỳ": preview.get("semester_number"),
            "Thời lượng": preview.get("duration_minutes"),
            "Tổng điểm": preview.get("total_score"),
            "Nguồn": preview.get("origin_type"),
        }
    )

    confirmed = st.checkbox(
        "Tôi đã kiểm tra ma trận, cấu trúc đề và nội dung các câu trong phạm vi sẽ duyệt",
        key=f"{key_prefix}_confirm",
    )
    selected_rows = [by_id[x] for x in selected_ids if x in by_id]

    a, b, c = st.columns(3)
    if a.button(
        "Duyệt đề đang xem",
        disabled=not confirmed,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_one",
    ):
        _approve(
            st,
            client=client,
            exams=[preview],
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_SINGLE",
            selection_key_prefix=key_prefix,
        )

    if b.button(
        f"Duyệt nhóm ({len(selected_rows)})",
        disabled=not confirmed or not selected_rows,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_group",
    ):
        _approve(
            st,
            client=client,
            exams=selected_rows,
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_GROUP",
            selection_key_prefix=key_prefix,
        )

    if c.button(
        f"Duyệt tất cả ({len(rows)})",
        disabled=not confirmed,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_approve_all",
    ):
        _approve(
            st,
            client=client,
            exams=rows,
            reviewer_user_id=reviewer_user_id,
            review_mode="ADMIN_CONFIRMED_ALL_VISIBLE",
            selection_key_prefix=key_prefix,
        )


def render_admin_assessment_exam_review(
    st: Any, *, client: Any, reviewer_user_id: str
) -> None:
    st.subheader("Duyệt đề kiểm tra môn Toán")
    st.caption(
        "Duyệt từng đề, nhóm đề hoặc toàn bộ đề đang hiển thị. "
        "Đề do chính ADMIN này sở hữu được loại khỏi danh sách vì governance không cho tự duyệt."
    )
    if client is None:
        st.warning("Chưa kết nối dữ liệu đề kiểm tra.")
        return

    try:
        catalog = SupabaseAssessmentExamSettingsCatalog(
            client=client, user_id=reviewer_user_id
        )
        if not catalog.is_admin():
            st.error("Chỉ tài khoản quản trị mới được duyệt đề.")
            return
        exams, excluded_own = _pending_exams(client, reviewer_user_id)
    except Exception as error:
        st.error(f"Không tải được hàng đợi đề kiểm tra: {error}")
        return

    if excluded_own:
        st.caption(
            f"Đã ẩn {excluded_own} đề do chính tài khoản ADMIN này sở hữu; "
            "cơ chế database không cho phép tự duyệt đề."
        )

    tabs = st.tabs([f"Đề Toán {grade}" for grade in GRADES])
    for tab, grade in zip(tabs, GRADES):
        with tab:
            _render_grade(
                st,
                client=client,
                reviewer_user_id=reviewer_user_id,
                exams=exams,
                grade=grade,
            )
