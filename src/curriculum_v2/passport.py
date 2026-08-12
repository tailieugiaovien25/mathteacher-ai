from src.core_v2.registry import (
    DataTypePassport,
    DataTypeStatus,
)


CURRICULUM_NODE_PASSPORT = DataTypePassport(
    data_type_id="CURRICULUM_NODE",
    name="Curriculum Node",
    family="D2",
    description=(
        "Nút nội dung chương trình tổng quát. "
        "Có thể đại diện cho mạch, chủ đề, chương, bài, "
        "nội dung hoặc loại node mở rộng khác."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "curriculum_node_id",
        "curriculum_ref",
        "code",
        "name",
        "node_type",
        "status",
    ),
    extensible_fields=(
        "parent_id",
        "sequence",
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "RELATIONSHIP",
        "MAP",
        "COMPOSE",
        "ROUTE",
    ),
    applicable_rules=(
        "RELATIONSHIP_RULE",
        "MAPPING_RULE",
        "COMPOSITION_RULE",
    ),
    allowed_outputs=(
        "BASE44",
        "WORD",
        "EXCEL",
        "PDF",
        "API",
    ),
    version_policy="VERSIONED_WHEN_NEEDED",
    update_policy="CONTROLLED",
    retention_policy="ACTIVE_FIRST",
)