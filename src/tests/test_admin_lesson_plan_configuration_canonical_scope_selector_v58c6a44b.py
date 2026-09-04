from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"


def _text() -> str:
    return UI.read_text(encoding="utf-8-sig")


def test_admin_configuration_reuses_canonical_subject_catalog() -> None:
    text = _text()
    assert "SupabaseSubjectCatalogRepository" in text
    assert "CatalogStatus.ACTIVE" in text
    assert "repository.list_subjects(status=CatalogStatus.ACTIVE)" in text
    assert "repository.list_components(status=CatalogStatus.ACTIVE)" in text


def test_create_profile_uses_canonical_scope_selector_not_free_text() -> None:
    text = _text()
    assert "_render_canonical_lesson_plan_scope_selector(" in text
    assert "subject_ref, component_ref = (" in text
    assert 'st.text_input(\\n                "Môn"' not in text
    assert 'st.text_input(\\n                "Phân môn"' not in text


def test_selector_uses_stable_canonical_ids_and_friendly_labels() -> None:
    text = _text()
    assert "subject.subject_id" in text
    assert "component.component_id" in text
    assert "subject_by_id[value].name" in text
    assert "component_by_id[value].name" in text


def test_component_policy_controls_component_selector() -> None:
    text = _text()
    assert "SubjectComponentPolicy.NONE" in text
    assert "SubjectComponentPolicy.REQUIRED" in text
    assert "— Không chọn Phân môn —" in text
    assert "Môn này không sử dụng Phân môn" in text
    assert "Môn này yêu cầu Phân môn" in text


def test_selector_does_not_hardcode_subject_or_component_ids() -> None:
    text = _text()
    for forbidden in (
        '"subject-math"',
        '"subject-literature"',
        '"subject-foreign-language-1"',
        '"component-algebra"',
    ):
        assert forbidden not in text
