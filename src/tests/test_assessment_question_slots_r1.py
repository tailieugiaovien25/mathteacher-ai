from decimal import Decimal
from pathlib import Path

import pytest

from assessment_generation_v2.services.assessment_question_slot_service import (
    AssessmentQuestionSlotPlanningError,
    AssessmentQuestionSlotPlanningService,
    BlueprintQuestionSlotCell,
    BlueprintQuestionSlotRequirement,
)


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase/migrations/"
    / "202609230002_assessment_blueprint_question_slots.sql"
)
BLUEPRINT_VERSION_ID = "f0079bc4-c788-4d6e-b8fe-5f22e2522610"


def _cell(
    cell_id: str,
    sequence: int,
    topic: str,
    section: str,
    level: str,
    question_type: str,
    question_count: int,
    target_score: str,
) -> BlueprintQuestionSlotCell:
    return BlueprintQuestionSlotCell(
        blueprint_cell_id=cell_id,
        sequence_number=sequence,
        section_code=section,
        topic_code=topic,
        cognitive_level_code=level,
        question_type_code=question_type,
        question_count=question_count,
        target_score=Decimal(target_score),
    )


def _requirement(
    code: str,
    sequence: int,
    topic: str,
    question_count: int,
    target_score: str,
) -> BlueprintQuestionSlotRequirement:
    return BlueprintQuestionSlotRequirement(
        requirement_code=code,
        topic_code=topic,
        sequence_number=sequence,
        target_question_count=question_count,
        target_score=Decimal(target_score),
    )


def _toan7_cells() -> tuple[BlueprintQuestionSlotCell, ...]:
    return (
        _cell(
            "f06f9afd-9c79-44f7-a244-94a2831000e5",
            10,
            "CURR-NODE-MATH-G7-004",
            "MCQ",
            "KNOW",
            "MULTIPLE_CHOICE",
            3,
            "0.75",
        ),
        _cell(
            "cad900aa-b744-4251-8984-ff5fd390ed34",
            11,
            "CURR-NODE-MATH-G7-005",
            "MCQ",
            "KNOW",
            "MULTIPLE_CHOICE",
            3,
            "0.75",
        ),
        _cell(
            "efbce423-5713-4b1f-aedb-3e24931c2846",
            12,
            "CURR-NODE-MATH-G7-008",
            "MCQ",
            "KNOW",
            "MULTIPLE_CHOICE",
            2,
            "0.50",
        ),
        _cell(
            "565998f6-9a27-40d2-a75b-05378b11fb27",
            13,
            "CURR-NODE-MATH-G7-025",
            "MCQ",
            "KNOW",
            "MULTIPLE_CHOICE",
            2,
            "0.50",
        ),
        _cell(
            "7215b2c8-4d49-4637-a5bc-f5268db0b113",
            14,
            "CURR-NODE-MATH-G7-034",
            "MCQ",
            "KNOW",
            "MULTIPLE_CHOICE",
            2,
            "0.50",
        ),
        _cell(
            "b83d7569-9cd8-4d83-84af-3976286b7888",
            20,
            "CURR-NODE-MATH-G7-023",
            "TF",
            "KNOW",
            "TRUE_FALSE",
            1,
            "1.00",
        ),
        _cell(
            "fb77ce3d-04bc-4b81-92c2-505ab5516de3",
            21,
            "CURR-NODE-MATH-G7-033",
            "TF",
            "UNDERSTAND",
            "TRUE_FALSE",
            1,
            "1.00",
        ),
        _cell(
            "0d8f846e-f8f8-4138-8ca8-d8f3b18666af",
            30,
            "CURR-NODE-MATH-G7-008",
            "SHORT",
            "UNDERSTAND",
            "SHORT_RESPONSE",
            2,
            "1.00",
        ),
        _cell(
            "c93a876b-bb59-491c-9570-b07d034ee02d",
            31,
            "CURR-NODE-MATH-G7-025",
            "SHORT",
            "UNDERSTAND",
            "SHORT_RESPONSE",
            2,
            "1.00",
        ),
        _cell(
            "2a760d9a-3702-4961-be69-bb594be155e7",
            40,
            "CURR-NODE-MATH-G7-005",
            "ESSAY",
            "APPLY",
            "ESSAY",
            1,
            "1.50",
        ),
        _cell(
            "fbcc0f66-d9b0-4ad2-ab93-478cec9bad12",
            41,
            "CURR-NODE-MATH-G7-025",
            "ESSAY",
            "APPLY",
            "ESSAY",
            1,
            "1.50",
        ),
    )


