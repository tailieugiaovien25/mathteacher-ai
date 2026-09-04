from lesson_planning_v2.models.lesson_plan_configuration import LessonPlanConfigurationSnapshot
from lesson_planning_v2.services.configuration_hierarchy import (
    merge_with_parent_authority,
    remove_parent_locked_values,
)
from lesson_planning_v2.services.lesson_plan_configuration_service import (
    LessonPlanConfigurationService,
)


def _snapshot(code, subject, payload):
    return LessonPlanConfigurationSnapshot(
        profile_id=code, profile_code=code, profile_name=code,
        subject_ref=subject, component_ref="", configuration_version_id=code + "-v1",
        version_number=1, configuration_payload=payload,
    )


def test_global_lesson_values_win_and_subject_only_adds_missing_fields():
    effective, conflicts = merge_with_parent_authority(
        parent={"layout": {"font": "Times New Roman", "size": 13}},
        child={"layout": {"font": "Arial", "subject_note": "Math"}},
    )
    assert effective == {"layout": {"font": "Times New Roman", "size": 13, "subject_note": "Math"}}
    assert conflicts == ("layout.font",)


def test_locked_parent_values_are_removed_before_subject_persistence():
    cleaned, removed = remove_parent_locked_values(
        parent={"layout": {"font": "Times New Roman", "size": 13}},
        child={"layout": {"font": "Arial", "subject_note": "Math"}},
    )
    assert cleaned == {"layout": {"subject_note": "Math"}}
    assert removed == ("layout.font",)


def test_runtime_resolver_exposes_global_authority_and_locked_paths():
    global_snapshot = _snapshot("GLOBAL", "", {"layout": {"font": "Times New Roman"}})
    subject_snapshot = _snapshot("MATH", "MATH", {"layout": {"font": "Arial", "note": "Toán"}})

    class Repository:
        def get_active_configuration_exact(self, *, subject_ref, component_ref=None):
            return global_snapshot if not subject_ref else subject_snapshot

        def get_active_configuration(self, **kwargs):
            raise AssertionError("legacy resolver must not be used")

    result = LessonPlanConfigurationService(Repository()).resolve(subject_ref="MATH")
    assert result.snapshot is global_snapshot
    assert result.global_snapshot is global_snapshot
    assert result.subject_snapshot is subject_snapshot
    assert result.configuration_payload["layout"]["font"] == "Times New Roman"
    assert result.configuration_payload["layout"]["note"] == "Toán"
    assert result.locked_paths == ("layout.font",)
    assert result.conflicts == ("layout.font",)
