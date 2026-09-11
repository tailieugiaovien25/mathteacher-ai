"""Credential-free Streamlit UI for the Mathematics 6 MVP workflow."""

from __future__ import annotations

from json import JSONDecodeError, dumps, loads
from typing import Any, Mapping

from assessment_generation_v2.services.math6_mvp_workflow import (
    ADMIN,
    APPROVED,
    DRAFT,
    PENDING_REVIEW,
    PUBLISHED,
    REVISION_REQUIRED,
    InMemoryMath6MvpWorkflow,
    Math6AssessmentConfig,
)


SESSION_WORKFLOW_KEY = "math6_mvp_demo_workflow"
SESSION_BUNDLE_KEY = "math6_mvp_demo_bundle"
SESSION_CONFIG_KEY = "math6_mvp_assessment_config"


def sample_question_rows() -> tuple[dict[str, object], ...]:
    """Return a fresh, deterministic Mathematics 6 sample batch."""

    return (
        {
            "question_code": "M6-NAT-001",
            "stem": "Tính 27 + 35.",
            "answer": "62",
            "score": "1",
            "topic_code": "M6-NATURAL-NUMBERS",
            "cognitive_level": "KNOW",
        },
        {
            "question_code": "M6-NAT-002",
            "stem": "Tìm số tự nhiên x biết x - 18 = 24.",
            "answer": "x = 42",
            "score": "1",
            "topic_code": "M6-NATURAL-NUMBERS",
            "cognitive_level": "UNDERSTAND",
        },
    )


def sample_import_json() -> str:
    return dumps(
        sample_question_rows(),
        ensure_ascii=False,
        indent=2,
    )


def parse_question_import_json(
    content: str,
) -> tuple[dict[str, object], ...]:
    """Parse only a JSON array of question objects; perform no mutation."""

    try:
        value = loads(str(content))
    except JSONDecodeError as error:
        raise ValueError("JSON nhập câu hỏi không hợp lệ.") from error
    if not isinstance(value, list) or not value:
        raise ValueError("Dữ liệu nhập phải là một mảng JSON không rỗng.")
    if any(not isinstance(row, Mapping) for row in value):
        raise ValueError("Mỗi phần tử nhập phải là một JSON object.")
    return tuple(dict(row) for row in value)


def workflow_status(
    workflow: InMemoryMath6MvpWorkflow,
) -> dict[str, int | bool]:
    """Build a UI-safe status summary without exposing mutable storage."""

    questions = workflow.questions
    blueprints = workflow.blueprints
    exams = workflow.exams
    packages = workflow.published_packages
    return {
        "question_count": len(questions),
        "question_pending": len(workflow.question_review_queue),
        "question_locked": sum(item.locked for item in questions),
        "blueprint_count": len(blueprints),
        "blueprint_pending": len(workflow.blueprint_review_queue),
        "blueprint_ready": any(
            item.review_status == APPROVED and item.locked
            for item in blueprints
        ),
        "exam_count": len(exams),
        "exam_pending": len(workflow.exam_review_queue),
        "exam_approved": any(
            item.review_status == APPROVED for item in exams
        ),
        "published_count": len(packages),
        "can_create_blueprint": sum(item.locked for item in questions) >= 2,
    }


def _question_rows(
    workflow: InMemoryMath6MvpWorkflow,
) -> list[dict[str, object]]:
    return [
        {
            "Mã": item.question_code,
            "Nội dung": item.stem,
            "Đáp án": item.answer,
            "Điểm": str(item.score),
            "Chủ đề": item.topic_code,
            "Mức độ": item.cognitive_level,
            "Duyệt": item.review_status,
            "Đã khóa": item.locked,
        }
        for item in workflow.questions
    ]


