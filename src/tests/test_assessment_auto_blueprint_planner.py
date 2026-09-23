from decimal import Decimal

import pytest

from assessment_generation_v2.services.assessment_auto_blueprint_planner import (
    AutoBlueprintError,
    plan_blueprint,
)


SECTIONS = [
    {'section_code': 'MCQ', 'question_type_code': 'MULTIPLE_CHOICE',
     'question_count': 2, 'response_count': 2, 'section_score': '.50'},
    {'section_code': 'ESSAY', 'question_type_code': 'ESSAY',
     'question_count': 1, 'response_count': 1, 'section_score': '1.50'},
]
LEVELS = {'KNOW': Decimal('.50'), 'APPLY': Decimal('1.50')}


def test_auto_planner_uses_reviewed_eligibility_and_exact_profile_totals():
    requirements = [
        {'requirement_code': 'R1', 'topic_code': 'T1', 'eligibility': [('MCQ', 'KNOW')]},
        {'requirement_code': 'R2', 'topic_code': 'T2', 'eligibility': [('ESSAY', 'APPLY')]},
    ]
    cells = plan_blueprint(sections=SECTIONS, cognitive_targets=LEVELS,
                           requirements=requirements, total_score=Decimal('2'))
    assert [(c.topic_code, c.question_count) for c in cells] == [('T1', 2), ('T2', 1)]
    assert sum((c.target_score for c in cells), Decimal(0)) == Decimal('2')


def test_auto_planner_can_propose_subset_when_selected_yccd_exceeds_slots():
    requirements = [
        {'requirement_code': f'R{i}', 'topic_code': 'T1',
         'eligibility': [('MCQ', 'KNOW')]} for i in range(4)
    ] + [{'requirement_code': 'R5', 'topic_code': 'T2', 'eligibility': [('ESSAY', 'APPLY')]}]
    cells = plan_blueprint(sections=SECTIONS, cognitive_targets=LEVELS,
                           requirements=requirements, total_score=Decimal('2'))
    assert sum(c.question_count for c in cells) == 3
    assert {'T1', 'T2'} == {c.topic_code for c in cells}


def test_auto_planner_requires_reviewed_level_and_type_policy():
    with pytest.raises(AutoBlueprintError, match='Missing curated eligibility'):
        plan_blueprint(sections=SECTIONS, cognitive_targets=LEVELS,
                       requirements=[{'requirement_code': 'R', 'topic_code': 'T'}],
                       total_score=Decimal('2'))


def test_auto_planner_rejects_incompatible_cognitive_targets():
    with pytest.raises(AutoBlueprintError, match='No exact governed allocation'):
        plan_blueprint(sections=SECTIONS, cognitive_targets=LEVELS,
                       requirements=[{'requirement_code': 'R', 'topic_code': 'T',
                                      'eligibility': [('MCQ', 'APPLY')]}],
                       total_score=Decimal('2'))
