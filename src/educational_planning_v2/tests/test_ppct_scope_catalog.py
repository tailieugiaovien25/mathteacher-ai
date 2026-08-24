import pytest

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.services.ppct_scope_catalog import (
    PPCTScopeCatalog,
)


def test_catalog_builds_unique_scope_options():
    catalog = PPCTScopeCatalog()

    options = catalog.build_options(
        rows=(
            PPCTRow(
                subject_grade="Toan 6",
                sub_subject="Dai so",
                period=1,
                lesson_name="Lesson 1",
            ),
            PPCTRow(
                subject_grade="Toan 6",
                sub_subject="Dai so",
                period=2,
                lesson_name="Lesson 2",
            ),
            PPCTRow(
                subject_grade="Toan 6",
                sub_subject="Hinh hoc",
                period=3,
                lesson_name="Lesson 3",
            ),
        )
    )

    assert len(options) == 2
    assert options[0].subject_grade == "Toan 6"
    assert options[0].sub_subject == "Dai so"
    assert options[0].label == "Toan 6 | Dai so"


def test_scope_without_sub_subject_is_supported():
    options = PPCTScopeCatalog().build_options(
        rows=(
            PPCTRow(
                subject_grade="Subject 6",
                period=1,
                lesson_name="Lesson",
            ),
        )
    )

    assert len(options) == 1
    assert options[0].sub_subject is None
    assert options[0].label == "Subject 6"


def test_catalog_rejects_non_tuple():
    with pytest.raises(
        TypeError,
        match="rows must be a tuple",
    ):
        PPCTScopeCatalog().build_options(
            rows=[],
        )
