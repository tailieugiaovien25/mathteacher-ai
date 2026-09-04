from datetime import date
from pathlib import Path

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
)
from educational_planning_v2.services.academic_week_configuration_service import (
    AcademicWeekConfigurationService,
)


class Repository:
    def __init__(self):
        self.saved = []

    def save(self, *, week):
        self.saved.append(week)
        return week


def week(number, start_day):
    start = date(2026, 9, start_day)
    return AcademicWeekConfiguration(
        academic_week_id=f"ay-week-{number}",
        academic_year_id="ay",
        academic_year="2026-2027",
        week_number=number,
        start_date=start,
        end_date=date(2026, 9, start_day + 6),
    )


def test_shift_from_week_moves_selected_and_every_following_week():
    repository = Repository()
    service = AcademicWeekConfigurationService(repository=repository)
    result = service.shift_from_week(
        weeks=(week(1, 1), week(2, 8), week(3, 15)),
        week_number=2,
        new_start_date=date(2026, 9, 10),
    )
    assert result[0].start_date == date(2026, 9, 1)
    assert result[1].start_date == date(2026, 9, 10)
    assert result[2].start_date == date(2026, 9, 17)
    assert len(repository.saved) == 2


def test_admin_dashboard_joins_roles_and_profiles():
    text = Path("src/portal_v2/ui/admin_shell.py").read_text(encoding="utf-8-sig")
    assert 'client.table("portal_roles")' in text
    assert 'client.table("teacher_profiles")' in text
    assert 'client.table("portal_roles")' in text
    assert 'client.table("teacher_profiles")' in text
    assert "admin_dashboard_user_status" in text


def test_week_ui_uses_one_date_and_cascade_service():
    text = Path(
        "src/portal_v2/ui/admin_academic_year_configuration_streamlit.py"
    ).read_text(encoding="utf-8-sig")
    assert '"Ngày bắt đầu mới"' in text
    assert "week_service.shift_from_week(" in text
    assert "new_start_date=week_start_date" in text
    assert "admin_week_end_date" not in text
