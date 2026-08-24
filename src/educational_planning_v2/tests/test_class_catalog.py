import pytest

from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
    ClassCatalogStatus,
)


def test_class_catalog_builds_active_class():
    item = ClassCatalog(
        class_id="class-6a1-2026",
        academic_year="2026-2027",
        grade_level="6",
        class_code="6A1",
        class_name="L?p 6A1",
    )

    assert item.class_id == "class-6a1-2026"
    assert item.academic_year == "2026-2027"
    assert item.grade_level == "6"
    assert item.class_code == "6A1"
    assert item.class_name == "L?p 6A1"
    assert item.status is ClassCatalogStatus.ACTIVE
    assert item.display_name == "L?p 6A1"


def test_class_catalog_normalizes_text():
    item = ClassCatalog(
        class_id="  class-6a2-2026  ",
        academic_year="  2026-2027  ",
        grade_level="  6  ",
        class_code="  6A2  ",
        class_name="  L?p 6A2  ",
    )

    assert item.class_id == "class-6a2-2026"
    assert item.academic_year == "2026-2027"
    assert item.grade_level == "6"
    assert item.class_code == "6A2"
    assert item.class_name == "L?p 6A2"


def test_class_catalog_accepts_flexible_class_name():
    item = ClassCatalog(
        class_id="class-custom-1",
        academic_year="2026-2027",
        grade_level="6",
        class_code="6CLC",
        class_name="L?p 6 Ch?t l??ng cao",
    )

    assert item.class_code == "6CLC"
    assert item.class_name == "L?p 6 Ch?t l??ng cao"


def test_class_catalog_accepts_non_standard_grade_label():
    item = ClassCatalog(
        class_id="class-combined",
        academic_year="2026-2027",
        grade_level="6-7",
        class_code="6A-7A",
        class_name="L?p gh?p 6A-7A",
    )

    assert item.grade_level == "6-7"


@pytest.mark.parametrize(
    "field_name,kwargs",
    (
        (
            "class_id",
            {
                "class_id": " ",
                "academic_year": "2026-2027",
                "grade_level": "6",
                "class_code": "6A1",
                "class_name": "L?p 6A1",
            },
        ),
        (
            "academic_year",
            {
                "class_id": "class-1",
                "academic_year": " ",
                "grade_level": "6",
                "class_code": "6A1",
                "class_name": "L?p 6A1",
            },
        ),
        (
            "grade_level",
            {
                "class_id": "class-1",
                "academic_year": "2026-2027",
                "grade_level": " ",
                "class_code": "6A1",
                "class_name": "L?p 6A1",
            },
        ),
        (
            "class_code",
            {
                "class_id": "class-1",
                "academic_year": "2026-2027",
                "grade_level": "6",
                "class_code": " ",
                "class_name": "L?p 6A1",
            },
        ),
        (
            "class_name",
            {
                "class_id": "class-1",
                "academic_year": "2026-2027",
                "grade_level": "6",
                "class_code": "6A1",
                "class_name": " ",
            },
        ),
    ),
)
def test_class_catalog_rejects_empty_required_text(
    field_name,
    kwargs,
):
    with pytest.raises(
        ValueError,
        match=f"{field_name} must not be empty",
    ):
        ClassCatalog(
            **kwargs
        )


def test_class_catalog_rejects_invalid_status():
    with pytest.raises(
        TypeError,
        match="status must be ClassCatalogStatus",
    ):
        ClassCatalog(
            class_id="class-1",
            academic_year="2026-2027",
            grade_level="6",
            class_code="6A1",
            class_name="L?p 6A1",
            status="ACTIVE",
        )
