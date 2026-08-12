from src.core_v2.registry import (
    DataTypeRegistry,
)

from src.core_v2.validation import (
    ValidatorRegistry,
)

from src.curriculum_v2.passport import (
    CURRICULUM_NODE_PASSPORT,
)

from src.curriculum_v2.validators import (
    CurriculumNodeValidator,
)


def register_curriculum_module(
    *,
    data_type_registry: DataTypeRegistry,
    validator_registry: ValidatorRegistry,
) -> None:
    """
    Đăng ký các thành phần của Curriculum V2
    vào Core V2.

    Core không import curriculum_v2.
    Curriculum module tự cắm vào Core.
    """

    data_type_registry.register(
        CURRICULUM_NODE_PASSPORT
    )

    validator_registry.register(
        CurriculumNodeValidator()
    )