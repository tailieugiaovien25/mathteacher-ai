from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608260004_english_canonical_assessment_projection.sql"
)

CANONICAL_ROOT = (
    ROOT
    / "src"
    / "curriculum_v2"
    / "data"
    / "canonical"
    / "english"
)


def migration_text():
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_migration_exists():
    assert MIGRATION.is_file()


def test_migration_targets_expected_tables():
    text = migration_text()

    for table in (
        "assessment_curriculum_programs",
        "assessment_curriculum_topics",
        "assessment_learning_requirements",
    ):
        assert (
            f"public.{table}"
            in text
        )


def test_migration_has_expected_identity():
    text = migration_text()

    assert (
        "GDPT2018-ENGLISH-THCS"
        in text
    )

    assert (
        "subject-foreign-language-1"
        in text
    )

    assert (
        "program-vn-gdpt-2018"
        in text
    )

    assert (
        "FOREIGN_LANGUAGE_1"
        in text
    )


def test_migration_contains_all_canonical_ids():
    text = migration_text()

    expected = []

    for grade in range(6, 10):
        records = json.loads(
            (
                CANONICAL_ROOT
                / f"grade_{grade:02d}"
                / "learning_requirements.json"
            ).read_text(
                encoding="utf-8-sig"
            )
        )

        expected.extend(
            record["canonical_id"]
            for record in records
        )

    assert len(expected) == 46

    for canonical_id in expected:
        assert canonical_id in text


def test_migration_contains_all_topic_ids():
    text = migration_text()

    expected = []

    for grade in range(6, 10):
        nodes = json.loads(
            (
                CANONICAL_ROOT
                / f"grade_{grade:02d}"
                / "curriculum_nodes.json"
            ).read_text(
                encoding="utf-8-sig"
            )
        )

        expected.extend(
            node["curriculum_node_id"]
            for node in nodes
        )

    assert len(expected) == 40

    for node_id in expected:
        assert node_id in text


def test_migration_uses_assert_or_insert_policy():
    text = migration_text().lower()

    assert (
        text.count("on conflict")
        == 87
    )

    assert (
        "english_assessment_program_conflict"
        in text
    )

    assert (
        "english_topic_conflict"
        in text
    )

    assert (
        "english_requirement_conflict"
        in text
    )


def test_migration_does_not_blindly_update():
    text = migration_text().lower()

    assert (
        "do update set"
        not in text
    )

    assert (
        "update public.assessment_learning_requirements"
        not in text
    )

    assert (
        "update public.assessment_curriculum_topics"
        not in text
    )


def test_migration_has_no_destructive_assessment_sql():
    text = migration_text().lower()

    forbidden = (
        "truncate ",
        "drop table",
        "delete from public.assessment_",
    )

    for value in forbidden:
        assert value not in text


def test_migration_uses_metadata_not_metadata_json():
    text = migration_text()

    assert "metadata" in text
    assert "metadata_json" not in text


def test_migration_preserves_canonical_verified():
    text = migration_text()

    assert (
        '"canonical_status":"VERIFIED"'
        in text
    )

    assert (
        "metadata ->> 'canonical_status' = 'VERIFIED'"
        in text
    )


def test_migration_has_postcondition_counts():
    text = migration_text()

    for value in (
        "program_count <> 1",
        "topic_count <> 40",
        "requirement_count <> 46",
        "orphan_topic_count <> 0",
        "orphan_requirement_count <> 0",
        "verified_metadata_count <> 46",
        "active_requirement_count <> 46",
    ):
        assert value in text


def test_migration_is_utf8_clean():
    text = migration_text()

    assert "\ufffd" not in text

    # Question marks in SQL operators are not used here;
    # canonical Vietnamese data must not be corrupted.
    assert "Ch??ng" not in text
    assert "Ti?ng Anh" not in text


def test_migration_program_insert_precedes_topics():
    text = migration_text()

    program_pos = text.index(
        "insert into public.assessment_curriculum_programs"
    )

    first_topic_pos = text.index(
        "insert into public.assessment_curriculum_topics"
    )

    assert program_pos < first_topic_pos


def test_migration_grade_topics_precede_category_requirements():
    text = migration_text()

    for grade in range(6, 10):
        grade_topic = (
            f"CURR-NODE-ENG-G{grade}-001"
        )

        first_requirement = (
            f"YCCD-ENG-{grade:02d}-0001"
        )

        assert (
            text.index(grade_topic)
            < text.index(first_requirement)
        )


def test_migration_has_exact_requirement_insert_count():
    text = migration_text()

    count = len(
        re.findall(
            r"insert into public\."
            r"assessment_learning_requirements",
            text,
            flags=re.IGNORECASE,
        )
    )

    assert count == 46


def test_migration_has_exact_topic_insert_count():
    text = migration_text()

    count = len(
        re.findall(
            r"insert into public\."
            r"assessment_curriculum_topics",
            text,
            flags=re.IGNORECASE,
        )
    )

    assert count == 40
