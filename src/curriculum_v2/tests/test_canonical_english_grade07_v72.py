from collections import Counter
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

GRADE_ROOT = (
    ROOT
    / "data"
    / "canonical"
    / "english"
    / "grade_07"
)

NODES = GRADE_ROOT / "curriculum_nodes.json"

REQUIREMENTS = (
    GRADE_ROOT
    / "learning_requirements.json"
)


def load(path):
    return json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )


def test_grade07_files_exist():
    assert NODES.is_file()
    assert REQUIREMENTS.is_file()


def test_grade07_node_count():
    assert len(load(NODES)) == 10


def test_grade07_requirement_count():
    assert len(load(REQUIREMENTS)) == 11


def test_grade07_ids_are_contiguous():
    records = load(REQUIREMENTS)

    assert [
        record["canonical_id"]
        for record in records
    ] == [
        f"YCCD-ENG-07-{i:04d}"
        for i in range(1, 12)
    ]


def test_grade07_schema_is_canonical():
    expected = {
        "canonical_id",
        "curriculum_node_ref",
        "provenance",
        "requirement_text_original",
        "status",
        "validation",
    }

    for record in load(REQUIREMENTS):
        assert set(record) == expected


def test_grade07_skill_distribution():
    mapping = {
        "CURR-NODE-ENG-G7-003":
            "LISTENING",
        "CURR-NODE-ENG-G7-004":
            "SPEAKING",
        "CURR-NODE-ENG-G7-005":
            "READING",
        "CURR-NODE-ENG-G7-006":
            "WRITING",
    }

    counts = Counter(
        mapping[
            record["curriculum_node_ref"]
        ]
        for record in load(REQUIREMENTS)
    )

    assert counts == {
        "LISTENING": 3,
        "SPEAKING": 4,
        "READING": 2,
        "WRITING": 2,
    }


def test_grade07_provenance():
    records = load(REQUIREMENTS)

    for record in records:

        provenance = record["provenance"]

        assert (
            provenance["source_document_id"]
            == "SRC-CUR-ENGLISH-2018"
        )

        assert (
            provenance["source_version"]
            == "2018"
        )

        assert provenance[
            "source_location"
        ].startswith(
            "GRADE_7/LANGUAGE_SKILL/"
        )

        assert provenance[
            "verified_copy_id"
        ].startswith(
            "sha256:"
        )


def test_grade07_verified():
    for record in load(REQUIREMENTS):

        assert record["status"] == "VERIFIED"

        assert set(
            record["validation"].values()
        ) == {"PASS"}


def test_grade07_text_unique():
    records = load(REQUIREMENTS)

    texts = [
        record[
            "requirement_text_original"
        ].strip()
        for record in records
    ]

    assert all(texts)
    assert len(set(texts)) == 11


def test_grade07_quantitative_markers():
    payload = REQUIREMENTS.read_text(
        encoding="utf-8-sig"
    )

    assert "120 - 140" in payload
    assert "120 - 150" in payload
    assert "60 - 80" in payload


def test_grade07_no_residual_word_join_damage():
    import json

    records = json.loads(
        REQUIREMENTS.read_text(
            encoding="utf-8-sig"
        )
    )

    payload = "\n".join(
        record["requirement_text_original"]
        for record in records
    )

    assert "quenthu\u1ed9c" not in payload
