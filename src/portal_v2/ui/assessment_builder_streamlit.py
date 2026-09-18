"""Source-only Streamlit prototype for the Mathematics 6-9 assessment builder.

A2-MATH69-C5 keeps the page persistence-free and production-route-free while
adding automatic PPCT scope suggestion when normalized PPCT rows are supplied
through the existing Streamlit session boundary. The page never discovers files,
calls Supabase, or invents assessment boundaries.
"""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    COGNITIVE_LEVEL_LABELS,
    QUESTION_TYPE_LABELS,
    SUPPORTED_GRADES,
    AssessmentBuilderCognitiveAllocation,
    AssessmentBuilderConfiguration,
    AssessmentBuilderConfigurationError,
    AssessmentBuilderSection,
)
from assessment_generation_v2.services.assessment_builder_matrix_preview_service import (
    AssessmentBuilderMatrixPreviewService,
)
from assessment_generation_v2.services.assessment_ppct_scope_suggestion_service import (
    AssessmentPpctScopeSuggestion,
    AssessmentPpctScopeSuggestionError,
    AssessmentPpctScopeSuggestionService,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from portal_v2.runtime.assessment_ppct_session_bridge import (
    ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY,
    ASSESSMENT_PPCT_ROWS_SESSION_KEY,
    AssessmentPpctRuntimeEvidence,
)
from portal_v2.runtime.assessment_builder_governed_defaults_runtime import (
    AssessmentBuilderGovernedDefaultsRuntime,
    AssessmentBuilderGovernedDefaultsRuntimeError,
)


ASSESSMENT_BUILDER_TITLE = "Tạo đề kiểm tra Toán 6–9"
ASSESSMENT_BUILDER_READ_ONLY = True
ASSESSMENT_BUILDER_DATABASE_WRITE = False
ASSESSMENT_BUILDER_PRODUCTION_ROUTE_CHANGE = False

_ASSESSMENT_TYPE_LABELS = {
    "REGULAR": "Kiểm tra thường xuyên",
    "MIDTERM": "Kiểm tra giữa học kỳ",
    "FINAL": "Kiểm tra cuối học kỳ",
}
_SECTION_DEFAULTS = {
    "MULTIPLE_CHOICE": ("MCQ", 12, 12, 3.0),
    "TRUE_FALSE": ("TF", 2, 8, 2.0),
    "SHORT_RESPONSE": ("SHORT", 4, 4, 2.0),
    "ESSAY": ("ESSAY", 2, 2, 3.0),
}
_COGNITIVE_DEFAULTS = {
    "KNOW": 40.0,
    "UNDERSTAND": 30.0,
    "APPLY": 30.0,
}


def _codes(value: object) -> tuple[str, ...]:
    text = str(value or "")
    return tuple(
        code
        for code in (
            item.strip() for item in text.replace("\n", ",").split(",")
        )
        if code
    )


# Backward-compatible alias retained for the C5 UI contract tests and any
# local callers that imported the private session-key name.
_ASSESSMENT_PPCT_ROWS_SESSION_KEY = ASSESSMENT_PPCT_ROWS_SESSION_KEY
_ASSESSMENT_SCOPE_CONFIRMATION_SESSION_KEY = "assessment_ppct_scope_confirmation"


def _ppct_rows_from_session(
    st: object,
) -> tuple[PPCTRow, ...] | None:
    """Read normalized PPCT rows supplied by the outer runtime, if present."""
    session_state = getattr(
        st,
        "session_state",
        None,
    )

    if session_state is None:
        return None

    try:
        value = session_state.get(
            ASSESSMENT_PPCT_ROWS_SESSION_KEY
        )
    except AttributeError:
        return None

    if value is None:
        return None

    if not isinstance(value, tuple):
        raise TypeError(
            "assessment_ppct_rows session value must be a tuple"
        )

    if not all(
        isinstance(row, PPCTRow)
        for row in value
    ):
        raise TypeError(
            "assessment_ppct_rows must contain PPCTRow values"
        )

    return value


def _automatic_ppct_scope_suggestion(
    *,
    ppct_rows: tuple[PPCTRow, ...] | None,
    grade_level: int,
    assessment_type_code: str,
    semester_number: int,
) -> tuple[
    AssessmentPpctScopeSuggestion | None,
    str | None,
]:
    """Resolve the current teacher selection against supplied PPCT rows."""
    if assessment_type_code == "REGULAR":
        return None, None

    if ppct_rows is None:
        return None, (
            "Chưa có dữ liệu PPCT chuẩn hóa từ hệ thống. "
            "Không tự suy đoán phạm vi kiểm tra."
        )

    try:
        suggestion = AssessmentPpctScopeSuggestionService().suggest(
            ppct_rows=ppct_rows,
            grade_level=grade_level,
            assessment_type=assessment_type_code,
            semester=semester_number,
            subject_name="Toán",
        )
    except (
        AssessmentPpctScopeSuggestionError,
        TypeError,
    ) as error:
        return None, str(error)

    return suggestion, None


def _ppct_runtime_evidence_from_session(
    st: object,
) -> AssessmentPpctRuntimeEvidence | None:
    session_state = getattr(
        st,
        "session_state",
        None,
    )

    if session_state is None:
        return None

    try:
        value = session_state.get(
            ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY
        )
    except AttributeError:
        return None

    if value is None:
        return None

    if not isinstance(
        value,
        AssessmentPpctRuntimeEvidence,
    ):
        raise TypeError(
            "assessment PPCT runtime evidence is invalid"
        )

    return value


def _ppct_scope_confirmation_token(
    suggestion: AssessmentPpctScopeSuggestion,
) -> str:
    """Bind confirmation to selection, boundary, marker, and PPCT content."""
    if not isinstance(
        suggestion,
        AssessmentPpctScopeSuggestion,
    ):
        raise TypeError(
            "suggestion must be AssessmentPpctScopeSuggestion"
        )

    row_payload = "\\n".join(
        "|".join(
            (
                row.subject_grade.strip(),
                str(row.period),
                row.lesson_name.strip(),
                (row.sub_subject or "").strip(),
            )
        )
        for row in suggestion.scope_rows
    )

    payload = "\\n".join(
        (
            str(suggestion.grade_level),
            suggestion.assessment_type,
            str(suggestion.semester),
            suggestion.subject_grade,
            suggestion.sub_subject or "",
            str(suggestion.period_from),
            str(suggestion.period_to),
            str(suggestion.marker_period),
            suggestion.marker_title,
            row_payload,
        )
    )

    return sha256(
        payload.encode("utf-8")
    ).hexdigest()



_GOVERNED_QUESTION_TYPE_TO_BUILDER = {
    "MCQ": "MULTIPLE_CHOICE",
    "MULTIPLE_CHOICE": "MULTIPLE_CHOICE",
    "TRUE_FALSE": "TRUE_FALSE",
    "TF": "TRUE_FALSE",
    "SHORT_ANSWER": "SHORT_RESPONSE",
    "SHORT_RESPONSE": "SHORT_RESPONSE",
    "ESSAY": "ESSAY",
}

_GOVERNED_COGNITIVE_TO_BUILDER = {
    "NB": "KNOW",
    "KNOW": "KNOW",
    "TH": "UNDERSTAND",
    "UNDERSTAND": "UNDERSTAND",
    "VD": "APPLY",
    "APPLY": "APPLY",
}


def _authenticated_portal_runtime_context(
    st: object,
) -> tuple[object | None, str | None]:
    session_state = getattr(st, "session_state", None)
    if session_state is None:
        return None, None

    try:
        client = session_state.get("portal_supabase_client")
        user_id = session_state.get("portal_user_id")
    except AttributeError:
        return None, None

    normalized_user_id = str(user_id or "").strip()

    if client is None or not normalized_user_id:
        return None, None

    return client, normalized_user_id


def _automatic_governed_defaults(
    *,
    st: object,
    grade_level: int,
    semester_number: int,
    ppct_runtime_evidence: AssessmentPpctRuntimeEvidence | None,
) -> tuple[object | None, str | None]:
    if ppct_runtime_evidence is None:
        return None, (
            "PPCT runtime evidence is required "
            "before governed assessment defaults "
            "can be loaded."
        )

    client, user_id = _authenticated_portal_runtime_context(st)

    if client is None or user_id is None:
        return None, (
            "authenticated portal runtime context "
            "is required for governed defaults."
        )

    try:
        result = AssessmentBuilderGovernedDefaultsRuntime(
            client=client,
            user_id=user_id,
        ).load_defaults(
            subject_code="MATH",
            grade_level=grade_level,
            academic_year=ppct_runtime_evidence.academic_year,
            semester_number=semester_number,
        )
    except (
        AssessmentBuilderGovernedDefaultsRuntimeError,
        TypeError,
        ValueError,
    ) as error:
        return None, str(error)

    return result.defaults, None


def _governed_builder_sections(
    defaults: object,
) -> tuple[AssessmentBuilderSection, ...]:
    sections_by_code = {}

    for item in defaults.sections:
        source_code = str(
            item.question_type_code
        ).strip().upper()

        builder_code = (
            _GOVERNED_QUESTION_TYPE_TO_BUILDER
            .get(source_code)
        )

        if builder_code is None:
            raise ValueError(
                "Unsupported governed question type: "
                + source_code
            )

        if builder_code in sections_by_code:
            raise ValueError(
                "Duplicate governed question type: "
                + builder_code
            )

        sections_by_code[builder_code] = AssessmentBuilderSection(
            section_code=item.section_code,
            question_type_code=builder_code,
            question_count=item.question_count,
            response_count=item.response_count,
            section_score=item.section_score,
        )

    expected = tuple(QUESTION_TYPE_LABELS)

    if set(sections_by_code) != set(expected):
        missing = sorted(set(expected) - set(sections_by_code))
        extra = sorted(set(sections_by_code) - set(expected))
        raise ValueError(
            "Governed profile question types do "
            "not match builder contract. "
            f"missing={missing}, extra={extra}"
        )

    return tuple(
        sections_by_code[code]
        for code in expected
    )


def _governed_builder_allocations(
    defaults: object,
) -> tuple[AssessmentBuilderCognitiveAllocation, ...]:
    allocations_by_code = {}

    for item in defaults.cognitive_allocations:
        source_code = str(
            item.cognitive_level_code
        ).strip().upper()

        builder_code = (
            _GOVERNED_COGNITIVE_TO_BUILDER
            .get(source_code)
        )

        if builder_code is None:
            raise ValueError(
                "Unsupported governed cognitive level: "
                + source_code
            )

        if builder_code in allocations_by_code:
            raise ValueError(
                "Duplicate governed cognitive level: "
                + builder_code
            )

        allocations_by_code[builder_code] = (
            AssessmentBuilderCognitiveAllocation(
                cognitive_level_code=builder_code,
                target_percentage=item.target_percentage,
            )
        )

    expected = tuple(COGNITIVE_LEVEL_LABELS)

    if set(allocations_by_code) != set(expected):
        missing = sorted(
            set(expected) - set(allocations_by_code)
        )
        extra = sorted(
            set(allocations_by_code) - set(expected)
        )
        raise ValueError(
            "Governed cognitive allocations do "
            "not match builder contract. "
            f"missing={missing}, extra={extra}"
        )

    return tuple(
        allocations_by_code[code]
        for code in expected
    )


def _ppct_scope_is_confirmed(
    *,
    st: object,
    suggestion: AssessmentPpctScopeSuggestion | None,
) -> bool:
    if suggestion is None:
        return False

    session_state = getattr(
        st,
        "session_state",
        None,
    )

    if session_state is None:
        return False

    try:
        stored = session_state.get(
            _ASSESSMENT_SCOPE_CONFIRMATION_SESSION_KEY
        )
    except AttributeError:
        return False

    return (
        stored
        == _ppct_scope_confirmation_token(
            suggestion
        )
    )


def _confirm_ppct_scope(
    *,
    st: object,
    suggestion: AssessmentPpctScopeSuggestion,
) -> None:
    session_state = getattr(
        st,
        "session_state",
        None,
    )

    if session_state is None:
        raise TypeError(
            "st.session_state is required"
        )

    session_state[
        _ASSESSMENT_SCOPE_CONFIRMATION_SESSION_KEY
    ] = _ppct_scope_confirmation_token(
        suggestion
    )


def _clear_ppct_scope_confirmation(
    *,
    st: object,
) -> None:
    session_state = getattr(
        st,
        "session_state",
        None,
    )

    if session_state is None:
        return

    try:
        session_state.pop(
            _ASSESSMENT_SCOPE_CONFIRMATION_SESSION_KEY,
            None,
        )
    except AttributeError:
        return


def _inject_builder_css(st: object) -> None:
    st.markdown(
        """
        <style>
        .math69-hero {
            padding: 0.25rem 0 0.45rem 0;
        }
        .math69-subtitle {
            color: #667085;
            font-size: 0.95rem;
            margin-top: -0.3rem;
        }
        .math69-steps {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 0.55rem 0 1rem 0;
        }
        .math69-step {
            background: #f2f4f7;
            border: 1px solid #e4e7ec;
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            color: #475467;
            font-size: 0.84rem;
            font-weight: 600;
        }
        .math69-step.active {
            background: #eef4ff;
            border-color: #c7d7fe;
            color: #1849a9;
        }
        .math69-card-title {
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .math69-muted {
            color: #667085;
            font-size: 0.85rem;
        }
        div[data-testid="stMetric"] {
            background: #fafafa;
            border: 1px solid #eaecf0;
            padding: 0.7rem 0.8rem;
            border-radius: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_assessment_builder_page(
    *,
    st: object,
    initial_grade_level: int = 6,
) -> None:
    """Render configuration, automatic PPCT scope suggestion, and preview."""
    if initial_grade_level not in SUPPORTED_GRADES:
        initial_grade_level = 6

    _inject_builder_css(st)

    st.markdown('<div class="math69-hero">', unsafe_allow_html=True)
    st.title(ASSESSMENT_BUILDER_TITLE)
    st.markdown(
        '<div class="math69-subtitle">'
        "Cấu hình dùng chung cho lớp 6, 7, 8, 9; tự kiểm tra PPCT khi runtime "
        "đã cung cấp dữ liệu chuẩn hóa; chưa lưu cơ sở dữ liệu."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="math69-steps">
          <span class="math69-step active">1. Cấu hình đề</span>
          <span class="math69-step">2. Ma trận</span>
          <span class="math69-step">3. Bản đặc tả</span>
          <span class="math69-step">4. Ngân hàng câu hỏi</span>
          <span class="math69-step">5. Ráp đề</span>
          <span class="math69-step">6. Kiểm định</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Chế độ thử nghiệm cục bộ: UI không tự gọi Supabase, không phê duyệt, "
        "không xuất bản và không thay route Production. PPCT chỉ được nhận "
        "qua session từ runtime bên ngoài."
    )

    with st.container(border=True):
        st.subheader("1. Thông tin đề kiểm tra")
        row1 = st.columns((1, 2, 1))
        with row1[0]:
            grade_level = st.selectbox(
                "Khối lớp",
                options=list(SUPPORTED_GRADES),
                index=list(SUPPORTED_GRADES).index(initial_grade_level),
                key="math69_builder_grade",
            )
        with row1[1]:
            assessment_type_code = st.selectbox(
                "Loại kiểm tra",
                options=list(_ASSESSMENT_TYPE_LABELS),
                format_func=lambda code: _ASSESSMENT_TYPE_LABELS[code],
                key="math69_builder_assessment_type",
            )
        with row1[2]:
            semester_number = st.selectbox(
                "Học kỳ",
                options=[1, 2],
                format_func=lambda value: f"Học kỳ {value}",
                key="math69_builder_semester",
            )

        ppct_runtime_evidence = (
            _ppct_runtime_evidence_from_session(st)
        )

        governed_defaults, governed_error = (
            _automatic_governed_defaults(
                st=st,
                grade_level=grade_level,
                semester_number=semester_number,
                ppct_runtime_evidence=ppct_runtime_evidence,
            )
        )

        if governed_defaults is None:
            st.error(
                "Không thể tự động nạp thiết đặt "
                "đề kiểm tra đã duyệt: "
                + str(
                    governed_error
                    or "Không đủ dữ liệu thiết đặt."
                )
            )
            return

        duration_minutes = int(
            governed_defaults.duration_minutes
        )
        total_score = Decimal(
            str(governed_defaults.total_score)
        )

        row2 = st.columns(2)
        row2[0].metric(
            "Thời lượng",
            f"{duration_minutes} phút",
        )
        row2[1].metric(
            "Tổng điểm",
            f"{total_score:g}",
        )
        st.caption(
            "Hệ thống tự động lấy từ thiết đặt đã duyệt "
            f"{governed_defaults.setting.setting_version_id} "
            f"· hồ sơ {governed_defaults.setting.profile_code}. "
            "Giáo viên không phải nhập lại các thông số cấu trúc."
        )

    try:
        ppct_rows = _ppct_rows_from_session(st)
        ppct_suggestion, ppct_error = _automatic_ppct_scope_suggestion(
            ppct_rows=ppct_rows,
            grade_level=grade_level,
            assessment_type_code=assessment_type_code,
            semester_number=semester_number,
        )
    except TypeError as error:
        ppct_suggestion = None
        ppct_error = str(error)

    with st.container(border=True):
        st.subheader("2. Phạm vi PPCT tự động")
        if assessment_type_code == "REGULAR":
            _clear_ppct_scope_confirmation(
                st=st,
            )
            st.info(
                "Kiểm tra thường xuyên chưa có mốc phạm vi cố định trong PPCT. "
                "Giáo viên sẽ xác nhận phạm vi ở bước chuyên môn."
            )
        elif ppct_suggestion is not None:
            st.success(
                "Hệ thống đã tự kiểm tra PPCT và xác định phạm vi đề xuất."
            )
            scope_metrics = st.columns(4)
            scope_metrics[0].metric(
                "Từ tiết PPCT",
                ppct_suggestion.period_from,
            )
            scope_metrics[1].metric(
                "Đến tiết PPCT",
                ppct_suggestion.period_to,
            )
            scope_metrics[2].metric(
                "Mốc kiểm tra",
                ppct_suggestion.marker_period,
            )
            scope_metrics[3].metric(
                "Nguồn",
                ppct_suggestion.evidence_source,
            )

            evidence_text = (
                "Bằng chứng: "
                f"{ppct_suggestion.subject_grade} · "
                f"{ppct_suggestion.marker_title} · "
                f"tiết {ppct_suggestion.marker_period}."
            )

            if ppct_runtime_evidence is not None:
                evidence_text += (
                    " Năm học "
                    f"{ppct_runtime_evidence.academic_year} · "
                    "nguồn "
                    f"{ppct_runtime_evidence.source_id} · "
                    "phiên bản "
                    f"{ppct_runtime_evidence.source_version}."
                )

            st.caption(
                evidence_text
                + " Đây là phạm vi hệ thống đề xuất."
            )

            scope_confirmed = _ppct_scope_is_confirmed(
                st=st,
                suggestion=ppct_suggestion,
            )

            if scope_confirmed:
                st.success(
                    "Phạm vi PPCT đã được giáo viên xác nhận."
                )
            elif st.button(
                "Xác nhận phạm vi PPCT",
                key="math69_builder_confirm_ppct_scope",
                type="primary",
                use_container_width=True,
            ):
                _confirm_ppct_scope(
                    st=st,
                    suggestion=ppct_suggestion,
                )
                st.rerun()
        else:
            _clear_ppct_scope_confirmation(
                st=st,
            )
            st.warning(
                "Chưa thể tự xác định phạm vi từ PPCT. "
                + str(ppct_error or "Không đủ bằng chứng PPCT.")
            )

    with st.container(border=True):
        st.subheader("3. Cấu trúc câu hỏi")
        st.caption(
            "Thiết lập số câu, số lượt trả lời và điểm cho từng dạng câu hỏi."
        )
        try:
            sections = list(
                _governed_builder_sections(
                    governed_defaults
                )
            )
        except ValueError as error:
            st.error(
                "Cấu trúc phần đề đã duyệt "
                f"không hợp lệ: {error}"
            )
            return

        section_columns = st.columns(len(sections))

        for index, section in enumerate(sections):
            question_type_name = (
                QUESTION_TYPE_LABELS[
                    section.question_type_code
                ]
            )

            with section_columns[index]:
                with st.container(border=True):
                    st.markdown(
                        f'<div class="math69-card-title">'
                        f"{question_type_name}"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    st.metric(
                        "Số câu",
                        section.question_count,
                    )
                    st.metric(
                        "Số lượt trả lời",
                        section.response_count,
                    )
                    st.metric(
                        "Điểm",
                        f"{section.section_score:g}",
                    )
                    st.caption(
                        "Mã phần: "
                        f"{section.section_code}"
                    )

    with st.container(border=True):
        st.subheader("4. Mức độ nhận thức")
        st.caption("Tổng tỷ lệ Nhận biết – Thông hiểu – Vận dụng phải bằng 100%.")
        try:
            allocations = list(
                _governed_builder_allocations(
                    governed_defaults
                )
            )
        except ValueError as error:
            st.error(
                "Phân bổ mức độ nhận thức "
                f"đã duyệt không hợp lệ: {error}"
            )
            return

        cognitive_columns = st.columns(
            len(allocations)
        )

        for index, allocation in enumerate(
            allocations
        ):
            cognitive_name = (
                COGNITIVE_LEVEL_LABELS[
                    allocation.cognitive_level_code
                ]
            )

            with cognitive_columns[index]:
                st.metric(
                    cognitive_name,
                    f"{allocation.target_percentage:g}%",
                )

    with st.container(border=True):
        st.subheader("5. Phạm vi kiến thức")
        st.caption(
            "Phạm vi tiết PPCT được đề xuất tự động ở phía trên. "
            "Mapping từ các bài trong phạm vi sang Chủ đề/YCCĐ canonical "
            "sẽ được nối ở bước tiếp theo; hiện chưa tự bịa mã khi dữ liệu bridge còn thiếu."
        )
        scope_columns = st.columns(2)
        with scope_columns[0]:
            topic_text = st.text_area(
                "Mã chủ đề đã chọn",
                value="",
                placeholder="Ví dụ: MATH7-HK1-T01, MATH7-HK1-T02",
                key="math69_builder_topics",
            )
        with scope_columns[1]:
            requirement_text = st.text_area(
                "Mã yêu cầu cần đạt đã chọn",
                value="",
                placeholder="Ví dụ: YC01, YC02, YC03",
                key="math69_builder_requirements",
            )

    total_questions = sum(section.question_count for section in sections)
    total_responses = sum(section.response_count for section in sections)
    configured_score = sum(
        (section.section_score for section in sections),
        Decimal("0"),
    )
    cognitive_total = sum(
        (allocation.target_percentage for allocation in allocations),
        Decimal("0"),
    )

    st.subheader("6. Kiểm tra nhanh cấu hình")
    metrics = st.columns(4)
    metrics[0].metric("Tổng số câu", total_questions)
    metrics[1].metric("Lượt trả lời", total_responses)
    metrics[2].metric("Điểm đã phân bổ", f"{configured_score:g}/{total_score:g}")
    metrics[3].metric("Tỷ lệ mức độ", f"{cognitive_total:g}%")

    score_ok = configured_score == total_score
    cognitive_ok = cognitive_total == Decimal("100")
    if not score_ok:
        st.warning("Tổng điểm của các phần chưa bằng tổng điểm của đề.")
    if not cognitive_ok:
        st.warning("Tổng tỷ lệ mức độ nhận thức chưa bằng 100%.")

    if (
        assessment_type_code != "REGULAR"
        and not _ppct_scope_is_confirmed(
            st=st,
            suggestion=ppct_suggestion,
        )
    ):
        st.info(
            "Hãy xác nhận phạm vi PPCT trước khi tạo ma trận."
        )
        return

    if not st.button(
        "Kiểm tra cấu hình & xem ma trận",
        key="math69_builder_preview",
        type="primary",
        use_container_width=True,
    ):
        return

    try:
        configuration = AssessmentBuilderConfiguration(
            grade_level=grade_level,
            assessment_type_code=assessment_type_code,
            semester_number=semester_number,
            duration_minutes=duration_minutes,
            total_score=total_score,
            sections=tuple(sections),
            cognitive_allocations=tuple(allocations),
            selected_topic_codes=_codes(topic_text),
            selected_requirement_codes=_codes(requirement_text),
        )
        preview = AssessmentBuilderMatrixPreviewService().build(configuration)
    except AssessmentBuilderConfigurationError as error:
        st.error(f"Cấu hình chưa hợp lệ: {error}")
        return

    st.success("Cấu hình hợp lệ. Đây là bản xem trước, chưa lưu dữ liệu.")
    st.subheader("7. Xem trước")
    matrix_tab, cognitive_tab, specification_tab = st.tabs(
        ["Cấu trúc ma trận", "Mức độ nhận thức", "Bản đặc tả sơ bộ"]
    )

    with matrix_tab:
        st.dataframe(
            [
                {
                    "Phần": row.section_code,
                    "Dạng câu hỏi": row.question_type_name,
                    "Số câu": row.question_count,
                    "Số lượt trả lời": row.response_count,
                    "Điểm": float(row.section_score),
                    "Tỷ lệ điểm (%)": float(row.score_percentage),
                }
                for row in preview.section_rows
            ],
            use_container_width=True,
            hide_index=True,
        )

    with cognitive_tab:
        st.dataframe(
            [
                {
                    "Mức độ": row.cognitive_level_name,
                    "Tỷ lệ (%)": float(row.target_percentage),
                    "Điểm mục tiêu": float(row.target_score),
                }
                for row in preview.cognitive_rows
            ],
            use_container_width=True,
            hide_index=True,
        )

    with specification_tab:
        st.info(
            "A2-MATH69 sẽ nối chủ đề, nội dung và yêu cầu cần đạt canonical "
            "để tạo bản đặc tả chi tiết."
        )
        st.write(
            {
                "Khối lớp": preview.grade_level,
                "Loại kiểm tra": _ASSESSMENT_TYPE_LABELS[
                    preview.assessment_type_code
                ],
                "Học kỳ": preview.semester_number,
                "Thời lượng": f"{preview.duration_minutes} phút",
                "Tổng điểm": float(preview.total_score),
                "Số chủ đề đã chọn": len(preview.selected_topic_codes),
                "Số YCCĐ đã chọn": len(preview.selected_requirement_codes),
            }
        )

    st.caption(
        "Phạm vi đã chọn: "
        f"{len(preview.selected_topic_codes)} chủ đề, "
        f"{len(preview.selected_requirement_codes)} YCCĐ. "
        "A2 sẽ nối các dòng nội dung/YCCĐ vào ma trận chi tiết."
    )
