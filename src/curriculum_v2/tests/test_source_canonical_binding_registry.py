import pytest

from curriculum_v2.source_binding import (
    CurriculumSourceItem,
    InMemorySourceCanonicalBindingRegistry,
    SourceCanonicalBinding,
    SourceCanonicalBindingProvenance,
    SourceCanonicalBindingResolutionError,
)


def _item(
    *,
    source_type="PPCT",
    source_id="SRC-PPCT-01",
    source_version="7",
    academic_year="2026-2027",
    subject_code="MATH",
    grade_level=7,
    external_item_key="PERIOD-001",
    sequence=1,
    title="Bài 1",
):
    return CurriculumSourceItem(
        source_type=source_type,
        source_id=source_id,
        source_version=source_version,
        academic_year=academic_year,
        subject_code=subject_code,
        grade_level=grade_level,
        external_item_key=external_item_key,
        sequence=sequence,
        title=title,
        source_location="sheet:PPCT",
    )


def _binding(
    *,
    binding_id="BIND-001",
    source_type="PPCT",
    source_id="SRC-PPCT-01",
    source_version="7",
    academic_year="2026-2027",
    subject_code="MATH",
    grade_level=7,
    external_item_key="PERIOD-001",
    canonical_lesson_id="TB-MATH7-KNTT-L001",
    status="VERIFIED",
):
    return SourceCanonicalBinding(
        binding_id=binding_id,
        source_type=source_type,
        source_id=source_id,
        source_version=source_version,
        academic_year=academic_year,
        subject_code=subject_code,
        grade_level=grade_level,
        external_item_key=external_item_key,
        canonical_lesson_id=canonical_lesson_id,
        status=status,
        provenance=(
            SourceCanonicalBindingProvenance(
                source_document_id="SRC-PPCT-01",
                mapping_method="MANUAL_VERIFIED",
                verified_by="CURRICULUM_REVIEW",
                source_location="sheet:PPCT",
                source_version=source_version,
            )
        ),
    )


def test_exact_verified_binding_resolves():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (_binding(),)
        )
    )

    result = registry.resolve_verified(
        _item()
    )

    assert result.binding_id == "BIND-001"
    assert (
        result.canonical_lesson_id
        == "TB-MATH7-KNTT-L001"
    )


def test_same_title_different_external_key_does_not_match():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (_binding(),)
        )
    )

    with pytest.raises(
        SourceCanonicalBindingResolutionError,
        match="no VERIFIED",
    ):
        registry.resolve_verified(
            _item(
                external_item_key="PERIOD-002",
                title="Bài 1",
            )
        )


def test_source_version_change_requires_binding_data_update():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (_binding(source_version="7"),)
        )
    )

    with pytest.raises(
        SourceCanonicalBindingResolutionError,
        match="no VERIFIED",
    ):
        registry.resolve_verified(
            _item(source_version="8")
        )


def test_candidate_binding_is_not_used_at_runtime():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (
                _binding(
                    status="CANDIDATE",
                ),
            )
        )
    )

    with pytest.raises(
        SourceCanonicalBindingResolutionError,
        match="no VERIFIED",
    ):
        registry.resolve_verified(
            _item()
        )


def test_multiple_verified_bindings_fail_closed():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (
                _binding(
                    binding_id="BIND-A",
                    canonical_lesson_id=(
                        "TB-MATH7-KNTT-L001"
                    ),
                ),
                _binding(
                    binding_id="BIND-B",
                    canonical_lesson_id=(
                        "TB-MATH7-KNTT-L002"
                    ),
                ),
            )
        )
    )

    with pytest.raises(
        SourceCanonicalBindingResolutionError,
        match="ambiguous",
    ):
        registry.resolve_verified(
            _item()
        )


def test_cross_grade_binding_does_not_match():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (
                _binding(
                    grade_level=8,
                ),
            )
        )
    )

    with pytest.raises(
        SourceCanonicalBindingResolutionError,
        match="no VERIFIED",
    ):
        registry.resolve_verified(
            _item(grade_level=7)
        )


def test_batch_resolution_dedupes_lesson_ids_preserving_source_order():
    registry = (
        InMemorySourceCanonicalBindingRegistry(
            (
                _binding(
                    binding_id="BIND-001",
                    external_item_key="PERIOD-001",
                    canonical_lesson_id=(
                        "TB-MATH7-KNTT-L001"
                    ),
                ),
                _binding(
                    binding_id="BIND-002",
                    external_item_key="PERIOD-002",
                    canonical_lesson_id=(
                        "TB-MATH7-KNTT-L001"
                    ),
                ),
                _binding(
                    binding_id="BIND-003",
                    external_item_key="PERIOD-003",
                    canonical_lesson_id=(
                        "TB-MATH7-KNTT-L002"
                    ),
                ),
            )
        )
    )

    result = registry.resolve_many_verified(
        (
            _item(
                external_item_key="PERIOD-001",
                sequence=1,
            ),
            _item(
                external_item_key="PERIOD-002",
                sequence=2,
            ),
            _item(
                external_item_key="PERIOD-003",
                sequence=3,
            ),
        )
    )

    assert tuple(
        item.canonical_lesson_id
        for item in result
    ) == (
        "TB-MATH7-KNTT-L001",
        "TB-MATH7-KNTT-L002",
    )


def test_registry_rejects_duplicate_binding_id():
    with pytest.raises(
        ValueError,
        match="duplicate binding_id",
    ):
        InMemorySourceCanonicalBindingRegistry(
            (
                _binding(
                    binding_id="DUP",
                    external_item_key="PERIOD-001",
                ),
                _binding(
                    binding_id="DUP",
                    external_item_key="PERIOD-002",
                ),
            )
        )


def test_source_type_and_subject_code_are_normalized():
    item = _item(
        source_type="ppct",
        subject_code="math",
    )

    assert item.source_type == "PPCT"
    assert item.subject_code == "MATH"
