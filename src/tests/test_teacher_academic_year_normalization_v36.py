from pathlib import Path

from educational_planning_v2.models.teacher_profile import TeacherProfile


def _profile(academic_year: str) -> TeacherProfile:
    return TeacherProfile(
        teacher_code="GV002",
        full_name="Teacher Two",
        school_name="School",
        subjects=("English",),
        grade_levels=("6",),
        default_academic_year=academic_year,
    )


def test_teacher_profile_normalizes_academic_year_spacing():
    assert _profile(" 2026 - 2027 ").default_academic_year == "2026-2027"


def test_teacher_profile_normalizes_unicode_dash():
    assert _profile("2026–2027").default_academic_year == "2026-2027"


def test_teacher_settings_prefers_admin_current_academic_year():
    text = Path("scripts/teacher_portal/app.py").read_text(encoding="utf-8-sig")
    start = text.index("def render_teacher_settings(")
    end = text.index("\ndef render_profile(", start)
    function_text = text[start:end]
    assert "SupabaseAcademicYearConfigurationRepository" in function_text
    assert ".get_current()" in function_text
    assert "normalize_academic_year(" in function_text
    assert 'else "2026-2027"' not in function_text
