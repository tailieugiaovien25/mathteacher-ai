from types import SimpleNamespace

from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_repository import (
    SupabaseLessonPlanConfigurationRepository,
)


def test_admin_selector_persists_canonical_subject_code():
    text = open(
        "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py",
        encoding="utf-8",
    ).read()
    assert text.count("return str(subject.code),") == 4
    assert "return str(subject_id)," not in text


def test_equivalent_subject_refs_maps_database_id_and_canonical_code(monkeypatch):
    import educational_planning_v2.adapters.supabase_subject_catalog_repository as module

    class FakeCatalog:
        def __init__(self, *, client):
            self.client = client

        def list_subjects(self):
            return (
                SimpleNamespace(
                    subject_id="SUB-BA16FF75",
                    code="FOREIGN_LANGUAGE_1",
                ),
            )

    monkeypatch.setattr(module, "SupabaseSubjectCatalogRepository", FakeCatalog)
    repository = SupabaseLessonPlanConfigurationRepository(client=object())
    assert repository._equivalent_subject_refs("FOREIGN_LANGUAGE_1") == {
        "FOREIGN_LANGUAGE_1",
        "SUB-BA16FF75",
    }
    assert repository._equivalent_subject_refs("SUB-BA16FF75") == {
        "FOREIGN_LANGUAGE_1",
        "SUB-BA16FF75",
    }
