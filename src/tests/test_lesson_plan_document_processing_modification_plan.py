from datetime import date
from types import SimpleNamespace

import lesson_planning_v2.services.lesson_plan_document_processing_service as module

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_modification_plan import (
    LessonPlanFieldModification,
    LessonPlanModificationPlan,
)
from educational_planning_v2.models import (
    TeachingSession,
)
from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)
from lesson_planning_v2.services.lesson_plan_document_processing_service import (
    LessonPlanDocumentProcessingService,
)


def make_context():
    return ScheduledLessonContext(
        teaching_date=date(2026, 9, 8),
        drafting_date=date(2026, 9, 7),
        class_id="8A1",
        subject_ref="MATHEMATICS",
        component_ref="ALGEBRA",
        curriculum_period=1,
        lesson_id="LESSON-001",
        lesson_title="Bài cũ",
        session=TeachingSession.MORNING,
        timetable_period=1,
        period_in_lesson=1,
    )


def make_row():
    return SimpleNamespace(
        teaching_date=date(2026, 9, 8),
        class_id="8A1",
        subject_ref="MATHEMATICS",
        component_ref="ALGEBRA",
        curriculum_period=1,
        lesson_id="LESSON-001",
        lesson_title="Bài cũ",
        session=TeachingSession.MORNING,
        timetable_period=1,
        period_in_lesson=1,
    )


def make_plan():
    return LessonPlanModificationPlan(
        modifications=(
            LessonPlanFieldModification(
                field=DocumentField.CLASS_NAME,
                value="8A2",
            ),
            LessonPlanFieldModification(
                field=DocumentField.CURRICULUM_PERIOD,
                value="9",
            ),
            LessonPlanFieldModification(
                field=DocumentField.LESSON_TITLE,
                value="Đơn thức",
            ),
        )
    )


def test_process_applies_plan_before_pipeline(
    tmp_path,
    monkeypatch,
):
    profile = tmp_path / "profile.json"
    profile.write_text(
        "{}",
        encoding="utf-8",
    )

    captured = {}

    class FakeContextService:
        def build_from_weekly_schedule_row(
            self,
            row,
            *,
            drafting_date,
        ):
            return make_context()

    class FakeStandardizer:
        @classmethod
        def from_json(
            cls,
            path,
        ):
            return object()

    class FakePipeline:
        def __init__(
            self,
            *,
            standardizer,
        ):
            pass

        def process(
            self,
            *,
            source,
            output,
            report_path,
            context,
        ):
            captured["context"] = context

            output.write_bytes(
                b"processed-docx"
            )

            return SimpleNamespace(
                context_result=SimpleNamespace(
                    unresolved_fields=()
                )
            )

    monkeypatch.setattr(
        module,
        "ScheduledLessonContextService",
        FakeContextService,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanWordStandardizer",
        FakeStandardizer,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanDocumentPipeline",
        FakePipeline,
    )

    service = (
        LessonPlanDocumentProcessingService(
            profile_path=profile
        )
    )

    result = service.process(
        row=make_row(),
        drafting_date=date(
            2026,
            9,
            7,
        ),
        content=b"PK-docx",
        original_name="lesson.docx",
        modification_plan=make_plan(),
    )

    context = captured["context"]

    assert context.class_id == "8A2"
    assert context.curriculum_period == 9
    assert context.lesson_title == "Đơn thức"

    assert (
        context.subject_ref
        == "MATHEMATICS"
    )

    assert (
        result.output_bytes
        == b"processed-docx"
    )


def test_process_without_plan_keeps_original_context(
    tmp_path,
    monkeypatch,
):
    profile = tmp_path / "profile.json"
    profile.write_text(
        "{}",
        encoding="utf-8",
    )

    captured = {}

    class FakeContextService:
        def build_from_weekly_schedule_row(
            self,
            row,
            *,
            drafting_date,
        ):
            return make_context()

    class FakeStandardizer:
        @classmethod
        def from_json(
            cls,
            path,
        ):
            return object()

    class FakePipeline:
        def __init__(
            self,
            *,
            standardizer,
        ):
            pass

        def process(
            self,
            *,
            source,
            output,
            report_path,
            context,
        ):
            captured["context"] = context

            output.write_bytes(
                b"processed-docx"
            )

            return SimpleNamespace(
                context_result=SimpleNamespace(
                    unresolved_fields=()
                )
            )

    monkeypatch.setattr(
        module,
        "ScheduledLessonContextService",
        FakeContextService,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanWordStandardizer",
        FakeStandardizer,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanDocumentPipeline",
        FakePipeline,
    )

    service = (
        LessonPlanDocumentProcessingService(
            profile_path=profile
        )
    )

    service.process(
        row=make_row(),
        drafting_date=date(
            2026,
            9,
            7,
        ),
        content=b"PK-docx",
        original_name="lesson.docx",
    )

    context = captured["context"]

    assert context.class_id == "8A1"
    assert context.curriculum_period == 1
    assert context.lesson_title == "Bài cũ"
