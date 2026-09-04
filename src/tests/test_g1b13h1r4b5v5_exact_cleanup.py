from pathlib import Path


def _text(path):
    return path.read_text(encoding="utf-8-sig")


def test_exact_cleanup_preserves_stable_fixes():
    root = Path(__file__).resolve().parents[2]
    management = _text(
        root / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
    )
    applier = _text(
        root / "src/document_standardization/lesson_plan_document_context_applier.py"
    )
    merge = _text(
        root / "src/lesson_planning_v2/services/lesson_plan_merge_service.py"
    )

    for token in (
        "_g1b_runtime_ole_manifest",
        "G1B_13H1R4B5N4_RUNTIME_OLE_INSPECTOR",
        "G1B_13H1R4B5T_RICH_OLE_MANIFEST",
        "G1B_13H1R4B5R2_DOMAIN_OLE_TRIGGER_TRACE",
        "G1B_R4B5R2_OLE_DIAGNOSTIC_TRIGGERED",
        "G1B_13H1R4B5N4_OLE_ERROR_DETAILS",
    ):
        assert token not in management

    assert "G1B_13H1R4B5M_CONTEXT_IDENTITY_DIAGNOSTIC" not in applier
    assert "G1B_13H1R4B5S4_REHYDRATE_STALE_CONTEXT" in applier
    assert "G1B_13H1R4B5S4_APPLY_RELOAD_SAFE_CONTEXT" in applier
    assert "G1B_13H1R4B5J_RAW_OPC_IMAGE_PART_COPY" in merge
    assert "G1B_13H1R4B5U1_RAW_OPC_OLE_PART_COPY" in merge


def test_merge_ui_core_seams_remain():
    root = Path(__file__).resolve().parents[2]
    text = _text(
        root / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
    )
    assert 'except LessonPlanMergeError as error:' in text
    assert 'st.error("Không thể gộp giáo án: " + str(error))' in text
    assert '_MERGE_RESULT_KEY' in text
    assert 'standardized_merge_preview_button_v4' in text
