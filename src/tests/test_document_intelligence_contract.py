import pytest

from document_intelligence import (
    AnalysisSource,
    DocumentAnalysis,
    DocumentAnalyzer,
    DocumentField,
    DocumentFieldProposal,
)


def test_document_field_proposal_is_structured():
    proposal = DocumentFieldProposal(
        field=DocumentField.LESSON_TITLE,
        value="Đơn thức",
        confidence=0.96,
        source=AnalysisSource.AI,
        evidence="TIẾT 1 - §4: ĐƠN THỨC",
    )

    assert proposal.field is DocumentField.LESSON_TITLE
    assert proposal.value == "Đơn thức"
    assert proposal.confidence == 0.96
    assert proposal.source is AnalysisSource.AI


def test_analysis_can_filter_by_field():
    analysis = DocumentAnalysis(
        proposals=(
            DocumentFieldProposal(
                field=DocumentField.CLASS_NAME,
                value="6A1",
                confidence=0.99,
                source=AnalysisSource.DETERMINISTIC,
            ),
            DocumentFieldProposal(
                field=DocumentField.LESSON_TITLE,
                value="Tập hợp",
                confidence=0.91,
                source=AnalysisSource.AI,
            ),
        )
    )

    proposals = analysis.for_field(
        DocumentField.CLASS_NAME
    )

    assert len(proposals) == 1
    assert proposals[0].value == "6A1"


@pytest.mark.parametrize(
    "confidence",
    (-0.01, 1.01),
)
def test_confidence_must_be_normalized(
    confidence,
):
    with pytest.raises(ValueError):
        DocumentFieldProposal(
            field=DocumentField.LESSON_TITLE,
            value="Đơn thức",
            confidence=confidence,
            source=AnalysisSource.AI,
        )


def test_empty_value_is_rejected():
    with pytest.raises(ValueError):
        DocumentFieldProposal(
            field=DocumentField.LESSON_TITLE,
            value="   ",
            confidence=0.8,
            source=AnalysisSource.AI,
        )


def test_analyzer_is_a_protocol():
    assert hasattr(
        DocumentAnalyzer,
        "analyze",
    )
