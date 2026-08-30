from types import SimpleNamespace

import pytest

from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_admin_repository import (
    SupabaseLessonPlanConfigurationAdminRepository,
)
from lesson_planning_v2.services.lesson_plan_configuration_admin_service import (
    LessonPlanConfigurationAdminError,
    LessonPlanConfigurationAdminService,
)


class FakeQuery:
    def __init__(self, table_name, recorder, response_rows):
        self.table_name = table_name
        self.recorder = recorder
        self.response_rows = response_rows

    def select(self, *args):
        self.recorder.append(("select", self.table_name, args))
        return self

    def insert(self, payload):
        self.recorder.append(("insert", self.table_name, payload))
        return self

    def update(self, payload):
        self.recorder.append(("update", self.table_name, payload))
        return self

    def eq(self, key, value):
        self.recorder.append(("eq", self.table_name, key, value))
        return self

    def limit(self, value):
        self.recorder.append(("limit", self.table_name, value))
        return self

    def order(self, value):
        self.recorder.append(("order", self.table_name, value))
        return self

    def execute(self):
        self.recorder.append(("execute", self.table_name))
        return SimpleNamespace(data=self.response_rows.get(self.table_name, []))


class _FakeAuth:
    def __init__(self, user_id="admin-test-user"):
        self.user_id = user_id

    def get_user(self):
        user = None if self.user_id is None else SimpleNamespace(id=self.user_id)
        return SimpleNamespace(user=user)


class FakeClient:
    def __init__(self, response_rows=None, user_id="admin-test-user"):
        self.recorder = []
        self.response_rows = response_rows or {}
        self.auth = _FakeAuth(user_id)

    def table(self, name):
        self.recorder.append(("table", name))
        return FakeQuery(name, self.recorder, self.response_rows)


class FakeAdminRepository:
    def __init__(self):
        self.calls = []
        self.profile = {
            "profile_id": "p1",
            "current_version_id": "v1",
            "lifecycle_status": "ACTIVE",
        }
        self.versions = {
            "v1": {
                "configuration_version_id": "v1",
                "profile_id": "p1",
                "version_number": 1,
                "version_status": "PUBLISHED",
            },
            "v2": {
                "configuration_version_id": "v2",
                "profile_id": "p1",
                "version_number": 2,
                "version_status": "PUBLISHED",
            },
        }

    def get_profile(self, *, profile_id):
        self.calls.append(("get_profile", profile_id))
        return self.profile if profile_id == "p1" else None

    def get_version(self, *, configuration_version_id):
        self.calls.append(("get_version", configuration_version_id))
        return self.versions.get(configuration_version_id)

    def list_versions(self, *, profile_id):
        self.calls.append(("list_versions", profile_id))
        return list(self.versions.values())

    def create_profile(self, **kwargs):
        self.calls.append(("create_profile", kwargs))
        return {"profile_id": "p-new", **kwargs, "lifecycle_status": "DRAFT"}

    def create_draft_version(self, **kwargs):
        self.calls.append(("create_draft_version", kwargs))
        return {
            "configuration_version_id": "v-new",
            "version_status": "DRAFT",
            **kwargs,
        }

    def update_draft_version(self, **kwargs):
        self.calls.append(("update_draft_version", kwargs))
        return {"version_status": "DRAFT", **kwargs}

    def publish_version(self, **kwargs):
        self.calls.append(("publish_version", kwargs))
        return {"configuration_version_id": kwargs["configuration_version_id"], "version_status": "PUBLISHED"}

    def set_current_version(self, **kwargs):
        self.calls.append(("set_current_version", kwargs))
        self.profile = {
            **self.profile,
            "current_version_id": kwargs["configuration_version_id"],
            "lifecycle_status": "ACTIVE",
        }
        return self.profile

    def retire_version(self, **kwargs):
        self.calls.append(("retire_version", kwargs))
        return {
            "configuration_version_id": kwargs["configuration_version_id"],
            "version_status": "RETIRED",
        }


def test_admin_repository_targets_exact_tables():
    assert (
        SupabaseLessonPlanConfigurationAdminRepository.PROFILE_TABLE
        == "lesson_plan_configuration_profiles"
    )
    assert (
        SupabaseLessonPlanConfigurationAdminRepository.VERSION_TABLE
        == "lesson_plan_configuration_versions"
    )


