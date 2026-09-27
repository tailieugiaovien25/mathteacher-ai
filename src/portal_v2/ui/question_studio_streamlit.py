"""Question Studio R2B controlled foundation.

R2B reads the real teacher-owned Math question bank, lets the teacher open
editable content into a working editor, creates a working revision from an
APPROVED version, and previews it. It intentionally performs NO database
writes. Transactional persistence is reserved for R2C.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PAGE_TITLE = "Xưởng câu hỏi"
WORKING_KEY = "qst_r2b_working_draft"
GRADES = (6, 7, 8, 9)
QUESTION_TYPES = (
    "MULTIPLE_CHOICE",
    "TRUE_FALSE",
    "SHORT_RESPONSE",
    "SHORT_ANSWER",
    "ESSAY",
)
EDITABLE_STATUSES = {"DRAFT", "REVISION_REQUIRED"}


def _rows(result: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in (getattr(result, "data", None) or [])
        if isinstance(row, Mapping)
    ]


def _new_working() -> dict[str, Any]:
    return {
        "question_id": None,
        "source_version_id": None,
        "source_status": "NEW",
        "base_version_number": 0,
        "question_code": "",
        "grade_level": 6,
        "question_type_code": "MULTIPLE_CHOICE",
        "cognitive_level_code": "NB",
        "prompt_text": "",
        "stimulus_text": "",
        "instruction_text": "",
        "estimated_minutes": 2.0,
        "default_score": 0.25,
        "origin_type": "HUMAN",
        "primary_requirement_code": "",
        "primary_competency_code": "",
        "options": [
            {"option_code": "A", "option_text": "", "is_correct": True},
            {"option_code": "B", "option_text": "", "is_correct": False},
            {"option_code": "C", "option_text": "", "is_correct": False},
            {"option_code": "D", "option_text": "", "is_correct": False},
        ],
        "statements": [
            {"statement_code": "a", "statement_text": "", "correct_value": True},
            {"statement_code": "b", "statement_text": "", "correct_value": True},
            {"statement_code": "c", "statement_text": "", "correct_value": True},
            {"statement_code": "d", "statement_text": "", "correct_value": True},
        ],
        "answer": {
            "exact_answer_text": "",
            "answer_explanation": "",
        },
        "solution_text": "",
        "scoring_steps": [
            {"step_code": "S1", "step_description": "", "step_score": 0.0},
            {"step_code": "S2", "step_description": "", "step_score": 0.0},
            {"step_code": "S3", "step_description": "", "step_score": 0.0},
            {"step_code": "S4", "step_description": "", "step_score": 0.0},
        ],
    }


def _load_versions(client: Any, user_id: str) -> list[dict[str, Any]]:
    items = _rows(
        client.table("assessment_question_items")
        .select(
            "question_id,question_code,grade_level,subject_code,education_level,"
            "current_version_number,lifecycle_status,created_at,updated_at"
        )
        .eq("owner_user_id", user_id)
        .eq("subject_code", "MATH")
        .in_("grade_level", list(GRADES))
        .order("updated_at", desc=True)
        .limit(1000)
        .execute()
    )
    if not items:
        return []

    by_id = {str(row["question_id"]): row for row in items}
    versions: list[dict[str, Any]] = []
    ids = list(by_id)
    for start in range(0, len(ids), 100):
        versions.extend(
            _rows(
                client.table("assessment_question_versions")
                .select(
                    "question_version_id,question_id,version_number,"
                    "question_type_code,cognitive_level_code,prompt_text,"
                    "stimulus_text,instruction_text,estimated_minutes,"
                    "default_score,origin_type,review_status,locked_at,"
                    "created_at,updated_at"
                )
                .in_("question_id", ids[start : start + 100])
                .order("updated_at", desc=True)
                .execute()
            )
        )
    combined = [
        {**version, "item": by_id[str(version["question_id"])]}
        for version in versions
        if str(version.get("question_id")) in by_id
    ]
    combined.sort(
        key=lambda row: (
            str(row.get("updated_at") or ""),
            int(row.get("version_number") or 0),
        ),
        reverse=True,
    )
    return combined


def _load_detail(client: Any, version_id: str) -> dict[str, list[dict[str, Any]]]:
    specs = (
        (
            "options",
            "assessment_question_options",
            "option_code,option_text,is_correct,sequence_number,feedback_text",
            "sequence_number",
        ),
        (
            "statements",
            "assessment_question_statements",
            "statement_code,statement_text,correct_value,sequence_number,explanation_text",
            "sequence_number",
        ),
        (
            "answers",
            "assessment_question_answers",
            "answer_mode,exact_answer_text,accepted_answers,numeric_answer,tolerance,"
            "unit_text,rounding_rule,answer_explanation",
            None,
        ),
        (
            "solutions",
            "assessment_question_solutions",
            "solution_id,solution_code,solution_text,sequence_number,is_primary,"
            "alternative_method_note",
            "sequence_number",
        ),
        (
            "scoring_steps",
            "assessment_question_scoring_steps",
            "solution_id,step_code,step_description,sequence_number,step_score,"
            "acceptance_note,allows_equivalent_method",
            "sequence_number",
        ),
        (
            "requirements",
            "assessment_question_requirement_links",
            "requirement_code,link_role,sequence_number,notes",
            "sequence_number",
        ),
        (
            "competencies",
            "assessment_question_competency_links",
            "competency_code,link_role,sequence_number,notes",
            "sequence_number",
        ),
    )
    detail: dict[str, list[dict[str, Any]]] = {}
    for key, table, fields, order_field in specs:
        query = client.table(table).select(fields).eq(
            "question_version_id", version_id
        )
        if order_field:
            query = query.order(order_field)
        detail[key] = _rows(query.execute())
    return detail


def _first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _working_from_version(
    row: dict[str, Any],
    detail: dict[str, list[dict[str, Any]]],
    *,
    as_revision: bool,
) -> dict[str, Any]:
    working = _new_working()
    item = dict(row.get("item") or {})
    working.update(
        {
            "question_id": row.get("question_id"),
            "source_version_id": row.get("question_version_id"),
            "source_status": (
                "APPROVED_SOURCE"
                if as_revision
                else str(row.get("review_status") or "")
            ),
            "base_version_number": int(row.get("version_number") or 0),
            "question_code": str(item.get("question_code") or ""),
            "grade_level": int(item.get("grade_level") or 6),
            "question_type_code": str(
                row.get("question_type_code") or "MULTIPLE_CHOICE"
            ),
            "cognitive_level_code": str(
                row.get("cognitive_level_code") or "NB"
            ),
            "prompt_text": str(row.get("prompt_text") or ""),
            "stimulus_text": str(row.get("stimulus_text") or ""),
            "instruction_text": str(row.get("instruction_text") or ""),
            "estimated_minutes": float(row.get("estimated_minutes") or 2.0),
            "default_score": float(row.get("default_score") or 0.25),
            "origin_type": "HUMAN",
        }
    )

    options = detail.get("options") or []
    if options:
        working["options"] = [
            {
                "option_code": str(x.get("option_code") or ""),
                "option_text": str(x.get("option_text") or ""),
                "is_correct": bool(x.get("is_correct")),
            }
            for x in options[:4]
        ]

    statements = detail.get("statements") or []
    if statements:
        working["statements"] = [
            {
                "statement_code": str(x.get("statement_code") or ""),
                "statement_text": str(x.get("statement_text") or ""),
                "correct_value": bool(x.get("correct_value")),
            }
            for x in statements[:4]
        ]

    answer = _first(detail.get("answers") or [])
    if answer:
        working["answer"] = {
            "exact_answer_text": str(answer.get("exact_answer_text") or ""),
            "answer_explanation": str(answer.get("answer_explanation") or ""),
        }

    solutions = detail.get("solutions") or []
    primary = next(
        (x for x in solutions if bool(x.get("is_primary"))),
        solutions[0] if solutions else {},
    )
    working["solution_text"] = str(primary.get("solution_text") or "")

    steps = detail.get("scoring_steps") or []
    if steps:
        working["scoring_steps"] = [
            {
                "step_code": str(x.get("step_code") or f"S{i}"),
                "step_description": str(x.get("step_description") or ""),
                "step_score": float(x.get("step_score") or 0.0),
            }
            for i, x in enumerate(steps[:4], 1)
        ]

    requirements = detail.get("requirements") or []
    primary_requirement = next(
        (x for x in requirements if str(x.get("link_role")) == "PRIMARY"),
        requirements[0] if requirements else {},
    )
    working["primary_requirement_code"] = str(
        primary_requirement.get("requirement_code") or ""
    )

    competencies = detail.get("competencies") or []
    primary_competency = next(
        (x for x in competencies if str(x.get("link_role")) == "PRIMARY"),
        competencies[0] if competencies else {},
    )
    working["primary_competency_code"] = str(
        primary_competency.get("competency_code") or ""
    )
    return working


def _cognitive_choices(client: Any, versions: list[dict[str, Any]]) -> list[str]:
    values = {
        str(row.get("cognitive_level_code") or "").strip()
        for row in versions
        if str(row.get("cognitive_level_code") or "").strip()
    }
    try:
        rows = _rows(
            client.table("assessment_cognitive_levels")
            .select("cognitive_level_code")
            .limit(100)
            .execute()
        )
        values.update(
            str(row.get("cognitive_level_code") or "").strip()
            for row in rows
            if str(row.get("cognitive_level_code") or "").strip()
        )
    except Exception:
        pass
    values.update({"NB", "TH", "VD"})
    return sorted(values)


def _render_preview(st: Any, working: dict[str, Any]) -> None:
    st.markdown(
        """
