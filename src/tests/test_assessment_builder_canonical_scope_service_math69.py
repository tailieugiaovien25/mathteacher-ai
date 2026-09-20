from dataclasses import replace
from pathlib import Path

from assessment_generation_v2.services.assessment_builder_canonical_scope_service import (
    BLOCKED_AMBIGUOUS,
    BLOCKED_UNAVAILABLE,
    BLOCKED_UNVERIFIED,
    READY,
    AssessmentBuilderCanonicalScopeService,
)
from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumProgram,
    AssessmentCurriculumSelection,
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)
from curriculum_v2.source_binding.models import (
    CurriculumSourceItem,
    SourceCanonicalBinding,
    SourceCanonicalBindingProvenance,
)
from curriculum_v2.source_binding.registry import (
    InMemorySourceCanonicalBindingRegistry,
)
from curriculum_v2.textbooks.models.textbook_requirement_mapping import (
    TextbookRequirementMapping,
    TextbookRequirementMappingProvenance,
)


PROGRAM = AssessmentCurriculumProgram(
    program_code="MOET-GDPT2018-MATH-THCS",
    program_name="Math THCS",
    subject_code="MATH",
    education_level="THCS",
    grade_min=6,
    grade_max=9,
    version_label="GDPT-2018-CURRENT",
    status="ACTIVE",
)

TOPICS = (
    AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G7-001",
        program_code=PROGRAM.program_code,
        parent_topic_code=None,
        grade_level=7,
        domain_code="CONTENT_ITEM",
        topic_name="Topic 1",
        sequence_number=1,
        status="ACTIVE",
        canonical_node_type="CONTENT_ITEM",
    ),
    AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G7-002",
        program_code=PROGRAM.program_code,
        parent_topic_code=None,
        grade_level=7,
        domain_code="CONTENT_ITEM",
        topic_name="Topic 2",
        sequence_number=2,
        status="ACTIVE",
        canonical_node_type="CONTENT_ITEM",
    ),
)

REQUIREMENTS = (
    AssessmentLearningRequirement(
        requirement_code="YCCD-MATH-07-0001",
        program_code=PROGRAM.program_code,
        topic_code="CURR-NODE-MATH-G7-001",
        grade_level=7,
        requirement_text="Requirement 1",
        source_locator="Grade 7",
        version_number=1,
        status="ACTIVE",
        canonical_status="VERIFIED",
    ),
    AssessmentLearningRequirement(
        requirement_code="YCCD-MATH-07-0002",
        program_code=PROGRAM.program_code,
        topic_code="CURR-NODE-MATH-G7-002",
        grade_level=7,
        requirement_text="Requirement 2",
        source_locator="Grade 7",
        version_number=1,
        status="ACTIVE",
        canonical_status="VERIFIED",
    ),
)


class FakeReader:
    def __init__(self, requirements=REQUIREMENTS):
        self.requirements = tuple(requirements)

    def load_grade_curriculum(
        self,
        *,
        subject_code,
        grade_level,
    ):
        assert subject_code == "MATH"
        assert grade_level == 7
        return AssessmentCurriculumSelection(
            program=PROGRAM,
            topics=TOPICS,
            requirements=self.requirements,
            topic_tree=(),
        )

    def build_topic_tree(self, topics):
        return ()


class FakeProvider:
    def __init__(self, mappings):
        self.mappings = tuple(mappings)

    def get_textbook_requirement_mappings(
        self,
        *,
        textbook_ref,
        curriculum_ref,
        subject,
        grade,
    ):
        assert textbook_ref == "TB-MATH7-KNTT"
        assert curriculum_ref == "CURRICULUM-MATH-2018"
        assert subject == "MATH"
        assert grade == 7
        return self.mappings


def source_item(period=1):
    return CurriculumSourceItem(
        source_type="PPCT",
        source_id="PPCT-MATH7",
        source_version="2026-09-18",
        academic_year="2026-2027",
        subject_code="MATH",
        grade_level=7,
        external_item_key=f"PERIOD:{period:04d}",
        sequence=period,
        title=f"Lesson {period}",
    )


def binding(
    item,
    *,
    binding_id,
    lesson_id,
    status="VERIFIED",
):
    return SourceCanonicalBinding(
        binding_id=binding_id,
        source_type=item.source_type,
        source_id=item.source_id,
        source_version=item.source_version,
        academic_year=item.academic_year,
        subject_code=item.subject_code,
        grade_level=item.grade_level,
        external_item_key=item.external_item_key,
        canonical_lesson_id=lesson_id,
        provenance=SourceCanonicalBindingProvenance(
            source_document_id="TEST-SOURCE",
            mapping_method="HUMAN_REVIEW",
            verified_by="TESTER",
        ),
        status=status,
    )


def mapping(
    mapping_id,
    lesson_id,
    requirement_id,
    *,
    status="VERIFIED",
):
    return TextbookRequirementMapping(
        mapping_id=mapping_id,
        lesson_id=lesson_id,
        canonical_requirement_id=requirement_id,
        provenance=TextbookRequirementMappingProvenance(
            source_document_id="TEST-MAPPING",
            mapping_method="HUMAN_REVIEW",
            verified_by="TESTER",
        ),
        status=status,
    )


