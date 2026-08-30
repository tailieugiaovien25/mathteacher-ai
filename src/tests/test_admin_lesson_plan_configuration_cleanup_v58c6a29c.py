from lesson_planning_v2.services.lesson_plan_configuration_admin_service import (
    LessonPlanConfigurationAdminError,
    LessonPlanConfigurationAdminService,
)


class FakeRepo:
    def __init__(self, profile):
        self.profile = profile
        self.deleted = []

    def get_profile(self, *, profile_id):
        if self.profile and self.profile.get("profile_id") == profile_id:
            return self.profile
        return None

    def delete_profile(self, *, profile_id):
        self.deleted.append(profile_id)


def test_cleanup_accepts_isolated_smoke_profile():
    repo = FakeRepo(
        {
            "profile_id": "p1",
            "profile_code": "__SMOKE_C6A29C__CODE",
            "subject_ref": "__SMOKE_C6A29C__SUBJECT",
            "component_ref": "__SMOKE_C6A29C__COMPONENT",
        }
    )
    LessonPlanConfigurationAdminService(repo).delete_disposable_profile(
        profile_id="p1"
    )
    assert repo.deleted == ["p1"]


def test_cleanup_rejects_real_profile():
    repo = FakeRepo(
        {
            "profile_id": "p1",
            "profile_code": "TOAN_6",
            "subject_ref": "math",
            "component_ref": "",
        }
    )
    try:
        LessonPlanConfigurationAdminService(repo).delete_disposable_profile(
            profile_id="p1"
        )
    except LessonPlanConfigurationAdminError:
        pass
    else:
        raise AssertionError("real profile cleanup must be rejected")

    assert repo.deleted == []


def test_cleanup_missing_profile_is_idempotent():
    repo = FakeRepo(None)
    LessonPlanConfigurationAdminService(repo).delete_disposable_profile(
        profile_id="missing"
    )
    assert repo.deleted == []


def test_cleanup_rejects_empty_profile_id():
    repo = FakeRepo(None)
    try:
        LessonPlanConfigurationAdminService(repo).delete_disposable_profile(
            profile_id="   "
        )
    except LessonPlanConfigurationAdminError:
        pass
    else:
        raise AssertionError("empty profile id must be rejected")

    assert repo.deleted == []