def _blueprint_rows(
    workflow: InMemoryMath6MvpWorkflow,
) -> list[dict[str, object]]:
    return [
        {
            "Mã": item.blueprint_code,
            "Tên": item.title,
            "Số câu": item.question_count,
            "Tổng điểm": str(item.total_score),
            "Chủ đề": ", ".join(item.topic_codes),
            "Duyệt": item.review_status,
            "Đã khóa": item.locked,
        }
        for item in workflow.blueprints
    ]


def _exam_rows(
    workflow: InMemoryMath6MvpWorkflow,
) -> list[dict[str, object]]:
    return [
        {
            "Mã": item.exam_code,
            "Tên": item.title,
            "Ma trận": item.blueprint_code,
            "Câu hỏi": ", ".join(item.question_codes),
            "Trạng thái": item.review_status,
        }
        for item in workflow.exams
    ]


def _rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _show_error(st: Any, operation: str, error: Exception) -> None:
    st.error(f"{operation}: {error}")


def _render_summary(st: Any, workflow: InMemoryMath6MvpWorkflow) -> None:
    status = workflow_status(workflow)
    columns = st.columns(4)
    columns[0].metric(
        "Câu hỏi đã khóa",
        f"{status['question_locked']}/{status['question_count']}",
    )
    columns[1].metric(
        "Ma trận sẵn sàng",
        "Có" if status["blueprint_ready"] else "Chưa",
    )
    columns[2].metric(
        "Đề chờ duyệt",
        status["exam_pending"],
    )
    columns[3].metric(
        "Gói đã xuất bản",
        status["published_count"],
    )


def _assessment_config_row(
    config: Math6AssessmentConfig,
) -> dict[str, object]:
    type_labels = {
        "REGULAR": "Kiá»ƒm tra thÆ°á»ng xuyÃªn",
        "MIDTERM": "Giá»¯a há»c ká»³",
        "FINAL": "Cuá»‘i há»c ká»³",
    }
    semester_labels = {
        "HK1": "Há»c ká»³ I",
        "HK2": "Há»c ká»³ II",
    }
    return {
        "MÃ´n": "ToÃ¡n",
        "Khá»‘i": 6,
        "MÃ£ cáº¥u hÃ¬nh": config.config_code,
        "TÃªn bÃ i kiá»ƒm tra": config.title,
        "NÄƒm há»c": config.academic_year,
        "Há»c ká»³": semester_labels.get(config.semester, config.semester),
        "Loáº¡i kiá»ƒm tra": type_labels.get(config.test_type, config.test_type),
        "Thá»i gian (phÃºt)": config.duration_minutes,
        "Tá»•ng Ä‘iá»ƒm": str(config.total_score),
        "Sá»‘ mÃ£ Ä‘á»": config.variant_count,
    }


