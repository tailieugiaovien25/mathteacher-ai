import json
from pathlib import Path


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


def test_first_requirement_files_exist():
    assert SOURCE_FILE.exists()
    assert NODES_FILE.exists()
    assert REQUIREMENTS_FILE.exists()


def test_first_requirement_references_authoritative_source():
    source = load_json(SOURCE_FILE)
    requirements = load_json(REQUIREMENTS_FILE)

    requirement = requirements["requirements"][0]

    assert requirement["provenance"]["source_document_id"] == (
        source["source_id"]
    )

    assert source["verification"]["source_status"] == "AUTHORITATIVE"


def test_first_requirement_references_existing_curriculum_node():
    nodes_data = load_json(NODES_FILE)
    requirements = load_json(REQUIREMENTS_FILE)

    requirement = requirements["requirements"][0]
    node_ids = {
        node["curriculum_node_id"]
        for node in nodes_data["nodes"]
    }

    assert requirement["curriculum_node_ref"] in node_ids
    assert requirement["curriculum_node_ref"] == (
        "CURR-NODE-MATH-G6-004"
    )


def test_first_requirement_identity():
    requirements = load_json(REQUIREMENTS_FILE)

    requirement = requirements["requirements"][0]

    assert requirement["canonical_id"] == "YCCD-MATH-06-0001"
    assert requirements["curriculum_ref"] == "CURRICULUM-MATH-2018"
    assert requirements["grade"] == 6


def test_first_requirement_text_is_present():
    requirements = load_json(REQUIREMENTS_FILE)

    requirement = requirements["requirements"][0]

    assert requirement["requirement_text_original"].strip() != ""


def test_first_requirement_verified_only_with_all_gates_pass():
    requirements = load_json(REQUIREMENTS_FILE)

    requirement = requirements["requirements"][0]
    validation = requirement["validation"]

    assert validation["text_integrity"] == "PASS"
    assert validation["structural_integrity"] == "PASS"
    assert validation["provenance_integrity"] == "PASS"
    assert validation["identity_integrity"] == "PASS"

    assert requirement["status"] == "VERIFIED"