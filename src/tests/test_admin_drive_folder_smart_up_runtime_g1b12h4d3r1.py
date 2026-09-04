from pathlib import Path

ADMIN = Path(
    "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"
).read_text(encoding="utf-8-sig")
BRIDGE = Path(
    "src/lesson_planning_v2/services/"
    "lesson_plan_configuration_runtime_bridge.py"
).read_text(encoding="utf-8-sig")
UI = Path(
    "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py"
).read_text(encoding="utf-8-sig")


def test_admin_has_drive_folder_field_and_payload_persistence():
    assert "G1B_H4D3_DRIVE_FOLDER_FIELD" in ADMIN
    assert "G1B_H4D3_PERSIST_DRIVE_FOLDER_FIELD" in ADMIN
    assert "google_drive_lesson_plan_folder_id" in ADMIN


def test_runtime_bridge_projects_drive_folder_id():
    assert "G1B_H4D3_PROJECT_DOCUMENT_REPOSITORY" in BRIDGE
    assert "ADMIN_LESSON_PLAN_DRIVE_FOLDER_ID_KEY" in BRIDGE
    assert 'normalized.get("document_repository")' in BRIDGE


def test_smart_up_priority_is_drive_then_catalog_then_local():
    button = UI.index('"Up giáo án"')
    drive = UI.index("list_folder_tree(", button)
    catalog = UI.index("TeacherDocumentCatalog(", button)
    local = UI.index("find_local_lesson_plans(", button)
    assert drive < catalog < local


def test_drive_discovery_is_read_only():
    block = UI[UI.index("G1B_H4D3_DRIVE_FIRST_SMART_UP"):]
    assert "list_folder_tree(" in block
    assert "runtime_storage.download(item.file_id)" in block
    assert "_ensure_folder(" not in block


def test_ambiguity_blocks_fallback():
    assert "blocked_by_ambiguity = True" in UI
    assert "if not blocked_by_ambiguity:" in UI


def test_filename_normalization_supports_week_padding():
    assert 'f"tuan{int(match.group(1)):02d}"' in UI
    assert 'f"bai{int(match.group(1)):02d}"' in UI
