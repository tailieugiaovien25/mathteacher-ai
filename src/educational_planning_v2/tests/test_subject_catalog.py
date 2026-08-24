import pytest

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)


def test_subject_normalizes_text():
    subject = Subject(
        subject_id=" subject-toan ",
        code=" TOAN ",
        name=" Toan ",
        component_policy=(
            SubjectComponentPolicy.REQUIRED
        ),
    )

    assert subject.subject_id == "subject-toan"
    assert subject.code == "TOAN"
    assert subject.name == "Toan"


def test_subject_without_components_supported():
    subject = Subject(
        subject_id="subject-english",
        code="ENGLISH",
        name="Tieng Anh",
        component_policy=(
            SubjectComponentPolicy.NONE
        ),
    )

    assert (
        subject.component_policy
        is SubjectComponentPolicy.NONE
    )


def test_subject_with_required_components_supported():
    subject = Subject(
        subject_id="subject-math",
        code="MATH",
        name="Toan",
        component_policy=(
            SubjectComponentPolicy.REQUIRED
        ),
    )

    assert (
        subject.component_policy
        is SubjectComponentPolicy.REQUIRED
    )


def test_subject_component_links_to_subject():
    component = SubjectComponent(
        component_id="component-algebra",
        subject_id="subject-math",
        code="ALGEBRA",
        name="Dai so",
    )

    assert (
        component.subject_id
        == "subject-math"
    )


def test_one_subject_can_have_multiple_components():
    components = (
        SubjectComponent(
            component_id="math-arithmetic",
            subject_id="subject-math",
            code="ARITHMETIC",
            name="So hoc",
            display_order=1,
        ),
        SubjectComponent(
            component_id="math-algebra",
            subject_id="subject-math",
            code="ALGEBRA",
            name="Dai so",
            display_order=2,
        ),
        SubjectComponent(
            component_id="math-statistics",
            subject_id="subject-math",
            code="SXTK",
            name="SXTK",
            display_order=3,
        ),
        SubjectComponent(
            component_id="math-geometry",
            subject_id="subject-math",
            code="GEOMETRY",
            name="Hinh hoc",
            display_order=4,
        ),
    )

    assert len(components) == 4

    assert all(
        item.subject_id
        == "subject-math"
        for item in components
    )


def test_component_description_normalizes_blank_to_none():
    component = SubjectComponent(
        component_id="component-1",
        subject_id="subject-1",
        code="C1",
        name="Component 1",
        description="   ",
    )

    assert component.description is None


def test_invalid_subject_policy_blocked():
    with pytest.raises(TypeError):
        Subject(
            subject_id="subject-1",
            code="S1",
            name="Subject",
            component_policy="REQUIRED",
        )


def test_negative_subject_display_order_blocked():
    with pytest.raises(ValueError):
        Subject(
            subject_id="subject-1",
            code="S1",
            name="Subject",
            component_policy=(
                SubjectComponentPolicy.NONE
            ),
            display_order=-1,
        )


def test_component_status_type_required():
    with pytest.raises(TypeError):
        SubjectComponent(
            component_id="component-1",
            subject_id="subject-1",
            code="C1",
            name="Component",
            status="ACTIVE",
        )


def test_inactive_catalog_item_supported():
    component = SubjectComponent(
        component_id="component-1",
        subject_id="subject-1",
        code="C1",
        name="Component",
        status=CatalogStatus.INACTIVE,
    )

    assert (
        component.status
        is CatalogStatus.INACTIVE
    )