<style>
.qst-r2b-preview {
    font-family: "Times New Roman", serif;
    font-size: 24px;
    line-height: 1.5;
}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown("### Xem trước như học sinh")
    st.caption(
        f"Lớp {working.get('grade_level')} · "
        f"{working.get('question_type_code')} · "
        f"{working.get('cognitive_level_code')} · "
        f"{working.get('default_score')} điểm"
    )
    stimulus = str(working.get("stimulus_text") or "").strip()
    if stimulus:
        st.markdown(stimulus)
    prompt = str(working.get("prompt_text") or "").strip()
    if prompt:
        st.markdown(
            f'<div class="qst-r2b-preview"><b>Câu hỏi.</b> {prompt}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Bản nháp chưa có nội dung câu hỏi.")

    kind = str(working.get("question_type_code") or "")
    if kind == "MULTIPLE_CHOICE":
        for option in working.get("options") or []:
            st.markdown(
                f"**{option.get('option_code')}.** "
                f"{option.get('option_text') or '…'}"
            )
    elif kind == "TRUE_FALSE":
        for i, statement in enumerate(working.get("statements") or [], 1):
            st.markdown(
                f"**{i}.** {statement.get('statement_text') or '…'}"
            )
    elif kind in {"SHORT_RESPONSE", "SHORT_ANSWER"}:
        st.text_input(
            "Câu trả lời của học sinh",
            value="",
            disabled=True,
            key="qst_r2b_preview_short",
        )
    elif kind == "ESSAY":
        st.text_area(
            "Bài làm của học sinh",
            value="",
            disabled=True,
            height=140,
            key="qst_r2b_preview_essay",
        )

    with st.expander("Đáp án / lời giải dành cho giáo viên", expanded=False):
        if kind == "MULTIPLE_CHOICE":
            correct = [
                str(x.get("option_code"))
                for x in working.get("options") or []
                if bool(x.get("is_correct"))
            ]
            st.write("Đáp án:", ", ".join(correct) or "Chưa chọn")
        elif kind == "TRUE_FALSE":
            st.write(
                "; ".join(
                    f"{i}. {'Đúng' if x.get('correct_value') else 'Sai'}"
                    for i, x in enumerate(working.get("statements") or [], 1)
                )
            )
        elif kind in {"SHORT_RESPONSE", "SHORT_ANSWER"}:
            st.write(
                "Đáp án:",
                str(
                    (working.get("answer") or {}).get("exact_answer_text")
                    or "Chưa nhập"
                ),
            )

        solution = str(working.get("solution_text") or "").strip()
        if solution:
            st.markdown("**Lời giải**")
            st.markdown(solution)

        if kind == "ESSAY":
            steps = [
                x
                for x in (working.get("scoring_steps") or [])
                if str(x.get("step_description") or "").strip()
            ]
            if steps:
                st.dataframe(
                    [
                        {
                            "Bước": x.get("step_code"),
                            "Mô tả": x.get("step_description"),
                            "Điểm": x.get("step_score"),
                        }
                        for x in steps
                    ],
                    hide_index=True,
                    use_container_width=True,
                )


def _render_editor(
    st: Any,
    *,
    client: Any,
    versions: list[dict[str, Any]],
) -> None:
    working = dict(st.session_state.get(WORKING_KEY) or _new_working())
    status = str(working.get("source_status") or "NEW")

    if status == "APPROVED_SOURCE":
        st.info(
            "Đây là bản sửa làm việc từ câu APPROVED. "
            "Bản APPROVED gốc không bị thay đổi."
        )
    elif status in EDITABLE_STATUSES:
        st.info(
            f"Đã mở nội dung {status} vào vùng làm việc. "
            "R2B chưa ghi thay đổi trở lại CSDL."
        )
    else:
        st.caption("Bản nháp làm việc mới · chưa ghi CSDL.")

    left, right = st.columns([1, 2])

    current_grade = int(working.get("grade_level") or 6)
    if current_grade not in GRADES:
        current_grade = 6
    grade = left.selectbox(
        "Lớp",
        GRADES,
        index=GRADES.index(current_grade),
        key="qst_r2b_grade",
    )

    current_kind = str(
        working.get("question_type_code") or "MULTIPLE_CHOICE"
    )
    if current_kind not in QUESTION_TYPES:
        current_kind = "MULTIPLE_CHOICE"
    kind = left.selectbox(
        "Dạng câu hỏi",
        QUESTION_TYPES,
        index=QUESTION_TYPES.index(current_kind),
        key="qst_r2b_kind",
    )

    cognitive_choices = _cognitive_choices(client, versions)
    current_level = str(working.get("cognitive_level_code") or "NB")
    if current_level not in cognitive_choices:
        cognitive_choices.append(current_level)
        cognitive_choices.sort()
    cognitive = left.selectbox(
        "Mức độ nhận thức",
        cognitive_choices,
        index=cognitive_choices.index(current_level),
        key="qst_r2b_cognitive",
    )

    default_score = left.number_input(
        "Điểm",
        min_value=0.01,
        max_value=10.0,
        value=float(working.get("default_score") or 0.25),
        step=0.25,
        key="qst_r2b_score",
    )
    estimated_minutes = left.number_input(
        "Thời gian dự kiến (phút)",
        min_value=0.1,
        max_value=120.0,
        value=float(working.get("estimated_minutes") or 2.0),
        step=0.5,
        key="qst_r2b_minutes",
    )
    question_code = left.text_input(
        "Mã câu hỏi",
        value=str(working.get("question_code") or ""),
        help="R2C sẽ kiểm tra trùng mã trước khi ghi CSDL.",
        key="qst_r2b_code",
    )

    prompt = right.text_area(
        "Nội dung câu hỏi",
        value=str(working.get("prompt_text") or ""),
        height=170,
        key="qst_r2b_prompt",
    )
    stimulus = right.text_area(
        "Ngữ liệu / dữ kiện (nếu có)",
        value=str(working.get("stimulus_text") or ""),
        height=90,
        key="qst_r2b_stimulus",
    )
    instruction = right.text_input(
        "Hướng dẫn làm câu",
        value=str(working.get("instruction_text") or ""),
        key="qst_r2b_instruction",
    )

    st.markdown("#### Liên kết chuẩn")
    c1, c2 = st.columns(2)
    requirement = c1.text_input(
        "YCCĐ chính",
        value=str(working.get("primary_requirement_code") or ""),
        help="Gợi ý SGK → PPCT → YCCĐ sẽ nối ở bước sau.",
        key="qst_r2b_requirement",
    )
    competency = c2.text_input(
        "Năng lực chính",
        value=str(working.get("primary_competency_code") or ""),
        key="qst_r2b_competency",
    )

    options = [dict(x) for x in (working.get("options") or [])]
    while len(options) < 4:
        i = len(options)
        options.append(
            {
                "option_code": chr(ord("A") + i),
                "option_text": "",
                "is_correct": i == 0,
            }
        )

    statements = [dict(x) for x in (working.get("statements") or [])]
    while len(statements) < 4:
        i = len(statements)
        statements.append(
            {
                "statement_code": chr(ord("a") + i),
                "statement_text": "",
                "correct_value": True,
            }
        )

    answer = dict(working.get("answer") or {})
    scoring_steps = [dict(x) for x in (working.get("scoring_steps") or [])]
    while len(scoring_steps) < 4:
        i = len(scoring_steps) + 1
        scoring_steps.append(
            {
                "step_code": f"S{i}",
                "step_description": "",
                "step_score": 0.0,
            }
        )

    if kind == "MULTIPLE_CHOICE":
        st.markdown("#### Bốn phương án trả lời")
        correct_default = next(
            (
                str(x.get("option_code"))
                for x in options
                if bool(x.get("is_correct"))
            ),
            "A",
        )
        if correct_default not in {"A", "B", "C", "D"}:
            correct_default = "A"
        correct = st.radio(
            "Phương án đúng",
            ("A", "B", "C", "D"),
            index=("A", "B", "C", "D").index(correct_default),
            horizontal=True,
            key="qst_r2b_correct_option",
        )
        options = [
            {
                "option_code": code,
                "option_text": st.text_area(
                    f"Phương án {code}",
                    value=str(options[i].get("option_text") or ""),
                    height=75,
                    key=f"qst_r2b_option_{code}",
                ),
                "is_correct": code == correct,
            }
            for i, code in enumerate(("A", "B", "C", "D"))
        ]

    elif kind == "TRUE_FALSE":
        st.markdown("#### Bốn ý Đúng / Sai")
        updated_statements = []
        for i, code in enumerate(("a", "b", "c", "d")):
            cols = st.columns([4, 1])
            updated_statements.append(
                {
                    "statement_code": code,
                    "statement_text": cols[0].text_area(
                        f"Ý {code}",
                        value=str(statements[i].get("statement_text") or ""),
                        height=75,
                        key=f"qst_r2b_statement_{code}",
                    ),
                    "correct_value": cols[1].checkbox(
                        "Đúng",
                        value=bool(statements[i].get("correct_value")),
                        key=f"qst_r2b_statement_correct_{code}",
                    ),
                }
            )
        statements = updated_statements

    elif kind in {"SHORT_RESPONSE", "SHORT_ANSWER"}:
        st.markdown("#### Đáp án ngắn")
        answer["exact_answer_text"] = st.text_input(
            "Đáp án chính xác",
            value=str(answer.get("exact_answer_text") or ""),
            key="qst_r2b_exact_answer",
        )
        answer["answer_explanation"] = st.text_area(
            "Giải thích đáp án",
            value=str(answer.get("answer_explanation") or ""),
            height=100,
            key="qst_r2b_answer_explanation",
        )

    st.markdown("#### Lời giải")
    solution_text = st.text_area(
        "Lời giải chính",
        value=str(working.get("solution_text") or ""),
        height=180,
        key="qst_r2b_solution",
    )

    if kind == "ESSAY":
        st.markdown("#### Thang điểm")
        updated_steps = []
        for i in range(4):
            cols = st.columns([1, 5, 1.4])
            updated_steps.append(
                {
                    "step_code": cols[0].text_input(
                        "Bước",
                        value=str(
                            scoring_steps[i].get("step_code") or f"S{i + 1}"
                        ),
                        key=f"qst_r2b_step_code_{i}",
                    ),
                    "step_description": cols[1].text_input(
                        "Nội dung chấm",
                        value=str(
                            scoring_steps[i].get("step_description") or ""
                        ),
                        key=f"qst_r2b_step_description_{i}",
                    ),
                    "step_score": cols[2].number_input(
                        "Điểm",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(scoring_steps[i].get("step_score") or 0.0),
                        step=0.25,
                        key=f"qst_r2b_step_score_{i}",
                    ),
                }
            )
        scoring_steps = updated_steps

    updated = {
        **working,
        "grade_level": grade,
        "question_type_code": kind,
        "cognitive_level_code": cognitive,
        "default_score": default_score,
        "estimated_minutes": estimated_minutes,
        "question_code": question_code.strip(),
        "prompt_text": prompt.strip(),
        "stimulus_text": stimulus.strip(),
        "instruction_text": instruction.strip(),
        "primary_requirement_code": requirement.strip(),
        "primary_competency_code": competency.strip(),
        "options": options,
        "statements": statements,
        "answer": answer,
        "solution_text": solution_text.strip(),
        "scoring_steps": scoring_steps,
    }

    save_col, reset_col, db_col = st.columns(3)
    if save_col.button(
        "💾 Lưu bản nháp làm việc",
        type="primary",
        use_container_width=True,
        key="qst_r2b_save_working",
    ):
        st.session_state[WORKING_KEY] = updated
        st.success(
            "Đã lưu bản nháp trong phiên làm việc. "
            "R2B chưa ghi bất kỳ thay đổi nào vào CSDL."
        )

    if reset_col.button(
        "🧹 Tạo bản nháp mới",
        use_container_width=True,
        key="qst_r2b_reset_working",
    ):
        st.session_state[WORKING_KEY] = _new_working()
        st.rerun()

    db_col.button(
        "🗄️ Ghi vào Ngân hàng (R2C)",
        disabled=True,
        use_container_width=True,
        help=(
            "Chỉ bật sau khi lớp lưu transaction nhiều bảng được kiểm thử."
        ),
        key="qst_r2b_database_save_disabled",
    )

    st.divider()
    _render_preview(st, updated)


def render_question_studio(*, st: Any, client: Any, user_id: str) -> None:
    """Render Question Studio R2B without database mutation."""
    st.title("🧰 Xưởng câu hỏi")
    st.caption(
        "QST-R2B · Đọc Ngân hàng câu hỏi thật + biên soạn bản nháp làm việc "
        "+ preview. Không ghi CSDL ở phiên bản này."
    )
    st.info(
        "R2B giữ nguyên governance: APPROVED/PENDING_REVIEW không bị sửa trực "
        "tiếp. Ghi vào Ngân hàng chỉ được mở ở R2C sau khi transaction save "
        "được kiểm thử."
    )

    if client is None:
        st.error("Chưa có kết nối Supabase.")
        return

    try:
        versions = _load_versions(client, user_id)
    except Exception as exc:
        st.error(f"Không tải được Ngân hàng câu hỏi: {exc}")
        return

    counts: dict[str, int] = {}
    for row in versions:
        status = str(row.get("review_status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1

    metrics = st.columns(4)
    metrics[0].metric("Tổng version", len(versions))
    metrics[1].metric("DRAFT", counts.get("DRAFT", 0))
    metrics[2].metric("Cần sửa", counts.get("REVISION_REQUIRED", 0))
    metrics[3].metric("APPROVED", counts.get("APPROVED", 0))

    bank_tab, editor_tab, preview_tab = st.tabs(
        ["📚 Câu hỏi của tôi", "✍️ Soạn câu hỏi", "👁️ Preview"]
    )

    with bank_tab:
        if not versions:
            st.info(
                "Tài khoản chưa có câu hỏi Toán 6–9. "
                "Bạn có thể tạo bản nháp làm việc mới."
            )
        else:
            f1, f2, f3 = st.columns(3)
            grade_filter = f1.selectbox(
                "Lọc lớp",
                ("Tất cả", 6, 7, 8, 9),
                key="qst_r2b_filter_grade",
            )
            statuses = sorted(
                {
                    str(row.get("review_status") or "")
                    for row in versions
                    if str(row.get("review_status") or "")
                }
            )
            status_filter = f2.selectbox(
                "Lọc trạng thái",
                ["Tất cả", *statuses],
                key="qst_r2b_filter_status",
            )
            types = sorted(
                {
                    str(row.get("question_type_code") or "")
                    for row in versions
                    if str(row.get("question_type_code") or "")
                }
            )
            type_filter = f3.selectbox(
                "Lọc dạng",
                ["Tất cả", *types],
                key="qst_r2b_filter_type",
            )

            filtered = []
            for row in versions:
                item = dict(row.get("item") or {})
                if (
                    grade_filter != "Tất cả"
                    and int(item.get("grade_level") or 0) != int(grade_filter)
                ):
                    continue
                if (
                    status_filter != "Tất cả"
                    and str(row.get("review_status")) != status_filter
                ):
                    continue
                if (
                    type_filter != "Tất cả"
                    and str(row.get("question_type_code")) != type_filter
                ):
                    continue
                filtered.append(row)

            st.dataframe(
                [
                    {
                        "Mã câu": (row.get("item") or {}).get("question_code"),
                        "Lớp": (row.get("item") or {}).get("grade_level"),
                        "Version": row.get("version_number"),
                        "Trạng thái": row.get("review_status"),
                        "Dạng": row.get("question_type_code"),
                        "Mức độ": row.get("cognitive_level_code"),
                        "Điểm": row.get("default_score"),
                        "Câu hỏi": row.get("prompt_text"),
                    }
                    for row in filtered
                ],
                hide_index=True,
                use_container_width=True,
            )

            if filtered:
                lookup = {
                    str(row["question_version_id"]): row for row in filtered
                }
                selected = st.selectbox(
                    "Chọn một version",
                    list(lookup),
                    format_func=lambda version_id: (
                        f"{(lookup[version_id].get('item') or {}).get('question_code', '')}"
                        f" · v{lookup[version_id].get('version_number')}"
                        f" · {lookup[version_id].get('review_status')}"
                        f" · {str(lookup[version_id].get('prompt_text') or '')[:85]}"
                    ),
                    key="qst_r2b_selected_version",
                )
                row = lookup[selected]
                try:
                    detail = _load_detail(client, selected)
                except Exception as exc:
                    st.error(f"Không tải đủ chi tiết câu hỏi: {exc}")
                    detail = {}

                st.markdown("#### Nội dung")
                st.markdown(str(row.get("prompt_text") or ""))
                status = str(row.get("review_status") or "")
                action = st.columns(3)[0]

                if status in EDITABLE_STATUSES:
                    if action.button(
                        "✍️ Mở để chỉnh",
                        use_container_width=True,
                        key=f"qst_r2b_edit_{selected}",
                    ):
                        st.session_state[WORKING_KEY] = _working_from_version(
                            row, detail, as_revision=False
                        )
                        st.success(
                            "Đã đưa nội dung vào vùng làm việc. "
                            "Chưa ghi thay đổi vào CSDL."
                        )
                elif status == "APPROVED":
                    if action.button(
                        "♻️ Tạo bản sửa từ câu này",
                        use_container_width=True,
                        key=f"qst_r2b_revision_{selected}",
                    ):
                        st.session_state[WORKING_KEY] = _working_from_version(
                            row, detail, as_revision=True
                        )
                        st.success(
                            "Đã tạo bản sửa làm việc từ APPROVED. "
                            "Bản APPROVED gốc không thay đổi."
                        )
                else:
                    action.button(
                        "🔒 Chỉ xem",
                        disabled=True,
                        use_container_width=True,
                        key=f"qst_r2b_readonly_{selected}",
                    )

                with st.expander(
                    "Chi tiết đáp án / lời giải / liên kết",
                    expanded=False,
                ):
                    for title, key in (
                        ("Phương án", "options"),
                        ("Mệnh đề", "statements"),
                        ("Đáp án", "answers"),
                        ("Lời giải", "solutions"),
                        ("Thang điểm", "scoring_steps"),
                        ("YCCĐ", "requirements"),
                        ("Năng lực", "competencies"),
                    ):
                        rows = detail.get(key) or []
                        if rows:
                            st.markdown(f"**{title}**")
                            st.dataframe(
                                rows,
                                hide_index=True,
                                use_container_width=True,
                            )

        if st.button(
            "➕ Tạo câu hỏi mới",
            type="primary",
            key="qst_r2b_new_question",
        ):
            st.session_state[WORKING_KEY] = _new_working()
            st.success(
                "Đã tạo vùng làm việc mới. Sang tab Soạn câu hỏi để nhập."
            )

    with editor_tab:
        _render_editor(st, client=client, versions=versions)

    with preview_tab:
        _render_preview(
            st,
            dict(st.session_state.get(WORKING_KEY) or _new_working()),
        )
