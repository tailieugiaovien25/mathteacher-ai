from types import SimpleNamespace

import pytest

from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
    ClassCatalogStatus,
)


class FakeQuery:
    def __init__(
        self,
        rows=None,
    ):
        self.rows = [] if rows is None else rows
        self.calls = []

    def select(
        self,
        value,
    ):
        self.calls.append(
            ("select", value)
        )
        return self

    def upsert(
        self,
        row,
        on_conflict=None,
    ):
        self.calls.append(
            (
                "upsert",
                row,
                on_conflict,
            )
        )
        self.rows = [row]
        return self

    def eq(
        self,
        field,
        value,
    ):
        self.calls.append(
            ("eq", field, value)
        )
        return self

    def limit(
        self,
        value,
    ):
        self.calls.append(
            ("limit", value)
        )
        return self

    def order(
        self,
        value,
    ):
        self.calls.append(
            ("order", value)
        )
        return self

    def delete(
        self,
    ):
        self.calls.append(
            ("delete",)
        )
        return self

    def execute(
        self,
    ):
        return SimpleNamespace(
            data=self.rows
        )


class FakeClient:
    def __init__(
        self,
        rows=None,
    ):
        self.query = FakeQuery(
            rows=rows
        )
        self.table_names = []

    def table(
        self,
        table_name,
    ):
        self.table_names.append(
            table_name
        )
        return self.query


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SupabaseClassCatalogRepository(
            client=None
        )


def test_save_class():
    client = FakeClient()

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    item = ClassCatalog(
        class_id="class-6a1-2026",
        academic_year="2026-2027",
        grade_level="6",
        class_code="6A1",
        class_name="L\u1edbp 6A1",
    )

    result = repository.save(
        class_item=item
    )

    assert result.class_id == "class-6a1-2026"
    assert result.class_code == "6A1"
    assert result.class_name == "L\u1edbp 6A1"

    assert (
        client.table_names[-1]
        == "class_catalogs"
    )

    upsert_call = next(
        call
        for call in client.query.calls
        if call[0] == "upsert"
    )

    row = upsert_call[1]

    assert row["class_id"] == "class-6a1-2026"
    assert row["academic_year"] == "2026-2027"
    assert row["grade_level"] == "6"
    assert row["class_code"] == "6A1"
    assert row["class_name"] == "L\u1edbp 6A1"
    assert row["status"] == "ACTIVE"


def test_get_class():
    client = FakeClient(
        rows=[
            {
                "class_id": "class-7a1-2026",
                "academic_year": "2026-2027",
                "grade_level": "7",
                "class_code": "7A1",
                "class_name": "L\u1edbp 7A1",
                "status": "ACTIVE",
            }
        ]
    )

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    result = repository.get(
        class_id="class-7a1-2026"
    )

    assert result is not None
    assert result.class_code == "7A1"
    assert result.class_name == "L\u1edbp 7A1"


def test_get_returns_none_when_missing():
    client = FakeClient(
        rows=[]
    )

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    assert (
        repository.get(
            class_id="missing"
        )
        is None
    )


def test_list_classes_filters_by_year():
    client = FakeClient(
        rows=[
            {
                "class_id": "class-6a1-2026",
                "academic_year": "2026-2027",
                "grade_level": "6",
                "class_code": "6A1",
                "class_name": "L\u1edbp 6A1",
                "status": "ACTIVE",
            },
            {
                "class_id": "class-6a2-2026",
                "academic_year": "2026-2027",
                "grade_level": "6",
                "class_code": "6A2",
                "class_name": "L\u1edbp 6A2",
                "status": "ACTIVE",
            },
        ]
    )

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    result = repository.list_classes(
        academic_year="2026-2027"
    )

    assert len(result) == 2

    assert (
        ("eq", "academic_year", "2026-2027")
        in client.query.calls
    )

    assert (
        ("order", "grade_level")
        in client.query.calls
    )

    assert (
        ("order", "class_code")
        in client.query.calls
    )


def test_list_classes_filters_grade_level():
    client = FakeClient(
        rows=[]
    )

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    repository.list_classes(
        academic_year="2026-2027",
        grade_level="6",
    )

    assert (
        ("eq", "grade_level", "6")
        in client.query.calls
    )


def test_list_classes_filters_status():
    client = FakeClient(
        rows=[]
    )

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    repository.list_classes(
        academic_year="2026-2027",
        status=ClassCatalogStatus.ACTIVE,
    )

    assert (
        ("eq", "status", "ACTIVE")
        in client.query.calls
    )


def test_list_classes_rejects_invalid_status():
    client = FakeClient()

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    with pytest.raises(
        TypeError,
        match="status must be ClassCatalogStatus or None",
    ):
        repository.list_classes(
            academic_year="2026-2027",
            status="ACTIVE",
        )


def test_delete_class():
    client = FakeClient()

    repository = (
        SupabaseClassCatalogRepository(
            client=client
        )
    )

    repository.delete(
        class_id="class-6a1-2026"
    )

    assert (
        ("delete",)
        in client.query.calls
    )

    assert (
        ("eq", "class_id", "class-6a1-2026")
        in client.query.calls
    )


def test_response_rows_rejects_non_list():
    response = SimpleNamespace(
        data={}
    )

    with pytest.raises(
        TypeError,
        match="Supabase response data must be a list",
    ):
        (
            SupabaseClassCatalogRepository
            ._response_rows(
                response
            )
        )


def test_response_rows_rejects_non_dict_rows():
    response = SimpleNamespace(
        data=[
            "invalid"
        ]
    )

    with pytest.raises(
        TypeError,
        match="Supabase response rows must be dict",
    ):
        (
            SupabaseClassCatalogRepository
            ._response_rows(
                response
            )
        )
