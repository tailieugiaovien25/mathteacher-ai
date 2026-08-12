import json
from collections import defaultdict
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "canonical" / "mathematics" / "grade_09" / "curriculum_nodes.json"

def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def test_grade09_file_exists():
    assert DATA_FILE.exists()

def test_grade09_metadata():
    d = load_data()
    assert d["schema_version"] == 1
    assert d["curriculum_ref"] == "CURRICULUM-MATH-2018"
    assert d["grade"] == 9

def test_grade09_all_nodes_in_order():
    ns = load_data()["nodes"]
    assert len(ns) == 41
    assert [n["curriculum_node_id"] for n in ns] == [f"CURR-NODE-MATH-G9-{i:03d}" for i in range(1, 42)]

def test_grade09_unique_ids_codes():
    ns = load_data()["nodes"]
    ids = [n["curriculum_node_id"] for n in ns]
    codes = [n["code"] for n in ns]
    assert len(ids) == len(set(ids))
    assert len(codes) == len(set(codes))

def test_grade09_parent_refs_exist():
    ns = load_data()["nodes"]
    ids = {n["curriculum_node_id"] for n in ns}
    assert all(n["parent_id"] is None or n["parent_id"] in ids for n in ns)

def test_grade09_nodes_well_formed():
    allowed = {"CONTENT_STRAND","CONTENT_DOMAIN","CONTENT_GROUP","CONTENT_ITEM"}
    for n in load_data()["nodes"]:
        assert n["node_type"] in allowed
        assert n["status"] == "ACTIVE"
        assert n["name"].strip() and n["code"].strip()

def test_grade09_root_strands():
    roots = [n for n in load_data()["nodes"] if n["parent_id"] is None]
    assert [n["name"] for n in roots] == ["Số và Đại số","Hình học và Đo lường","Một số yếu tố Thống kê và Xác suất"]
    assert [n["sequence"] for n in roots] == [1,2,3]

def test_grade09_sibling_sequences_unique():
    d = defaultdict(list)
    for n in load_data()["nodes"]:
        d[n["parent_id"]].append(n)
    for ss in d.values():
        seq = [n["sequence"] for n in ss]
        assert len(seq) == len(set(seq))
