from document_intelligence import (
    AnalysisSource,
    DocumentAnalysis,
    DocumentField,
    DocumentFieldProposal,
    HybridDocumentAnalyzer,
)


class FakeAnalyzer:
    def __init__(
        self,
        analysis,
    ):
        self.analysis = analysis
        self.calls = 0

    def analyze(
        self,
        *,
        document_text: str,
    ):
        self.calls += 1
        return self.analysis


class FailingAnalyzer:
    def analyze(
        self,
        *,
        document_text: str,
    ):
        raise RuntimeError(
            "AI unavailable"
        )


def proposal(
    field,
    value,
    confidence,
    source,
):
    return DocumentFieldProposal(
        field=field,
        value=value,
        confidence=confidence,
        source=source,
    )


def complete_deterministic_analysis():
    return DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.DRAFTING_DATE,
                "07/09/2026",
                0.99,
                AnalysisSource.DETERMINISTIC,
            ),
            proposal(
                DocumentField.TEACHING_DATE,
                "08/09/2026",
                0.99,
                AnalysisSource.DETERMINISTIC,
            ),
            proposal(
                DocumentField.CLASS_NAME,
                "8A2",
                0.99,
                AnalysisSource.DETERMINISTIC,
            ),
            proposal(
                DocumentField.CURRICULUM_PERIOD,
                "4",
                0.99,
                AnalysisSource.DETERMINISTIC,
            ),
            proposal(
                DocumentField.LESSON_TITLE,
                "Đơn thức",
                0.95,
                AnalysisSource.DETERMINISTIC,
            ),
        )
    )


def test_ai_is_not_called_when_deterministic_is_complete():
    deterministic = FakeAnalyzer(
        complete_deterministic_analysis()
    )

    ai = FakeAnalyzer(
        DocumentAnalysis()
    )

    analyzer = HybridDocumentAnalyzer(
        deterministic_analyzer=deterministic,
        ai_analyzer=ai,
    )

    result = analyzer.analyze(
        document_text="document"
    )

    assert result.ai_used is False
    assert deterministic.calls == 1
    assert ai.calls == 0


def test_ai_is_called_for_missing_field():
    deterministic = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.CLASS_NAME,
                    "8A2",
                    0.99,
                    AnalysisSource.DETERMINISTIC,
                ),
            )
        )
    )

    ai = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.LESSON_TITLE,
                    "Đơn thức",
                    0.92,
                    AnalysisSource.AI,
                ),
            )
        )
    )

    analyzer = HybridDocumentAnalyzer(
        deterministic_analyzer=deterministic,
        ai_analyzer=ai,
        required_fields=(
            DocumentField.CLASS_NAME,
            DocumentField.LESSON_TITLE,
        ),
    )

    result = analyzer.analyze(
        document_text="document"
    )

    assert result.ai_used is True
    assert ai.calls == 1

    titles = result.analysis.for_field(
        DocumentField.LESSON_TITLE
    )

    assert len(titles) == 1
    assert titles[0].source is AnalysisSource.AI


def test_ai_is_called_for_low_confidence_field():
    deterministic = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.LESSON_TITLE,
                    "Đơn thức",
                    0.60,
                    AnalysisSource.DETERMINISTIC,
                ),
            )
        )
    )

    ai = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.LESSON_TITLE,
                    "Đơn thức",
                    0.95,
                    AnalysisSource.AI,
                ),
            )
        )
    )

    analyzer = HybridDocumentAnalyzer(
        deterministic_analyzer=deterministic,
        ai_analyzer=ai,
        required_fields=(
            DocumentField.LESSON_TITLE,
        ),
        confidence_threshold=0.90,
    )

    result = analyzer.analyze(
        document_text="document"
    )

    assert result.ai_used is True

    proposals = result.analysis.for_field(
        DocumentField.LESSON_TITLE
    )

    assert len(proposals) == 2


def test_ai_cannot_override_strong_deterministic_field():
    deterministic = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.CLASS_NAME,
                    "8A2",
                    0.99,
                    AnalysisSource.DETERMINISTIC,
                ),
            )
        )
    )

    ai = FakeAnalyzer(
        DocumentAnalysis(
            proposals=(
                proposal(
                    DocumentField.CLASS_NAME,
                    "6A1",
                    0.99,
                    AnalysisSource.AI,
                ),
                proposal(
                    DocumentField.LESSON_TITLE,
                    "Đơn thức",
                    0.95,
                    AnalysisSource.AI,
                ),
            )
        )
    )

    analyzer = HybridDocumentAnalyzer(
        deterministic_analyzer=deterministic,
        ai_analyzer=ai,
        required_fields=(
            DocumentField.CLASS_NAME,
            DocumentField.LESSON_TITLE,
        ),
    )

    result = analyzer.analyze(
        document_text="document"
    )

    classes = result.analysis.for_field(
        DocumentField.CLASS_NAME
    )

    assert len(classes) == 1
    assert classes[0].value == "8A2"


def test_ai_failure_falls_back_to_deterministic():
    deterministic_analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.CLASS_NAME,
                "8A2",
                0.99,
                AnalysisSource.DETERMINISTIC,
            ),
        )
    )

    analyzer = HybridDocumentAnalyzer(
        deterministic_analyzer=FakeAnalyzer(
            deterministic_analysis
        ),
        ai_analyzer=FailingAnalyzer(),
        required_fields=(
            DocumentField.CLASS_NAME,
            DocumentField.LESSON_TITLE,
        ),
    )

    result = analyzer.analyze(
        document_text="document"
    )

    assert result.ai_used is True
    assert result.ai_error == "AI unavailable"
    assert result.analysis == deterministic_analysis


def test_invalid_threshold_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        HybridDocumentAnalyzer(
            deterministic_analyzer=FakeAnalyzer(
                DocumentAnalysis()
            ),
            confidence_threshold=1.1,
        )
