from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataIndependenceViolation:
    file_path: str
    token: str
    line_number: int
    line_text: str


class DataIndependenceGuard:
    """
    Continuous architecture guard for stable system boundaries.

    Educational data may change while stable Core/Planning/
    Orchestration code must remain independent from:
    - physical storage;
    - concrete authority datasets;
    - concrete textbook editions;
    - fixed educational values.
    """

    DEFAULT_FORBIDDEN_TOKENS = (
        "openpyxl",
        "load_workbook",
        ".xlsm",
        ".xlsx",
        "lbg-tuyen",
        "data/input/",
        "data\\input\\",
        "textbook_lessons.json",
        "learning_requirements.json",
        "kết nối tri thức",
        "kntt",
    )

    DEFAULT_PROTECTED_ROOTS = (
        "curriculum_v2/providers",
        "curriculum_v2/authority",
        "educational_planning_v2/services",
        "educational_planning_v2/builders",
        "educational_planning_v2/models",
        "lesson_planning_v2",
        "orchestrator_v2",
    )

    def __init__(
        self,
        *,
        source_root: str | Path,
        protected_roots: tuple[str, ...] | None = None,
        forbidden_tokens: tuple[str, ...] | None = None,
    ) -> None:
        self._source_root = Path(
            source_root
        ).resolve()

        self._protected_roots = (
            protected_roots
            if protected_roots is not None
            else self.DEFAULT_PROTECTED_ROOTS
        )

        self._forbidden_tokens = (
            forbidden_tokens
            if forbidden_tokens is not None
            else self.DEFAULT_FORBIDDEN_TOKENS
        )

        if not isinstance(
            self._protected_roots,
            tuple,
        ):
            raise TypeError(
                "protected_roots must be a tuple"
            )

        if not isinstance(
            self._forbidden_tokens,
            tuple,
        ):
            raise TypeError(
                "forbidden_tokens must be a tuple"
            )

    def scan(
        self,
    ) -> tuple[
        DataIndependenceViolation,
        ...,
    ]:
        violations = []

        for relative_root in self._protected_roots:
            root = (
                self._source_root
                / relative_root
            )

            if not root.exists():
                continue

            for file_path in root.rglob(
                "*.py"
            ):
                if self._should_skip(
                    file_path
                ):
                    continue

                violations.extend(
                    self._scan_file(
                        file_path
                    )
                )

        violations.sort(
            key=lambda item: (
                item.file_path,
                item.line_number,
                item.token,
            )
        )

        return tuple(
            violations
        )

    def assert_clean(
        self,
    ) -> None:
        violations = self.scan()

        if not violations:
            return

        details = "\n".join(
            (
                f"{item.file_path}:"
                f"{item.line_number}: "
                f"{item.token!r} -> "
                f"{item.line_text.strip()}"
            )
            for item in violations
        )

        raise AssertionError(
            "Data Independence violations detected:\n"
            + details
        )

    def _scan_file(
        self,
        file_path: Path,
    ) -> list[
        DataIndependenceViolation
    ]:
        text = file_path.read_text(
            encoding="utf-8-sig",
        )

        violations = []

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            normalized = line.lower()

            for token in self._forbidden_tokens:
                if token.lower() in normalized:
                    violations.append(
                        DataIndependenceViolation(
                            file_path=str(
                                file_path.relative_to(
                                    self._source_root
                                )
                            ),
                            token=token,
                            line_number=line_number,
                            line_text=line,
                        )
                    )

        return violations

    @staticmethod
    def _should_skip(
        file_path: Path,
    ) -> bool:
        parts = {
            part.lower()
            for part in file_path.parts
        }

        if "__pycache__" in parts:
            return True

        if "tests" in parts:
            return True

        return False
