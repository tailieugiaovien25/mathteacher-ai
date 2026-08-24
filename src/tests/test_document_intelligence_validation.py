from document_intelligence import (
    AnalysisSource,
    CanonicalDocumentContext,
    DocumentAnalysis,
    DocumentAnalysisValidator,
    DocumentField,
    DocumentFieldProposal,
    ValidationStatus,
)


def proposal(
    field,
    value,
):
    return DocumentFieldProposal(
        field=field,
        value=value,
        confidence=0.9,
        source=AnalysisSource.AI,
    )


def test_matching_canonical_value_is_accepted():
    analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.CLASS_NAME,
                "6A1",
            ),
        )
    )

    result = DocumentAnalysisValidator().validate(
        analysis=analysis,
        canonical=CanonicalDocumentContext(
            class_name="6A1"
        ),
    )

    assert (
        result.proposals[0].status
        is ValidationStatus.ACCEPTED
    )


def test_conflicting_ai_value_is_rejected_as_conflict():
    analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.CLASS_NAME,
                "6A1",
            ),
        )
    )

    result = DocumentAnalysisValidator().validate(
        analysis=analysis,
        canonical=CanonicalDocumentContext(
            class_name="6A2"
        ),
    )

    validated = result.proposals[0]

    assert (
        validated.status
        is ValidationStatus.CONFLICT
    )

    assert validated.canonical_value == "6A2"


def test_missing_canonical_value_is_unverified():
    analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.LESSON_TITLE,
                "Đơn thức",
            ),
        )
    )

    result = DocumentAnalysisValidator().validate(
        analysis=analysis,
        canonical=CanonicalDocumentContext(),
    )

    assert (
        result.proposals[0].status
        is ValidationStatus.UNVERIFIED
    )


def test_validation_normalizes_case_and_spaces():
    analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.LESSON_TITLE,
                "  ĐƠN   THỨC ",
            ),
        )
    )

    result = DocumentAnalysisValidator().validate(
        analysis=analysis,
        canonical=CanonicalDocumentContext(
            lesson_title="đơn thức"
        ),
    )

    assert (
        result.proposals[0].status
        is ValidationStatus.ACCEPTED
    )


def test_curriculum_period_is_compared_as_text():
    analysis = DocumentAnalysis(
        proposals=(
            proposal(
                DocumentField.CURRICULUM_PERIOD,
                "4",
            ),
        )
    )

    result = DocumentAnalysisValidator().validate(
        analysis=analysis,
        canonical=CanonicalDocumentContext(
            curriculum_period=4
        ),
    )

    assert (
        result.proposals[0].status
        is ValidationStatus.ACCEPTED
    )