def _render_assessment_config(
    st: Any,
    *,
    role: str,
) -> None:
    st.header("0. Cáº¥u hÃ¬nh bÃ i kiá»ƒm tra")
    st.caption(
        "MÃ´n ToÃ¡n Â· Lá»›p 6. Cáº¥u hÃ¬nh hiá»‡n chá»‰ lÆ°u trong phiÃªn "
        "Streamlit; chÆ°a ghi Supabase vÃ  chÆ°a rÃ ng buá»™c ma tráº­n/Ä‘á»."
    )

    config = st.session_state.get(SESSION_CONFIG_KEY)
    if config is not None and not isinstance(config, Math6AssessmentConfig):
        st.session_state.pop(SESSION_CONFIG_KEY, None)
        config = None

    if role == "admin":
        if config is None:
            st.info("GiÃ¡o viÃªn chÆ°a lÆ°u cáº¥u hÃ¬nh bÃ i kiá»ƒm tra trong phiÃªn nÃ y.")
        else:
            st.dataframe(
                [_assessment_config_row(config)],
                hide_index=True,
                use_container_width=True,
            )
        return

    semester_options = ("HK1", "HK2")
    test_type_options = ("REGULAR", "MIDTERM", "FINAL")
    test_type_labels = {
        "REGULAR": "Kiá»ƒm tra thÆ°á»ng xuyÃªn",
        "MIDTERM": "Giá»¯a há»c ká»³",
        "FINAL": "Cuá»‘i há»c ká»³",
    }
    current_semester = (
        config.semester
        if isinstance(config, Math6AssessmentConfig)
        and config.semester in semester_options
        else "HK1"
    )
    current_test_type = (
        config.test_type
        if isinstance(config, Math6AssessmentConfig)
        and config.test_type in test_type_options
        else "MIDTERM"
    )

    with st.form("math6_mvp_assessment_config"):
        config_code = st.text_input(
            "MÃ£ cáº¥u hÃ¬nh",
            value=(config.config_code if isinstance(config, Math6AssessmentConfig) else "M6-2026-HK1-MIDTERM"),
        )
        title = st.text_input(
            "TÃªn bÃ i kiá»ƒm tra",
            value=(config.title if isinstance(config, Math6AssessmentConfig) else "Kiá»ƒm tra giá»¯a há»c ká»³ I - ToÃ¡n 6"),
        )
        academic_year = st.text_input(
            "NÄƒm há»c",
            value=(config.academic_year if isinstance(config, Math6AssessmentConfig) else "2026-2027"),
        )
        semester = st.selectbox(
            "Há»c ká»³",
            semester_options,
            index=semester_options.index(current_semester),
            format_func=lambda value: {"HK1": "Há»c ká»³ I", "HK2": "Há»c ká»³ II"}[value],
        )
        test_type = st.selectbox(
            "Loáº¡i kiá»ƒm tra",
            test_type_options,
            index=test_type_options.index(current_test_type),
            format_func=lambda value: test_type_labels[value],
        )
        duration_minutes = st.number_input(
            "Thá»i gian lÃ m bÃ i (phÃºt)",
            min_value=1,
            value=(config.duration_minutes if isinstance(config, Math6AssessmentConfig) else 90),
            step=1,
        )
        total_score = st.number_input(
            "Tá»•ng Ä‘iá»ƒm",
            min_value=0.25,
            value=(float(config.total_score) if isinstance(config, Math6AssessmentConfig) else 10.0),
            step=0.25,
        )
        variant_count = st.number_input(
            "Sá»‘ mÃ£ Ä‘á» tÆ°Æ¡ng Ä‘Æ°Æ¡ng",
            min_value=1,
            value=(config.variant_count if isinstance(config, Math6AssessmentConfig) else 2),
            step=1,
        )
        save_config = st.form_submit_button(
            "LÆ°u cáº¥u hÃ¬nh bÃ i kiá»ƒm tra",
            type="primary",
            use_container_width=True,
        )

    if save_config:
        try:
            saved = Math6AssessmentConfig(
                config_code=config_code,
                title=title,
                academic_year=academic_year,
                semester=semester,
                test_type=test_type,
                duration_minutes=duration_minutes,
                total_score=total_score,
                variant_count=variant_count,
            )
        except Exception as error:
            _show_error(st, "KhÃ´ng thá»ƒ lÆ°u cáº¥u hÃ¬nh bÃ i kiá»ƒm tra", error)
        else:
            st.session_state[SESSION_CONFIG_KEY] = saved
            st.success("ÄÃ£ lÆ°u cáº¥u hÃ¬nh bÃ i kiá»ƒm tra trong phiÃªn hiá»‡n táº¡i.")
            _rerun(st)

    config = st.session_state.get(SESSION_CONFIG_KEY)
    if isinstance(config, Math6AssessmentConfig):
        st.dataframe(
            [_assessment_config_row(config)],
            hide_index=True,
            use_container_width=True,
        )


