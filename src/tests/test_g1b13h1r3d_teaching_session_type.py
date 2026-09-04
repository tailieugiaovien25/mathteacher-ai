from educational_planning_v2.models import TeachingSession
from pathlib import Path


SOURCE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def test_teaching_session_canonical_values_are_stable():
    assert TeachingSession("MORNING") is TeachingSession.MORNING
    assert TeachingSession("AFTERNOON") is TeachingSession.AFTERNOON


def test_v2_adapter_converts_session_to_canonical_enum():
    source = SOURCE.read_text(encoding="utf-8")
    adapter = source[source.index("# G1B_13H1_V2_STANDARDIZE_ADAPTER"):]
    assert "from educational_planning_v2.models import TeachingSession" in adapter
    assert 'first("session", default=TeachingSession.MORNING)' in adapter
    assert '.removeprefix("TEACHINGSESSION.")' in adapter
    assert "session_value = TeachingSession(normalized_session)" in adapter
    assert "session=session_value," in adapter
    assert 'session=str(first("session"' not in adapter


def test_prior_runtime_contract_fixes_remain_present():
    source = SOURCE.read_text(encoding="utf-8")
    assert "supported_kwargs = {" in source
    assert 'occurrences = tuple(context.get("occurrences", ()) or ())' in source
