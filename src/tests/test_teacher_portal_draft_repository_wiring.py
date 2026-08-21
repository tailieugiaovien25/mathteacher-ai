from lesson_planning_v2.adapters.supabase_lesson_plan_workspace_draft_repository import (
    SupabaseLessonPlanWorkspaceDraftRepository,
)
from scripts.teacher_portal.app import (
    connect_feature_repositories,
)


class FakeClient:
    pass


def test_connect_feature_repositories_wires_lesson_plan_draft_repository():
    state = {}
    client = FakeClient()

    connect_feature_repositories(
        state,
        client,
        "teacher-123",
    )

    assert (
        "lesson_plan_workspace_draft_repository"
        in state
    )

    repository = state[
        "lesson_plan_workspace_draft_repository"
    ]

    assert isinstance(
        repository,
        SupabaseLessonPlanWorkspaceDraftRepository,
    )

    assert repository._client is client
