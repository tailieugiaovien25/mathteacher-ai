from dataclasses import dataclass

import pytest

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(
        self,
        client,
        table_name,
    ):
        self.client = client
        self.table_name = table_name
        self.operation = None
        self.row = None
        self.filters = []
        self.orders = []
        self.limit_value = None

    def upsert(
        self,
        row,
        on_conflict,
    ):
        self.operation = "upsert"
        self.row = dict(row)
        self.on_conflict = on_conflict
        return self

    def select(
        self,
        columns,
    ):
        self.operation = "select"
        return self

    def eq(
        self,
        column,
        value,
    ):
        self.filters.append(
            (column, value)
        )
        return self

    def order(
        self,
        column,
    ):
        self.orders.append(
            column
        )
        return self

    def limit(
        self,
        value,
    ):
        self.limit_value = value
        return self

    def execute(self):
        rows = self.client.tables[
            self.table_name
        ]

        if self.operation == "upsert":
            key = self.on_conflict

            rows[
                self.row[key]
            ] = dict(
                self.row
            )

            return Response(
                [dict(self.row)]
            )

        result = list(
            rows.values()
        )

        for column, value in self.filters:
            result = [
                row
                for row in result
                if row.get(column)
                == value
            ]

        for column in reversed(
            self.orders
        ):
            result.sort(
                key=lambda row: (
                    row.get(column)
                    if row.get(column)
                    is not None
                    else ""
                )
            )

        if self.limit_value is not None:
            result = result[
                :self.limit_value
            ]

        return Response(
            [
                dict(row)
                for row in result
            ]
        )


class FakeClient:
    def __init__(self):
        self.tables = {
            "subjects": {},
            "subject_components": {},
        }

    def table(
        self,
        table_name,
    ):
        assert table_name in self.tables

        return FakeQuery(
            self,
            table_name,
        )


def _subject(
    *,
    subject_id="subject-math",
    code="MATH",
    name="Toan",
    component_policy=(
        SubjectComponentPolicy.REQUIRED
    ),
    status=CatalogStatus.ACTIVE,
    display_order=1,
):
    return Subject(
        subject_id=subject_id,
        code=code,
        name=name,
        component_policy=(
            component_policy
        ),
        status=status,
        display_order=display_order,
    )


def _component(
    *,
    component_id="component-algebra",
    subject_id="subject-math",
    code="ALGEBRA",
    name="Dai so",
    status=CatalogStatus.ACTIVE,
    display_order=1,
    description=None,
):
    return SubjectComponent(
        component_id=component_id,
        subject_id=subject_id,
        code=code,
        name=name,
        status=status,
        display_order=display_order,
        description=description,
    )


def test_save_and_get_subject():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    saved = repository.save_subject(
        subject=_subject()
    )

    assert saved.subject_id == "subject-math"
    assert saved.code == "MATH"
    assert (
        saved.component_policy
        is SubjectComponentPolicy.REQUIRED
    )

    loaded = repository.get_subject(
        subject_id="subject-math"
    )

    assert loaded is not None
    assert loaded.name == "Toan"


def test_save_and_get_component():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    saved = repository.save_component(
        component=_component(
            description="Algebra component",
        )
    )

    assert (
        saved.component_id
        == "component-algebra"
    )

    loaded = repository.get_component(
        component_id="component-algebra"
    )

    assert loaded is not None
    assert (
        loaded.subject_id
        == "subject-math"
    )
    assert (
        loaded.description
        == "Algebra component"
    )


def test_list_subjects_filters_status():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    repository.save_subject(
        subject=_subject(
            subject_id="subject-math",
            code="MATH",
            name="Toan",
            status=CatalogStatus.ACTIVE,
            display_order=2,
        )
    )

    repository.save_subject(
        subject=_subject(
            subject_id="subject-old",
            code="OLD",
            name="Old subject",
            status=CatalogStatus.INACTIVE,
            display_order=1,
        )
    )

    active = repository.list_subjects(
        status=CatalogStatus.ACTIVE
    )

    assert len(active) == 1
    assert (
        active[0].subject_id
        == "subject-math"
    )


def test_list_subjects_orders_by_display_order_then_name():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    repository.save_subject(
        subject=_subject(
            subject_id="subject-b",
            code="B",
            name="B",
            display_order=2,
        )
    )

    repository.save_subject(
        subject=_subject(
            subject_id="subject-a",
            code="A",
            name="A",
            display_order=1,
        )
    )

    subjects = repository.list_subjects()

    assert [
        item.subject_id
        for item in subjects
    ] == [
        "subject-a",
        "subject-b",
    ]


def test_list_components_filters_by_subject():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    repository.save_component(
        component=_component(
            component_id="math-algebra",
            subject_id="subject-math",
            code="ALGEBRA",
            name="Dai so",
            display_order=2,
        )
    )

    repository.save_component(
        component=_component(
            component_id="math-geometry",
            subject_id="subject-math",
            code="GEOMETRY",
            name="Hinh hoc",
            display_order=1,
        )
    )

    repository.save_component(
        component=_component(
            component_id="art-music",
            subject_id="subject-art",
            code="MUSIC",
            name="Am nhac",
        )
    )

    components = (
        repository.list_components(
            subject_id="subject-math"
        )
    )

    assert [
        item.component_id
        for item in components
    ] == [
        "math-geometry",
        "math-algebra",
    ]


def test_list_components_can_load_all_subjects():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    repository.save_component(
        component=_component(
            component_id="math-algebra",
            subject_id="subject-math",
            code="ALGEBRA",
            name="Dai so",
            display_order=1,
        )
    )

    repository.save_component(
        component=_component(
            component_id="art-music",
            subject_id="subject-art",
            code="MUSIC",
            name="Am nhac",
            display_order=2,
        )
    )

    components = repository.list_components()

    assert {
        item.component_id
        for item in components
    } == {
        "math-algebra",
        "art-music",
    }


def test_list_components_filters_status():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    repository.save_component(
        component=_component(
            component_id="component-active",
            status=CatalogStatus.ACTIVE,
        )
    )

    repository.save_component(
        component=_component(
            component_id="component-inactive",
            status=CatalogStatus.INACTIVE,
        )
    )

    active = repository.list_components(
        subject_id="subject-math",
        status=CatalogStatus.ACTIVE,
    )

    assert len(active) == 1
    assert (
        active[0].component_id
        == "component-active"
    )


def test_missing_subject_returns_none():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    assert (
        repository.get_subject(
            subject_id="missing"
        )
        is None
    )


def test_missing_component_returns_none():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    assert (
        repository.get_component(
            component_id="missing"
        )
        is None
    )


def test_save_subject_requires_subject():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    with pytest.raises(TypeError):
        repository.save_subject(
            subject="MATH"
        )


def test_save_component_requires_component():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    with pytest.raises(TypeError):
        repository.save_component(
            component="ALGEBRA"
        )


def test_status_filter_type_is_validated():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    with pytest.raises(TypeError):
        repository.list_subjects(
            status="ACTIVE"
        )

    with pytest.raises(TypeError):
        repository.list_components(
            subject_id="subject-math",
            status="ACTIVE",
        )


def test_blank_subject_id_is_blocked():
    repository = (
        SupabaseSubjectCatalogRepository(
            client=FakeClient()
        )
    )

    with pytest.raises(ValueError):
        repository.get_subject(
            subject_id="   "
        )

    with pytest.raises(ValueError):
        repository.list_components(
            subject_id="   "
        )


def test_repository_requires_client():
    with pytest.raises(ValueError):
        SupabaseSubjectCatalogRepository(
            client=None
        )
