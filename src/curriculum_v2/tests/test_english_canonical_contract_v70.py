import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE = (
    ROOT
    / "data"
    / "sources"
    / "SRC-CUR-ENGLISH-2018.json"
)

CONTRACT = (
    ROOT.parents[1]
    / "docs"
    / "curriculum_v2"
    / "ENGLISH_CANONICAL_CONTRACT.md"
)

CORE_MIGRATION = (
    ROOT.parents[1]
    / "supabase"
    / "migrations"
    / "202608260002_educational_core_identity_foundation.sql"
)


MOET = (
    "B\u1ed9 Gi\u00e1o d\u1ee5c "
    "v\u00e0 \u0110\u00e0o t\u1ea1o"
)

TIENG_ANH = (
    "Ti\u1ebfng Anh"
)

SOURCE_TITLE = (
    "Ch\u01b0\u01a1ng tr\u00ecnh "
    "gi\u00e1o d\u1ee5c ph\u1ed5 th\u00f4ng "
    "m\u00f4n Ti\u1ebfng Anh"
)

REGULATION = (
    "32/2018/TT-BGD\u0110T"
)


def _source():
    return json.loads(
        SOURCE.read_text(
            encoding="utf-8"
        )
    )


def _contract():
    return CONTRACT.read_text(
        encoding="utf-8"
    )


def test_english_authority_source_identity():
    data = _source()

    assert (
        data["source_id"]
        == "SRC-CUR-ENGLISH-2018"
    )

    assert (
        data["source_type"]
        == "OFFICIAL_CURRICULUM"
    )

    assert data["title"] == SOURCE_TITLE

    assert (
        data["legal_basis"]["regulation_id"]
        == REGULATION
    )

    assert (
        data["legal_authority"]["organization"]
        == MOET
    )

    assert (
        data["scope"]["target_grades"]
        == [6, 7, 8, 9]
    )


def test_english_subject_identity_is_locked():
    text = _contract()

    assert "subject-foreign-language-1" in text

    assert TIENG_ANH in text

    assert "Component policy: `NONE`" in text

    assert (
        "English MUST NOT be modeled "
        "as a subject component."
        in text
    )


def test_database_foundation_agrees_with_subject_identity():
    sql = CORE_MIGRATION.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "subject-foreign-language-1"
        in sql
    )

    assert (
        "name = '" + TIENG_ANH + "'"
        in sql
    )

    assert (
        "component_policy = 'NONE'"
        in sql
    )


def test_english_yccd_id_contract():
    text = _contract()

    assert (
        "YCCD-ENG-{GRADE_2_DIGITS}-"
        "{SEQUENCE_4_DIGITS}"
        in text
    )

    examples = (
        "YCCD-ENG-06-0001",
        "YCCD-ENG-07-0001",
        "YCCD-ENG-08-0001",
        "YCCD-ENG-09-0001",
    )

    pattern = re.compile(
        r"^YCCD-ENG-(06|07|08|09)-"
        r"\d{4}$"
    )

    assert all(
        pattern.fullmatch(value)
        for value in examples
    )


def test_english_curriculum_node_id_contract():
    text = _contract()

    examples = (
        "CURR-NODE-ENG-G6-001",
        "CURR-NODE-ENG-G7-001",
        "CURR-NODE-ENG-G8-001",
        "CURR-NODE-ENG-G9-001",
    )

    pattern = re.compile(
        r"^CURR-NODE-ENG-G[6-9]-"
        r"\d{3}$"
    )

    assert all(
        value in text
        and pattern.fullmatch(value)
        for value in examples
    )


def test_requirement_schema_reuses_canonical_fields():
    text = _contract()

    required = (
        "canonical_id",
        "curriculum_node_ref",
        "provenance",
        "requirement_text_original",
        "status",
        "validation",
    )

    for field in required:
        assert f"`{field}`" in text


def test_provenance_schema_is_locked():
    text = _contract()

    required = (
        "legal_authority",
        "regulation_id",
        "source_document_id",
        "source_location",
        "source_version",
        "verified_copy_id",
    )

    for field in required:
        assert f"`{field}`" in text

    assert (
        "SRC-CUR-ENGLISH-2018"
        in text
    )

    assert MOET in text

    assert REGULATION in text


def test_textbook_is_not_authority_source():
    text = _contract()

    assert (
        "Global Success is an initial "
        "textbook family"
        in text
    )

    assert (
        "not the authority source "
        "for canonical YCCD"
        in text
    )


def test_english_canonical_namespace_is_governed():
    canonical_root = (
        ROOT
        / "data"
        / "canonical"
    )

    official = (
        canonical_root
        / "english"
    )

    competing = (
        canonical_root
        / "foreign_language_1",
        canonical_root
        / "english_language",
    )

    assert official.is_dir()

    assert not any(
        candidate.exists()
        for candidate in competing
    )

    grade06 = (
        official
        / "grade_06"
    )

    assert (
        grade06
        / "curriculum_nodes.json"
    ).is_file()

    assert (
        grade06
        / "learning_requirements.json"
    ).is_file()


def test_source_and_contract_have_no_replacement_character():
    source_text = SOURCE.read_text(
        encoding="utf-8"
    )

    contract_text = CONTRACT.read_text(
        encoding="utf-8"
    )

    assert "\ufffd" not in source_text
    assert "\ufffd" not in contract_text
