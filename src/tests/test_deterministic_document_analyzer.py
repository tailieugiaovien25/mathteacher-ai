from document_intelligence import (
    AnalysisSource,
    DeterministicDocumentAnalyzer,
    DocumentField,
)


def test_analyzer_recognizes_multiple_fields():
    analyzer = DeterministicDocumentAnalyzer()

    analysis = analyzer.analyze(
        document_text=(
            "Ngày soạn: 07/09/2026\n"
            "Ngày dạy: 08/09/2026 - Lớp: 8A2\n"
            "TIẾT 4 - §4: PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN\n"
        )
    )

    fields = {
        proposal.field: proposal
        for proposal in analysis.proposals
    }

    assert (
        fields[DocumentField.DRAFTING_DATE].value
        == "07/09/2026"
    )

    assert (
        fields[DocumentField.TEACHING_DATE].value
        == "08/09/2026"
    )

    assert (
        fields[DocumentField.CLASS_NAME].value
        == "8A2"
    )

    assert (
        fields[
            DocumentField.CURRICULUM_PERIOD
        ].value
        == "4"
    )

    assert (
        fields[DocumentField.LESSON_TITLE].value
        == "PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN"
    )


def test_analyzer_marks_source_as_deterministic():
    analyzer = DeterministicDocumentAnalyzer()

    analysis = analyzer.analyze(
        document_text=(
            "Tên bài: Đơn thức"
        )
    )

    proposal = analysis.proposals[0]

    assert (
        proposal.source
        is AnalysisSource.DETERMINISTIC
    )


def test_analyzer_preserves_evidence():
    analyzer = DeterministicDocumentAnalyzer()

    source_line = (
        "TIẾT 4 - §4: PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN"
    )

    analysis = analyzer.analyze(
        document_text=source_line
    )

    lesson_proposals = (
        analysis.for_field(
            DocumentField.LESSON_TITLE
        )
    )

    assert lesson_proposals
    assert (
        lesson_proposals[0].evidence
        == source_line
    )


def test_deterministic_confidence_is_high():
    analyzer = DeterministicDocumentAnalyzer()

    analysis = analyzer.analyze(
        document_text=(
            "Lớp: 6A1\n"
            "Tên bài: Đơn thức"
        )
    )

    for proposal in analysis.proposals:
        assert proposal.confidence >= 0.95


def test_analyzer_does_not_modify_input():
    analyzer = DeterministicDocumentAnalyzer()

    original = (
        "Hoạt động 1: Giáo viên giao nhiệm vụ."
    )

    analysis = analyzer.analyze(
        document_text=original
    )

    assert analysis.proposals == ()
    assert original == (
        "Hoạt động 1: Giáo viên giao nhiệm vụ."
    )
