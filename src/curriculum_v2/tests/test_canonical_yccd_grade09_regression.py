import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "canonical" / "mathematics" / "grade_09" / "learning_requirements.json"

def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def test_grade09_yccd_count_range():
    rs = load_data()["requirements"]
    assert len(rs) == 74
    assert rs[0]["canonical_id"] == "YCCD-MATH-09-0001"
    assert rs[-1]["canonical_id"] == "YCCD-MATH-09-0074"

def test_grade09_yccd_ids_contiguous_unique():
    rs = load_data()["requirements"]
    actual = [r["canonical_id"] for r in rs]
    assert actual == [f"YCCD-MATH-09-{i:04d}" for i in range(1, 75)]
    assert len(actual) == len(set(actual))

def test_grade09_yccd_verified():
    for r in load_data()["requirements"]:
        assert r["status"] == "VERIFIED"
        assert r["requirement_text_original"].strip()
        assert r["curriculum_node_ref"].startswith("CURR-NODE-MATH-G9-")
        assert all(v == "PASS" for v in r["validation"].values())
