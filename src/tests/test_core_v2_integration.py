from typing import Any

from src.core_v2.registry import (
    ACADEMIC_UNIT,
    DataTypeRegistry,
)

from src.core_v2.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    Validator,
    ValidatorRegistry,
)

from src.core_v2.rules import (
    Rule,
    RuleRegistry,
)

from src.core_v2.processing import (
    Processor,
    ProcessorRouter,
)

from src.core_v2.mapping import (
    Mapping,
    MappingRegistry,
)

from src.core_v2.routing import (
    OutputAdapter,
    OutputRouter,
)

from src.core_v2.governance import (
    GovernancePolicy,
    LifecycleStatus,
    RetentionPolicy,
    UpdatePolicy,
)


# ============================================================
# FAKE VALIDATOR
# ============================================================

class AcademicUnitValidator(Validator):

    @property
    def data_type_id(self) -> str:
        return "ACADEMIC_UNIT"

    def validate(
        self,
        data: Any,
    ) -> ValidationResult:

        if not isinstance(data, dict):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="AU_INVALID_DATA",
                    message="Dữ liệu phải là dict.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        required = (
            "academic_unit_id",
            "code",
            "name",
            "status",
        )

        issues = []

        for field_name in required:

            if not data.get(field_name):

                issues.append(
                    ValidationIssue(
                        code="AU_REQUIRED_FIELD",
                        message=(
                            f"Thiếu trường bắt buộc: "
                            f"{field_name}"
                        ),
                        severity=ValidationSeverity.ERROR,
                        field=field_name,
                    )
                )

        if issues:
            return ValidationResult(
                issues=tuple(issues)
            )

        return ValidationResult.pass_result()


# ============================================================
# FAKE PROCESSOR
# ============================================================

class AcademicUnitComposeProcessor(
    Processor
):

    @property
    def processor_id(self) -> str:
        return "PROC-AU-COMPOSE"

    @property
    def data_type_id(self) -> str:
        return "ACADEMIC_UNIT"

    @property
    def capability(self) -> str:
        return "COMPOSE"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        result = dict(data)

        result["processed_by"] = (
            self.processor_id
        )

        result["context"] = (
            context or {}
        )

        return result


# ============================================================
# FAKE OUTPUT ADAPTER
# ============================================================

