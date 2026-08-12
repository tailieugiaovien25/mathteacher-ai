from .data_type_passport import (
    DataTypePassport,
    DataTypeStatus,
)


ACADEMIC_UNIT = DataTypePassport(
    data_type_id="ACADEMIC_UNIT",
    name="Academic Unit",
    family="D1",
    description=(
        "Đơn vị học thuật tổng quát, "
        "có thể đại diện cho môn, phân môn "
        "hoặc đơn vị học thuật tương đương."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "academic_unit_id",
        "code",
        "name",
        "status",
    ),
    extensible_fields=(
        "parent_id",
        "description",
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "RELATIONSHIP",
        "VERSION",
        "MAP",
        "COMPOSE",
        "ROUTE",
    ),
    applicable_rules=(
        "RELATIONSHIP_RULE",
        "COMPOSITION_RULE",
        "MAPPING_RULE",
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


GRADE_LEVEL = DataTypePassport(
    data_type_id="GRADE_LEVEL",
    name="Grade Level",
    family="D1",
    description=(
        "Khối/cấp học dùng để xác định "
        "phạm vi chương trình và lớp học."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "grade_level_id",
        "code",
        "name",
        "sequence",
        "status",
    ),
    extensible_fields=(
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "RELATIONSHIP",
        "VERSION",
        "MAP",
        "ROUTE",
    ),
    applicable_rules=(
        "RELATIONSHIP_RULE",
        "MAPPING_RULE",
    ),
    allowed_outputs=(
        "BASE44",
        "WORD",
        "EXCEL",
        "PDF",
        "API",
    ),
    version_policy="SIMPLE",
    update_policy="CONTROLLED",
    retention_policy="ACTIVE_FIRST",
)


CLASS_GROUP = DataTypePassport(
    data_type_id="CLASS_GROUP",
    name="Class Group",
    family="D1",
    description=(
        "Lớp học thực tế trong một "
        "khoảng thời gian/năm học xác định."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "class_group_id",
        "code",
        "name",
        "grade_level_ref",
        "academic_period_ref",
        "status",
    ),
    extensible_fields=(
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "RELATIONSHIP",
        "EFFECTIVE_PERIOD",
        "ASSIGN",
        "SCHEDULE",
        "MAP",
        "ROUTE",
    ),
    applicable_rules=(
        "RELATIONSHIP_RULE",
        "ASSIGNMENT_RULE",
        "SCHEDULE_RULE",
    ),
    allowed_outputs=(
        "BASE44",
        "WORD",
        "EXCEL",
        "PDF",
        "API",
    ),
    version_policy="PERIOD_BASED",
    update_policy="CONTROLLED",
    retention_policy="ACTIVE_FIRST",
)


TEACHER = DataTypePassport(
    data_type_id="TEACHER",
    name="Teacher",
    family="D1",
    description=(
        "Identity của giáo viên. "
        "Role, Assignment và Schedule "
        "được quản lý độc lập."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "teacher_id",
        "code",
        "display_name",
        "status",
    ),
    extensible_fields=(
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "IDENTITY",
        "RELATIONSHIP",
        "EFFECTIVE_PERIOD",
        "ASSIGN",
        "MAP",
        "ROUTE",
    ),
    applicable_rules=(
        "IDENTITY_RULE",
        "ASSIGNMENT_RULE",
        "RELATIONSHIP_RULE",
    ),
    allowed_outputs=(
        "BASE44",
        "WORD",
        "EXCEL",
        "PDF",
        "API",
    ),
    version_policy="IDENTITY_STABLE",
    update_policy="CONTROLLED",
    retention_policy="ACTIVE_FIRST",
)


CURRICULUM = DataTypePassport(
    data_type_id="CURRICULUM",
    name="Curriculum",
    family="D2",
    description=(
        "Identity chương trình giáo dục; "
        "thay đổi theo thời gian được quản lý "
        "bằng Versioning và Mapping."
    ),
    status=DataTypeStatus.ACCEPTED,
    required_fields=(
        "curriculum_id",
        "code",
        "name",
        "status",
    ),
    extensible_fields=(
        "description",
        "metadata",
    ),
    supported_capabilities=(
        "VALIDATE",
        "VERSION",
        "RELATIONSHIP",
        "MAP",
        "COMPOSE",
        "ROUTE",
    ),
    applicable_rules=(
        "VERSION_RULE",
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
    version_policy="VERSIONED",
    update_policy="CONTROLLED",
    retention_policy="ACTIVE_FIRST",
)


DEFAULT_PASSPORTS = (
    ACADEMIC_UNIT,
    GRADE_LEVEL,
    CLASS_GROUP,
    TEACHER,
    CURRICULUM,
)