def test_profile_creation_is_draft():
    client = FakeClient(
        {"lesson_plan_configuration_profiles": [{"profile_id": "p1"}]}
    )
    repo = SupabaseLessonPlanConfigurationAdminRepository(client)
    repo.create_profile(profile_code=" X ", profile_name=" Name ")
    insert = next(x for x in client.recorder if x[0] == "insert")
    assert insert[2]["lifecycle_status"] == "DRAFT"
    assert insert[2]["profile_code"] == "X"


def test_version_creation_is_draft():
    client = FakeClient(
        {"lesson_plan_configuration_versions": [{"configuration_version_id": "v1"}]}
    )
    repo = SupabaseLessonPlanConfigurationAdminRepository(client)
    repo.create_draft_version(
        profile_id="p1",
        version_number=1,
        configuration_payload={"date_policy": {}},
    )
    insert = next(x for x in client.recorder if x[0] == "insert")
    assert insert[2]["version_status"] == "DRAFT"


def test_publish_sets_published_at():
    client = FakeClient(
        {"lesson_plan_configuration_versions": [{"configuration_version_id": "v1"}]}
    )
    repo = SupabaseLessonPlanConfigurationAdminRepository(client)
    repo.publish_version(configuration_version_id="v1")
    update = next(x for x in client.recorder if x[0] == "update")
    assert update[2]["version_status"] == "PUBLISHED"
    assert update[2]["published_at"]
    assert update[2]["published_by"] == "admin-test-user"


def test_create_next_draft_uses_next_number():
    repo = FakeAdminRepository()
    service = LessonPlanConfigurationAdminService(repo)
    row = service.create_next_draft_version(
        profile_id="p1",
        configuration_payload={},
    )
    assert row["version_number"] == 3
    assert row["version_status"] == "DRAFT"


def test_only_draft_can_be_edited():
    repo = FakeAdminRepository()
    service = LessonPlanConfigurationAdminService(repo)
    with pytest.raises(LessonPlanConfigurationAdminError):
        service.update_draft(
            configuration_version_id="v1",
            configuration_payload={},
        )


def test_only_draft_can_be_published():
    repo = FakeAdminRepository()
    service = LessonPlanConfigurationAdminService(repo)
    with pytest.raises(LessonPlanConfigurationAdminError):
        service.publish(configuration_version_id="v1")


def test_only_published_can_be_activated():
    repo = FakeAdminRepository()
    repo.versions["v2"]["version_status"] = "DRAFT"
    service = LessonPlanConfigurationAdminService(repo)
    with pytest.raises(LessonPlanConfigurationAdminError):
        service.activate_published_version(
            profile_id="p1",
            configuration_version_id="v2",
        )


def test_version_must_belong_to_profile():
    repo = FakeAdminRepository()
    repo.versions["v2"]["profile_id"] = "other"
    service = LessonPlanConfigurationAdminService(repo)
    with pytest.raises(LessonPlanConfigurationAdminError):
        service.activate_published_version(
            profile_id="p1",
            configuration_version_id="v2",
        )


def test_current_moves_before_previous_retirement():
    repo = FakeAdminRepository()
    service = LessonPlanConfigurationAdminService(repo)
    service.activate_published_version(
        profile_id="p1",
        configuration_version_id="v2",
        retire_previous=True,
    )
    set_index = next(i for i, c in enumerate(repo.calls) if c[0] == "set_current_version")
    retire_index = next(i for i, c in enumerate(repo.calls) if c[0] == "retire_version")
    assert set_index < retire_index


def test_previous_not_retired_by_default():
    repo = FakeAdminRepository()
    service = LessonPlanConfigurationAdminService(repo)
    service.activate_published_version(
        profile_id="p1",
        configuration_version_id="v2",
    )
    assert not any(c[0] == "retire_version" for c in repo.calls)

def test_delete_profile_uses_profile_table_constant_not_missing_plural_constant():
    from pathlib import Path
    import ast

    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "src"
        / "lesson_planning_v2"
        / "adapters"
        / "supabase_lesson_plan_configuration_admin_repository.py"
    ).read_text(encoding="utf-8")

    tree = ast.parse(source)
    method = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SupabaseLessonPlanConfigurationAdminRepository":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "delete_profile":
                    method = ast.get_source_segment(source, item)
                    break

    assert method is not None
    assert "self.PROFILE_TABLE" in method
    assert "self._PROFILES_TABLE" not in method
