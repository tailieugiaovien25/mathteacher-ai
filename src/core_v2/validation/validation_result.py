from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity
    field: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...] = field(
        default_factory=tuple
    )

    @property
    def has_errors(self) -> bool:
        return any(
            issue.severity == ValidationSeverity.ERROR
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )

    @property
    def is_valid(self) -> bool:
        return not self.has_errors

    @classmethod
    def pass_result(cls) -> "ValidationResult":
        return cls()

    @classmethod
    def from_issues(
        cls,
        *issues: ValidationIssue,
    ) -> "ValidationResult":
        return cls(
            issues=tuple(issues)
        )