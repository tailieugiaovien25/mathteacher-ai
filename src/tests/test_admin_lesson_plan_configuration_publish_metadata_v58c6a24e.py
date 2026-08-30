from types import SimpleNamespace
import pytest
from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_admin_repository import (
    LessonPlanConfigurationAdminWriteError,
    SupabaseLessonPlanConfigurationAdminRepository,
)

class Query:
    def __init__(self, client):
        self.client = client
    def update(self, payload):
        self.client.update_payload = payload
        return self
    def eq(self, *args):
        return self
    def execute(self):
        return SimpleNamespace(data=[{"configuration_version_id": "v1", **self.client.update_payload}])

class Auth:
    def __init__(self, user_id):
        self.user_id = user_id
    def get_user(self):
        user = None if self.user_id is None else SimpleNamespace(id=self.user_id)
        return SimpleNamespace(user=user)

class Client:
    def __init__(self, user_id):
        self.auth = Auth(user_id)
        self.update_payload = None
    def table(self, name):
        return Query(self)

def test_publish_records_authenticated_admin_user():
    client = Client("admin-123")
    repo = SupabaseLessonPlanConfigurationAdminRepository(client)
    result = repo.publish_version(configuration_version_id="v1")
    assert client.update_payload["published_by"] == "admin-123"
    assert client.update_payload["published_at"]
    assert result["published_by"] == "admin-123"

def test_publish_fails_closed_without_authenticated_user():
    client = Client(None)
    repo = SupabaseLessonPlanConfigurationAdminRepository(client)
    with pytest.raises(LessonPlanConfigurationAdminWriteError):
        repo.publish_version(configuration_version_id="v1")
    assert client.update_payload is None
