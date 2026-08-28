from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250014_assessment_exam_variants.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_variant_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_three_variant_tables_are_created() -> None:
    text = _migration_text()

    tables = re.findall(
        r"create table if not exists\s+"
        r"public\.(assessment_[a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "assessment_exam_variants",
        "assessment_exam_variant_questions",
        "assessment_exam_variant_option_mappings",
    ]


def test_variant_is_generated_from_snapshot_only() -> None:
    text = _migration_text()

    assert "snapshot_id uuid not null" in text
    assert "source_snapshot_document" in text
    assert "snapshot.snapshot_document" in text
    assert "assessment_exam_snapshot_hash_matches" in text


def test_only_owner_generates_variant() -> None:
    text = _migration_text()

    assert "source_owner_user_id" in text
    assert "source_owner_user_id is distinct from" in text
    assert "Only the exam owner may generate variants." in text


def test_seed_and_sha256_make_order_deterministic() -> None:
    text = _migration_text()

    assert "generation_seed text not null" in text
    assert "target_generation_seed" in text
    assert "extensions.digest(" in text
    assert "'sha256'" in text
    assert "question_order_key" in text
    assert "option_order_key" in text


def test_only_questions_with_options_are_shuffleable() -> None:
    text = _migration_text()

    assert "question_shuffle_allowed" in text
    assert "jsonb_typeof(" in text
    assert "question_element -> 'options'" in text
    assert "jsonb_array_length(" in text


def test_non_option_questions_keep_original_position() -> None:
    text = _migration_text()

    assert (
        "else\n"
        "                ranked_questions.original_display_number"
    ) in text


def test_shuffle_uses_existing_slots_within_matrix_cell() -> None:
    text = _migration_text()

    assert "shuffle_slots" in text
    assert "array_agg(" in text
    assert "display_numbers[" in text
    assert "ranked_questions.shuffled_rank::integer" in text
    assert "partition by blueprint_cell_id" in text
    assert "group by blueprint_cell_id" in text
    assert (
        "shuffle_slots.blueprint_cell_id =\n"
        "            ranked_questions.blueprint_cell_id"
    ) in text
    assert "cross join shuffle_slots" not in text


def test_option_mapping_preserves_correctness() -> None:
    text = _migration_text()

    assert "original_option_code" in text
    assert "variant_option_code" in text
    assert "variant_sequence_number" in text
    assert "is_correct boolean not null" in text
    assert "option_element ->> 'is_correct'" in text


def test_option_count_is_limited_to_alphabet_labels() -> None:
    text = _migration_text()

    assert "> 26" in text
    assert "may not exceed 26 options" in text
    assert "chr(" in text


def test_variant_hash_covers_question_and_option_mapping() -> None:
    text = _migration_text()

    assert "'original_exam_question_id'" in text
    assert "'variant_display_number'" in text
    assert "'original_option_code'" in text
    assert "'variant_option_code'" in text
    assert "computed_variant_hash" in text


def test_variant_locks_after_generation() -> None:
    text = _migration_text()

    assert "variant_status = 'LOCKED'" in text
    assert "prevent_assessment_exam_variant_mutation" in text
    assert "before update or delete" in text
    assert "variants are immutable" in text
    assert "if tg_op = 'DELETE' then" in text
    assert "return old;" in text
    assert "return new;" in text
    assert "old.variant_question_id" in text
    assert "new.variant_question_id" in text
    assert "coalesce(\n            new.variant_id" not in text


def test_variant_tables_have_select_only_grants() -> None:
    text = _migration_text()

    start = text.index(
        "grant select\n"
        "on table\n"
        "    public.assessment_exam_variants"
    )
    end = text.index(
        "create policy",
        start,
    )
    grant_text = text[start:end]

    assert "insert" not in grant_text
    assert "update" not in grant_text
    assert "delete" not in grant_text


def test_rls_covers_all_variant_tables() -> None:
    text = _migration_text()

    for table_name in (
        "assessment_exam_variants",
        "assessment_exam_variant_questions",
        "assessment_exam_variant_option_mappings",
    ):
        assert (
            f"alter table public.{table_name}\n"
            "    enable row level security;"
        ) in text

    assert "assessment_exam_version_is_visible" in text
    assert "from anon;" in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")


