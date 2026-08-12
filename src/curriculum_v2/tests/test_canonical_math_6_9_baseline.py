import json
from pathlib import Path

CANONICAL_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "canonical"
    / "mathematics"
)

BASELINE = {
    6: {"nodes": 43, "requirements": 80},
    7: {"nodes": 41, "requirements": 68},
    8: {"nodes": 40, "requirements": 68},
    9: {"nodes": 41, "requirements": 74},
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def grade_dir(grade: int) -> Path:
    return CANONICAL_ROOT / f"grade_{grade:02d}"


def test_math_6_9_baseline_files_exist():
    for grade in BASELINE:
        root = grade_dir(grade)
        assert root.is_dir(), f"Missing grade directory: {root}"
        assert (root / "curriculum_nodes.json").is_file()
        assert (root / "learning_requirements.json").is_file()


def test_math_6_9_baseline_counts_are_locked():
    for grade, expected in BASELINE.items():
        nodes = load_json(grade_dir(grade) / "curriculum_nodes.json")["nodes"]
        reqs = load_json(
            grade_dir(grade) / "learning_requirements.json"
        )["requirements"]

        assert len(nodes) == expected["nodes"], (
            f"Grade {grade}: expected {expected['nodes']} nodes, "
            f"got {len(nodes)}"
        )
        assert len(reqs) == expected["requirements"], (
            f"Grade {grade}: expected {expected['requirements']} requirements, "
            f"got {len(reqs)}"
        )


def test_math_6_9_node_ids_are_contiguous_and_unique():
    for grade, expected in BASELINE.items():
        nodes = load_json(grade_dir(grade) / "curriculum_nodes.json")["nodes"]
        actual = [n["curriculum_node_id"] for n in nodes]
        expected_ids = [
            f"CURR-NODE-MATH-G{grade}-{i:03d}"
            for i in range(1, expected["nodes"] + 1)
        ]

        assert actual == expected_ids
        assert len(actual) == len(set(actual))


def test_math_6_9_yccd_ids_are_contiguous_and_unique():
    for grade, expected in BASELINE.items():
        reqs = load_json(
            grade_dir(grade) / "learning_requirements.json"
        )["requirements"]

        actual = [r["canonical_id"] for r in reqs]
        expected_ids = [
            f"YCCD-MATH-{grade:02d}-{i:04d}"
            for i in range(1, expected["requirements"] + 1)
        ]

        assert actual == expected_ids
        assert len(actual) == len(set(actual))


def test_math_6_9_requirement_node_refs_are_valid():
    for grade in BASELINE:
        nodes = load_json(grade_dir(grade) / "curriculum_nodes.json")["nodes"]
        reqs = load_json(
            grade_dir(grade) / "learning_requirements.json"
        )["requirements"]

        node_ids = {n["curriculum_node_id"] for n in nodes}

        for req in reqs:
            ref = req["curriculum_node_ref"]
            assert ref in node_ids, (
                f"{req['canonical_id']} references missing node {ref}"
            )


def test_math_6_9_no_cross_grade_identity_leakage():
    all_node_ids = []
    all_yccd_ids = []

    for grade in BASELINE:
        nodes = load_json(grade_dir(grade) / "curriculum_nodes.json")["nodes"]
        reqs = load_json(
            grade_dir(grade) / "learning_requirements.json"
        )["requirements"]

        node_prefix = f"CURR-NODE-MATH-G{grade}-"
        yccd_prefix = f"YCCD-MATH-{grade:02d}-"

        for node in nodes:
            assert node["curriculum_node_id"].startswith(node_prefix)
            all_node_ids.append(node["curriculum_node_id"])

        for req in reqs:
            assert req["canonical_id"].startswith(yccd_prefix)
            assert req["curriculum_node_ref"].startswith(node_prefix)
            all_yccd_ids.append(req["canonical_id"])

    assert len(all_node_ids) == len(set(all_node_ids))
    assert len(all_yccd_ids) == len(set(all_yccd_ids))


def test_math_6_9_verified_requirements_remain_verified():
    for grade in BASELINE:
        reqs = load_json(
            grade_dir(grade) / "learning_requirements.json"
        )["requirements"]

        for req in reqs:
            assert req["status"] == "VERIFIED"
            assert req["requirement_text_original"].strip()
            assert all(
                value == "PASS"
                for value in req["validation"].values()
            )
