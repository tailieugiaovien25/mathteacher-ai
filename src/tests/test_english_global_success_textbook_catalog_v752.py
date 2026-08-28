from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/202608280003_english_global_success_textbook_catalog.sql"


def source() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_migration_exists_and_is_transactional():
    text = source().lower()
    assert text.startswith("begin;")
    assert text.rstrip().endswith("commit;")


def test_catalog_is_english_global_success_only():
    text = source()
    assert "subject-foreign-language-1" in text
    assert "ENGLISH-GLOBAL-SUCCESS" in text
    assert "subject-math" not in text


def test_five_restricted_sources_are_seeded():
    text = source()
    assert text.count("User-provided reference PDF;") == 5
    assert "'RESTRICTED','AUTHORIZED_USERS','ACTIVE'" in text


def test_all_reference_hashes_are_sha256():
    hashes = re.findall(r"'([0-9a-f]{64})'", source())
    assert len(hashes) == 5
    assert len(set(hashes)) == 5


def test_five_textbooks_are_seeded():
    text = source()
    book_rows = re.findall(r"\((6,[12]|[789],0),'[^']+',20(?:21|22|23|24)\)", text)
    assert len(book_rows) == 5  # five textbook catalog rows


def test_48_units_are_seeded():
    text = source()
    rows = re.findall(r"\(([6789]),(\d+),'([^']+)'\)", text)
    assert len(rows) == 48
    for grade in "6789":
        numbers = [int(number) for row_grade, number, _ in rows if row_grade == grade]
        assert numbers == list(range(1, 13))


def test_grade_six_units_are_split_between_two_volumes():
    text = source()
    assert "case when unit_number<=6 then 1 else 2 end" in text


def test_no_full_text_or_requirement_mapping_is_claimed():
    text = source()
    assert text.count("'full_text_stored',false") >= 3
    assert "requires_requirement_alignment_review',true" in text
    assert "learning_requirement_content_links" not in text


def test_expected_unit_titles_are_present():
    text = source()
    for title in (
        "My New School", "English-speaking Countries", "Life on Other Planets",
        "Vietnamese Lifestyle: Then and Now", "Career Choices",
    ):
        assert title in text
