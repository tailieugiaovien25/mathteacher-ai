import pytest

from document_intelligence.ai_provider import (
    AIDocumentAnalyzer,
    AIDocumentProvider,
    AIFieldCandidate,
)
from document_intelligence.contracts import (
    AnalysisSource,
    DocumentField,
)


class FakeAIProvider:
    def analyze(
        self,
        *,
        document_text: str,
    ):
        return (
            AIFieldCandidate(
                field=DocumentField.LESSON_TITLE,
                value="Đơn thức",
                confidence=0.92,
                evidence="Tiết 1 - Đơn thức",
            ),
        )


def test_ai_provider_is_protocol():
    assert hasattr(
        AIDocumentProvider,
        "analyze",
    )


def test_ai_analyzer_converts_candidate_to_proposal():
    analyzer = AIDocumentAnalyzer(
        provider=FakeAIProvider()
    )

    analysis = analyzer.analyze(
        document_text="Một giáo án"
    )

    assert len(analysis.proposals) == 1

    proposal = analysis.proposals[0]

    assert (
        proposal.field
        is DocumentField.LESSON_TITLE
    )
    assert proposal.value == "Đơn thức"
    assert proposal.confidence == 0.92
    assert proposal.source is AnalysisSource.AI
    assert (
        proposal.evidence
        == "Tiết 1 - Đơn thức"
    )


def test_ai_analyzer_does_not_modify_input():
    analyzer = AIDocumentAnalyzer(
        provider=FakeAIProvider()
    )

    original = "Nội dung giáo án"

    analyzer.analyze(
        document_text=original
    )

    assert original == "Nội dung giáo án"


@pytest.mark.parametrize(
    "confidence",
    (-0.01, 1.01),
)
def test_ai_candidate_rejects_invalid_confidence(
    confidence,
):
    with pytest.raises(ValueError):
        AIFieldCandidate(
            field=DocumentField.LESSON_TITLE,
            value="Đơn thức",
            confidence=confidence,
        )


def test_ai_candidate_rejects_empty_value():
    with pytest.raises(ValueError):
        AIFieldCandidate(
            field=DocumentField.LESSON_TITLE,
            value="   ",
            confidence=0.8,
        )
