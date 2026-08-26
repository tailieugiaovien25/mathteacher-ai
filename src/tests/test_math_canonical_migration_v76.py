from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608260005_math_canonical_assessment_projection.sql"
)

CANONICAL_ROOT = (
    ROOT
    / "src"
    / "curriculum_v2"
    / "data"
    / "canonical"
    / "mathematics"
)


def migration_text():
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def requirement_records(grade):
    data = json.loads(
        (
            CANONICAL_ROOT
            / f"grade_{grade:02d}"
            / "learning_requirements.json"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    return data["requirements"]


def node_records(grade):
    data = json.loads(
        (
            CANONICAL_ROOT
            / f"grade_{grade:02d}"
            / "curriculum_nodes.json"
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    if isinstance(data, list):
        return data

    if "nodes" in data:
        return data["nodes"]

    return data["curriculum_nodes"]


def test_math_migration_exists():
    assert MIGRATION.exists()


def test_math_program_is_reused_not_inserted():
    text = migration_text().lower()

    assert (
        "insert into public."
        "assessment_curriculum_programs"
        not in text
    )

    assert (
        "moet-gdpt2018-math-thcs"
        in text
    )


def test_math_topic_insert_count():
    text = migration_text()

    count = len(
        re.findall(
            r"insert\s+into\s+public\."
            r"assessment_curriculum_topics",
            text,
            flags=re.IGNORECASE,
        )
    )

    assert count == 165


def test_math_requirement_insert_count():
    text = migration_text()

    count = len(
        re.findall(
            r"insert\s+into\s+public\."
            r"assessment_learning_requirements",
            text,
            flags=re.IGNORECASE,
        )
    )

    assert count == 290


def test_math_on_conflict_count():
    text = migration_text()

    count = len(
        re.findall(
            r"\bon\s+conflict\b",
            text,
            flags=re.IGNORECASE,
        )
    )

    assert count == 455


def test_math_blind_update_prohibited():
    text = migration_text().lower()

    assert "do update set" not in text
    assert "update public.assessment_" not in text


def test_math_destructive_sql_prohibited():
    text = migration_text().lower()

    forbidden = (
        "truncate ",
        "drop table",
        "delete from public.assessment_",
    )

    for token in forbidden:
        assert token not in text


def test_legacy_topics_are_asserted():
    text = migration_text()

    for value in (
        "M6-SH",
        "M6-HH",
        "M6-TKXS",
    ):
        assert value in text

    assert text.count(
        "LEGACY_MATH_TOPIC_CONFLICT"
    ) == 3


def test_math_topic_conflict_guards():
    text = migration_text()

    canonical_topic_conflicts = (
        text.count(
            "MATH_TOPIC_CONFLICT:"
        )
        - text.count(
            "LEGACY_MATH_TOPIC_CONFLICT:"
        )
    )

    assert canonical_topic_conflicts == 165


def test_math_requirement_conflict_guards():
    text = migration_text()

    assert text.count(
        "MATH_REQUIREMENT_CONFLICT:"
    ) == 290


def test_all_canonical_node_ids_present():
    text = migration_text()

    expected = []

    for grade in range(6, 10):
        for node in node_records(grade):
            expected.append(
                node.get("curriculum_node_id")
                or node.get("node_id")
                or node.get("canonical_id")
            )

    assert len(expected) == 165
    assert len(set(expected)) == 165

    missing = [
        value
        for value in expected
        if value not in text
    ]

    assert missing == []


def test_all_math_yccd_ids_present():
    text = migration_text()

    expected = []

    for grade in range(6, 10):
        expected.extend(
            record["canonical_id"]
            for record
            in requirement_records(grade)
        )

    assert len(expected) == 290
    assert len(set(expected)) == 290

    missing = [
        value
        for value in expected
        if value not in text
    ]

    assert missing == []


def test_all_math_requirement_texts_present():
    text = migration_text()

    expected = []

    for grade in range(6, 10):
        expected.extend(
            record[
                "requirement_text_original"
            ]
            for record
            in requirement_records(grade)
        )

    assert len(expected) == 290

    missing = [
        value
        for value in expected
        if value.replace(
            "'",
            "''",
        ) not in text
    ]

    assert missing == []


def test_null_verified_copy_id_preserved():
    text = migration_text()

    records = []

    for grade in range(6, 10):
        records.extend(
            requirement_records(grade)
        )

    assert len(records) == 290

    assert all(
        record["provenance"].get(
            "verified_copy_id"
        )
        is None
        for record in records
    )

    assert (
        '"verified_copy_id":null'
        in text
    )


def test_metadata_column_contract():
    text = migration_text().lower()

    assert "metadata_json" not in text
    assert "metadata" in text


def test_postconditions_present():
    text = migration_text()

    required = (
        "MATH_CANONICAL_TOPIC_COUNT_INVALID",
        "MATH_TOTAL_TOPIC_COUNT_INVALID",
        "MATH_CANONICAL_REQUIREMENT_COUNT_INVALID",
        "MATH_ACTIVE_REQUIREMENT_COUNT_INVALID",
        "MATH_VERIFIED_REQUIREMENT_COUNT_INVALID",
        "MATH_LEGACY_TOPIC_COUNT_INVALID",
        "MATH_ORPHAN_PARENT_COUNT_INVALID",
        "MATH_ORPHAN_REQUIREMENT_COUNT_INVALID",
        "MATH_GRADE_DISTRIBUTION_INVALID",
    )

    for value in required:
        assert value in text
