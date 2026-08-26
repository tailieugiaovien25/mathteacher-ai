from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT
    / "data"
    / "canonical"
    / "english"
    / "grade_08"
    / "learning_requirements.json"
)


def _records():
    return json.loads(
        DATA_FILE.read_text(
            encoding="utf-8-sig"
        )
    )


def test_grade08_dataset_exists():
    assert DATA_FILE.exists()


def test_grade08_record_count():
    assert len(_records()) == 12


def test_grade08_canonical_id_sequence():
    records = _records()

    assert [
        record["canonical_id"]
        for record in records
    ] == [
        f"YCCD-ENG-08-{i:04d}"
        for i in range(1, 13)
    ]


def test_grade08_record_schema():
    required = {
        "canonical_id",
        "curriculum_node_ref",
        "provenance",
        "requirement_text_original",
        "status",
        "validation",
    }

    for record in _records():
        assert set(record) == required


def test_grade08_skill_distribution():
    records = _records()

    counts = {}

    for record in records:
        node = record[
            "curriculum_node_ref"
        ]

        counts[node] = (
            counts.get(node, 0) + 1
        )

    assert counts == {
        "CURR-NODE-ENG-G8-003": 3,
        "CURR-NODE-ENG-G8-004": 4,
        "CURR-NODE-ENG-G8-005": 3,
        "CURR-NODE-ENG-G8-006": 2,
    }


def test_grade08_authority_provenance():
    for record in _records():
        provenance = record["provenance"]

        assert (
            provenance["legal_authority"]
            == "Bộ Giáo dục và Đào tạo"
        )

        assert (
            provenance["regulation_id"]
            == "32/2018/TT-BGDĐT"
        )

        assert (
            provenance["source_document_id"]
            == "SRC-CUR-ENGLISH-2018"
        )

        assert provenance[
            "source_location"
        ]

        assert provenance[
            "verified_copy_id"
        ]


def test_grade08_quantitative_progression():
    text = "\n".join(
        record["requirement_text_original"]
        for record in _records()
    )

    assert "140 - 160" in text
    assert "150 - 180" in text
    assert "80 - 100" in text


def test_grade08_known_word_join_is_normalized():
    text = "\n".join(
        record["requirement_text_original"]
        for record in _records()
    )

    assert "các chủ đề" in text
    assert "cácchủ đề" not in text
    assert "ngữ điệu" in text
    assert "ngữđiệu" not in text


def test_grade08_expected_requirement_texts():
    records = _records()

    assert (
        records[0]["requirement_text_original"]
        == (
            "Nghe và nhận biết âm, trọng âm, "
            "ngữ điệu và nhịp điệu trong các "
            "câu ghép cơ bản."
        )
    )

    assert (
        records[1]["requirement_text_original"]
        == (
            "Nghe hiểu nội dung chính, nội dung "
            "chi tiết các đoạn hội thoại, độc "
            "thoại đơn giản khoảng 140 - 160 từ "
            "về các chủ đề trong Chương trình."
        )
    )

    assert (
        records[-1]["requirement_text_original"]
        == (
            "Viết các hướng dẫn, chỉ dẫn, "
            "thông báo, … ngắn, đơn giản khoảng "
            "80 - 100 từ liên quan đến các chủ "
            "đề quen thuộc."
        )
    )


def test_grade08_records_are_canonical_verified():
    expected = {
        "identity_integrity": "PASS",
        "provenance_integrity": "PASS",
        "structural_integrity": "PASS",
        "text_integrity": "PASS",
    }

    for record in _records():
        assert record["status"] == "VERIFIED"

        assert (
            record["validation"]
            == expected
        )


def test_grade08_no_known_word_join_damage():
    payload = "\n".join(
        record["requirement_text_original"]
        for record in _records()
    )

    bad_fragments = (
        "c\u01a1b\u1ea3n",
        "li\u00ean quan\u0111\u1ebfn",
        "t\u1eebli\u00ean quan",
        "c\u00e1cch\u1ee7 \u0111\u1ec1",
    )

    for fragment in bad_fragments:
        assert fragment not in payload


def test_grade08_curriculum_nodes_exist():
    node_file = (
        DATA_FILE.parent
        / "curriculum_nodes.json"
    )

    assert node_file.is_file()

    nodes = json.loads(
        node_file.read_text(
            encoding="utf-8-sig"
        )
    )

    assert len(nodes) == 10

    node_ids = {
        node["curriculum_node_id"]
        for node in nodes
    }

    for record in _records():
        assert (
            record["curriculum_node_ref"]
            in node_ids
        )
