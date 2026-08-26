import pytest

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumProgram,
    AssessmentCurriculumQueryError,
    AssessmentCurriculumQueryService,
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)


def program():
    return AssessmentCurriculumProgram(
        program_code="MOET-GDPT2018-MATH-THCS",
        program_name="Math",
        subject_code="MATH",
        education_level="THCS",
        grade_min=6,
        grade_max=9,
        version_label="GDPT-2018-CURRENT",
        status="ACTIVE",
    )


def topic(
    code="CURR-NODE-MATH-G6-001",
    *,
    parent=None,
    sequence=1,
):
    return AssessmentCurriculumTopic(
        topic_code=code,
        program_code="MOET-GDPT2018-MATH-THCS",
        parent_topic_code=parent,
        grade_level=6,
        domain_code="CONTENT_STRAND",
        topic_name=code,
        sequence_number=sequence,
        status="ACTIVE",
        canonical_node_type="CONTENT_STRAND",
    )


def requirement(
    code="YCCD-MATH-06-0001",
    topic_code="CURR-NODE-MATH-G6-001",
    *,
    canonical_status="VERIFIED",
):
    return AssessmentLearningRequirement(
        requirement_code=code,
        program_code="MOET-GDPT2018-MATH-THCS",
        topic_code=topic_code,
        grade_level=6,
        requirement_text="Yêu cầu cần đạt",
        source_locator="Lớp 6",
        version_number=1,
        status="ACTIVE",
        canonical_status=canonical_status,
    )


class FakeCatalog:
    def __init__(
        self,
        *,
        program_value=None,
        topics=(),
        requirements=(),
    ):
        self.program_value = (
            program_value
            if program_value is not None
            else program()
        )
        self.topics = tuple(topics)
        self.requirements = tuple(requirements)
        self.calls = []

    def find_active_program(
        self,
        *,
        subject_code,
        grade_level,
    ):
        self.calls.append(
            (
                "program",
                subject_code,
                grade_level,
            )
        )
        return self.program_value

    def list_topics(
        self,
        *,
        program_code,
        grade_level,
    ):
        self.calls.append(
            (
                "topics",
                program_code,
                grade_level,
            )
        )
        return self.topics

    def list_requirements(
        self,
        *,
        program_code,
        grade_level,
        topic_codes=None,
    ):
        self.calls.append(
            (
                "requirements",
                program_code,
                grade_level,
                None
                if topic_codes is None
                else tuple(topic_codes),
            )
        )

        if topic_codes is None:
            return self.requirements

        allowed = set(topic_codes)

        return tuple(
            item
            for item in self.requirements
            if item.topic_code in allowed
        )


def test_load_grade_curriculum_includes_tree():
    root = topic(
        "CURR-NODE-MATH-G6-001",
        sequence=1,
    )

    child = topic(
        "CURR-NODE-MATH-G6-002",
        parent=root.topic_code,
        sequence=1,
    )

    catalog = FakeCatalog(
        topics=(root, child),
        requirements=(
            requirement(
                topic_code=child.topic_code,
            ),
        ),
    )

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    result = service.load_grade_curriculum(
        subject_code="MATH",
        grade_level=6,
    )

    assert len(result.topics) == 2
    assert len(result.requirements) == 1
    assert len(result.topic_tree) == 1
    assert result.topic_tree[0].topic == root
    assert result.topic_tree[0].children[0].topic == child


def test_tree_orders_siblings_by_sequence_then_code():
    root = topic("ROOT")

    later = topic(
        "CHILD-B",
        parent="ROOT",
        sequence=2,
    )

    first_b = topic(
        "CHILD-C",
        parent="ROOT",
        sequence=1,
    )

    first_a = topic(
        "CHILD-A",
        parent="ROOT",
        sequence=1,
    )

    tree = AssessmentCurriculumQueryService.build_topic_tree(
        (
            later,
            first_b,
            root,
            first_a,
        )
    )

    assert [
        node.topic.topic_code
        for node in tree[0].children
    ] == [
        "CHILD-A",
        "CHILD-C",
        "CHILD-B",
    ]


def test_tree_rejects_missing_parent():
    child = topic(
        "CHILD",
        parent="MISSING",
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="parent outside",
    ):
        AssessmentCurriculumQueryService.build_topic_tree(
            (child,)
        )


def test_tree_rejects_cycle():
    first = topic(
        "FIRST",
        parent="SECOND",
    )

    second = topic(
        "SECOND",
        parent="FIRST",
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="cyclic|cycle",
    ):
        AssessmentCurriculumQueryService.build_topic_tree(
            (first, second)
        )


def test_tree_rejects_duplicate_topic_codes():
    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="Duplicate topic code",
    ):
        AssessmentCurriculumQueryService.build_topic_tree(
            (
                topic("DUP"),
                topic("DUP"),
            )
        )


def test_missing_program_is_rejected():
    catalog = FakeCatalog()

    catalog.program_value = None

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="No active curriculum program",
    ):
        service.load_grade_curriculum(
            subject_code="MATH",
            grade_level=6,
        )


def test_orphan_requirement_is_rejected():
    catalog = FakeCatalog(
        topics=(topic(),),
        requirements=(
            requirement(
                topic_code="UNKNOWN-TOPIC"
            ),
        ),
    )

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="outside the selected grade",
    ):
        service.load_grade_curriculum(
            subject_code="MATH",
            grade_level=6,
        )


def test_non_verified_requirement_is_rejected():
    catalog = FakeCatalog(
        topics=(topic(),),
        requirements=(
            requirement(
                canonical_status="DRAFT"
            ),
        ),
    )

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="Non-verified",
    ):
        service.load_grade_curriculum(
            subject_code="MATH",
            grade_level=6,
        )


def test_topic_filter():
    first = topic(
        "CURR-NODE-MATH-G6-001"
    )

    second = topic(
        "CURR-NODE-MATH-G6-002"
    )

    catalog = FakeCatalog(
        topics=(first, second),
        requirements=(
            requirement(
                "YCCD-MATH-06-0001",
                first.topic_code,
            ),
            requirement(
                "YCCD-MATH-06-0002",
                second.topic_code,
            ),
        ),
    )

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    result = service.list_requirements_for_topics(
        subject_code="MATH",
        grade_level=6,
        topic_codes=(second.topic_code,),
    )

    assert [
        row.requirement_code
        for row in result
    ] == [
        "YCCD-MATH-06-0002"
    ]


def test_unknown_topic_filter_is_rejected():
    catalog = FakeCatalog(
        topics=(topic(),),
        requirements=(requirement(),),
    )

    service = AssessmentCurriculumQueryService(
        catalog=catalog
    )

    with pytest.raises(
        AssessmentCurriculumQueryError,
        match="Unknown topic codes",
    ):
        service.list_requirements_for_topics(
            subject_code="MATH",
            grade_level=6,
            topic_codes=("UNKNOWN",),
        )
