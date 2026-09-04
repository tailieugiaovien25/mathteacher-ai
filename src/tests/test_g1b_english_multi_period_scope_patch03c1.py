from document_standardization.lesson_plan_multi_period_scope import (
    PeriodScopeStatus,
    resolve_multi_period_scope,
)


def context():
    return {
        "curriculum_periods": [10, 11, 12],
        "occurrences": [
            {"curriculum_period": 10, "teaching_date": "2026-09-14", "class_id": "6A1", "timetable_period": 2},
            {"curriculum_period": 10, "teaching_date": "2026-09-14", "class_id": "6A2", "timetable_period": 1},
            {"curriculum_period": 11, "teaching_date": "2026-09-15", "class_id": "6A1", "timetable_period": 1},
            {"curriculum_period": 11, "teaching_date": "2026-09-15", "class_id": "6A2", "timetable_period": 3},
            {"curriculum_period": 12, "teaching_date": "2026-09-16", "class_id": "6A1", "timetable_period": 1},
            {"curriculum_period": 12, "teaching_date": "2026-09-16", "class_id": "6A2", "timetable_period": 1},
        ],
    }


def test_maps_each_selected_period_to_its_own_occurrences():
    result = resolve_multi_period_scope(group_context=context(), document_periods=range(9, 16))
    mapped = result.occurrence_map()
    assert tuple(mapped) == (10, 11, 12)
    assert {item.teaching_date.isoformat() for item in mapped[10]} == {"2026-09-14"}
    assert {item.teaching_date.isoformat() for item in mapped[11]} == {"2026-09-15"}
    assert {item.teaching_date.isoformat() for item in mapped[12]} == {"2026-09-16"}


def test_periods_outside_week_are_locked_and_warned():
    result = resolve_multi_period_scope(group_context=context(), document_periods=range(9, 16))
    assert result.status is PeriodScopeStatus.PARTIAL
    assert result.document_periods_outside_scope == (9, 13, 14, 15)
    warned = {
        warning.curriculum_period
        for warning in result.warnings
        if warning.code == "DOCUMENT_PERIOD_OUTSIDE_SELECTED_SCOPE"
    }
    assert warned == {9, 13, 14, 15}


def test_selected_period_missing_from_document_is_reported():
    result = resolve_multi_period_scope(group_context=context(), document_periods=(9, 10, 11, 13, 14, 15))
    assert result.missing_document_periods == (12,)
    assert any(
        warning.code == "SELECTED_PERIOD_NOT_FOUND_IN_DOCUMENT"
        and warning.curriculum_period == 12
        for warning in result.warnings
    )


def test_missing_occurrence_blocks_unsafe_period_update():
    value = context()
    value["occurrences"] = [item for item in value["occurrences"] if item["curriculum_period"] != 11]
    result = resolve_multi_period_scope(group_context=value, document_periods=range(9, 16))
    assert result.occurrence_map()[11] == ()
    assert any(
        warning.code == "MISSING_PERIOD_OCCURRENCE"
        and warning.curriculum_period == 11
        for warning in result.warnings
    )


def test_no_selected_period_fails_closed():
    result = resolve_multi_period_scope(group_context={"occurrences": []}, document_periods=(9, 10))
    assert result.status is PeriodScopeStatus.FAILED
