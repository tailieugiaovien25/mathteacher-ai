from collections import Counter
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

GRADE_ROOT = (
    ROOT
    / "data"
    / "canonical"
    / "english"
    / "grade_09"
)

NODES = (
    GRADE_ROOT
    / "curriculum_nodes.json"
)

REQUIREMENTS = (
    GRADE_ROOT
    / "learning_requirements.json"
)


def _load(path):
    return json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )


def test_grade09_files_exist():
    assert NODES.is_file()
    assert REQUIREMENTS.is_file()


def test_grade09_node_count():
    assert len(_load(NODES)) == 10


def test_grade09_requirement_count():
    assert len(_load(REQUIREMENTS)) == 12


def test_grade09_ids_are_contiguous():
    records = _load(REQUIREMENTS)

    assert [
        record["canonical_id"]
        for record in records
    ] == [
        f"YCCD-ENG-09-{i:04d}"
        for i in range(1, 13)
    ]


def test_grade09_canonical_schema():
    expected = {
        "canonical_id",
        "curriculum_node_ref",
        "provenance",
        "requirement_text_original",
        "status",
        "validation",
    }

    for record in _load(REQUIREMENTS):
        assert set(record) == expected


def test_grade09_skill_distribution():
    mapping = {
        "CURR-NODE-ENG-G9-003":
            "LISTENING",
        "CURR-NODE-ENG-G9-004":
            "SPEAKING",
        "CURR-NODE-ENG-G9-005":
            "READING",
        "CURR-NODE-ENG-G9-006":
            "WRITING",
    }

    counts = Counter(
        mapping[
            record[
                "curriculum_node_ref"
            ]
        ]
        for record in _load(
            REQUIREMENTS
        )
    )

    assert counts == {
        "LISTENING": 3,
        "SPEAKING": 4,
        "READING": 3,
        "WRITING": 2,
    }


def test_grade09_node_refs_exist():
    nodes = _load(NODES)

    node_ids = {
        node[
            "curriculum_node_id"
        ]
        for node in nodes
    }

    for record in _load(
        REQUIREMENTS
    ):
        assert (
            record[
                "curriculum_node_ref"
            ]
            in node_ids
        )


def test_grade09_provenance_contract():
    required = {
        "legal_authority",
        "regulation_id",
        "source_document_id",
        "source_location",
        "source_version",
        "verified_copy_id",
    }

    for record in _load(
        REQUIREMENTS
    ):
        provenance = record[
            "provenance"
        ]

        assert set(
            provenance
        ) == required

        assert (
            provenance[
                "source_document_id"
            ]
            == "SRC-CUR-ENGLISH-2018"
        )

        assert (
            provenance[
                "source_version"
            ]
            == "2018"
        )

        assert provenance[
            "source_location"
        ].startswith(
            "GRADE_9/LANGUAGE_SKILL/"
        )

        assert provenance[
            "verified_copy_id"
        ].startswith(
            "sha256:"
        )


def test_grade09_status_and_validation():
    expected_validation = {
        "identity_integrity":
            "PASS",
        "provenance_integrity":
            "PASS",
        "structural_integrity":
            "PASS",
        "text_integrity":
            "PASS",
    }

    for record in _load(
        REQUIREMENTS
    ):
        assert (
            record["status"]
            == "VERIFIED"
        )

        assert (
            record["validation"]
            == expected_validation
        )


def test_grade09_quantitative_markers():
    payload = (
        REQUIREMENTS.read_text(
            encoding="utf-8-sig"
        )
    )

    assert "160 - 180" in payload
    assert "180 - 200" in payload
    assert "100 - 120" in payload


def test_grade09_known_word_join_damage_absent():
    payload = "\n".join(
        record[
            "requirement_text_original"
        ]
        for record in _load(
            REQUIREMENTS
        )
    )

    bad = (
        "c\u00e1cch\u1ee7",
        "v\u1ec1quan",
        "giao"
        "ti\u1ebfp",
        "trongc\u00e1c",
        "t\u1eebli\u00ean",
    )

    for fragment in bad:
        assert fragment not in payload


def test_grade09_exact_known_normalizations():
    records = _load(
        REQUIREMENTS
    )

    by_id = {
        record["canonical_id"]:
        record[
            "requirement_text_original"
        ]
        for record in records
    }

    assert (
        "nhu c\u1ea7u giao ti\u1ebfp "
        "h\u1eb1ng ng\u00e0y"
        in by_id[
            "YCCD-ENG-09-0001"
        ]
    )

    assert (
        "v\u1ec1 c\u00e1c ch\u1ee7 "
        "\u0111\u1ec1 trong Ch\u01b0\u01a1ng tr\u00ecnh"
        in by_id[
            "YCCD-ENG-09-0002"
        ]
    )

    assert (
        "v\u1ec1 quan \u0111i\u1ec3m "
        "c\u00e1 nh\u00e2n"
        in by_id[
            "YCCD-ENG-09-0006"
        ]
    )
