"""Read-only library of a teacher's saved assessment exam versions."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any, Mapping
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from assessment_generation_v2.services.assessment_draft_document_export import (
    export_draft_documents,
)


_STATUS_LABELS = {
    "DRAFT": "Bản nháp",
    "AI_PROPOSED": "AI đề xuất",
    "ASSEMBLED": "Đã ráp đề · bản nháp",
    "PENDING_REVIEW": "Chờ duyệt",
    "REVISION_REQUIRED": "Cần chỉnh sửa",
    "APPROVED": "Đã duyệt",
    "REJECTED": "Bị từ chối",
    "PUBLISHED": "Đã phát hành",
    "RETIRED": "Đã ngừng sử dụng",
}
_DRAFT_EXPORTABLE = frozenset({"ASSEMBLED", "PENDING_REVIEW"})


class AssessmentExamLibraryError(RuntimeError):
    """Raised when saved exam rows do not match the library contract."""


@dataclass(frozen=True, slots=True)
class AssessmentExamLibraryEntry:
    exam_version_id: str
    exam_id: str
    exam_code: str
    title: str
    subject_code: str
    grade_level: int
    version_number: int
    academic_year: str
    semester_number: int | None
    scheduled_date: str
    assembly_status: str
    created_at: str

    @property
    def label(self) -> str:
        year = f" · {self.academic_year}" if self.academic_year else ""
        return (
            f"Lớp {self.grade_level} · {self.title} · "
            f"v{self.version_number} · {_STATUS_LABELS[self.assembly_status]}{year}"
        )


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _relation(value: object) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentExamLibraryError(
                "Quan hệ đề kiểm tra trả về dữ liệu không hợp lệ."
            )
        value = value[0]
    if not isinstance(value, Mapping):
        raise AssessmentExamLibraryError(
            "Không đọc được thông tin đề kiểm tra."
        )
    return dict(value)


class SupabaseAssessmentExamLibrary:
    """Load only exam versions owned by the currently signed-in teacher."""

    def __init__(self, *, client: Any, user_id: str) -> None:
        if client is None:
            raise ValueError("client must not be None")
        try:
            self._user_id = str(UUID(user_id))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("Tài khoản giáo viên không hợp lệ.") from error
        self._client = client

    def list_entries(self) -> tuple[AssessmentExamLibraryEntry, ...]:
        response = (
            self._client.table("assessment_exam_versions")
            .select(
                "exam_version_id,exam_id,version_number,exam_title,"
                "academic_year,semester_number,scheduled_date,assembly_status,"
                "created_at,assessment_exams!inner(exam_code,subject_code,"
                "grade_level,owner_user_id)"
            )
            .eq("assessment_exams.owner_user_id", self._user_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = _data(response)
        if rows is None:
            return ()
        if isinstance(rows, Mapping):
            rows = [rows]
        if not isinstance(rows, list) or any(
            not isinstance(row, Mapping) for row in rows
        ):
            raise AssessmentExamLibraryError(
                "Danh sách đề kiểm tra trả về dữ liệu không hợp lệ."
            )

        entries: list[AssessmentExamLibraryEntry] = []
        for raw in rows:
            row = dict(raw)
            exam = _relation(row.get("assessment_exams"))
            if str(exam.get("owner_user_id", "")) != self._user_id:
                raise PermissionError(
                    "Danh sách có đề không thuộc tài khoản hiện tại."
                )
            status = _text(row.get("assembly_status")).upper()
            if status not in _STATUS_LABELS:
                raise AssessmentExamLibraryError(
                    "Đề có trạng thái chưa được hỗ trợ trong thư viện."
                )
            try:
                grade = int(exam.get("grade_level"))
                version_number = int(row.get("version_number"))
                exam_id = str(UUID(_text(row.get("exam_id"))))
                version_id = str(UUID(_text(row.get("exam_version_id"))))
            except (TypeError, ValueError, AttributeError) as error:
                raise AssessmentExamLibraryError(
                    "Đề có mã định danh hoặc khối lớp không hợp lệ."
                ) from error
            if not 1 <= grade <= 12 or version_number < 1:
                raise AssessmentExamLibraryError(
                    "Đề có khối lớp hoặc phiên bản không hợp lệ."
                )
            entries.append(
                AssessmentExamLibraryEntry(
                    exam_version_id=version_id,
                    exam_id=exam_id,
                    exam_code=_text(exam.get("exam_code")),
                    title=_text(row.get("exam_title")) or "Đề chưa đặt tên",
                    subject_code=_text(exam.get("subject_code")),
                    grade_level=grade,
                    version_number=version_number,
                    academic_year=_text(row.get("academic_year")),
                    semester_number=(
                        int(row["semester_number"])
                        if row.get("semester_number") is not None
                        else None
                    ),
                    scheduled_date=_text(row.get("scheduled_date")),
                    assembly_status=status,
                    created_at=_text(row.get("created_at")),
                )
            )
        return tuple(entries)


def _render_entry_table(st: Any, entries: tuple[AssessmentExamLibraryEntry, ...]) -> None:
    rows = [
        {
            "Mã đề": item.exam_code,
            "Tên đề": item.title,
            "Môn": item.subject_code,
            "Lớp": item.grade_level,
            "Phiên bản": item.version_number,
            "Năm học": item.academic_year or "—",
            "Học kỳ": item.semester_number or "—",
            "Ngày kiểm tra": item.scheduled_date or "—",
            "Trạng thái": _STATUS_LABELS[item.assembly_status],
        }
        for item in entries
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_assessment_exam_library_page(
    *, st: Any, client: Any, user_id: str,
    catalog: Any | None = None,
) -> None:
    """Render a teacher-owned exam library with safe draft downloads."""

    st.title("Thư viện đề kiểm tra")
    st.caption(
        "Tra cứu các phiên bản đề bạn đã tạo. Thư viện chỉ hiển thị dữ liệu "
        "thuộc tài khoản đang đăng nhập; tải bản nháp không làm thay đổi trạng thái duyệt."
    )
    try:
        source = catalog or SupabaseAssessmentExamLibrary(
            client=client, user_id=user_id
        )
        entries = tuple(source.list_entries())
    except Exception as error:
        st.error(f"Không thể tải thư viện đề kiểm tra: {error}")
        return

    if not entries:
        st.info("Bạn chưa có đề kiểm tra nào được lưu.")
        return

    grades = sorted({entry.grade_level for entry in entries})
    statuses = sorted({entry.assembly_status for entry in entries})
    filter_columns = st.columns((1, 1, 2))
    with filter_columns[0]:
        selected_grade = st.selectbox(
            "Khối lớp", ("Tất cả", *grades), key="exam_library_grade"
        )
    with filter_columns[1]:
        selected_status = st.selectbox(
            "Trạng thái",
            ("Tất cả", *(_STATUS_LABELS[value] for value in statuses)),
            key="exam_library_status",
        )
    with filter_columns[2]:
        query = st.text_input(
            "Tìm theo tên hoặc mã đề", key="exam_library_search"
        ).strip().casefold()

    label_to_status = {
        _STATUS_LABELS[status]: status for status in statuses
    }
    filtered = tuple(
        entry for entry in entries
        if (selected_grade == "Tất cả" or entry.grade_level == selected_grade)
        and (
            selected_status == "Tất cả"
            or entry.assembly_status == label_to_status.get(selected_status)
        )
        and (
            not query
            or query in entry.title.casefold()
            or query in entry.exam_code.casefold()
        )
    )
    st.caption(f"Hiển thị {len(filtered)} / {len(entries)} phiên bản đề.")
    if not filtered:
        st.info("Không có đề phù hợp với bộ lọc hiện tại.")
        return

    _render_entry_table(st, filtered)
    exportable = tuple(
        entry for entry in filtered
        if entry.assembly_status in _DRAFT_EXPORTABLE
    )
    if not exportable:
        st.caption(
            "Chỉ đề đã ráp hoặc đang chờ duyệt mới có thể tải bộ Word bản nháp."
        )
        return

    selected = st.selectbox(
        "Chọn đề để tải bộ Word bản nháp",
        exportable,
        format_func=lambda entry: entry.label,
        key="exam_library_export_version",
    )
    if st.button(
        "Chuẩn bị bộ Word bản nháp",
        type="primary",
        key="exam_library_prepare_export",
    ):
        try:
            files = export_draft_documents(
                client=client,
                user_id=user_id,
                exam_version_id=selected.exam_version_id,
            )
            archive = BytesIO()
            with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
                for filename, content in files.items():
                    bundle.writestr(filename, content)
            key = f"assessment_exam_library_export_{user_id}_{selected.exam_version_id}"
            st.session_state[key] = archive.getvalue()
            st.success("Đã chuẩn bị bộ Word bản nháp.")
        except Exception as error:
            st.error(f"Không thể tạo bộ Word bản nháp: {error}")

    key = f"assessment_exam_library_export_{user_id}_{selected.exam_version_id}"
    archive_data = st.session_state.get(key)
    if archive_data:
        st.download_button(
            "Tải bộ Word bản nháp (ZIP)",
            data=archive_data,
            file_name=f"{selected.exam_code or 'de-kiem-tra'}-ban-nhap.zip",
            mime="application/zip",
            key="exam_library_download_export",
            use_container_width=True,
        )