def make_service(
    *,
    bindings,
    mappings,
    requirements=REQUIREMENTS,
):
    return AssessmentBuilderCanonicalScopeService(
        binding_registry=InMemorySourceCanonicalBindingRegistry(
            bindings
        ),
        mapping_provider=FakeProvider(mappings),
        curriculum_reader=FakeReader(requirements),
    )


def resolve(service, items):
    return service.resolve(
        source_items=items,
        textbook_ref="TB-MATH7-KNTT",
        curriculum_ref="CURRICULUM-MATH-2018",
        subject_code="MATH",
        grade_level=7,
        program_code=PROGRAM.program_code,
    )


def test_zero_source_items_fail_closed():
    result = resolve(
        make_service(bindings=(), mappings=()),
        (),
    )
    assert result.status == BLOCKED_UNAVAILABLE
    assert result.ready is False


def test_no_verified_source_binding_fail_closed():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
                status="CANDIDATE",
            ),
        ),
        mappings=(),
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNAVAILABLE


def test_multiple_verified_source_bindings_are_ambiguous():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
            binding(
                item,
                binding_id="B2",
                lesson_id="TB-MATH7-KNTT-L002",
            ),
        ),
        mappings=(),
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_AMBIGUOUS


def test_candidate_mapping_is_never_authority():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
                status="CANDIDATE",
            ),
        ),
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNVERIFIED
    assert result.requirement_codes == ()


def test_verified_exact_scope_is_ready():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
            ),
        ),
    )
    result = resolve(service, (item,))
    assert result.status == READY
    assert result.lesson_ids == ("TB-MATH7-KNTT-L001",)
    assert result.topic_codes == ("CURR-NODE-MATH-G7-001",)
    assert result.requirement_codes == ("YCCD-MATH-07-0001",)
    assert result.ready is True


def test_stable_dedupe_preserves_canonical_order():
    first = source_item(1)
    second = source_item(2)
    service = make_service(
        bindings=(
            binding(
                first,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
            binding(
                second,
                binding_id="B2",
                lesson_id="TB-MATH7-KNTT-L002",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
            ),
            mapping(
                "M2",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
            ),
            mapping(
                "M3",
                "TB-MATH7-KNTT-L002",
                "YCCD-MATH-07-0002",
            ),
        ),
    )
    result = resolve(service, (first, second))
    assert result.status == READY
    assert result.requirement_codes == (
        "YCCD-MATH-07-0001",
        "YCCD-MATH-07-0002",
    )
    assert result.topic_codes == (
        "CURR-NODE-MATH-G7-001",
        "CURR-NODE-MATH-G7-002",
    )


def test_missing_canonical_requirement_fails_closed():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-9999",
            ),
        ),
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNAVAILABLE


def test_mixed_verified_and_candidate_mapping_is_blocked():
    item = source_item()
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
            ),
            mapping(
                "M2",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0002",
                status="CANDIDATE",
            ),
        ),
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNVERIFIED


def test_non_verified_canonical_requirement_is_blocked():
    item = source_item()
    damaged = (
        replace(
            REQUIREMENTS[0],
            canonical_status="DRAFT",
        ),
    )
    service = make_service(
        bindings=(
            binding(
                item,
                binding_id="B1",
                lesson_id="TB-MATH7-KNTT-L001",
            ),
        ),
        mappings=(
            mapping(
                "M1",
                "TB-MATH7-KNTT-L001",
                "YCCD-MATH-07-0001",
            ),
        ),
        requirements=damaged,
    )
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNVERIFIED


def test_source_subject_grade_mismatch_is_blocked():
    item = replace(source_item(), grade_level=6)
    service = make_service(bindings=(), mappings=())
    result = resolve(service, (item,))
    assert result.status == BLOCKED_UNAVAILABLE


def test_service_contains_no_raw_ppct_or_external_persistence_path():
    path = Path(
        "src/assessment_generation_v2/services/"
        "assessment_builder_canonical_scope_service.py"
    )
    text = path.read_text(encoding="utf-8-sig").lower()
    assert "ppct_plan_item_adapter" not in text
    assert "ppctrow" not in text
    assert "json.load" not in text
    assert "from supabase" not in text
    assert "import supabase" not in text
    assert "rapidfuzz" not in text
    assert "difflib" not in text


def test_builder_manual_scope_path_remains_and_is_not_auto_filled():
    path = Path(
        "src/portal_v2/ui/assessment_builder_streamlit.py"
    )
    text = path.read_text(encoding="utf-8-sig")
    assert 'key="math69_builder_topics"' in text
    assert 'key="math69_builder_requirements"' in text
    # Manual teacher-editable scope fields must remain present.
    assert 'key="math69_builder_topics"' in text
    assert 'key="math69_builder_requirements"' in text
    assert text.count("st.text_area(") >= 2

    # A session-backed field may intentionally omit value="" so an explicit
    # teacher Apply action can populate it on rerun. Recommendation state must
    # remain separate until that explicit action.
    assert "_store_requirement_recommendation_state(" in text
    assert "_apply_requirement_recommendation_state(" in text
    assert "topic_text = specification_preview" not in text
    assert "requirement_text = specification_preview" not in text
    assert "topic_text = canonical_scope_result" not in text
    assert "requirement_text = canonical_scope_result" not in text
    assert "_ASSESSMENT_CANONICAL_SCOPE_SESSION_KEY" in text