def _toan7_requirements() -> tuple[BlueprintQuestionSlotRequirement, ...]:
    return (
        _requirement("YCCD-MATH-07-0001", 1, "CURR-NODE-MATH-G7-004", 1, "0.25"),
        _requirement("YCCD-MATH-07-0002", 2, "CURR-NODE-MATH-G7-004", 1, "0.25"),
        _requirement("YCCD-MATH-07-0004", 3, "CURR-NODE-MATH-G7-004", 1, "0.25"),
        _requirement("YCCD-MATH-07-0006", 4, "CURR-NODE-MATH-G7-005", 2, "0.50"),
        _requirement("YCCD-MATH-07-0007", 5, "CURR-NODE-MATH-G7-005", 1, "0.25"),
        _requirement("YCCD-MATH-07-0013", 7, "CURR-NODE-MATH-G7-008", 1, "0.25"),
        _requirement("YCCD-MATH-07-0014", 8, "CURR-NODE-MATH-G7-008", 1, "0.25"),
        _requirement("YCCD-MATH-07-0048", 9, "CURR-NODE-MATH-G7-025", 1, "0.25"),
        _requirement("YCCD-MATH-07-0052", 10, "CURR-NODE-MATH-G7-025", 1, "0.25"),
        _requirement("YCCD-MATH-07-0060", 11, "CURR-NODE-MATH-G7-034", 1, "0.25"),
        _requirement("YCCD-MATH-07-0062", 12, "CURR-NODE-MATH-G7-034", 1, "0.25"),
        _requirement("YCCD-MATH-07-0042", 13, "CURR-NODE-MATH-G7-023", 1, "1.00"),
        _requirement("YCCD-MATH-07-0058", 14, "CURR-NODE-MATH-G7-033", 1, "1.00"),
        _requirement("YCCD-MATH-07-0015", 15, "CURR-NODE-MATH-G7-008", 1, "0.50"),
        _requirement("YCCD-MATH-07-0019", 16, "CURR-NODE-MATH-G7-008", 1, "0.50"),
        _requirement("YCCD-MATH-07-0049", 17, "CURR-NODE-MATH-G7-025", 1, "0.50"),
        _requirement("YCCD-MATH-07-0050", 18, "CURR-NODE-MATH-G7-025", 1, "0.50"),
        _requirement("YCCD-MATH-07-0010", 19, "CURR-NODE-MATH-G7-005", 1, "1.50"),
        _requirement("YCCD-MATH-07-0046", 20, "CURR-NODE-MATH-G7-025", 1, "1.50"),
    )


def test_toan7_approved_blueprint_partitions_into_exactly_20_slots() -> None:
    slots = AssessmentQuestionSlotPlanningService().plan(
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        cells=_toan7_cells(),
        requirements=_toan7_requirements(),
    )

    assert len(slots) == 20
    assert tuple(row.display_position for row in slots) == tuple(range(1, 21))
    assert slots[0].requirement_code == "YCCD-MATH-07-0001"
    assert slots[-1].requirement_code == "YCCD-MATH-07-0046"

    counts: dict[str, int] = {}
    for slot in slots:
        counts[slot.section_code] = counts.get(slot.section_code, 0) + 1

    assert counts == {
        "MCQ": 12,
        "TF": 2,
        "SHORT": 4,
        "ESSAY": 2,
    }


