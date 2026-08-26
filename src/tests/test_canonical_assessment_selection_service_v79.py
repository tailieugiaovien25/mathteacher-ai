from dataclasses import replace

import pytest

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumProgram,
    AssessmentCurriculumSelection,
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
    CanonicalAssessmentSelectionError,
    CanonicalAssessmentSelectionService,
)


PROGRAM = AssessmentCurriculumProgram(
    program_code="MOET-GDPT2018-MATH-THCS",
    program_name="Ch??ng tr?nh m?n To?n THCS - GDPT 2018",
    subject_code="MATH",
    education_level="THCS",
    grade_min=6,
    grade_max=9,
    version_label="GDPT-2018-CURRENT",
    status="ACTIVE",
)


TOPICS = (
    AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G6-001",
        program_code=PROGRAM.program_code,
        parent_topic_code=None,
        grade_level=6,
        domain_code="CONTENT_STRAND",
        topic_name="Số và Đại số",
        sequence_number=1,
        status="ACTIVE",
        canonical_node_type="CONTENT_STRAND",
    ),
    AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G6-002",
        program_code=PROGRAM.program_code,
        parent_topic_code="CURR-NODE-MATH-G6-001",
        grade_level=6,
        domain_code="CONTENT_DOMAIN",
        topic_name="Số",
        sequence_number=1,
        status="ACTIVE",
        canonical_node_type="CONTENT_DOMAIN",
    ),
    AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G6-003",
        program_code=PROGRAM.program_code,
        parent_topic_code="CURR-NODE-MATH-G6-002",
        grade_level=6,
        domain_code="CONTENT_ITEM",
        topic_name="Số tự nhiên",
        sequence_number=1,
        status="ACTIVE",
        canonical_node_type="CONTENT_ITEM",
    ),
)


REQUIREMENTS = (
    AssessmentLearningRequirement(
        requirement_code="YCCD-MATH-06-0001",
        program_code=PROGRAM.program_code,
        topic_code="CURR-NODE-MATH-G6-003",
        grade_level=6,
        requirement_text="Yêu cầu 1",
        source_locator="Lớp 6",
        version_number=1,
        status="ACTIVE",
        canonical_status="VERIFIED",
    ),
    AssessmentLearningRequirement(
        requirement_code="YCCD-MATH-06-0002",
        program_code=PROGRAM.program_code,
        topic_code="CURR-NODE-MATH-G6-003",
        grade_level=6,
        requirement_text="Yêu cầu 2",
        source_locator="Lớp 6",
        version_number=1,
        status="ACTIVE",
        canonical_status="VERIFIED",
    ),
)


class FakeReader:
    def __init__(
        self,
        *,
        requirements=REQUIREMENTS,
    ):
        self.requirements = requirements

    def load_grade_curriculum(
        self,
        *,
        subject_code,
        grade_level,
    ):
        assert subject_code == "MATH"
        assert grade_level == 6

        return AssessmentCurriculumSelection(
            program=PROGRAM,
            topics=TOPICS,
            requirements=self.requirements,
            topic_tree=(),
        )

    def build_topic_tree(
        self,
        topics,
    ):
        raise AssertionError(
            "selection service must not depend "
            "on tree materialization"
        )


def service(
    *,
    requirements=REQUIREMENTS,
):
    return CanonicalAssessmentSelectionService(
        curriculum_reader=FakeReader(
            requirements=requirements,
        )
    )


def valid_selection():
    return CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-003",
        ),
        selected_requirement_codes=(
            "YCCD-MATH-06-0001",
        ),
    )


def test_accepts_valid_editing_selection():
    result = service().validate_selection(
        valid_selection()
    )

    assert result.finalized is False
    assert len(result.selected_topics) == 1
    assert len(result.selected_requirements) == 1


