import json

import pytest

from curriculum_v2.source_binding.json_loader import (
    SourceCanonicalBindingDataError,
    SourceCanonicalBindingJsonLoader,
)
from curriculum_v2.source_binding.registry import (
    InMemorySourceCanonicalBindingRegistry,
)
from curriculum_v2.source_binding.models import (
    CurriculumSourceItem,
)


def _binding(
    *,
    binding_id="BIND-001",
    external_item_key="PERIOD:0001",
    canonical_lesson_id="TB-MATH7-KNTT-L001",
    source_version="7",
    status="VERIFIED",
):
    return {
        "binding_id": binding_id,
        "source_type": "PPCT",
        "source_id": "SRC-PPCT-MATH7-2026",
        "source_version": source_version,
        "academic_year": "2026-2027",
        "subject_code": "MATH",
        "grade_level": 7,
        "external_item_key": external_item_key,
        "canonical_lesson_id": (
            canonical_lesson_id
        ),
        "status": status,
        "schema_version": 1,
        "provenance": {
            "source_document_id": (
                "SRC-PPCT-MATH7-2026"
            ),
            "mapping_method": (
                "MANUAL_VERIFIED"
            ),
            "verified_by": (
                "CURRICULUM_REVIEW"
            ),
            "source_location": (
                "workbook:PPCT"
            ),
            "source_version": source_version,
        },
    }


def _dataset(*bindings):
    return {
        "dataset_id": "DATASET-MATH7-PPCT-V7",
        "schema_version": 1,
        "bindings": list(bindings),
    }


def test_valid_dataset_loads_into_binding_objects():
    dataset = (
        SourceCanonicalBindingJsonLoader()
        .load_payload(
            _dataset(
                _binding(),
            )
        )
    )

    assert (
        dataset.dataset_id
        == "DATASET-MATH7-PPCT-V7"
    )
    assert len(dataset.bindings) == 1
    assert (
        dataset.bindings[0].status
        == "VERIFIED"
    )


def test_loaded_dataset_drives_registry_without_code_mapping():
    dataset = (
        SourceCanonicalBindingJsonLoader()
        .load_payload(
            _dataset(
                _binding(),
            )
        )
    )

    registry = (
        InMemorySourceCanonicalBindingRegistry(
            dataset.bindings
        )
    )

    result = registry.resolve_verified(
        CurriculumSourceItem(
            source_type="PPCT",
            source_id="SRC-PPCT-MATH7-2026",
            source_version="7",
            academic_year="2026-2027",
            subject_code="MATH",
            grade_level=7,
            external_item_key="PERIOD:0001",
            sequence=1,
            title="Tên hiển thị bất kỳ",
        )
    )

    assert (
        result.canonical_lesson_id
        == "TB-MATH7-KNTT-L001"
    )


def test_source_version_is_data_not_code():
    v7 = (
        SourceCanonicalBindingJsonLoader()
        .load_payload(
            _dataset(
                _binding(
                    source_version="7",
                ),
            )
        )
    )

    v8_payload = _dataset(
        _binding(
            binding_id="BIND-008",
            source_version="8",
        ),
    )
    v8_payload["dataset_id"] = (
        "DATASET-MATH7-PPCT-V8"
    )

    v8 = (
        SourceCanonicalBindingJsonLoader()
        .load_payload(v8_payload)
    )

    assert (
        v7.bindings[0].source_version
        == "7"
    )
    assert (
        v8.bindings[0].source_version
        == "8"
    )


def test_unknown_root_field_fails_closed():
    payload = _dataset(
        _binding(),
    )
    payload["unexpected"] = True

    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="unknown fields",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_payload(payload)
        )


def test_unknown_binding_field_fails_closed():
    row = _binding()
    row["lesson_title_guess"] = "Không dùng"

    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="unknown fields",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_payload(
                _dataset(row)
            )
        )


def test_unsupported_schema_version_fails_closed():
    payload = _dataset(
        _binding(),
    )
    payload["schema_version"] = 2

    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="unsupported",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_payload(payload)
        )


def test_duplicate_binding_id_fails_closed():
    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="duplicate binding_id",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_payload(
                _dataset(
                    _binding(
                        binding_id="DUP",
                        external_item_key=(
                            "PERIOD:0001"
                        ),
                    ),
                    _binding(
                        binding_id="DUP",
                        external_item_key=(
                            "PERIOD:0002"
                        ),
                    ),
                )
            )
        )


def test_multiple_verified_same_identity_fail_at_load_time():
    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="multiple VERIFIED",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_payload(
                _dataset(
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


def test_candidate_and_verified_same_identity_can_coexist():
    dataset = (
        SourceCanonicalBindingJsonLoader()
        .load_payload(
            _dataset(
                _binding(
                    binding_id="CANDIDATE",
                    status="CANDIDATE",
                ),
                _binding(
                    binding_id="VERIFIED",
                    status="VERIFIED",
                ),
            )
        )
    )

    assert len(dataset.bindings) == 2


def test_json_text_loader_rejects_invalid_json():
    with pytest.raises(
        SourceCanonicalBindingDataError,
        match="not valid JSON",
    ):
        (
            SourceCanonicalBindingJsonLoader()
            .load_text("{")
        )


def test_payload_round_trip_is_plain_data():
    payload = _dataset(
        _binding(),
    )

    text = json.dumps(
        payload,
        ensure_ascii=False,
    )

    dataset = (
        SourceCanonicalBindingJsonLoader()
        .load_text(text)
    )

    assert (
        dataset.bindings[0]
        .external_item_key
        == "PERIOD:0001"
    )