def _render_question_bank(
    st: Any,
    workflow: InMemoryMath6MvpWorkflow,
    *,
    role: str,
) -> None:
    st.header("1. Ngân hàng câu hỏi")
    st.caption(
        "Tạo hoặc import câu hỏi, gửi duyệt, ADMIN duyệt rồi khóa. "
        "Câu đã khóa không thể chỉnh sửa."
    )

    seed_column, reset_column = st.columns(2)
    if seed_column.button(
        "Nạp bộ 2 câu Toán 6 mẫu",
        use_container_width=True,
        disabled=bool(workflow.questions),
    ):
        try:
            workflow.import_questions(sample_question_rows())
        except Exception as error:
            _show_error(st, "Không thể nạp bộ mẫu", error)
        else:
            st.success("Đã nạp bộ câu hỏi mẫu.")
            _rerun(st)

    if reset_column.button(
        "Xóa phiên demo và làm lại",
        use_container_width=True,
    ):
        st.session_state[SESSION_WORKFLOW_KEY] = InMemoryMath6MvpWorkflow()
        st.session_state.pop(SESSION_BUNDLE_KEY, None)
        st.session_state.pop(SESSION_CONFIG_KEY, None)
        _rerun(st)

    with st.expander("Import câu hỏi bằng JSON", expanded=False):
        import_content = st.text_area(
            "Mảng câu hỏi JSON",
            value=sample_import_json(),
            height=260,
            key="math6_mvp_import_json",
        )
        if st.button(
            "Import JSON",
            key="math6_mvp_import_submit",
            use_container_width=True,
        ):
            try:
                rows = parse_question_import_json(import_content)
                workflow.import_questions(rows)
            except Exception as error:
                _show_error(st, "Import thất bại", error)
            else:
                st.success(f"Đã import {len(rows)} câu hỏi.")
                _rerun(st)

    with st.expander("Tạo một câu hỏi", expanded=False):
        with st.form("math6_mvp_create_question"):
            code = st.text_input("Mã câu hỏi", value="M6-NAT-003")
            stem = st.text_area("Nội dung câu hỏi")
            answer = st.text_area("Đáp án")
            score = st.number_input(
                "Điểm", min_value=0.25, value=1.0, step=0.25
            )
            topic_code = st.text_input(
                "Mã chủ đề", value="M6-NATURAL-NUMBERS"
            )
            cognitive_level = st.selectbox(
                "Mức độ", ("KNOW", "UNDERSTAND", "APPLY")
            )
            create_submitted = st.form_submit_button(
                "Tạo câu hỏi", use_container_width=True
            )
        if create_submitted:
            try:
                workflow.create_question(
                    question_code=code,
                    stem=stem,
                    answer=answer,
                    score=score,
                    topic_code=topic_code,
                    cognitive_level=cognitive_level,
                )
            except Exception as error:
                _show_error(st, "Không thể tạo câu hỏi", error)
            else:
                st.success("Đã tạo câu hỏi ở trạng thái DRAFT.")
                _rerun(st)

    if workflow.questions:
        st.dataframe(
            _question_rows(workflow),
            hide_index=True,
            use_container_width=True,
        )

    editable = tuple(
        item for item in workflow.questions
        if not item.locked
        and item.review_status in {DRAFT, REVISION_REQUIRED}
    )
    if editable:
        st.subheader("Chỉnh sửa và gửi duyệt")
        editable_by_code = {
            item.question_code: item for item in editable
        }
        selected_code = st.selectbox(
            "Câu hỏi có thể chỉnh sửa",
            tuple(editable_by_code),
            key="math6_mvp_edit_question_code",
        )
        selected = editable_by_code[selected_code]
        with st.form("math6_mvp_edit_question"):
            edited_stem = st.text_area("Nội dung", value=selected.stem)
            edited_answer = st.text_area("Đáp án", value=selected.answer)
            edit_columns = st.columns(2)
            save_edit = edit_columns[0].form_submit_button(
                "Lưu chỉnh sửa", use_container_width=True
            )
            submit_review = edit_columns[1].form_submit_button(
                "Gửi duyệt", use_container_width=True
            )
        try:
            if save_edit:
                workflow.edit_question(
                    selected_code,
                    stem=edited_stem,
                    answer=edited_answer,
                )
                st.success("Đã lưu chỉnh sửa.")
                _rerun(st)
            if submit_review:
                if (
                    edited_stem.strip() != selected.stem
                    or edited_answer.strip() != selected.answer
                ):
                    workflow.edit_question(
                        selected_code,
                        stem=edited_stem,
                        answer=edited_answer,
                    )
                workflow.submit_question(selected_code)
                st.success("Đã đưa câu hỏi vào hàng đợi ADMIN.")
                _rerun(st)
        except Exception as error:
            _show_error(st, "Không thể cập nhật câu hỏi", error)

    if role == "admin" and workflow.question_review_queue:
        st.subheader("ADMIN duyệt câu hỏi")
        pending_codes = tuple(
            item.question_code for item in workflow.question_review_queue
        )
        pending_code = st.selectbox(
            "Câu hỏi chờ duyệt",
            pending_codes,
            key="math6_mvp_pending_question",
        )
        review_note = st.text_input(
            "Nhận xét khi yêu cầu sửa",
            key="math6_mvp_question_review_note",
        )
        review_columns = st.columns(2)
        if review_columns[0].button(
            "Phê duyệt câu hỏi",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.review_question(
                    pending_code, role=ADMIN, approve=True
                )
            except Exception as error:
                _show_error(st, "Không thể duyệt câu hỏi", error)
            else:
                _rerun(st)
        if review_columns[1].button(
            "Yêu cầu chỉnh sửa",
            use_container_width=True,
            disabled=not review_note.strip(),
        ):
            try:
                workflow.review_question(
                    pending_code,
                    role=ADMIN,
                    approve=False,
                    note=review_note,
                )
            except Exception as error:
                _show_error(st, "Không thể trả câu hỏi", error)
            else:
                _rerun(st)

    lockable = tuple(
        item for item in workflow.questions
        if item.review_status == APPROVED and not item.locked
    )
    if role == "admin" and lockable:
        st.subheader("ADMIN khóa câu hỏi")
        lock_code = st.selectbox(
            "Câu hỏi đã duyệt",
            tuple(item.question_code for item in lockable),
            key="math6_mvp_lock_question",
        )
        if st.button(
            "Khóa câu hỏi",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.lock_question(lock_code, role=ADMIN)
            except Exception as error:
                _show_error(st, "Không thể khóa câu hỏi", error)
            else:
                _rerun(st)


def _render_blueprint(
    st: Any,
    workflow: InMemoryMath6MvpWorkflow,
    *,
    role: str,
) -> None:
    st.header("2. Ma trận")
    status = workflow_status(workflow)
    if not workflow.blueprints:
        with st.form("math6_mvp_create_blueprint"):
            code = st.text_input("Mã ma trận", value="M6-DEMO-BP-001")
            title = st.text_input(
                "Tên ma trận", value="Ma trận minh họa Toán 6"
            )
            question_count = st.number_input(
                "Số câu", min_value=1, value=2, step=1
            )
            total_score = st.number_input(
                "Tổng điểm", min_value=0.25, value=2.0, step=0.25
            )
            topic_codes = st.text_input(
                "Mã chủ đề",
                value="M6-NATURAL-NUMBERS",
                help="Phân cách nhiều mã bằng dấu phẩy.",
            )
            create_blueprint = st.form_submit_button(
                "Tạo ma trận",
                type="primary",
                use_container_width=True,
                disabled=not bool(status["can_create_blueprint"]),
            )
        if not status["can_create_blueprint"]:
            st.info("Cần ít nhất 2 câu hỏi đã khóa trước khi tạo ma trận.")
        if create_blueprint:
            try:
                workflow.create_blueprint(
                    blueprint_code=code,
                    title=title,
                    question_count=int(question_count),
                    total_score=total_score,
                    topic_codes=tuple(
                        item.strip() for item in topic_codes.split(",")
                        if item.strip()
                    ),
                )
            except Exception as error:
                _show_error(st, "Không thể tạo ma trận", error)
            else:
                _rerun(st)

    if not workflow.blueprints:
        return
    st.dataframe(
        _blueprint_rows(workflow),
        hide_index=True,
        use_container_width=True,
    )
    blueprint = workflow.blueprints[0]
    if blueprint.review_status in {DRAFT, REVISION_REQUIRED}:
        if st.button(
            "Gửi ma trận để ADMIN duyệt",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.submit_blueprint(blueprint.blueprint_code)
            except Exception as error:
                _show_error(st, "Không thể gửi ma trận", error)
            else:
                _rerun(st)
    elif blueprint.review_status == PENDING_REVIEW:
        st.warning("Ma trận đang chờ ADMIN duyệt.")
        if role != "admin":
            return
        note = st.text_input(
            "Nhận xét ma trận khi yêu cầu sửa",
            key="math6_mvp_blueprint_note",
        )
        columns = st.columns(2)
        if columns[0].button(
            "ADMIN phê duyệt và khóa ma trận",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.review_blueprint(
                    blueprint.blueprint_code, role=ADMIN, approve=True
                )
            except Exception as error:
                _show_error(st, "Không thể duyệt ma trận", error)
            else:
                _rerun(st)
        if columns[1].button(
            "Yêu cầu sửa ma trận",
            use_container_width=True,
            disabled=not note.strip(),
        ):
            try:
                workflow.review_blueprint(
                    blueprint.blueprint_code,
                    role=ADMIN,
                    approve=False,
                    note=note,
                )
            except Exception as error:
                _show_error(st, "Không thể trả ma trận", error)
            else:
                _rerun(st)
    elif blueprint.review_status == APPROVED and blueprint.locked:
        st.success("Ma trận đã được ADMIN duyệt và khóa.")


def _render_exam(
    st: Any,
    workflow: InMemoryMath6MvpWorkflow,
    *,
    role: str,
) -> None:
    st.header("3. Tạo, duyệt và xuất bản đề")
    ready_blueprints = tuple(
        item for item in workflow.blueprints
        if item.review_status == APPROVED and item.locked
    )
    if not workflow.exams:
        with st.form("math6_mvp_generate_exam"):
            exam_code = st.text_input("Mã đề nội bộ", value="M6-DEMO-001")
            title = st.text_input(
                "Tên đề", value="Đề minh họa Toán 6"
            )
            blueprint_codes = tuple(
                item.blueprint_code for item in ready_blueprints
            )
            blueprint_code = st.selectbox(
                "Ma trận đã duyệt",
                blueprint_codes or ("Chưa có ma trận sẵn sàng",),
            )
            generate = st.form_submit_button(
                "Tạo đề từ câu hỏi đã khóa",
                type="primary",
                use_container_width=True,
                disabled=not bool(ready_blueprints),
            )
        if not ready_blueprints:
            st.info("Cần ma trận đã được ADMIN duyệt và khóa.")
        if generate:
            try:
                workflow.generate_exam(
                    exam_code=exam_code,
                    title=title,
                    blueprint_code=blueprint_code,
                )
            except Exception as error:
                _show_error(st, "Không thể tạo đề", error)
            else:
                _rerun(st)

    if not workflow.exams:
        return
    st.dataframe(
        _exam_rows(workflow),
        hide_index=True,
        use_container_width=True,
    )
    exam = workflow.exams[0]
    if exam.review_status in {DRAFT, REVISION_REQUIRED}:
        if st.button(
            "Gửi đề để ADMIN duyệt",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.submit_exam(exam.exam_code)
            except Exception as error:
                _show_error(st, "Không thể gửi đề", error)
            else:
                _rerun(st)
    elif exam.review_status == PENDING_REVIEW:
        st.warning("Đề đang chờ ADMIN duyệt.")
        if role != "admin":
            return
        note = st.text_input(
            "Nhận xét đề khi yêu cầu sửa",
            key="math6_mvp_exam_note",
        )
        columns = st.columns(2)
        if columns[0].button(
            "ADMIN phê duyệt đề",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.review_exam(
                    exam.exam_code, role=ADMIN, approve=True
                )
            except Exception as error:
                _show_error(st, "Không thể duyệt đề", error)
            else:
                _rerun(st)
        if columns[1].button(
            "Yêu cầu sửa đề",
            use_container_width=True,
            disabled=not note.strip(),
        ):
            try:
                workflow.review_exam(
                    exam.exam_code,
                    role=ADMIN,
                    approve=False,
                    note=note,
                )
            except Exception as error:
                _show_error(st, "Không thể trả đề", error)
            else:
                _rerun(st)
    elif exam.review_status == APPROVED:
        st.success("Đề đã được ADMIN duyệt, có thể xuất bản.")
        if role != "admin":
            return
        variant_code = st.text_input(
            "Mã đề", value="101", key="math6_mvp_variant_code"
        )
        if st.button(
            "ADMIN xuất bản, tạo snapshot và khóa mã đề",
            type="primary",
            use_container_width=True,
        ):
            try:
                workflow.publish_exam(
                    exam.exam_code,
                    role=ADMIN,
                    variant_code=variant_code,
                )
                st.session_state[SESSION_BUNDLE_KEY] = (
                    workflow.export_zip(exam.exam_code)
                )
            except Exception as error:
                _show_error(st, "Không thể xuất bản đề", error)
            else:
                _rerun(st)
    elif exam.review_status == PUBLISHED:
        st.success("Đề đã xuất bản; snapshot và mã đề đang ở trạng thái khóa.")

    packages = workflow.published_packages
    if packages:
        package = packages[0]
        bundle = st.session_state.get(SESSION_BUNDLE_KEY)
        if not isinstance(bundle, bytes):
            try:
                bundle = workflow.export_zip(package.exam_code)
                st.session_state[SESSION_BUNDLE_KEY] = bundle
            except Exception as error:
                _show_error(st, "Không thể dựng lại ZIP", error)
                return
        st.code(f"SHA-256 snapshot: {package.snapshot_hash}")
        st.download_button(
            "Tải ZIP đề Toán 6",
            data=bundle,
            file_name="math6-mvp-demo.zip",
            mime="application/zip",
            use_container_width=True,
        )


def render_math6_mvp_demo_role(
    st: Any,
    *,
    role: str,
) -> None:
    """Render the Math 6 MVP with deterministic Teacher/ADMIN controls."""

    if role not in {"teacher", "admin"}:
        raise ValueError(f"invalid role: {role}")

    st.title("MVP tạo đề Toán 6 · Demo không credential")
    st.caption(
        "Dữ liệu chỉ tồn tại trong phiên Streamlit hiện tại; "
        "không kết nối Supabase và không thay đổi dữ liệu production."
    )

    workflow = st.session_state.get(SESSION_WORKFLOW_KEY)
    if not isinstance(workflow, InMemoryMath6MvpWorkflow):
        workflow = InMemoryMath6MvpWorkflow()
        st.session_state[SESSION_WORKFLOW_KEY] = workflow

    _render_summary(st, workflow)
    _render_assessment_config(st, role=role)
    st.divider()
    _render_question_bank(st, workflow, role=role)
    st.divider()
    _render_blueprint(st, workflow, role=role)
    st.divider()
    _render_exam(st, workflow, role=role)


def render_math6_mvp_demo(st: Any) -> None:
    """Render the complete legacy demo with ADMIN capabilities."""

    render_math6_mvp_demo_role(st, role="admin")


__all__ = [
    "SESSION_BUNDLE_KEY",
    "SESSION_CONFIG_KEY",
    "SESSION_WORKFLOW_KEY",
    "parse_question_import_json",
    "render_math6_mvp_demo",
    "render_math6_mvp_demo_role",
    "sample_import_json",
    "sample_question_rows",
    "workflow_status",
]