def test_rejects_duplicate_topic_ids():
    with pytest.raises(
        CanonicalAssessmentSelectionError
    ):
        CanonicalAssessmentSelection(
            subject_code="MATH",
            grade_level=6,
            program_code=PROGRAM.program_code,
            selected_topic_codes=(
                "CURR-NODE-MATH-G6-003",
                "CURR-NODE-MATH-G6-003",
            ),
            selected_requirement_codes=(),
        )


def test_rejects_duplicate_requirement_ids():
    with pytest.raises(
        CanonicalAssessmentSelectionError
    ):
        CanonicalAssessmentSelection(
            subject_code="MATH",
            grade_level=6,
            program_code=PROGRAM.program_code,
            selected_topic_codes=(
                "CURR-NODE-MATH-G6-003",
            ),
            selected_requirement_codes=(
                "YCCD-MATH-06-0001",
                "YCCD-MATH-06-0001",
            ),
        )


def test_rejects_unknown_topic_id():
    selection = replace(
        valid_selection(),
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-999",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="unknown canonical topic",
    ):
        service().validate_selection(
            selection
        )


def test_rejects_unknown_requirement_id():
    selection = replace(
        valid_selection(),
        selected_requirement_codes=(
            "YCCD-MATH-06-9999",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="unknown canonical requirement",
    ):
        service().validate_selection(
            selection
        )


def test_rejects_requirement_outside_selected_topic_scope():
    selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-002",
        ),
        selected_requirement_codes=(
            "YCCD-MATH-06-0001",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="outside selected topic scope",
    ):
        service().validate_selection(
            selection
        )


def test_rejects_non_verified_requirement():
    damaged = (
        replace(
            REQUIREMENTS[0],
            canonical_status="DRAFT",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="not VERIFIED",
    ):
        service(
            requirements=damaged,
        ).validate_selection(
            valid_selection()
        )


def test_rejects_inactive_requirement():
    damaged = (
        replace(
            REQUIREMENTS[0],
            status="INACTIVE",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="not ACTIVE",
    ):
        service(
            requirements=damaged,
        ).validate_selection(
            valid_selection()
        )


def test_editing_selection_may_be_empty():
    result = service().build_editing_selection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
    )

    assert result.selected_topic_codes == ()
    assert result.selected_requirement_codes == ()
    assert result.finalized is False


def test_finalization_requires_requirement():
    empty = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-003",
        ),
        selected_requirement_codes=(),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="at least one canonical requirement",
    ):
        service().finalize_selection(
            empty
        )


def test_parent_selection_does_not_auto_expand():
    result = service().build_editing_selection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-001",
        ),
    )

    assert result.selected_topic_codes == (
        "CURR-NODE-MATH-G6-001",
    )


def test_explicit_descendant_expansion_is_deterministic():
    result = (
        service()
        .expand_topic_descendants_explicitly(
            subject_code="MATH",
            grade_level=6,
            topic_codes=(
                "CURR-NODE-MATH-G6-001",
            ),
        )
    )

    assert result == (
        "CURR-NODE-MATH-G6-001",
        "CURR-NODE-MATH-G6-002",
        "CURR-NODE-MATH-G6-003",
    )


def test_service_has_no_supabase_dependency():
    from pathlib import Path

    path = Path(
        "src/assessment_generation_v2/services/"
        "canonical_assessment_selection_service.py"
    )

    text = path.read_text(
        encoding="utf-8-sig"
    ).lower()

    assert "from supabase" not in text
    assert "import supabase" not in text
    assert ".table(" not in text



def test_rejects_program_mismatch():
    selection = valid_selection()

    damaged_program = replace(
        PROGRAM,
        program_code="OTHER-PROGRAM",
    )

    class Reader:
        def load_grade_curriculum(
            self,
            *,
            subject_code,
            grade_level,
        ):
            return AssessmentCurriculumSelection(
                program=damaged_program,
                topics=TOPICS,
                requirements=REQUIREMENTS,
                topic_tree=(),
            )

        def build_topic_tree(
            self,
            topics,
        ):
            return ()

    selection_service = (
        CanonicalAssessmentSelectionService(
            curriculum_reader=Reader(),
        )
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="program_code",
    ):
        selection_service.validate_selection(
            selection
        )


