from datetime import date
from io import BytesIO

from docx import Document

from document_standardization.lesson_plan_multi_period_scope import (
    apply_scoped_english_period_dates,
    resolve_multi_period_scope,
)


def build(periods, *, corrupted=False):
    document = Document()
    for period in periods:
        table = document.add_table(rows=1, cols=2)
        left, right = table.rows[0].cells
        left.text = "Date of planning:..........\nDate of teaching: ..........\nWEEK: 4"
        shown = 10 if corrupted else period
        right.text = f"Period {shown} : UNIT 2: MY HOUSE\nLesson for source period {period}"
    value = BytesIO()
    document.save(value)
    return value.getvalue()


def context():
    return {
        "curriculum_periods": [10, 11, 12],
        "occurrences": [
            {"curriculum_period": 10, "teaching_date": "2026-09-14", "class_id": "6A1"},
            {"curriculum_period": 10, "teaching_date": "2026-09-14", "class_id": "6A2"},
            {"curriculum_period": 11, "teaching_date": "2026-09-15", "class_id": "6A1"},
            {"curriculum_period": 11, "teaching_date": "2026-09-15", "class_id": "6A2"},
            {"curriculum_period": 12, "teaching_date": "2026-09-16", "class_id": "6A1"},
            {"curriculum_period": 12, "teaching_date": "2026-09-16", "class_id": "6A2"},
        ],
    }


def table_texts(content):
    document = Document(BytesIO(content))
    return ["\n".join(cell.text for row in table.rows for cell in row.cells) for table in document.tables]


def test_scoped_overlay_restores_periods_and_updates_only_10_to_12():
    periods = tuple(range(9, 16))
    scope = resolve_multi_period_scope(group_context=context(), document_periods=periods)
    result = apply_scoped_english_period_dates(
        source_content=build(periods),
        output_content=build(periods, corrupted=True),
        scope=scope,
        drafting_date=date(2026, 9, 11),
    )
    texts = table_texts(result.content)
    assert result.applied_periods == (10, 11, 12)
    for index, period in enumerate(periods):
        assert f"Period {period} " in texts[index]
        assert f"Lesson for source period {period}" in texts[index]
    assert "Date of planning: 11/09/2026" in texts[1]
    assert "Date of planning: 11/09/2026" in texts[2]
    assert "Date of planning: 11/09/2026" in texts[3]
    assert "Date of teaching: 6A1 - 14/09/2026; 6A2 - 14/09/2026" in texts[1]
    assert "Date of teaching: 6A1 - 15/09/2026; 6A2 - 15/09/2026" in texts[2]
    assert "Date of teaching: 6A1 - 16/09/2026; 6A2 - 16/09/2026" in texts[3]
    for index in (0, 4, 5, 6):
        assert "Date of planning:.........." in texts[index]
        assert "Date of teaching: .........." in texts[index]


def test_conflicting_dates_fail_closed_for_that_period():
    value = context()
    value["occurrences"].append(
        {"curriculum_period": 11, "teaching_date": "2026-09-16", "class_id": "6A3"}
    )
    periods = tuple(range(9, 16))
    scope = resolve_multi_period_scope(group_context=value, document_periods=periods)
    result = apply_scoped_english_period_dates(
        source_content=build(periods),
        output_content=build(periods, corrupted=True),
        scope=scope,
        drafting_date=date(2026, 9, 11),
    )
    assert result.applied_periods == (10, 11, 12)
    text = table_texts(result.content)[2]
    assert "6A1 - 15/09/2026; 6A2 - 15/09/2026; 6A3 - 16/09/2026" in text


def test_distinct_class_dates_are_written_as_class_date_pairs():
    value = context()
    value["curriculum_periods"] = [10]
    value["occurrences"] = [
        {
            "curriculum_period": 10,
            "teaching_date": "2026-09-14",
            "class_id": "6A1",
            "class_display": "6A1",
        },
        {
            "curriculum_period": 10,
            "teaching_date": "2026-09-15",
            "class_id": "6A2",
            "class_display": "6A2",
        },
    ]
    scope = resolve_multi_period_scope(group_context=value, document_periods=(10, 11))
    result = apply_scoped_english_period_dates(
        source_content=build((10, 11)),
        output_content=build((10, 11)),
        scope=scope,
        drafting_date=date(2026, 9, 11),
    )

    texts = table_texts(result.content)
    assert result.applied_periods == (10,)
    assert "Date of teaching: 6A1 - 14/09/2026; 6A2 - 15/09/2026" in texts[0]
    assert "Period 11" in texts[1]
    assert "Date of teaching: .........." in texts[1]


def test_separate_class_specific_teaching_fields_are_filled_independently():
    document = Document()
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = (
        "Date of planning:..........\n"
        "Date of teaching: .......... (for 6A1)\n"
        "Ngày dạy: .......... (đối với 6A2)\n"
        "WEEK: 4"
    )
    table.cell(0, 1).text = "Period 28: UNIT 4"
    source = BytesIO()
    document.save(source)
    context_value = {
        "curriculum_periods": [28],
        "occurrences": [
            {
                "curriculum_period": 28,
                "teaching_date": "2026-11-09",
                "class_id": "6A1",
                "class_display": "6A1",
            },
            {
                "curriculum_period": 28,
                "teaching_date": "2026-11-10",
                "class_id": "6A2",
                "class_display": "6A2",
            },
        ],
    }
    scope = resolve_multi_period_scope(group_context=context_value, document_periods=(28,))
    result = apply_scoped_english_period_dates(
        source_content=source.getvalue(),
        output_content=source.getvalue(),
        scope=scope,
        drafting_date=date(2026, 11, 6),
    )
    cell_text = table_texts(result.content)[0]

    assert "Date of planning: 06/11/2026" in cell_text
    assert "Date of teaching: 09/11/2026 (for 6A1)" in cell_text
    assert "Ngày dạy: 10/11/2026 (đối với 6A2)" in cell_text
