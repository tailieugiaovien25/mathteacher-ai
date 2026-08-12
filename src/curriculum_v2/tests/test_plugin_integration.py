from src.core_v2.registry import (
    DataTypeRegistry,
)

from src.core_v2.validation import (
    ValidatorRegistry,
)

from src.curriculum_v2.models import (
    CurriculumNode,
)

from src.curriculum_v2.plugin import (
    register_curriculum_module,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-001D - "
        "CURRICULUM PLUGIN INTEGRATION"
    )
    print("=" * 72)

    data_type_registry = (
        DataTypeRegistry()
    )

    validator_registry = (
        ValidatorRegistry()
    )

    register_curriculum_module(
        data_type_registry=(
            data_type_registry
        ),
        validator_registry=(
            validator_registry
        ),
    )

    assert data_type_registry.exists(
        "CURRICULUM_NODE"
    )

    print(
        "Passport plugin registration: PASS"
    )

    assert validator_registry.exists(
        "CURRICULUM_NODE"
    )

    print(
        "Validator plugin registration: PASS"
    )

    passport = data_type_registry.get(
        "CURRICULUM_NODE"
    )

    assert (
        passport.data_type_id
        == "CURRICULUM_NODE"
    )

    validator = validator_registry.get(
        "CURRICULUM_NODE"
    )

    node = CurriculumNode(
        curriculum_node_id="CN-001",
        curriculum_ref="CURR-001",
        code="TOPIC-001",
        name="Số và Đại số",
        node_type="CONTENT_STRAND",
    )

    result = validator.validate(
        node
    )

    assert result.is_valid

    print(
        "Plugin validation through Core: PASS"
    )

    duplicate_blocked = False

    try:
        register_curriculum_module(
            data_type_registry=(
                data_type_registry
            ),
            validator_registry=(
                validator_registry
            ),
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate plugin registration blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - CURRICULUM MODULE PLUGGED INTO CORE"
    )


if __name__ == "__main__":
    main()