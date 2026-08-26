from collections import Counter
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]

GRADE_ROOT = (
    ROOT
    / "data"
    / "canonical"
    / "english"
    / "grade_06"
)

NODES = (
    GRADE_ROOT
    / "curriculum_nodes.json"
)

REQUIREMENTS = (
    GRADE_ROOT
    / "learning_requirements.json"
)


def _load(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )


def test_grade06_files_exist():
    assert NODES.is_file()
    assert REQUIREMENTS.is_file()


def test_grade06_has_expected_nodes():
    nodes = _load(NODES)

    assert len(nodes) == 10

    ids = {
        node["curriculum_node_id"]
        for node in nodes
    }

    assert len(ids) == 10

    expected_codes = {
        "ENG-G6",
        "LANGUAGE_SKILL",
        "LISTENING",
        "SPEAKING",
        "READING",
        "WRITING",
        "LANGUAGE_KNOWLEDGE",
        "PRONUNCIATION",
        "VOCABULARY",
        "GRAMMAR",
    }

    assert {
        node["code"]
        for node in nodes
    } == expected_codes


def test_grade06_has_exactly_11_requirements():
    records = _load(REQUIREMENTS)

    assert len(records) == 11


def test_grade06_requirement_schema_is_canonical():
    records = _load(REQUIREMENTS)

    expected = {
        "canonical_id",
        "curriculum_node_ref",
        "provenance",
        "requirement_text_original",
        "status",
        "validation",
    }

    for record in records:
        assert set(record) == expected


def test_grade06_ids_are_contiguous():
    records = _load(REQUIREMENTS)

    expected = [
        f"YCCD-ENG-06-{index:04d}"
        for index in range(1, 12)
    ]

    assert [
        record["canonical_id"]
        for record in records
    ] == expected


def test_grade06_skill_distribution():
    records = _load(REQUIREMENTS)

    mapping = {
        "CURR-NODE-ENG-G6-003": "LISTENING",
        "CURR-NODE-ENG-G6-004": "SPEAKING",
        "CURR-NODE-ENG-G6-005": "READING",
        "CURR-NODE-ENG-G6-006": "WRITING",
    }

    counts = Counter(
        mapping[
            record["curriculum_node_ref"]
        ]
        for record in records
    )

    assert counts == {
        "LISTENING": 3,
        "SPEAKING": 4,
        "READING": 2,
        "WRITING": 2,
    }


def test_grade06_provenance_is_complete():
    records = _load(REQUIREMENTS)

    required = {
        "legal_authority",
        "regulation_id",
        "source_document_id",
        "source_location",
        "source_version",
        "verified_copy_id",
    }

    for record in records:

        provenance = record["provenance"]

        assert set(provenance) == required

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
            "GRADE_6/LANGUAGE_SKILL/"
        )

        assert provenance[
            "verified_copy_id"
        ].startswith(
            "sha256:"
        )


def test_grade06_validation_is_verified():
    records = _load(REQUIREMENTS)

    expected_validation = {
        "identity_integrity": "PASS",
        "provenance_integrity": "PASS",
        "structural_integrity": "PASS",
        "text_integrity": "PASS",
    }

    for record in records:

        assert (
            record["status"]
            == "VERIFIED"
        )

        assert (
            record["validation"]
            == expected_validation
        )


def test_grade06_text_is_nonempty_and_unique():
    records = _load(REQUIREMENTS)

    texts = [
        re.sub(
            r"\s+",
            " ",
            record[
                "requirement_text_original"
            ].strip(),
        )
        for record in records
    ]

    assert all(texts)

    assert len(set(texts)) == 11


def test_grade06_has_no_obvious_encoding_damage():
    payload = (
        NODES.read_text(
            encoding="utf-8-sig"
        )
        +
        REQUIREMENTS.read_text(
            encoding="utf-8-sig"
        )
    )

    assert "\ufffd" not in payload
    assert "Ti?ng" not in payload
    assert "Ng?" not in payload
    assert "Ch??ng" not in payload


def test_grade06_no_residual_word_join_damage():
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

    assert "thu\u1ed9c(c\u00f3" not in payload
