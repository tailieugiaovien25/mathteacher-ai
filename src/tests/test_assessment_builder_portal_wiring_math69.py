from pathlib import Path


PORTAL = Path("scripts/teacher_portal/app.py")


def _source() -> str:
    return PORTAL.read_text(encoding="utf-8-sig")


def test_math69_builder_is_added_without_removing_existing_assessment_routes():
    source = _source()

    assert "Tạo đề kiểm tra Toán 6–9" in source
    assert "Thiết đặt đề kiểm tra" in source
    assert "Ma trận & bản đặc tả" in source
    assert 'elif selected == "Tạo đề kiểm tra":' in source
    assert 'elif selected == "Tạo đề kiểm tra Toán 6":' in source


def test_math69_builder_route_uses_current_admin_academic_year_and_active_ppct():
    source = _source()

    assert 'elif selected == "Tạo đề kiểm tra Toán 6–9":' in source
    assert "SupabaseAcademicYearConfigurationRepository" in source
    assert "get_current()" in source
    assert "SystemWeeklyScheduleRuntime" in source
    assert "load_active_ppct_snapshot" in source


def test_math69_builder_route_injects_runtime_ppct_with_provenance():
    source = _source()

    assert "inject_assessment_ppct_rows" in source
    assert "AssessmentPpctRuntimeEvidence" in source
    assert "snapshot.source_id" in source
    assert "snapshot.source_version" in source


def test_math69_builder_route_fails_closed_and_clears_stale_session_ppct():
    source = _source()

    assert "clear_assessment_ppct_rows" in source
    assert "Không thể nạp PPCT cho hệ thống tạo đề" in source


def test_logout_session_clear_contract_includes_assessment_ppct_state():
    source = _source()

    for key in (
        "assessment_ppct_rows",
        "assessment_ppct_evidence",
        "assessment_ppct_scope_confirmation",
    ):
        assert f'"{key}"' in source
