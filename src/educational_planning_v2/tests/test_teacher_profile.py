import pytest

from educational_planning_v2.models import TeacherProfile


def test_profile_normalizes_teacher_entered_values():
    profile = TeacherProfile(
        teacher_code=" GV001 ",
        full_name=" Nguyễn Văn A ",
        school_name=" THCS Mẫu ",
        subjects=("Toán", "Toán", "Tin học"),
        grade_levels=("6", "7"),
        default_academic_year="2026-2027",
    )
    assert profile.teacher_code == "GV001"
    assert profile.subjects == ("Toán", "Tin học")


@pytest.mark.parametrize("field", ("teacher_code", "full_name", "school_name", "default_academic_year"))
def test_profile_requires_identity_fields(field):
    values = {
        "teacher_code": "GV001", "full_name": "Nguyễn Văn A",
        "school_name": "THCS Mẫu", "subjects": ("Toán",),
        "grade_levels": ("6",), "default_academic_year": "2026-2027",
    }
    values[field] = ""
    with pytest.raises(ValueError):
        TeacherProfile(**values)


def test_profile_requires_subjects_and_grade_levels():
    with pytest.raises(ValueError):
        TeacherProfile("GV001", "Nguyễn Văn A", "THCS Mẫu", (), ("6",), "2026-2027")
