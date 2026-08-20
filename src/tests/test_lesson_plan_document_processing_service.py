from pathlib import Path
import inspect

from lesson_planning_v2.services import (
    LessonPlanDocumentProcessingResult,
    LessonPlanDocumentProcessingService,
)


def test_processing_result_contract():
    result = LessonPlanDocumentProcessingResult(
        output_name="lesson.lbg-standardized.docx",
        output_bytes=b"PK",
        unresolved_fields=(),
    )

    assert result.output_name.endswith(
        ".docx"
    )

    assert result.output_bytes == b"PK"
    assert result.unresolved_fields == ()


def test_processing_service_owns_workspace_boundary():
    module = inspect.getmodule(
        LessonPlanDocumentProcessingService
    )

    source = inspect.getsource(
        module
    )

    assert "TemporaryDirectory(" in source
    assert ".write_bytes(" in source
    assert ".read_bytes(" in source


def test_processing_service_owns_document_pipeline():
    module = inspect.getmodule(
        LessonPlanDocumentProcessingService
    )

    source = inspect.getsource(
        module
    )

    assert (
        "LessonPlanDocumentPipeline"
        in source
    )

    assert (
        "LessonPlanWordStandardizer"
        in source
    )


def test_processing_service_owns_schedule_context_resolution():
    module = inspect.getmodule(
        LessonPlanDocumentProcessingService
    )

    source = inspect.getsource(
        module
    )

    assert (
        "ScheduledLessonContextService"
        in source
    )


def test_processing_service_does_not_import_streamlit():
    module = inspect.getmodule(
        LessonPlanDocumentProcessingService
    )

    source = inspect.getsource(
        module
    )

    import_lines = tuple(
        line.strip().lower()
        for line in source.splitlines()
        if line.strip().startswith(
            ("import ", "from ")
        )
    )

    assert not any(
        "streamlit" in line
        for line in import_lines
    )
