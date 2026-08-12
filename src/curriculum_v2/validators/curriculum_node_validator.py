from collections.abc import Iterable

from src.core_v2.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    Validator,
)

from src.curriculum_v2.models.curriculum_node import (
    CurriculumNode,
)


class CurriculumNodeValidator(Validator):

    @property
    def data_type_id(self) -> str:
        return "CURRICULUM_NODE"

    def validate(
        self,
        data,
    ) -> ValidationResult:

        if not isinstance(
            data,
            CurriculumNode,
        ):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="CN_INVALID_TYPE",
                    message=(
                        "Dữ liệu phải là "
                        "CurriculumNode."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                )
            )

        issues = []

        required_text_fields = (
            (
                "curriculum_node_id",
                data.curriculum_node_id,
            ),
            (
                "curriculum_ref",
                data.curriculum_ref,
            ),
            (
                "code",
                data.code,
            ),
            (
                "name",
                data.name,
            ),
            (
                "node_type",
                data.node_type,
            ),
            (
                "status",
                data.status,
            ),
        )

        for field_name, value in (
            required_text_fields
        ):
            if not (
                isinstance(value, str)
                and value.strip()
            ):
                issues.append(
                    ValidationIssue(
                        code="CN_REQUIRED_FIELD",
                        message=(
                            f"{field_name} "
                            "không được để trống."
                        ),
                        severity=(
                            ValidationSeverity.ERROR
                        ),
                        field=field_name,
                    )
                )

        if (
            data.parent_id
            == data.curriculum_node_id
        ):
            issues.append(
                ValidationIssue(
                    code="CN_SELF_PARENT",
                    message=(
                        "CurriculumNode không thể "
                        "là parent của chính nó."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field="parent_id",
                )
            )

        if not isinstance(
            data.sequence,
            int,
        ):
            issues.append(
                ValidationIssue(
                    code="CN_INVALID_SEQUENCE",
                    message=(
                        "sequence phải là số nguyên."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field="sequence",
                )
            )

        if issues:
            return ValidationResult(
                issues=tuple(issues)
            )

        return ValidationResult.pass_result()

    def validate_relationships(
        self,
        node: CurriculumNode,
        *,
        existing_nodes: Iterable[
            CurriculumNode
        ],
    ) -> ValidationResult:

        node_map = {
            item.curriculum_node_id: item
            for item in existing_nodes
        }

        issues = []

        if node.parent_id is None:
            return ValidationResult.pass_result()

        parent = node_map.get(
            node.parent_id
        )

        if parent is None:
            issues.append(
                ValidationIssue(
                    code="CN_PARENT_NOT_FOUND",
                    message=(
                        "Không tìm thấy parent: "
                        f"{node.parent_id}"
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field="parent_id",
                )
            )

            return ValidationResult(
                issues=tuple(issues)
            )

        if (
            parent.curriculum_ref
            != node.curriculum_ref
        ):
            issues.append(
                ValidationIssue(
                    code=(
                        "CN_PARENT_CURRICULUM_"
                        "MISMATCH"
                    ),
                    message=(
                        "Parent và child phải "
                        "thuộc cùng Curriculum."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field="parent_id",
                )
            )

        visited = {
            node.curriculum_node_id
        }

        current = parent

        while current is not None:

            if (
                current.curriculum_node_id
                in visited
            ):
                issues.append(
                    ValidationIssue(
                        code="CN_CYCLE_DETECTED",
                        message=(
                            "Phát hiện vòng lặp "
                            "trong cây Curriculum."
                        ),
                        severity=(
                            ValidationSeverity.ERROR
                        ),
                        field="parent_id",
                    )
                )

                break

            visited.add(
                current.curriculum_node_id
            )

            if current.parent_id is None:
                break

            current = node_map.get(
                current.parent_id
            )

            if current is None:
                break

        if issues:
            return ValidationResult(
                issues=tuple(issues)
            )

        return ValidationResult.pass_result()