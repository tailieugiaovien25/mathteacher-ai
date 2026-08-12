import json
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "canonical" / "mathematics" / "grade_07" / "learning_requirements.json"
)

def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def test_grade07_yccd_count_and_range():
    reqs = load_data()["requirements"]
    assert len(reqs) == 68
    assert reqs[0]["canonical_id"] == "YCCD-MATH-07-0001"
    assert reqs[-1]["canonical_id"] == "YCCD-MATH-07-0068"

def test_grade07_yccd_ids_are_contiguous_and_unique():
    reqs = load_data()["requirements"]
    expected = [f"YCCD-MATH-07-{i:04d}" for i in range(1, 69)]
    actual = [r["canonical_id"] for r in reqs]
    assert actual == expected
    assert len(actual) == len(set(actual))

def test_grade07_yccd_verified():
    for r in load_data()["requirements"]:
        assert r["status"] == "VERIFIED"
        assert r["requirement_text_original"].strip()
        assert r["curriculum_node_ref"].startswith("CURR-NODE-MATH-G7-")
        assert all(v == "PASS" for v in r["validation"].values())
