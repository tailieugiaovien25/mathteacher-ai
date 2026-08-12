import json
from collections import defaultdict
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "canonical" / "mathematics" / "grade_07" / "curriculum_nodes.json"
)

def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def test_grade07_curriculum_nodes_file_exists():
    assert DATA_FILE.exists()

def test_grade07_metadata():
    data = load_data()
    assert data["schema_version"] == 1
    assert data["curriculum_ref"] == "CURRICULUM-MATH-2018"
    assert data["grade"] == 7

def test_all_41_nodes_exist_in_canonical_order():
    nodes = load_data()["nodes"]
    assert len(nodes) == 41
    assert [n["curriculum_node_id"] for n in nodes] == [
        f"CURR-NODE-MATH-G7-{i:03d}" for i in range(1, 42)
    ]

def test_grade07_node_ids_and_codes_are_unique():
    nodes = load_data()["nodes"]
    ids = [n["curriculum_node_id"] for n in nodes]
    codes = [n["code"] for n in nodes]
    assert len(ids) == len(set(ids))
    assert len(codes) == len(set(codes))

def test_grade07_nodes_are_well_formed():
    allowed = {"CONTENT_STRAND","CONTENT_DOMAIN","CONTENT_GROUP","CONTENT_ITEM"}
    for n in load_data()["nodes"]:
        assert n["status"] == "ACTIVE"
        assert n["node_type"] in allowed
        assert isinstance(n["sequence"], int) and n["sequence"] >= 1
        assert n["name"].strip()
        assert n["code"].strip()

def test_grade07_parent_references_exist():
    nodes = load_data()["nodes"]
    ids = {n["curriculum_node_id"] for n in nodes}
    for n in nodes:
        if n["parent_id"] is not None:
            assert n["parent_id"] in ids

def test_grade07_root_strands():
    roots = [n for n in load_data()["nodes"] if n["parent_id"] is None]
    assert [n["curriculum_node_id"] for n in roots] == [
        "CURR-NODE-MATH-G7-001",
        "CURR-NODE-MATH-G7-015",
        "CURR-NODE-MATH-G7-030",
    ]
    assert [n["sequence"] for n in roots] == [1,2,3]

def test_grade07_sibling_sequences_are_unique():
    by_parent = defaultdict(list)
    for n in load_data()["nodes"]:
        by_parent[n["parent_id"]].append(n)
    for siblings in by_parent.values():
        seq = [n["sequence"] for n in siblings]
        assert len(seq) == len(set(seq))