def test_rejects_grade_out_of_range():
    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="grade_level",
    ):
        CanonicalAssessmentSelection(
            subject_code="MATH",
            grade_level=13,
            program_code=PROGRAM.program_code,
            selected_topic_codes=(),
            selected_requirement_codes=(),
        )


def test_rejects_blank_subject_code():
    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="subject_code",
    ):
        CanonicalAssessmentSelection(
            subject_code="   ",
            grade_level=6,
            program_code=PROGRAM.program_code,
            selected_topic_codes=(),
            selected_requirement_codes=(),
        )


def test_rejects_blank_program_code():
    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="program_code",
    ):
        CanonicalAssessmentSelection(
            subject_code="MATH",
            grade_level=6,
            program_code=" ",
            selected_topic_codes=(),
            selected_requirement_codes=(),
        )


def test_finalization_requires_topic():
    empty = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(),
        selected_requirement_codes=(
            "YCCD-MATH-06-0001",
        ),
    )

    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="at least one canonical topic",
    ):
        service().finalize_selection(
            empty
        )


def test_valid_finalization_returns_resolved_selection():
    result = service().finalize_selection(
        valid_selection()
    )

    assert result.finalized is True
    assert result.selected_topic_codes == (
        "CURR-NODE-MATH-G6-003",
    )
    assert result.selected_requirement_codes == (
        "YCCD-MATH-06-0001",
    )
    assert tuple(
        topic.topic_code
        for topic in result.selected_topics
    ) == result.selected_topic_codes
    assert tuple(
        requirement.requirement_code
        for requirement
        in result.selected_requirements
    ) == result.selected_requirement_codes


def test_expansion_of_multiple_overlapping_topics_is_duplicate_safe():
    result = (
        service()
        .expand_topic_descendants_explicitly(
            subject_code="MATH",
            grade_level=6,
            topic_codes=(
                "CURR-NODE-MATH-G6-001",
                "CURR-NODE-MATH-G6-002",
            ),
        )
    )

    assert result == (
        "CURR-NODE-MATH-G6-001",
        "CURR-NODE-MATH-G6-002",
        "CURR-NODE-MATH-G6-003",
    )

    assert len(result) == len(set(result))


def test_expansion_rejects_unknown_topic():
    with pytest.raises(
        CanonicalAssessmentSelectionError,
        match="unknown canonical topic code",
    ):
        (
            service()
            .expand_topic_descendants_explicitly(
                subject_code="MATH",
                grade_level=6,
                topic_codes=(
                    "CURR-NODE-MATH-G6-999",
                ),
            )
        )


def test_resolved_topics_follow_selected_id_order():
    selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-002",
            "CURR-NODE-MATH-G6-003",
        ),
        selected_requirement_codes=(),
    )

    result = service().validate_selection(
        selection
    )

    assert tuple(
        topic.topic_code
        for topic in result.selected_topics
    ) == selection.selected_topic_codes


def test_resolved_requirements_follow_selected_id_order():
    selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code=PROGRAM.program_code,
        selected_topic_codes=(
            "CURR-NODE-MATH-G6-003",
        ),
        selected_requirement_codes=(
            "YCCD-MATH-06-0002",
            "YCCD-MATH-06-0001",
        ),
    )

    result = service().validate_selection(
        selection
    )

    assert tuple(
        requirement.requirement_code
        for requirement
        in result.selected_requirements
    ) == selection.selected_requirement_codes



def test_service_has_no_streamlit_dependency():
    from pathlib import Path

    path = Path(
        "src/assessment_generation_v2/services/"
        "canonical_assessment_selection_service.py"
    )

    text = path.read_text(
        encoding="utf-8-sig"
    ).lower()

    assert "import streamlit" not in text
    assert "from streamlit" not in text
    assert "st." not in text
