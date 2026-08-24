from datetime import date
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

MODULE_PATH = Path(
    "src/lesson_planning_v2/services/lesson_plan_unit_selector_service.py"
)
SPEC = importlib.util.spec_from_file_location("v31_unit_selector", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
LessonPlanSelectionMode = MODULE.LessonPlanSelectionMode
LessonPlanUnitSelectorService = MODULE.LessonPlanUnitSelectorService


def _row(class_id: str, teaching_date: date, *, component: str = "music"):
    return SimpleNamespace(
        curriculum_period=1,
        lesson_title="Chủ đề 1: Ngày khai trường",
        lesson_id="lesson-opening-day",
        class_id=class_id,
        teaching_date=teaching_date,
        subject_ref="arts",
        component_ref=component,
        topic_id="",
        topic_title="",
    )


def test_same_subject_component_period_across_classes_is_one_option():
    units = LessonPlanUnitSelectorService().build_units(
        rows=(
            _row("7A1", date(2026, 9, 8)),
            _row("7A2", date(2026, 9, 10)),
        ),
        mode=LessonPlanSelectionMode.PERIOD,
    )
    assert len(units) == 1
    assert units[0].class_ids == ("7A1", "7A2")
    assert units[0].row_indices == (0, 1)


def test_period_identity_never_merges_another_component():
    units = LessonPlanUnitSelectorService().build_units(
        rows=(
            _row("7A1", date(2026, 9, 8), component="music"),
            _row("7A1", date(2026, 9, 9), component="fine-art"),
        ),
        mode=LessonPlanSelectionMode.PERIOD,
    )
    assert len(units) == 2


def test_standardization_fields_use_uniform_single_line_controls_and_scoped_keys():
    text = Path("src/portal_v2/ui/weekly_schedule_streamlit.py").read_text(
        encoding="utf-8-sig"
    )
    assert 'text_input(\n        "Lớp dạy"' in text
    assert 'text_input(\n        "Ngày dạy"' in text
    assert 'font-size:14px!important' in text
    assert "+ selected_subject_ref" in text
    assert "+ selected_component_ref" in text


def test_ai_linked_fields_are_same_height_single_line_controls():
    text = Path("src/portal_v2/ui/lesson_authoring_ai_streamlit.py").read_text(
        encoding="utf-8-sig"
    )
    assert '[class*="st-key-ai_"] input' in text
    assert "height:42px !important" in text
    for key in ("ai_class_", "ai_title_", "ai_tkb_", "ai_date_", "ai_equipment_"):
        assert f'key=f"{key}' in text
