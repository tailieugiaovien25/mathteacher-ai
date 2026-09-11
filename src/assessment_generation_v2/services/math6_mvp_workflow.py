"""Credential-free vertical slice for a governed Mathematics 6 exam workflow.

The workflow deliberately uses in-memory state.  It proves the application
sequence without touching Supabase or production data:

question draft/import -> question review/lock -> blueprint review -> exam
review -> immutable publication snapshot -> locked variant -> ZIP export.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
from itertools import combinations
from json import dumps, loads
from typing import Iterable, Mapping
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


DRAFT = "DRAFT"
PENDING_REVIEW = "PENDING_REVIEW"
APPROVED = "APPROVED"
REVISION_REQUIRED = "REVISION_REQUIRED"
PUBLISHED = "PUBLISHED"
ADMIN = "ADMIN"


class Math6MvpWorkflowError(RuntimeError):
    """Raised when a workflow transition or invariant is invalid."""


def _text(value: object, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise Math6MvpWorkflowError(f"{field_name} must not be blank")
    return normalized


def _score(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise Math6MvpWorkflowError("score must be numeric") from error
    if result <= 0:
        raise Math6MvpWorkflowError("score must be positive")
    return result


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise Math6MvpWorkflowError(
            f"{field_name} must be a positive integer"
        )
    try:
        numeric = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise Math6MvpWorkflowError(
            f"{field_name} must be a positive integer"
        ) from error
    if numeric != numeric.to_integral_value() or numeric <= 0:
        raise Math6MvpWorkflowError(
            f"{field_name} must be a positive integer"
        )
    return int(numeric)


def _admin(role: str) -> None:
    if str(role).strip().upper() != ADMIN:
        raise PermissionError("this transition requires ADMIN")


def _json_bytes(value: object) -> bytes:
    return dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class Math6AssessmentConfig:
    config_code: str
    title: str
    academic_year: str
    semester: str
    test_type: str
    duration_minutes: int
    total_score: Decimal
    variant_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_code",
            _text(self.config_code, "config_code").upper(),
        )
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(
            self,
            "academic_year",
            _text(self.academic_year, "academic_year"),
        )
        object.__setattr__(
            self,
            "semester",
            _text(self.semester, "semester").upper(),
        )
        object.__setattr__(
            self,
            "test_type",
            _text(self.test_type, "test_type").upper(),
        )
        object.__setattr__(
            self,
            "duration_minutes",
            _positive_int(self.duration_minutes, "duration_minutes"),
        )
        object.__setattr__(
            self,
            "total_score",
            _score(self.total_score),
        )
        object.__setattr__(
            self,
            "variant_count",
            _positive_int(self.variant_count, "variant_count"),
        )


@dataclass(frozen=True, slots=True)
class Math6Question:
    question_code: str
    stem: str
    answer: str
    score: Decimal
    topic_code: str
    cognitive_level: str
    review_status: str = DRAFT
    locked: bool = False
    review_note: str = ""


@dataclass(frozen=True, slots=True)
class Math6Blueprint:
    blueprint_code: str
    title: str
    config_code: str
    question_count: int
    total_score: Decimal
    topic_codes: tuple[str, ...]
    review_status: str = DRAFT
    locked: bool = False
    review_note: str = ""


@dataclass(frozen=True, slots=True)
class Math6Exam:
    exam_code: str
    title: str
    blueprint_code: str
    question_codes: tuple[str, ...]
    review_status: str = DRAFT
    review_note: str = ""


@dataclass(frozen=True, slots=True)
class Math6PublishedPackage:
    exam_code: str
    variant_code: str
    snapshot_json: str
    snapshot_hash: str
    variant_locked: bool

    def snapshot(self) -> dict[str, object]:
        value = loads(self.snapshot_json)
        if not isinstance(value, dict):
            raise Math6MvpWorkflowError("published snapshot is invalid")
        return value


class InMemoryMath6MvpWorkflow:
    """Small, deterministic workflow used by tests and the local demo."""

    def __init__(self) -> None:
        self._questions: dict[str, Math6Question] = {}
        self._blueprints: dict[str, Math6Blueprint] = {}
        self._exams: dict[str, Math6Exam] = {}
        self._published: dict[str, Math6PublishedPackage] = {}

    @property
    def questions(self) -> tuple[Math6Question, ...]:
        return tuple(self._questions.values())

    @property
    def blueprints(self) -> tuple[Math6Blueprint, ...]:
        return tuple(self._blueprints.values())

    @property
    def exams(self) -> tuple[Math6Exam, ...]:
        return tuple(self._exams.values())

    @property
    def published_packages(self) -> tuple[Math6PublishedPackage, ...]:
        return tuple(self._published.values())

    @property
    def question_review_queue(self) -> tuple[Math6Question, ...]:
        return tuple(
            item for item in self._questions.values()
            if item.review_status == PENDING_REVIEW
        )

    @property
    def blueprint_review_queue(self) -> tuple[Math6Blueprint, ...]:
        return tuple(
            item for item in self._blueprints.values()
            if item.review_status == PENDING_REVIEW
        )

    @property
    def exam_review_queue(self) -> tuple[Math6Exam, ...]:
        return tuple(
            item for item in self._exams.values()
            if item.review_status == PENDING_REVIEW
        )

    def create_question(
        self,
        *,
        question_code: str,
        stem: str,
        answer: str,
        score: object,
        topic_code: str,
        cognitive_level: str,
    ) -> Math6Question:
        code = _text(question_code, "question_code").upper()
        if code in self._questions:
            raise Math6MvpWorkflowError(f"question already exists: {code}")
        question = Math6Question(
            question_code=code,
            stem=_text(stem, "stem"),
            answer=_text(answer, "answer"),
            score=_score(score),
            topic_code=_text(topic_code, "topic_code").upper(),
            cognitive_level=_text(
                cognitive_level, "cognitive_level"
            ).upper(),
        )
        self._questions[code] = question
        return question

    def import_questions(
        self, rows: Iterable[Mapping[str, object]]
    ) -> tuple[Math6Question, ...]:
        prepared = tuple(dict(row) for row in rows)
        codes = tuple(
            _text(row.get("question_code"), "question_code").upper()
            for row in prepared
        )
        if len(set(codes)) != len(codes):
            raise Math6MvpWorkflowError("import contains duplicate codes")
        conflicts = tuple(code for code in codes if code in self._questions)
        if conflicts:
            raise Math6MvpWorkflowError(
                "questions already exist: " + ", ".join(conflicts)
            )
        # Validate the complete batch before mutating state.
        validated = tuple(
            Math6Question(
                question_code=code,
                stem=_text(row.get("stem"), "stem"),
                answer=_text(row.get("answer"), "answer"),
                score=_score(row.get("score")),
                topic_code=_text(
                    row.get("topic_code"), "topic_code"
                ).upper(),
                cognitive_level=_text(
                    row.get("cognitive_level"), "cognitive_level"
                ).upper(),
            )
            for code, row in zip(codes, prepared)
        )
        for question in validated:
            self._questions[question.question_code] = question
        return validated

    def edit_question(
        self, question_code: str, **changes: object
    ) -> Math6Question:
        question = self._question(question_code)
        if question.locked or question.review_status not in {
            DRAFT,
            REVISION_REQUIRED,
        }:
            raise Math6MvpWorkflowError(
                "only an editable question may be changed"
            )
        allowed = {
            "stem",
            "answer",
            "score",
            "topic_code",
            "cognitive_level",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise Math6MvpWorkflowError(
                "unsupported question fields: " + ", ".join(sorted(unknown))
            )
        values: dict[str, object] = {}
        for name, value in changes.items():
            if name == "score":
                values[name] = _score(value)
            else:
                normalized = _text(value, name)
                values[name] = (
                    normalized.upper()
                    if name in {"topic_code", "cognitive_level"}
                    else normalized
                )
        updated = replace(
            question,
            **values,
            review_status=DRAFT,
            review_note="",
        )
        self._questions[updated.question_code] = updated
        return updated

    def submit_question(self, question_code: str) -> Math6Question:
        question = self._question(question_code)
        if question.locked or question.review_status not in {
            DRAFT,
            REVISION_REQUIRED,
        }:
            raise Math6MvpWorkflowError("question cannot be submitted")
        updated = replace(question, review_status=PENDING_REVIEW)
        self._questions[updated.question_code] = updated
        return updated

    def review_question(
        self,
        question_code: str,
        *,
        role: str,
        approve: bool,
        note: str = "",
    ) -> Math6Question:
        _admin(role)
        question = self._question(question_code)
        if question.review_status != PENDING_REVIEW:
            raise Math6MvpWorkflowError("question is not pending review")
        if not approve and not str(note).strip():
            raise Math6MvpWorkflowError("revision note is required")
        updated = replace(
            question,
            review_status=APPROVED if approve else REVISION_REQUIRED,
            review_note=str(note).strip(),
        )
        self._questions[updated.question_code] = updated
        return updated

    def lock_question(
        self, question_code: str, *, role: str
    ) -> Math6Question:
        _admin(role)
        question = self._question(question_code)
        if question.review_status != APPROVED:
            raise Math6MvpWorkflowError("only an approved question can lock")
        updated = replace(question, locked=True)
        self._questions[updated.question_code] = updated
        return updated

    def create_blueprint(
        self,
        *,
        blueprint_code: str,
        title: str,
        assessment_config: Math6AssessmentConfig,
        question_count: int,
        total_score: object,
        topic_codes: Iterable[str],
    ) -> Math6Blueprint:
        if not isinstance(assessment_config, Math6AssessmentConfig):
            raise Math6MvpWorkflowError("assessment_config is required")
        normalized_total_score = _score(total_score)
        if normalized_total_score != assessment_config.total_score:
            raise Math6MvpWorkflowError(
                "blueprint total_score must match assessment config"
            )
        code = _text(blueprint_code, "blueprint_code").upper()
        if code in self._blueprints:
            raise Math6MvpWorkflowError(f"blueprint already exists: {code}")
        if isinstance(question_count, bool) or int(question_count) < 1:
            raise Math6MvpWorkflowError("question_count must be positive")
        topics = tuple(
            dict.fromkeys(
                _text(value, "topic_code").upper()
                for value in topic_codes
            )
        )
        if not topics:
            raise Math6MvpWorkflowError("topic_codes must not be empty")
        blueprint = Math6Blueprint(
            blueprint_code=code,
            title=_text(title, "title"),
            config_code=assessment_config.config_code,
            question_count=int(question_count),
            total_score=normalized_total_score,
            topic_codes=topics,
        )
        self._blueprints[code] = blueprint
        return blueprint

    def submit_blueprint(self, blueprint_code: str) -> Math6Blueprint:
        blueprint = self._blueprint(blueprint_code)
        if blueprint.locked or blueprint.review_status not in {
            DRAFT,
            REVISION_REQUIRED,
        }:
            raise Math6MvpWorkflowError("blueprint cannot be submitted")
        updated = replace(blueprint, review_status=PENDING_REVIEW)
        self._blueprints[updated.blueprint_code] = updated
        return updated

    def review_blueprint(
        self,
        blueprint_code: str,
        *,
        role: str,
        approve: bool,
        note: str = "",
    ) -> Math6Blueprint:
        _admin(role)
        blueprint = self._blueprint(blueprint_code)
        if blueprint.review_status != PENDING_REVIEW:
            raise Math6MvpWorkflowError("blueprint is not pending review")
        if not approve and not str(note).strip():
            raise Math6MvpWorkflowError("revision note is required")
        updated = replace(
            blueprint,
            review_status=APPROVED if approve else REVISION_REQUIRED,
            locked=bool(approve),
            review_note=str(note).strip(),
        )
        self._blueprints[updated.blueprint_code] = updated
        return updated

    def generate_exam(
        self,
        *,
        exam_code: str,
        title: str,
        blueprint_code: str,
    ) -> Math6Exam:
        code = _text(exam_code, "exam_code").upper()
        if code in self._exams:
            raise Math6MvpWorkflowError(f"exam already exists: {code}")
        blueprint = self._blueprint(blueprint_code)
        if blueprint.review_status != APPROVED or not blueprint.locked:
            raise Math6MvpWorkflowError(
                "exam requires an approved locked blueprint"
            )
        candidates = tuple(
            sorted(
                (
                    question for question in self._questions.values()
                    if question.review_status == APPROVED
                    and question.locked
                    and question.topic_code in blueprint.topic_codes
                ),
                key=lambda question: question.question_code,
            )
        )
        selected = next(
            (
                group for group in combinations(
                    candidates, blueprint.question_count
                )
                if sum(
                    (item.score for item in group), Decimal("0")
                ) == blueprint.total_score
            ),
            None,
        )
        if selected is None:
            raise Math6MvpWorkflowError(
                "locked question bank cannot satisfy blueprint count/score"
            )
        exam = Math6Exam(
            exam_code=code,
            title=_text(title, "title"),
            blueprint_code=blueprint.blueprint_code,
            question_codes=tuple(
                question.question_code for question in selected
            ),
        )
        self._exams[code] = exam
        return exam

    def submit_exam(self, exam_code: str) -> Math6Exam:
        exam = self._exam(exam_code)
        if exam.review_status not in {DRAFT, REVISION_REQUIRED}:
            raise Math6MvpWorkflowError("exam cannot be submitted")
        updated = replace(exam, review_status=PENDING_REVIEW)
        self._exams[updated.exam_code] = updated
        return updated

    def review_exam(
        self,
        exam_code: str,
        *,
        role: str,
        approve: bool,
        note: str = "",
    ) -> Math6Exam:
        _admin(role)
        exam = self._exam(exam_code)
        if exam.review_status != PENDING_REVIEW:
            raise Math6MvpWorkflowError("exam is not pending review")
        if not approve and not str(note).strip():
            raise Math6MvpWorkflowError("revision note is required")
        updated = replace(
            exam,
            review_status=APPROVED if approve else REVISION_REQUIRED,
            review_note=str(note).strip(),
        )
        self._exams[updated.exam_code] = updated
        return updated

    def publish_exam(
        self,
        exam_code: str,
        *,
        role: str,
        variant_code: str = "101",
    ) -> Math6PublishedPackage:
        _admin(role)
        exam = self._exam(exam_code)
        if exam.review_status != APPROVED:
            raise Math6MvpWorkflowError("only an approved exam can publish")
        if exam.exam_code in self._published:
            return self._published[exam.exam_code]
        blueprint = self._blueprint(exam.blueprint_code)
        questions = tuple(
            self._question(code) for code in exam.question_codes
        )
        snapshot = {
            "schema_version": 1,
            "subject": "Toán",
            "grade_level": 6,
            "exam": {
                "exam_code": exam.exam_code,
                "title": exam.title,
                "review_status": APPROVED,
            },
            "blueprint": {
                "blueprint_code": blueprint.blueprint_code,
                "title": blueprint.title,
                "config_code": blueprint.config_code,
                "question_count": blueprint.question_count,
                "total_score": str(blueprint.total_score),
                "topic_codes": list(blueprint.topic_codes),
            },
            "questions": [
                {
                    "question_code": item.question_code,
                    "stem": item.stem,
                    "answer": item.answer,
                    "score": str(item.score),
                    "topic_code": item.topic_code,
                    "cognitive_level": item.cognitive_level,
                }
                for item in questions
            ],
            "variant": {
                "variant_code": _text(
                    variant_code, "variant_code"
                ).upper(),
                "status": "LOCKED",
            },
        }
        snapshot_content = _json_bytes(snapshot)
        package = Math6PublishedPackage(
            exam_code=exam.exam_code,
            variant_code=str(snapshot["variant"]["variant_code"]),
            snapshot_json=snapshot_content.decode("utf-8"),
            snapshot_hash=sha256(snapshot_content).hexdigest(),
            variant_locked=True,
        )
        self._published[exam.exam_code] = package
        self._exams[exam.exam_code] = replace(
            exam, review_status=PUBLISHED
        )
        return package

    def export_zip(self, exam_code: str) -> bytes:
        code = _text(exam_code, "exam_code").upper()
        package = self._published.get(code)
        if package is None or not package.variant_locked:
            raise Math6MvpWorkflowError(
                "export requires a published snapshot and locked variant"
            )
        snapshot = package.snapshot()
        content = _json_bytes(snapshot)
        if sha256(content).hexdigest() != package.snapshot_hash:
            raise Math6MvpWorkflowError("snapshot integrity check failed")
        questions = list(snapshot["questions"])
        exam_lines = [
            str(snapshot["exam"]["title"]),
            f"Mã đề: {package.variant_code}",
            "",
        ]
        answer_lines = ["ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM", ""]
        for index, question in enumerate(questions, start=1):
            exam_lines.append(f"Câu {index}. {question['stem']}")
            exam_lines.append(f"({question['score']} điểm)")
            exam_lines.append("")
            answer_lines.append(
                f"Câu {index}: {question['answer']} "
                f"({question['score']} điểm)"
            )
        files = {
            "de-kiem-tra.txt": "\n".join(exam_lines).encode("utf-8"),
            "dap-an-huong-dan-cham.txt": "\n".join(
                answer_lines
            ).encode("utf-8"),
            "ma-tran-ban-dac-ta.json": _json_bytes(
                snapshot["blueprint"]
            ),
            "snapshot.json": content,
        }
        manifest = {
            "schema_version": 1,
            "exam_code": code,
            "variant_code": package.variant_code,
            "variant_status": "LOCKED",
            "snapshot_hash": package.snapshot_hash,
            "files": {
                name: sha256(value).hexdigest()
                for name, value in files.items()
            },
        }
        files["manifest.json"] = dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for name in sorted(files):
                info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, files[name])
        return output.getvalue()

    def _question(self, code: str) -> Math6Question:
        normalized = _text(code, "question_code").upper()
        try:
            return self._questions[normalized]
        except KeyError as error:
            raise Math6MvpWorkflowError(
                f"unknown question: {normalized}"
            ) from error

    def _blueprint(self, code: str) -> Math6Blueprint:
        normalized = _text(code, "blueprint_code").upper()
        try:
            return self._blueprints[normalized]
        except KeyError as error:
            raise Math6MvpWorkflowError(
                f"unknown blueprint: {normalized}"
            ) from error

    def _exam(self, code: str) -> Math6Exam:
        normalized = _text(code, "exam_code").upper()
        try:
            return self._exams[normalized]
        except KeyError as error:
            raise Math6MvpWorkflowError(
                f"unknown exam: {normalized}"
            ) from error
