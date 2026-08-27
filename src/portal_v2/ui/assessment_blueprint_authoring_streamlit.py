"""Teacher workspace for canonical assessment blueprint authoring."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from uuid import UUID

from assessment_generation_v2.adapters import (
    SupabaseAssessmentCurriculumCatalog,
    SupabaseBlueprintRequirementLinkGateway,
)
from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumQueryService,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
    BlueprintRequirementLinkService,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelectionService,
)


class AssessmentBlueprintAuthoringError(RuntimeError):
    """Raised when the authoring catalog violates its UI contract."""


@dataclass(frozen=True, slots=True)
class AssessmentProfileOption:
    profile_code: str
    profile_name: str
    program_code: str
    subject_code: str
    education_level: str
    grade_min: int
    grade_max: int
    total_score: Decimal
    duration_minutes: int

    @property
    def label(self) -> str:
        return (
            f"{self.profile_name} · {self.subject_code} · "
            f"Lớp {self.grade_min}–{self.grade_max}"
        )


@dataclass(frozen=True, slots=True)
class EditableBlueprintOption:
    blueprint_version_id: str
    blueprint_code: str
    blueprint_name: str
    profile_code: str
    subject_code: str
    grade_level: int
    review_status: str
    version_number: int
    total_score: Decimal

    @property
    def label(self) -> str:
        return (
            f"{self.blueprint_code} — {self.blueprint_name} "
            f"(Lớp {self.grade_level}, v{self.version_number})"
        )


@dataclass(frozen=True, slots=True)
class AssessmentProfileSectionOption:
    section_code: str
    section_name: str
    question_type_code: str
    sequence_number: int
    question_count: int
    response_count: int
    section_score: Decimal

    @property
    def label(self) -> str:
        return f"{self.section_code} — {self.section_name}"


@dataclass(frozen=True, slots=True)
class CognitiveLevelOption:
    cognitive_level_code: str
    cognitive_level_name: str
    sequence_number: int

    @property
    def label(self) -> str:
        return (
            f"{self.cognitive_level_code} — "
            f"{self.cognitive_level_name}"
        )


@dataclass(frozen=True, slots=True)
class ProfileLevelAllocation:
    cognitive_level_code: str
    target_score: Decimal
    target_percentage: Decimal


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object) -> list[dict[str, Any]]:
    data = _data(response)
    if data is None:
        return []
    if isinstance(data, Mapping):
        return [dict(data)]
    if not isinstance(data, list):
        raise AssessmentBlueprintAuthoringError(
            "Supabase không trả về danh sách hợp lệ."
        )
    if any(not isinstance(row, Mapping) for row in data):
        raise AssessmentBlueprintAuthoringError(
            "Danh sách chứa bản ghi không hợp lệ."
        )
    return [dict(row) for row in data]


def _text(value: object, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise AssessmentBlueprintAuthoringError(
            f"Thiếu trường {field_name}."
        )
    return normalized


def _relation(value: object, field_name: str) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentBlueprintAuthoringError(
                f"Quan hệ {field_name} phải có đúng một bản ghi."
            )
        value = value[0]
    if not isinstance(value, Mapping):
        raise AssessmentBlueprintAuthoringError(
            f"Quan hệ {field_name} không hợp lệ."
        )
    return dict(value)


class SupabaseAssessmentBlueprintAuthoringCatalog:
    """Read teacher drafts and create drafts only through governed RPCs."""

    CREATE_DRAFT_RPC = "create_assessment_blueprint_draft"
    REPLACE_CELLS_RPC = "replace_assessment_blueprint_cells"
    READY_RPC = "assessment_blueprint_ready_for_review"
    SUBMIT_RPC = "submit_assessment_blueprint_for_review"

    def __init__(self, *, client: Any, user_id: str) -> None:
        self._client = client
        try:
            self._user_id = str(UUID(str(user_id).strip()))
        except ValueError as error:
            raise AssessmentBlueprintAuthoringError(
                "Tài khoản giáo viên không hợp lệ."
            ) from error

    def list_active_profiles(self) -> tuple[AssessmentProfileOption, ...]:
        response = (
            self._client.table("assessment_profiles")
            .select(
                "profile_code,profile_name,program_code,subject_code,"
                "education_level,grade_min,grade_max,total_score,"
                "duration_minutes,status"
            )
            .eq("status", "ACTIVE")
            .order("subject_code")
            .order("profile_code")
            .execute()
        )
        return tuple(
            AssessmentProfileOption(
                profile_code=_text(row.get("profile_code"), "profile_code"),
                profile_name=_text(row.get("profile_name"), "profile_name"),
                program_code=_text(row.get("program_code"), "program_code"),
                subject_code=_text(row.get("subject_code"), "subject_code"),
                education_level=_text(
                    row.get("education_level"),
                    "education_level",
                ),
                grade_min=int(row.get("grade_min", 0)),
                grade_max=int(row.get("grade_max", 0)),
                total_score=Decimal(str(row.get("total_score", 0))),
                duration_minutes=int(row.get("duration_minutes", 0)),
            )
            for row in _rows(response)
        )

    def list_editable_blueprints(
        self,
    ) -> tuple[EditableBlueprintOption, ...]:
        response = (
            self._client.table("assessment_blueprint_versions")
            .select(
                "blueprint_version_id,version_number,profile_code,"
                "blueprint_name,total_score,review_status,locked_at,"
                "assessment_blueprints!inner(blueprint_code,subject_code,"
                "grade_level,owner_user_id,lifecycle_status)"
            )
            .eq("assessment_blueprints.owner_user_id", self._user_id)
            .in_(
                "review_status",
                ("DRAFT", "AI_PROPOSED", "REVISION_REQUIRED"),
            )
            .is_("locked_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        result: list[EditableBlueprintOption] = []
        for row in _rows(response):
            blueprint = _relation(
                row.get("assessment_blueprints"),
                "assessment_blueprints",
            )
            if _text(blueprint.get("owner_user_id"), "owner_user_id") != (
                self._user_id
            ):
                raise PermissionError(
                    "Danh mục trả về ma trận của tài khoản khác."
                )
            result.append(
                EditableBlueprintOption(
                    blueprint_version_id=_text(
                        row.get("blueprint_version_id"),
                        "blueprint_version_id",
                    ),
                    blueprint_code=_text(
                        blueprint.get("blueprint_code"),
                        "blueprint_code",
                    ),
                    blueprint_name=_text(
                        row.get("blueprint_name"),
                        "blueprint_name",
                    ),
                    profile_code=_text(
                        row.get("profile_code"),
                        "profile_code",
                    ),
                    subject_code=_text(
                        blueprint.get("subject_code"),
                        "subject_code",
                    ),
                    grade_level=int(blueprint.get("grade_level", 0)),
                    review_status=_text(
                        row.get("review_status"),
                        "review_status",
                    ),
                    version_number=int(row.get("version_number", 0)),
                    total_score=Decimal(str(row.get("total_score", 0))),
                )
            )
        return tuple(result)

    def create_draft(
        self,
        *,
        profile: AssessmentProfileOption,
        grade_level: int,
        blueprint_code: str,
        blueprint_name: str,
        academic_year: str,
        semester_number: int | None,
    ) -> str:
        response = self._client.rpc(
            self.CREATE_DRAFT_RPC,
            {
                "target_profile_code": profile.profile_code,
                "target_grade_level": int(grade_level),
                "target_blueprint_code": blueprint_code,
                "target_blueprint_name": blueprint_name,
                "target_academic_year": academic_year,
                "target_semester_number": semester_number,
            },
        ).execute()
        rows = _rows(response)
        if len(rows) != 1:
            raise AssessmentBlueprintAuthoringError(
                "RPC tạo ma trận phải trả về đúng một phiên bản."
            )
        return _text(
            rows[0].get("blueprint_version_id"),
            "blueprint_version_id",
        )

    def list_requirement_links(
        self,
        *,
        blueprint_version_id: str,
    ) -> tuple[dict[str, Any], ...]:
        response = (
            self._client.table("assessment_blueprint_requirement_links")
            .select(
                "requirement_code,coverage_role,target_question_count,"
                "target_score,sequence_number,specification_note"
            )
            .eq("blueprint_version_id", blueprint_version_id)
            .order("sequence_number")
            .order("requirement_code")
            .execute()
        )
        return tuple(_rows(response))

    def list_profile_sections(
        self,
        *,
        profile_code: str,
    ) -> tuple[AssessmentProfileSectionOption, ...]:
        response = (
            self._client.table("assessment_profile_sections")
            .select(
                "section_code,section_name,question_type_code,"
                "sequence_number,question_count,response_count,"
                "section_score"
            )
            .eq("profile_code", profile_code)
            .order("sequence_number")
            .execute()
        )
        return tuple(
            AssessmentProfileSectionOption(
                section_code=_text(
                    row.get("section_code"), "section_code"
                ),
                section_name=_text(
                    row.get("section_name"), "section_name"
                ),
                question_type_code=_text(
                    row.get("question_type_code"),
                    "question_type_code",
                ),
                sequence_number=int(row.get("sequence_number", 0)),
                question_count=int(row.get("question_count", 0)),
                response_count=int(row.get("response_count", 0)),
                section_score=Decimal(
                    str(row.get("section_score", 0))
                ),
            )
            for row in _rows(response)
        )

    def list_cognitive_levels(
        self,
    ) -> tuple[CognitiveLevelOption, ...]:
        response = (
            self._client.table("assessment_cognitive_levels")
            .select(
                "cognitive_level_code,cognitive_level_name,"
                "sequence_number"
            )
            .eq("status", "ACTIVE")
            .order("sequence_number")
            .execute()
        )
        return tuple(
            CognitiveLevelOption(
                cognitive_level_code=_text(
                    row.get("cognitive_level_code"),
                    "cognitive_level_code",
                ),
                cognitive_level_name=_text(
                    row.get("cognitive_level_name"),
                    "cognitive_level_name",
                ),
                sequence_number=int(row.get("sequence_number", 0)),
            )
            for row in _rows(response)
        )

    def list_profile_level_allocations(
        self,
        *,
        profile_code: str,
    ) -> tuple[ProfileLevelAllocation, ...]:
        response = (
            self._client.table("assessment_profile_level_allocations")
            .select(
                "cognitive_level_code,target_score,target_percentage"
            )
            .eq("profile_code", profile_code)
            .order("cognitive_level_code")
            .execute()
        )
        return tuple(
            ProfileLevelAllocation(
                cognitive_level_code=_text(
                    row.get("cognitive_level_code"),
                    "cognitive_level_code",
                ),
                target_score=Decimal(str(row.get("target_score", 0))),
                target_percentage=Decimal(
                    str(row.get("target_percentage", 0))
                ),
            )
            for row in _rows(response)
        )

    def list_cells(
        self,
        *,
        blueprint_version_id: str,
    ) -> tuple[dict[str, Any], ...]:
        response = (
            self._client.table("assessment_blueprint_cells")
            .select(
                "section_code,topic_code,cognitive_level_code,"
                "question_type_code,question_count,response_count,"
                "target_score,sequence_number,specification_note"
            )
            .eq("blueprint_version_id", blueprint_version_id)
            .order("sequence_number")
            .execute()
        )
        return tuple(_rows(response))

    def replace_cells(
        self,
        *,
        blueprint_version_id: str,
        cells: Sequence[Mapping[str, object]],
    ) -> tuple[dict[str, Any], ...]:
        response = self._client.rpc(
            self.REPLACE_CELLS_RPC,
            {
                "target_blueprint_version_id": blueprint_version_id,
                "target_cells": [dict(cell) for cell in cells],
            },
        ).execute()
        return tuple(_rows(response))

    def ready_for_review(
        self,
        *,
        blueprint_version_id: str,
    ) -> bool:
        response = self._client.rpc(
            self.READY_RPC,
            {
                "target_blueprint_version_id": blueprint_version_id,
            },
        ).execute()
        data = _data(response)
        if isinstance(data, list):
            if len(data) != 1:
                return False
            data = data[0]
        if isinstance(data, Mapping):
            data = next(iter(data.values()), False)
        return bool(data)

    def submit_for_review(
        self,
        *,
        blueprint_version_id: str,
    ) -> None:
        self._client.rpc(
            self.SUBMIT_RPC,
            {
                "target_blueprint_version_id": blueprint_version_id,
            },
        ).execute()


def _assignment_rows(
    *,
    requirement_codes: Sequence[str],
    existing_links: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    existing = {
        str(row.get("requirement_code", "")): row
        for row in existing_links
    }
    result = []
    for index, code in enumerate(requirement_codes, start=1):
        row = existing.get(code, {})
        result.append(
            {
                "requirement_code": code,
                "coverage_role": row.get("coverage_role", "PRIMARY"),
                "target_question_count": int(
                    row.get("target_question_count", 1) or 1
                ),
                "target_score": row.get("target_score"),
                "sequence_number": int(
                    row.get("sequence_number", index * 10) or index * 10
                ),
                "specification_note": str(
                    row.get("specification_note") or ""
                ),
            }
        )
    return result


def _build_assignments(
    rows: Sequence[Mapping[str, object]],
) -> tuple[BlueprintRequirementAssignment, ...]:
    assignments = []
    for row in rows:
        raw_score = row.get("target_score")
        try:
            score = (
                None
                if raw_score is None or str(raw_score).strip() == ""
                else Decimal(str(raw_score))
            )
        except InvalidOperation as error:
            raise AssessmentBlueprintAuthoringError(
                "Điểm mục tiêu phải là một số hợp lệ."
            ) from error
        assignments.append(
            BlueprintRequirementAssignment(
                requirement_code=str(row.get("requirement_code", "")),
                coverage_role=str(row.get("coverage_role", "")),
                target_question_count=int(
                    row.get("target_question_count", 0)
                ),
                target_score=score,
                sequence_number=int(row.get("sequence_number", -1)),
                specification_note=str(
                    row.get("specification_note") or ""
                ),
            )
        )
    return tuple(assignments)


def _default_cell_rows(
    *,
    sections: Sequence[AssessmentProfileSectionOption],
    topic_codes: Sequence[str],
    cognitive_levels: Sequence[CognitiveLevelOption],
    level_allocations: Sequence[ProfileLevelAllocation],
    existing_cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if existing_cells:
        return [
            {
                "section_code": str(row.get("section_code", "")),
                "topic_code": str(row.get("topic_code", "")),
                "cognitive_level_code": str(
                    row.get("cognitive_level_code", "")
                ),
                "question_count": int(
                    row.get("question_count", 0) or 0
                ),
                "response_count": int(
                    row.get("response_count", 0) or 0
                ),
                "target_score": float(
                    row.get("target_score", 0) or 0
                ),
                "sequence_number": int(
                    row.get("sequence_number", 0) or 0
                ),
                "specification_note": str(
                    row.get("specification_note") or ""
                ),
            }
            for row in existing_cells
        ]
    if not topic_codes or not cognitive_levels:
        return []
    allocation_by_level = {
        item.cognitive_level_code: item.target_score
        for item in level_allocations
    }
    ordered_targets = [
        [
            level.cognitive_level_code,
            allocation_by_level.get(level.cognitive_level_code, Decimal(0)),
        ]
        for level in cognitive_levels
        if allocation_by_level.get(level.cognitive_level_code, Decimal(0))
        > 0
    ]
    allocated_rows: list[dict[str, object]] = []
    target_index = 0
    allocation_possible = bool(ordered_targets)
    for section_index, section in enumerate(sections):
        remaining_score = section.section_score
        section_part = 0
        while remaining_score > 0 and target_index < len(ordered_targets):
            level_code, level_remaining = ordered_targets[target_index]
            chunk_score = min(remaining_score, level_remaining)
            question_fraction = (
                Decimal(section.question_count)
                * chunk_score
                / section.section_score
            )
            response_fraction = (
                Decimal(section.response_count)
                * chunk_score
                / section.section_score
            )
            if (
                question_fraction != question_fraction.to_integral_value()
                or response_fraction
                != response_fraction.to_integral_value()
            ):
                allocation_possible = False
                break
            allocated_rows.append(
                {
                    "section_code": section.section_code,
                    "topic_code": topic_codes[
                        len(allocated_rows) % len(topic_codes)
                    ],
                    "cognitive_level_code": level_code,
                    "question_count": int(question_fraction),
                    "response_count": int(response_fraction),
                    "target_score": float(chunk_score),
                    "sequence_number": (
                        section.sequence_number + section_part
                    ),
                    "specification_note": "",
                }
            )
            section_part += 1
            remaining_score -= chunk_score
            ordered_targets[target_index][1] -= chunk_score
            if ordered_targets[target_index][1] == 0:
                target_index += 1
        if not allocation_possible or remaining_score != 0:
            allocation_possible = False
            break
    if (
        allocation_possible
        and all(remaining == 0 for _, remaining in ordered_targets)
    ):
        return allocated_rows
    result: list[dict[str, object]] = []
    for index, section in enumerate(sections):
        level = cognitive_levels[index % len(cognitive_levels)]
        result.append(
            {
                "section_code": section.section_code,
                "topic_code": topic_codes[index % len(topic_codes)],
                "cognitive_level_code": level.cognitive_level_code,
                "question_count": section.question_count,
                "response_count": section.response_count,
                "target_score": float(section.section_score),
                "sequence_number": section.sequence_number,
                "specification_note": "",
            }
        )
    return result


def _cell_payload(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    result = []
    for row in rows:
        section_code = str(row.get("section_code", "")).strip()
        topic_code = str(row.get("topic_code", "")).strip()
        cognitive_level_code = str(
            row.get("cognitive_level_code", "")
        ).strip()
        if not section_code or not topic_code or not cognitive_level_code:
            raise AssessmentBlueprintAuthoringError(
                "Mỗi ô ma trận phải có phần đề, chủ đề và mức độ."
            )
        try:
            target_score = Decimal(str(row.get("target_score", 0)))
        except InvalidOperation as error:
            raise AssessmentBlueprintAuthoringError(
                "Điểm của ô ma trận phải là số hợp lệ."
            ) from error
        result.append(
            {
                "section_code": section_code,
                "topic_code": topic_code,
                "cognitive_level_code": cognitive_level_code,
                "question_count": int(row.get("question_count", 0)),
                "response_count": int(row.get("response_count", 0)),
                "target_score": str(target_score),
                "sequence_number": int(row.get("sequence_number", 0)),
                "specification_note": str(
                    row.get("specification_note") or ""
                ).strip(),
            }
        )
    if not result:
        raise AssessmentBlueprintAuthoringError(
            "Ma trận phải có ít nhất một ô phân bổ."
        )
    return tuple(result)


def render_assessment_blueprint_authoring_page(
    *,
    st: Any,
    client: Any,
    user_id: str,
) -> None:
    st.title("Ma trận và bản đặc tả")
    st.caption(
        "Chọn chủ đề và yêu cầu cần đạt từ cơ sở dữ liệu giáo dục "
        "chuẩn; không nhập lại nội dung chương trình bằng tay."
    )
    st.info(
        "Mỗi lần lưu sẽ thay thế nguyên tử toàn bộ phạm vi YCCĐ của "
        "phiên bản ma trận đang chỉnh sửa."
    )

    try:
        catalog = SupabaseAssessmentBlueprintAuthoringCatalog(
            client=client,
            user_id=user_id,
        )
        profiles = catalog.list_active_profiles()
    except Exception as error:
        st.error(f"Không thể tải hồ sơ đánh giá: {error}")
        return

    if not profiles:
        st.warning(
            "Chưa có hồ sơ đánh giá ACTIVE. Quản trị viên cần phê "
            "duyệt và kích hoạt hồ sơ trước khi giáo viên tạo ma trận."
        )
        return

    st.subheader("1. Tạo hoặc chọn bản nháp ma trận")
    profile_by_label = {profile.label: profile for profile in profiles}
    selected_profile_label = st.selectbox(
        "Hồ sơ đánh giá",
        tuple(profile_by_label),
        key="assessment_blueprint_profile",
    )
    profile = profile_by_label[selected_profile_label]
    grade_level = st.selectbox(
        "Khối lớp",
        tuple(range(profile.grade_min, profile.grade_max + 1)),
        key="assessment_blueprint_grade",
    )
    draft_columns = st.columns(2)
    with draft_columns[0]:
        blueprint_code = st.text_input(
            "Mã ma trận",
            placeholder="Ví dụ: TOAN6_GHK1_2026",
            max_chars=140,
        )
        academic_year = st.text_input(
            "Năm học",
            placeholder="2026-2027",
            max_chars=20,
        )
    with draft_columns[1]:
        blueprint_name = st.text_input(
            "Tên ma trận",
            placeholder="Kiểm tra giữa học kỳ I môn Toán 6",
            max_chars=300,
        )
        semester_choice = st.selectbox(
            "Học kỳ",
            ("Không xác định", "Học kỳ I", "Học kỳ II", "Cả năm"),
        )
    semester_number = {
        "Không xác định": None,
        "Học kỳ I": 1,
        "Học kỳ II": 2,
        "Cả năm": 3,
    }[semester_choice]

    if st.button(
        "Tạo/mở bản nháp ma trận",
        type="primary",
        use_container_width=True,
    ):
        try:
            version_id = catalog.create_draft(
                profile=profile,
                grade_level=int(grade_level),
                blueprint_code=blueprint_code,
                blueprint_name=blueprint_name,
                academic_year=academic_year,
                semester_number=semester_number,
            )
        except Exception as error:
            st.error(f"Không thể tạo bản nháp ma trận: {error}")
        else:
            st.session_state[
                "assessment_blueprint_version_id"
            ] = version_id
            st.success("Đã tạo hoặc mở bản nháp ma trận.")
            st.rerun()

    try:
        drafts = catalog.list_editable_blueprints()
    except Exception as error:
        st.error(f"Không thể tải bản nháp ma trận: {error}")
        return
    if not drafts:
        st.info("Chưa có bản nháp ma trận để nhập YCCĐ.")
        return

    draft_by_label = {draft.label: draft for draft in drafts}
    default_version_id = st.session_state.get(
        "assessment_blueprint_version_id"
    )
    labels = tuple(draft_by_label)
    default_index = next(
        (
            index
            for index, label in enumerate(labels)
            if draft_by_label[label].blueprint_version_id
            == default_version_id
        ),
        0,
    )
    draft_label = st.selectbox(
        "Bản nháp đang chỉnh sửa",
        labels,
        index=default_index,
        key="assessment_blueprint_draft",
    )
    draft = draft_by_label[draft_label]
    st.session_state[
        "assessment_blueprint_version_id"
    ] = draft.blueprint_version_id

    curriculum_reader = AssessmentCurriculumQueryService(
        catalog=SupabaseAssessmentCurriculumCatalog(client=client)
    )
    selection_service = CanonicalAssessmentSelectionService(
        curriculum_reader=curriculum_reader
    )
    try:
        curriculum = curriculum_reader.load_grade_curriculum(
            subject_code=draft.subject_code,
            grade_level=draft.grade_level,
        )
    except Exception as error:
        st.error(f"Không thể tải dữ liệu chương trình chuẩn: {error}")
        return

    try:
        existing_links = catalog.list_requirement_links(
            blueprint_version_id=draft.blueprint_version_id
        )
    except Exception as error:
        st.error(f"Không thể tải liên kết YCCĐ hiện có: {error}")
        return

    existing_requirement_codes = {
        str(link.get("requirement_code", ""))
        for link in existing_links
    }
    existing_topic_codes = {
        requirement.topic_code
        for requirement in curriculum.requirements
        if requirement.requirement_code in existing_requirement_codes
    }

    st.subheader("2. Chọn chủ đề và yêu cầu cần đạt")
    topic_by_label = {
        f"{topic.topic_name} [{topic.topic_code}]": topic
        for topic in curriculum.topics
    }
    default_topic_labels = tuple(
        label
        for label, topic in topic_by_label.items()
        if topic.topic_code in existing_topic_codes
    )
    selected_topic_labels = st.multiselect(
        "Chủ đề/nội dung đánh giá",
        tuple(topic_by_label),
        default=default_topic_labels,
        key="assessment_blueprint_topics",
    )
    requested_topic_codes = tuple(
        topic_by_label[label].topic_code
        for label in selected_topic_labels
    )
    include_descendants = st.checkbox(
        "Bao gồm toàn bộ chủ đề con",
        value=True,
        help="Việc mở rộng được thực hiện tường minh và có thể kiểm tra.",
    )
    try:
        selected_topic_codes = (
            selection_service.expand_topic_descendants_explicitly(
                subject_code=draft.subject_code,
                grade_level=draft.grade_level,
                topic_codes=requested_topic_codes,
            )
            if include_descendants
            else requested_topic_codes
        )
    except Exception as error:
        st.error(f"Không thể mở rộng cây chủ đề: {error}")
        return

    selected_topic_set = set(selected_topic_codes)
    available_requirements = tuple(
        requirement
        for requirement in curriculum.requirements
        if requirement.topic_code in selected_topic_set
    )
    requirement_by_label = {
        f"{requirement.requirement_text} [{requirement.requirement_code}]": (
            requirement
        )
        for requirement in available_requirements
    }
    default_requirement_labels = tuple(
        label
        for label, requirement in requirement_by_label.items()
        if requirement.requirement_code in existing_requirement_codes
    )
    selected_requirement_labels = st.multiselect(
        "Yêu cầu cần đạt được đánh giá",
        tuple(requirement_by_label),
        default=default_requirement_labels,
        key="assessment_blueprint_requirements",
    )
    selected_requirement_codes = tuple(
        requirement_by_label[label].requirement_code
        for label in selected_requirement_labels
    )

    st.subheader("3. Phân bổ YCCĐ trong bản đặc tả")
    editor_rows = _assignment_rows(
        requirement_codes=selected_requirement_codes,
        existing_links=existing_links,
    )
    edited_rows = st.data_editor(
        editor_rows,
        use_container_width=True,
        hide_index=True,
        disabled=("requirement_code",),
        key=(
            "assessment_blueprint_assignment_editor_"
            + draft.blueprint_version_id
        ),
    )

    if existing_links:
        with st.expander("Liên kết YCCĐ đã lưu", expanded=False):
            st.dataframe(
                list(existing_links),
                use_container_width=True,
                hide_index=True,
            )

    if st.button(
        "Lưu YCCĐ vào ma trận",
        type="primary",
        use_container_width=True,
        disabled=not selected_requirement_codes,
    ):
        try:
            editing_selection = selection_service.build_editing_selection(
                subject_code=draft.subject_code,
                grade_level=draft.grade_level,
                program_code=curriculum.program.program_code,
                selected_topic_codes=selected_topic_codes,
                selected_requirement_codes=selected_requirement_codes,
            )
            finalized_selection = selection_service.finalize_selection(
                editing_selection
            )
            assignments = _build_assignments(edited_rows)
            saved = BlueprintRequirementLinkService(
                gateway=SupabaseBlueprintRequirementLinkGateway(
                    client=client
                )
            ).replace_from_selection(
                blueprint_version_id=draft.blueprint_version_id,
                selection=finalized_selection,
                assignments=assignments,
            )
        except Exception as error:
            st.error(f"Không thể lưu phạm vi YCCĐ: {error}")
        else:
            st.success(
                f"Đã lưu nguyên tử {len(saved)} YCCĐ vào ma trận."
            )
            st.session_state[
                "assessment_blueprint_last_saved_count"
            ] = len(saved)

    st.subheader("4. Phân bổ ô ma trận")
    st.caption(
        "Có thể thêm nhiều dòng cho cùng một phần đề để chia theo "
        "chủ đề và mức độ. Tổng số câu, số ý và điểm của từng phần "
        "phải khớp hồ sơ đánh giá."
    )
    try:
        sections = catalog.list_profile_sections(
            profile_code=draft.profile_code
        )
        cognitive_levels = catalog.list_cognitive_levels()
        level_allocations = catalog.list_profile_level_allocations(
            profile_code=draft.profile_code
        )
        existing_cells = catalog.list_cells(
            blueprint_version_id=draft.blueprint_version_id
        )
    except Exception as error:
        st.error(f"Không thể tải cấu trúc ô ma trận: {error}")
        return

    if not sections or not cognitive_levels:
        st.warning(
            "Hồ sơ chưa có phần đề hoặc mức độ nhận thức hoạt động."
        )
        return

    section_reference = [
        {
            "section_code": section.section_code,
            "section_name": section.section_name,
            "question_type_code": section.question_type_code,
            "question_count": section.question_count,
            "response_count": section.response_count,
            "section_score": float(section.section_score),
        }
        for section in sections
    ]
    with st.expander("Cấu hình phần đề cần đáp ứng", expanded=True):
        st.dataframe(
            section_reference,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Mức độ hợp lệ: "
            + ", ".join(
                level.cognitive_level_code
                for level in cognitive_levels
            )
        )
        if level_allocations:
            st.caption(
                "Phân bổ điểm theo mức độ: "
                + ", ".join(
                    f"{item.cognitive_level_code} "
                    f"{item.target_score:g} điểm"
                    for item in level_allocations
                )
            )

    cell_rows = _default_cell_rows(
        sections=sections,
        topic_codes=selected_topic_codes,
        cognitive_levels=cognitive_levels,
        level_allocations=level_allocations,
        existing_cells=existing_cells,
    )
    edited_cells = st.data_editor(
        cell_rows,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=(
            "assessment_blueprint_cell_editor_"
            + draft.blueprint_version_id
        ),
    )
    if st.button(
        "Lưu các ô ma trận",
        type="primary",
        use_container_width=True,
        disabled=not selected_topic_codes,
    ):
        try:
            saved_cells = catalog.replace_cells(
                blueprint_version_id=draft.blueprint_version_id,
                cells=_cell_payload(edited_cells),
            )
        except Exception as error:
            st.error(f"Không thể lưu các ô ma trận: {error}")
        else:
            st.success(
                f"Đã lưu nguyên tử {len(saved_cells)} ô ma trận."
            )
            st.rerun()

    st.subheader("5. Gửi ma trận để duyệt")
    try:
        ready_for_review = catalog.ready_for_review(
            blueprint_version_id=draft.blueprint_version_id
        )
    except Exception as error:
        st.error(f"Không thể kiểm tra điều kiện gửi duyệt: {error}")
        return

    if ready_for_review:
        st.success(
            "Ma trận đã đủ YCCĐ chính và phân bổ điểm; có thể gửi duyệt."
        )
    else:
        st.warning(
            "Ma trận chưa đủ điều kiện: cần ít nhất một YCCĐ PRIMARY, "
            "các ô ma trận hợp lệ và tổng điểm khớp hồ sơ."
        )
    if not st.button(
        "Gửi ma trận để duyệt",
        type="primary",
        use_container_width=True,
        disabled=not ready_for_review,
    ):
        return
    try:
        catalog.submit_for_review(
            blueprint_version_id=draft.blueprint_version_id
        )
    except Exception as error:
        st.error(f"Không thể gửi ma trận để duyệt: {error}")
        return
    st.session_state.pop("assessment_blueprint_version_id", None)
    st.success("Đã gửi ma trận cho quản trị viên duyệt.")
    st.rerun()