def test_repeated_requirement_materializes_distinct_occurrences() -> None:
    slots = AssessmentQuestionSlotPlanningService().plan(
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        cells=_toan7_cells(),
        requirements=_toan7_requirements(),
    )

    repeated = tuple(
        row
        for row in slots
        if row.requirement_code == "YCCD-MATH-07-0006"
    )

    assert len(repeated) == 2
    assert tuple(row.requirement_occurrence_number for row in repeated) == (1, 2)
    assert all(row.target_score == Decimal("0.25") for row in repeated)


def test_ambiguous_requirement_to_cell_mapping_fails_closed() -> None:
    cells = (
        _cell(
            "11111111-1111-4111-8111-111111111111",
            1,
            "TOPIC-X",
            "MCQ-A",
            "KNOW",
            "MULTIPLE_CHOICE",
            1,
            "0.25",
        ),
        _cell(
            "22222222-2222-4222-8222-222222222222",
            2,
            "TOPIC-X",
            "MCQ-B",
            "UNDERSTAND",
            "MULTIPLE_CHOICE",
            1,
            "0.25",
        ),
    )
    requirements = (
        _requirement("REQ-X", 1, "TOPIC-X", 1, "0.25"),
    )

    with pytest.raises(
        AssessmentQuestionSlotPlanningError,
        match="exactly one matrix cell",
    ):
        AssessmentQuestionSlotPlanningService().plan(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            cells=cells,
            requirements=requirements,
        )


def test_incomplete_partition_fails_closed() -> None:
    requirements = tuple(
        row
        for row in _toan7_requirements()
        if row.requirement_code != "YCCD-MATH-07-0062"
    )

    with pytest.raises(
        AssessmentQuestionSlotPlanningError,
        match="exactly partition",
    ):
        AssessmentQuestionSlotPlanningService().plan(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            cells=_toan7_cells(),
            requirements=requirements,
        )


def test_migration_is_governed_and_not_directly_writable() -> None:
    text = MIGRATION.read_text(encoding="utf-8")

    for marker in (
        "assessment_blueprint_question_slots",
        "materialize_assessment_blueprint_question_slots",
        "APPROVED_ACTIVE_LOCKED_BLUEPRINT_REQUIRED",
        "REQUIREMENT_TO_CELL_MAPPING_NOT_UNIQUE",
        "QUESTION_SLOT_PARTITION_MISMATCH",
        "QUESTION_SLOT_COUNT_MISMATCH",
        "security definer",
        "set search_path = ''",
        "enable row level security",
        "grant select on table",
        "grant execute on function",
    ):
        assert marker in text

    assert (
        "grant insert on table\n"
        "    public.assessment_blueprint_question_slots"
    ) not in text
    assert (
        "grant update on table\n"
        "    public.assessment_blueprint_question_slots"
    ) not in text
    assert (
        "grant delete on table\n"
        "    public.assessment_blueprint_question_slots"
    ) not in text


def test_fractional_per_question_score_keeps_precision() -> None:
    slots = AssessmentQuestionSlotPlanningService().plan(
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        cells=(
            _cell(
                "11111111-1111-4111-8111-111111111111",
                1, "TOPIC-X", "MCQ", "KNOW", "MULTIPLE_CHOICE",
                3, "1.00",
            ),
        ),
        requirements=(
            _requirement("REQ-X", 1, "TOPIC-X", 3, "1.00"),
        ),
    )
    assert len(slots) == 3
    assert abs(sum((slot.target_score for slot in slots), Decimal(0))
               - Decimal("1.00")) <= Decimal("0.0001")


def test_migration_checks_existing_rows_and_stored_scores() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert "EXISTING_QUESTION_SLOTS_INCOMPLETE" in text
    assert "QUESTION_SLOT_SCORE_MISMATCH" in text
    assert "pg_advisory_xact_lock" in text
    assert "numeric(12,6)" in text
    assert "numeric(6,2)" not in text
