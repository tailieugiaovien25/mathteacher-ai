import pytest

from curriculum_v2.source_binding import (
    CurriculumSourceItem,
)
from curriculum_v2.source_binding.authoring import (
    SourceCanonicalBindingAuthoringError,
    SourceCanonicalBindingAuthoringService,
    SourceCanonicalBindingDatasetWriter,
)
from curriculum_v2.source_binding.json_loader import (
    SourceCanonicalBindingJsonLoader,
)


def _item(
    *,
    title="Bài hiển thị",
    source_version="7",
):
    return CurriculumSourceItem(
        source_type="PPCT",
        source_id="SRC-PPCT-MATH7-2026",
        source_version=source_version,
        academic_year="2026-2027",
        subject_code="MATH",
        grade_level=7,
        external_item_key="PERIOD:0001",
        sequence=1,
        title=title,
        source_location="workbook:PPCT#period=1",
    )


def _candidate(
    *,
    mapping_method="MANUAL_REVIEW",
):
    return (
        SourceCanonicalBindingAuthoringService()
        .create_candidate(
            binding_id="BIND-001",
            item=_item(),
            canonical_lesson_id=(
                "TB-MATH7-KNTT-L001"
            ),
            source_document_id=(
                "SRC-PPCT-MATH7-2026"
            ),
            mapping_method=mapping_method,
        )
    )


def test_candidate_copies_exact_source_identity():
    item = _item()

    binding = (
        SourceCanonicalBindingAuthoringService()
        .create_candidate(
            binding_id="BIND-001",
            item=item,
            canonical_lesson_id=(
                "TB-MATH7-KNTT-L001"
            ),
            source_document_id=(
                "SRC-PPCT-MATH7-2026"
            ),
            mapping_method="MANUAL_REVIEW",
        )
    )

    assert binding.identity == item.identity
    assert binding.status == "CANDIDATE"
    assert binding.provenance.verified_by is None


def test_title_does_not_enter_binding_identity():
    service = (
        SourceCanonicalBindingAuthoringService()
    )

    first = service.create_candidate(
        binding_id="BIND-A",
        item=_item(title="Tên A"),
        canonical_lesson_id="LESSON-1",
        source_document_id="SRC",
        mapping_method="MANUAL_REVIEW",
    )

    second = service.create_candidate(
        binding_id="BIND-B",
        item=_item(title="Tên B"),
        canonical_lesson_id="LESSON-1",
        source_document_id="SRC",
        mapping_method="MANUAL_REVIEW",
    )

    assert first.identity == second.identity


def test_verify_requires_explicit_human_or_admin_identity():
    with pytest.raises(
        SourceCanonicalBindingAuthoringError,
        match="verified_by",
    ):
        (
            SourceCanonicalBindingAuthoringService()
            .verify(
                binding=_candidate(),
                verified_by=" ",
            )
        )


def test_candidate_can_be_explicitly_verified():
    result = (
        SourceCanonicalBindingAuthoringService()
        .verify(
            binding=_candidate(),
            verified_by="CURRICULUM_REVIEWER",
        )
    )

    assert result.status == "VERIFIED"
    assert (
        result.provenance.verified_by
        == "CURRICULUM_REVIEWER"
    )
    assert (
        result.canonical_lesson_id
        == "TB-MATH7-KNTT-L001"
    )


def test_ai_suggestion_is_candidate_until_explicit_verification():
    candidate = _candidate(
        mapping_method="AI_ASSISTED_SUGGESTION",
    )

    assert candidate.status == "CANDIDATE"
    assert candidate.provenance.verified_by is None

    verified = (
        SourceCanonicalBindingAuthoringService()
        .verify(
            binding=candidate,
            verified_by="HUMAN-REVIEWER",
        )
    )

    assert verified.status == "VERIFIED"
    assert (
        verified.provenance.mapping_method
        == "AI_ASSISTED_SUGGESTION"
    )
    assert (
        verified.provenance.verified_by
        == "HUMAN-REVIEWER"
    )


def test_verified_binding_cannot_self_transition_again():
    service = (
        SourceCanonicalBindingAuthoringService()
    )

    verified = service.verify(
        binding=_candidate(),
        verified_by="REVIEWER",
    )

    with pytest.raises(
        SourceCanonicalBindingAuthoringError,
        match="only CANDIDATE",
    ):
        service.verify(
            binding=verified,
            verified_by="REVIEWER-2",
        )


def test_deprecate_does_not_change_identity_or_target():
    service = (
        SourceCanonicalBindingAuthoringService()
    )

    verified = service.verify(
        binding=_candidate(),
        verified_by="REVIEWER",
    )

    deprecated = service.deprecate(
        binding=verified
    )

    assert deprecated.status == "DEPRECATED"
    assert deprecated.identity == verified.identity
    assert (
        deprecated.canonical_lesson_id
        == verified.canonical_lesson_id
    )


def test_writer_round_trips_through_strict_loader():
    service = (
        SourceCanonicalBindingAuthoringService()
    )

    verified = service.verify(
        binding=_candidate(),
        verified_by="REVIEWER",
    )

    text = (
        SourceCanonicalBindingDatasetWriter()
        .dumps(
            dataset_id=(
                "DATASET-MATH7-PILOT"
            ),
            bindings=(verified,),
        )
    )

    loaded = (
        SourceCanonicalBindingJsonLoader()
        .load_text(text)
    )

    assert len(loaded.bindings) == 1
    assert (
        loaded.bindings[0].status
        == "VERIFIED"
    )


def test_writer_is_deterministic_for_same_input():
    writer = (
        SourceCanonicalBindingDatasetWriter()
    )
    candidate = _candidate()

    first = writer.dumps(
        dataset_id="DATASET-1",
        bindings=(candidate,),
    )
    second = writer.dumps(
        dataset_id="DATASET-1",
        bindings=(candidate,),
    )

    assert first == second


def test_source_version_change_is_new_data_identity():
    service = (
        SourceCanonicalBindingAuthoringService()
    )

    v7 = service.create_candidate(
        binding_id="BIND-V7",
        item=_item(source_version="7"),
        canonical_lesson_id="LESSON-1",
        source_document_id="SRC",
        mapping_method="MANUAL_REVIEW",
    )

    v8 = service.create_candidate(
        binding_id="BIND-V8",
        item=_item(source_version="8"),
        canonical_lesson_id="LESSON-1",
        source_document_id="SRC",
        mapping_method="MANUAL_REVIEW",
    )

    assert v7.identity != v8.identity
    assert (
        v7.canonical_lesson_id
        == v8.canonical_lesson_id
    )