class Base44OutputAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-BASE44"

    @property
    def output_type(self) -> str:
        return "BASE44"

    def render(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "adapter": self.adapter_id,
            "output_type": self.output_type,
            "payload": data,
            "context": context or {},
        }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 76)
    print(
        "V2-CORE-010 - "
        "CORE INTEGRATION TEST"
    )
    print("=" * 76)

    # --------------------------------------------------------
    # 1. Data Type Registry
    # --------------------------------------------------------

    data_type_registry = (
        DataTypeRegistry()
    )

    data_type_registry.register(
        ACADEMIC_UNIT
    )

    passport = (
        data_type_registry.get(
            "ACADEMIC_UNIT"
        )
    )

    assert (
        passport.data_type_id
        == "ACADEMIC_UNIT"
    )

    print(
        "1. Data Type Registry: PASS"
    )

    # --------------------------------------------------------
    # 2. Validator Registry
    # --------------------------------------------------------

    validator_registry = (
        ValidatorRegistry()
    )

    validator = (
        AcademicUnitValidator()
    )

    validator_registry.register(
        validator
    )

    source_data = {
        "academic_unit_id": "AU-DAI-SO",
        "code": "DAI_SO",
        "name": "Đại số",
        "status": "ACTIVE",
        "parent_id": "AU-TOAN",
    }

    validation_result = (
        validator_registry
        .get(
            "ACADEMIC_UNIT"
        )
        .validate(
            source_data
        )
    )

    assert (
        validation_result.is_valid
    )

    print(
        "2. Validation: PASS"
    )

    # --------------------------------------------------------
    # 3. Rule Registry
    # --------------------------------------------------------

    rule_registry = (
        RuleRegistry()
    )

    merge_rule = Rule(
        rule_id="RULE-AU-MERGE-001",
        rule_type="COMPOSITION",
        applies_to_data_type=(
            "ACADEMIC_UNIT"
        ),
        context="SUBJECT_SUMMARY",
        priority=10,
        condition={
            "parent_id": "AU-TOAN",
        },
        action={
            "operation": "MERGE",
        },
    )

    rule_registry.register(
        merge_rule
    )

    rules = rule_registry.find(
        data_type_id="ACADEMIC_UNIT",
        context="SUBJECT_SUMMARY",
        rule_type="COMPOSITION",
    )

    assert len(rules) == 1

    assert (
        rules[0].action[
            "operation"
        ]
        == "MERGE"
    )

    print(
        "3. Rule Resolution: PASS"
    )

    # --------------------------------------------------------
    # 4. Processor Router
    # --------------------------------------------------------

    processor_router = (
        ProcessorRouter()
    )

    processor = (
        AcademicUnitComposeProcessor()
    )

    processor_router.register(
        processor
    )

    resolved_processor = (
        processor_router.resolve(
            data_type_id="ACADEMIC_UNIT",
            capability="COMPOSE",
        )
    )

    processed_data = (
        resolved_processor.process(
            source_data,
            context={
                "rule_id": (
                    rules[0].rule_id
                ),
                "operation": (
                    rules[0].action[
                        "operation"
                    ]
                ),
            },
        )
    )

    assert (
        processed_data[
            "processed_by"
        ]
        == "PROC-AU-COMPOSE"
    )

    print(
        "4. Processor Routing: PASS"
    )

    # --------------------------------------------------------
    # 5. Mapping Registry
    # --------------------------------------------------------

    mapping_registry = (
        MappingRegistry()
    )

    mapping = Mapping(
        mapping_id="MAP-AU-CURR-001",
        source_data_type=(
            "ACADEMIC_UNIT"
        ),
        source_id="AU-DAI-SO",
        target_data_type="CURRICULUM",
        target_id="CURR-001",
        mapping_type=(
            "CURRICULUM_MEMBERSHIP"
        ),
        priority=10,
    )

    mapping_registry.register(
        mapping
    )

    mappings = (
        mapping_registry.find_from(
            source_data_type=(
                "ACADEMIC_UNIT"
            ),
            source_id="AU-DAI-SO",
            mapping_type=(
                "CURRICULUM_MEMBERSHIP"
            ),
        )
    )

    assert len(mappings) == 1

    assert (
        mappings[0].target_id
        == "CURR-001"
    )

    print(
        "5. Mapping: PASS"
    )

    # --------------------------------------------------------
    # 6. Governance
    # --------------------------------------------------------

    governance_policy = (
        GovernancePolicy(
            update_policy=(
                UpdatePolicy.CONTROLLED
            ),
            retention_policy=(
                RetentionPolicy.ACTIVE_FIRST
            ),
            publish_required=False,
            allow_overwrite_before_publish=True,
            allow_hard_delete=False,
        )
    )

    assert (
        governance_policy
        .should_use_in_engine(
            LifecycleStatus.ACTIVE
        )
    )

    assert not (
        governance_policy
        .should_use_in_engine(
            LifecycleStatus.ARCHIVED
        )
    )

    print(
        "6. Governance: PASS"
    )

    # --------------------------------------------------------
    # 7. Output Router
    # --------------------------------------------------------

    output_router = (
        OutputRouter()
    )

    output_adapter = (
        Base44OutputAdapter()
    )

    output_router.register(
        output_adapter
    )

    rendered = (
        output_router
        .resolve(
            "BASE44"
        )
        .render(
            processed_data,
            context={
                "mapping_count": (
                    len(mappings)
                ),
            },
        )
    )

    assert (
        rendered[
            "output_type"
        ]
        == "BASE44"
    )

    assert (
        rendered[
            "payload"
        ][
            "academic_unit_id"
        ]
        == "AU-DAI-SO"
    )

    print(
        "7. Output Routing: PASS"
    )

    # --------------------------------------------------------
    # 8. P4 check
    # --------------------------------------------------------

    assert (
        mapping.source_id
        == source_data[
            "academic_unit_id"
        ]
    )

    assert not hasattr(
        mapping,
        "source_content",
    )

    print(
        "8. P4 Single Source of Truth: PASS"
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print()
    print("=" * 76)

    print(
        "RESULT: "
        "PASS - CORE V2 END-TO-END VERIFIED"
    )

    print("=" * 76)


if __name__ == "__main__":
    main()