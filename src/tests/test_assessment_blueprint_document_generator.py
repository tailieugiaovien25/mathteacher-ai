from decimal import Decimal

import pytest

from assessment_generation_v2.services.assessment_blueprint_document_generator import (
    BlueprintDocumentError,
    generate_blueprint_documents,
)


def fixture_data():
    cells = [
        dict(sequence_number=1, topic_code='T1', section_code='MCQ',
             question_type_code='MULTIPLE_CHOICE', cognitive_level_code='KNOW',
             question_count=2, response_count=2, target_score='0.50'),
        dict(sequence_number=2, topic_code='T1', section_code='ESSAY',
             question_type_code='ESSAY', cognitive_level_code='APPLY',
             question_count=1, response_count=1, target_score='1.50'),
    ]
    links = [
        dict(requirement_code='R1', target_question_count=2, target_score='0.50'),
        dict(requirement_code='R2', target_question_count=1, target_score='1.50'),
    ]
    requirements = {code: dict(topic_code='T1', requirement_text=f'Đạt {code}',
                               status='ACTIVE', metadata={'canonical_status': 'VERIFIED'})
                    for code in ('R1', 'R2')}
    return dict(cells=cells, links=links, requirements=requirements,
                selected_topic_codes=frozenset({'T1'}),
                selected_requirement_codes=frozenset({'R1', 'R2'}),
                expected_question_count=3, expected_response_count=3,
                expected_total_score=Decimal('2.00'))


def test_generated_documents_constrain_ai_to_exact_matrix_and_yccd():
    result = generate_blueprint_documents(**fixture_data())
    assert [r.requirement_code for r in result.specification_rows] == ['R1', 'R1', 'R2']
    assert [r.score for r in result.specification_rows] == [Decimal('.25'), Decimal('.25'), Decimal('1.50')]
    assert result.specification_rows[2].ai_input()['cognitive_level_code'] == 'APPLY'
    assert result.authority == 'DRAFT_PREVIEW'


def test_mismatched_topic_fails_instead_of_misallocating_requirements():
    data = fixture_data()
    data['requirements']['R2']['topic_code'] = 'OTHER'
    with pytest.raises(BlueprintDocumentError, match='outside selected topics'):
        generate_blueprint_documents(**data)


def test_missing_canonical_verification_fails_closed():
    data = fixture_data()
    data['requirements']['R1']['metadata'] = {}
    with pytest.raises(BlueprintDocumentError, match='Unverified requirement'):
        generate_blueprint_documents(**data)


def test_excess_or_incomplete_links_fail_closed():
    data = fixture_data()
    data['links'][0]['target_question_count'] = 3
    with pytest.raises(BlueprintDocumentError, match='exceed matrix'):
        generate_blueprint_documents(**data)


def test_ai_can_only_draft_questions_for_exact_governed_slots():
    from assessment_generation_v2.services.assessment_blueprint_document_generator import draft_questions_with_ai
    documents = generate_blueprint_documents(**fixture_data())
    drafts = draft_questions_with_ai(documents, generate=lambda brief: {
        'prompt_text': f"Câu hỏi {brief['slot_number']}",
        'answer': 'Đáp án', 'solution': 'Lời giải',
    })
    assert len(drafts) == 3
    assert all(row['review_status'] == 'DRAFT' for row in drafts)
    assert [row['requirement_code'] for row in drafts] == ['R1', 'R1', 'R2']
    with pytest.raises(BlueprintDocumentError, match='changed a governed allocation'):
        draft_questions_with_ai(documents, generate=lambda _: {
            'prompt_text': 'A', 'answer': 'B', 'solution': 'C', 'score': '100',
        })
