from dataclasses import replace

from src.curriculum_v2.models import (
    Competency,
)

from src.curriculum_v2.validators import (
    CompetencyValidator,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-003C - "
        "COMPETENCY BASIC TEST"
    )
    print("=" * 72)

    validator = CompetencyValidator()

    competency = Competency(
        competency_id="COMP-001",
        name="Tư duy và lập luận toán học",
        competency_type="SUBJECT_SPECIFIC",
        description=(
            "Năng lực đặc thù thuộc môn Toán."
        ),
        status="ACTIVE",
        effective_from="2026-09-01",
    )

    # T1 ADD
    result = validator.validate(
        competency
    )

    assert result.is_valid

    print(
        "T1 ADD valid competency: PASS"
    )

    # T2 CHANGE
    changed = replace(
        competency,
        name=(
            "Tư duy và lập luận toán học "
            "được cập nhật"
        ),
        metadata={
            "source_version": "V2",
        },
    )

    assert validator.validate(
        changed
    ).is_valid

    assert (
        changed.competency_id
        == competency.competency_id
    )

    print(
        "T2 CHANGE stable identity: PASS"
    )

    # P1/P8:
    # loại mới không cần sửa model/core
    future_type = replace(
        competency,
        competency_type="FUTURE_NEW_TYPE",
    )

    assert validator.validate(
        future_type
    ).is_valid

    print(
        "P1 new competency type: PASS"
    )

    # T7 name rỗng
    empty_name = replace(
        competency,
        name="",
    )

    assert not validator.validate(
        empty_name
    ).is_valid

    print(
        "T7 empty name blocked: PASS"
    )

    # T7 ngày sai
    invalid_date = replace(
        competency,
        effective_from="01/09/2026",
    )

    assert not validator.validate(
        invalid_date
    ).is_valid

    print(
        "T7 invalid date blocked: PASS"
    )

    # T7 khoảng hiệu lực sai
    invalid_period = replace(
        competency,
        effective_from="2027-09-01",
        effective_to="2026-08-31",
    )

    assert not validator.validate(
        invalid_period
    ).is_valid

    print(
        "T7 invalid effective period blocked: PASS"
    )

    # P8
    competency_fields = set(
        competency.__dataclass_fields__
    )

    forbidden_identity_fields = {
        "official_code",
        "abbreviation",
        "external_code",
    }

    assert not (
        competency_fields
        & forbidden_identity_fields
    )

    print(
        "P8 identity independent from encoding: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - COMPETENCY BASIC VERIFIED"
    )


if __name__ == "__main__":
    main()