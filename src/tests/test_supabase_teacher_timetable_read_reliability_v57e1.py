from educational_planning_v2.adapters.supabase_teacher_timetable_repository import (
    SupabaseTeacherTimetableRepository, _is_transient_read_error,
)
from educational_planning_v2.models.teacher_timetable import TeacherTimetableSlotStatus

class ConnectionTerminated(Exception):
    pass

class Query:
    def __init__(self, outcomes):
        self.outcomes=list(outcomes); self.execute_count=0
    def select(self,*a): return self
    def eq(self,*a): return self
    def execute(self):
        self.execute_count += 1
        outcome=self.outcomes.pop(0)
        if isinstance(outcome, BaseException): raise outcome
        return outcome

class Response:
    def __init__(self, data): self.data=data

class Client:
    def __init__(self,q): self.q=q
    def table(self,n): return self.q

def repo(q):
    return SupabaseTeacherTimetableRepository(client=Client(q),user_id="u1")

def call(q):
    return repo(q).list_slots(owner_id="u1",academic_year="2026-2027",
        status=TeacherTimetableSlotStatus.ACTIVE)

def test_transient_classifier():
    assert _is_transient_read_error(ConnectionTerminated("x"))
    assert not _is_transient_read_error(ValueError("x"))

def test_one_retry_then_success(monkeypatch):
    monkeypatch.setattr("educational_planning_v2.adapters.supabase_teacher_timetable_repository.time.sleep",lambda x:None)
    q=Query([ConnectionTerminated("x"),Response([])])
    assert call(q)==()
    assert q.execute_count==2

def test_business_error_not_retried(monkeypatch):
    monkeypatch.setattr("educational_planning_v2.adapters.supabase_teacher_timetable_repository.time.sleep",lambda x:None)
    q=Query([ValueError("business")])
    try: call(q)
    except ValueError: pass
    else: raise AssertionError
    assert q.execute_count==1

def test_second_transient_failure_propagates(monkeypatch):
    monkeypatch.setattr("educational_planning_v2.adapters.supabase_teacher_timetable_repository.time.sleep",lambda x:None)
    q=Query([ConnectionTerminated("1"),ConnectionTerminated("2")])
    try: call(q)
    except ConnectionTerminated as e: assert str(e)=="2"
    else: raise AssertionError
    assert q.execute_count==2
