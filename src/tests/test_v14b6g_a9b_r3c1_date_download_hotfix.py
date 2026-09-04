from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCOPE = ROOT / "src" / "document_standardization" / "lesson_plan_multi_period_scope.py"


def test_regex_import_and_first_period_planning_overlay():
    text = SCOPE.read_text(encoding="utf-8-sig")
    helper = text.split("def _remove_english_planning_field", 1)[1].split(
        "def apply_scoped_english_period_dates", 1
    )[0]
    assert "import re" in helper
    function_text = text.split("def apply_scoped_english_period_dates", 1)[1]
    assert "if period == planning_owner_period:" in function_text
    assert 'label="Date of planning"' in function_text
    assert 'label="Date of teaching"' in function_text


def test_later_period_planning_labels_are_removed():
    text = SCOPE.read_text(encoding="utf-8-sig")
    assert "planning_owner_period = min(selected) if selected else None" in text
    assert "period != planning_owner_period" in text
    assert "_remove_english_planning_field(planning_paragraph)" in text
