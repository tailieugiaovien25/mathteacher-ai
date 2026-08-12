import json
from copy import deepcopy
from pathlib import Path

from curriculum_v2.validators.canonical_dataset_validator import (
    validate_canonical_dataset,
)


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_FILE = (
    BASE_DIR
    / "data"
    / "sources"
    / "SRC-CUR-MATH-2018.json"
)

NODES_FILE = (
    BASE_DIR
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "curriculum_nodes.json"
)

REQUIREMENTS_FILE = (
    BASE_DIR
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "learning_requirements.json"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def test_current_dataset_is_valid():
    errors = validate_canonical_dataset(
        REQUIREMENTS_FILE,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert errors == []


def test_duplicate_canonical_id_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    duplicate = deepcopy(data["requirements"][0])
    data["requirements"].append(duplicate)

    test_file = tmp_path / "requirements_duplicate.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert "DUPLICATE_CANONICAL_ID" in errors


def test_unknown_curriculum_node_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    data["requirements"][0]["curriculum_node_ref"] = (
        "CURR-NODE-MATH-G6-999"
    )

    test_file = tmp_path / "requirements_bad_node.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert (
        "UNKNOWN_CURRICULUM_NODE:YCCD-MATH-06-0001"
        in errors
    )


def test_unknown_source_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    data["requirements"][0]["provenance"][
        "source_document_id"
    ] = "SRC-UNKNOWN"

    test_file = tmp_path / "requirements_bad_source.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert "UNKNOWN_SOURCE:YCCD-MATH-06-0001" in errors


def test_empty_requirement_text_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    data["requirements"][0]["requirement_text_original"] = "   "

    test_file = tmp_path / "requirements_empty_text.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert (
        "EMPTY_REQUIREMENT_TEXT:YCCD-MATH-06-0001"
        in errors
    )


def test_invalid_verified_status_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    data["requirements"][0]["validation"][
        "provenance_integrity"
    ] = "PENDING"

    test_file = tmp_path / "requirements_bad_verified.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert (
        "INVALID_VERIFIED_STATUS:YCCD-MATH-06-0001"
        in errors
    )


def test_invalid_schema_version_is_detected(tmp_path):
    data = load_json(REQUIREMENTS_FILE)

    data["schema_version"] = 999

    test_file = tmp_path / "requirements_bad_schema.json"
    write_json(test_file, data)

    errors = validate_canonical_dataset(
        test_file,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert "INVALID_SCHEMA_VERSION" in errors