from dataclasses import replace

from src.curriculum_v2.models import (
    LearningOutcome,
)

from src.curriculum_v2.validators import (
    LearningOutcomeValidator,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-002B - "
        "LEARNING OUTCOME TEST"
    )
    print("=" * 72)

    validator = LearningOutcomeValidator()

    outcome = LearningOutcome(
        learning_outcome_id="LO-001",
        curriculum_ref="CURR-001",
        code="LO-001",
        statement=(
            "Thực hiện được một yêu cầu "
            "học tập xác định."
        ),
        outcome_type="GENERAL",
        status="ACTIVE",
        effective_from="2026-09-01",
    )

    # T1 ADD
    result = validator.validate(
        outcome
    )

    assert result.is_valid

    print(
        "T1 ADD valid outcome: PASS"
    )

    # T2 CHANGE
    changed = replace(
        outcome,
        statement=(
            "Nội dung YCCD được cập nhật "
            "theo nguồn có thẩm quyền."
        ),
        metadata={
            "source_version": "V2",
        },
    )

    assert validator.validate(
        changed
    ).is_valid

    assert (
        changed.learning_outcome_id
        == outcome.learning_outcome_id
    )

    print(
        "T2 CHANGE stable identity: PASS"
    )

    # P1: outcome_type mới
    future_type = replace(
        outcome,
        outcome_type="FUTURE_NEW_TYPE",
    )

    assert validator.validate(
        future_type
    ).is_valid

    print(
        "P1 new outcome type: PASS"
    )

    # T7: statement rỗng
    empty_statement = replace(
        outcome,
        statement="",
    )

    assert not validator.validate(
        empty_statement
    ).is_valid

    print(
        "T7 empty statement blocked: PASS"
    )

    # T7: ngày sai định dạng
    invalid_date = replace(
        outcome,
        effective_from="01/09/2026",
    )

    assert not validator.validate(
        invalid_date
    ).is_valid

    print(
        "T7 invalid date blocked: PASS"
    )

    # T7: khoảng hiệu lực sai
    invalid_period = replace(
        outcome,
        effective_from="2027-09-01",
        effective_to="2026-08-31",
    )

    assert not validator.validate(
        invalid_period
    ).is_valid

    print(
        "T7 invalid effective period blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - LEARNING OUTCOME BASIC VERIFIED"
    )


if __name__ == "__main__":
    main()