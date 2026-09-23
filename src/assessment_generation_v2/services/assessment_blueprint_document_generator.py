"""Generate an assessment matrix, specification and AI briefs from governed data.

The caller supplies persisted blueprint cells, active canonical requirements and
approved scope. No subject, grade, or textbook content is hard coded here.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence


class BlueprintDocumentError(ValueError):
    """The supplied curriculum data cannot safely produce a specification."""


@dataclass(frozen=True)
class QuestionBrief:
    cell_sequence: int
    slot_number: int
    topic_code: str
    requirement_code: str
    section_code: str
    question_type_code: str
    cognitive_level_code: str
    score: Decimal
    requirement_text: str

    def ai_input(self) -> dict[str, str | int]:
        """Constrained AI input; a generated item still needs human review."""
        return {
            "cell_sequence": self.cell_sequence,
            "slot_number": self.slot_number,
            "topic_code": self.topic_code,
            "requirement_code": self.requirement_code,
            "requirement_text": self.requirement_text,
            "section_code": self.section_code,
            "question_type_code": self.question_type_code,
            "cognitive_level_code": self.cognitive_level_code,
            "score": str(self.score),
        }


@dataclass(frozen=True)
class GeneratedBlueprintDocuments:
    matrix_rows: tuple[dict[str, object], ...]
    specification_rows: tuple[QuestionBrief, ...]
    total_questions: int
    total_responses: int
    total_score: Decimal
    authority: str = "DRAFT_PREVIEW"


def generate_blueprint_documents(
    *,
    cells: Sequence[Mapping[str, object]],
    links: Sequence[Mapping[str, object]],
    requirements: Mapping[str, Mapping[str, object]],
    selected_topic_codes: frozenset[str],
    selected_requirement_codes: frozenset[str],
    expected_question_count: int,
    expected_response_count: int,
    expected_total_score: Decimal,
) -> GeneratedBlueprintDocuments:
    """Partition every cell into question slots using exact canonical links.

    A requirement link may cover several questions in one topic. Ambiguous
    topic/score allocations fail closed instead of guessing a matrix cell.
    """
    if not cells or not links or not selected_topic_codes or not selected_requirement_codes:
        raise BlueprintDocumentError("Missing blueprint or selected curriculum scope")
    if len({str(c['sequence_number']) for c in cells}) != len(cells):
        raise BlueprintDocumentError("Duplicate matrix cell sequence")
    if len({str(l['requirement_code']) for l in links}) != len(links):
        raise BlueprintDocumentError("Duplicate requirement link")
    if {str(l['requirement_code']) for l in links} != selected_requirement_codes:
        raise BlueprintDocumentError("Requirement links must match selected requirements")
    linked_count = sum(int(link['target_question_count']) for link in links)
    cell_count = sum(int(cell['question_count']) for cell in cells)
    if linked_count > cell_count:
        raise BlueprintDocumentError("YCC? links exceed matrix question count")
    if linked_count < cell_count:
        raise BlueprintDocumentError("YCC? links do not cover matrix question count")

    slots_by_topic: dict[str, list[tuple[str, Decimal]]] = defaultdict(list)
    for link in links:
        code = str(link['requirement_code'])
        requirement = requirements.get(code)
        if (not requirement or str(requirement.get('status')) != 'ACTIVE'
            or not isinstance(requirement.get('metadata'), Mapping)
            or requirement['metadata'].get('canonical_status') != 'VERIFIED'):
            raise BlueprintDocumentError(f"Unverified requirement: {code}")
        topic = str(requirement['topic_code'])
        if topic not in selected_topic_codes:
            raise BlueprintDocumentError(f"Requirement outside selected topics: {code}")
        count = int(link['target_question_count'])
        score = Decimal(str(link['target_score']))
        if count <= 0 or score <= 0:
            raise BlueprintDocumentError(f"Cannot distribute score for {code}")
        slots_by_topic[topic].extend((code, score / count) for _ in range(count))

    # Without an explicit cognitive allocation on a requirement link, two
    # cells in one topic with the same per-question score are ambiguous.
    seen_allocations: set[tuple[str, Decimal]] = set()
    for cell in cells:
        count = int(cell['question_count'])
        if count <= 0:
            raise BlueprintDocumentError("Invalid matrix question count")
        allocation = (str(cell['topic_code']), Decimal(str(cell['target_score'])) / count)
        if allocation in seen_allocations:
            raise BlueprintDocumentError("Ambiguous requirement-to-cell allocation")
        seen_allocations.add(allocation)

    # Each topic may span several cells. Match by exact per-question score;
    # never infer an unknown cognitive allocation from a requirement label.
    briefs: list[QuestionBrief] = []
    rows: list[dict[str, object]] = []
    for cell in sorted(cells, key=lambda c: int(c['sequence_number'])):
        topic = str(cell['topic_code'])
        count = int(cell['question_count'])
        responses = int(cell['response_count'])
        score = Decimal(str(cell['target_score']))
        if topic not in selected_topic_codes or count <= 0 or responses < count or score <= 0:
            raise BlueprintDocumentError("Invalid matrix cell scope or allocation")
        per_question = score / count
        pool = slots_by_topic[topic]
        matching = [slot for slot in pool if slot[1] == per_question]
        if len(matching) < count:
            raise BlueprintDocumentError(f"Insufficient exact YCCĐ slots for {topic}")
        for slot_number, (code, _) in enumerate(matching[:count], 1):
            pool.remove((code, per_question))
            briefs.append(QuestionBrief(
                cell_sequence=int(cell['sequence_number']),
                slot_number=slot_number,
                topic_code=topic,
                requirement_code=code,
                section_code=str(cell['section_code']),
                question_type_code=str(cell['question_type_code']),
                cognitive_level_code=str(cell['cognitive_level_code']),
                score=per_question,
                requirement_text=str(requirements[code].get('requirement_text', '')).strip(),
            ))
        rows.append({
            "topic_code": topic,
            "section_code": str(cell['section_code']),
            "cognitive_level_code": str(cell['cognitive_level_code']),
            "question_type_code": str(cell['question_type_code']),
            "question_count": count,
            "response_count": responses,
            "target_score": score,
        })
    if any(slots_by_topic.values()):
        raise BlueprintDocumentError("YCCĐ links exceed matrix allocation")
    if (sum(int(row['question_count']) for row in rows) != expected_question_count
        or sum(int(row['response_count']) for row in rows) != expected_response_count
        or sum((row['target_score'] for row in rows), Decimal(0)) != expected_total_score):
        raise BlueprintDocumentError("Blueprint totals disagree with profile")
    if any(not brief.requirement_text for brief in briefs):
        raise BlueprintDocumentError("Missing canonical YCCĐ description")
    return GeneratedBlueprintDocuments(
        matrix_rows=tuple(rows),
        specification_rows=tuple(briefs),
        total_questions=expected_question_count,
        total_responses=expected_response_count,
        total_score=expected_total_score,
    )


def draft_questions_with_ai(
    documents: GeneratedBlueprintDocuments,
    *,
    generate: object,
) -> tuple[dict[str, object], ...]:
    """Invoke an injected AI adapter per slot and keep all outputs as drafts.

    The provider adapter accepts the exact ``QuestionBrief.ai_input`` dict and
    returns a mapping with ``prompt_text``, ``answer`` and ``solution``.
    Persistence/review belongs to the existing governed question workflow.
    """
    if not callable(generate):
        raise BlueprintDocumentError("AI question generator is not configured")
    drafts: list[dict[str, object]] = []
    for brief in documents.specification_rows:
        candidate = generate(brief.ai_input())
        if not isinstance(candidate, Mapping):
            raise BlueprintDocumentError("AI result must be a question mapping")
        for field in ("prompt_text", "answer", "solution"):
            if not str(candidate.get(field, "")).strip():
                raise BlueprintDocumentError(f"AI result is missing {field}")
        if any(str(candidate.get(field, expected)) != expected for field, expected in (
            ("topic_code", brief.topic_code),
            ("requirement_code", brief.requirement_code),
            ("question_type_code", brief.question_type_code),
            ("cognitive_level_code", brief.cognitive_level_code),
            ("score", str(brief.score)),
        )):
            raise BlueprintDocumentError("AI result changed a governed allocation")
        drafts.append({
            "prompt_text": str(candidate["prompt_text"]).strip(),
            "answer": str(candidate["answer"]).strip(),
            "solution": str(candidate["solution"]).strip(),
            **brief.ai_input(),
            "review_status": "DRAFT",
        })
    return tuple(drafts)
