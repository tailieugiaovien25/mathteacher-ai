"""Streamlit interface for the personal teacher document catalog."""

from __future__ import annotations

import os
from typing import Mapping
from urllib.parse import urlparse
from uuid import uuid4

from teacher_document_library_v2 import (
    DOCUMENT_CATEGORY_LABELS,
    DocumentCategory,
    DocumentFilter,
    TeacherDocument,
    TeacherDocumentCatalog,
)
from teacher_document_library_v2.adapters import SupabaseTeacherDocumentRepository


MIME_OPTIONS = {
    "Word (.docx)": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "Excel (.xlsx)": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "PDF (.pdf)": "application/pdf",
    "Tệp khác": "application/octet-stream",
}


def supabase_settings(environment: Mapping[str, str] | None = None) -> tuple[str, str] | None:
    values = environment if environment is not None else os.environ
    url = values.get("SUPABASE_URL", "").strip()
    key = values.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    return (url, key) if url and key else None


def create_supabase_client(url: str, key: str):
    from supabase import create_client

    return create_client(url, key)


def authenticate(client, email: str, password: str) -> SupabaseTeacherDocumentRepository:
    email = email.strip()
    if not email or not password:
        raise ValueError("Email và mật khẩu không được để trống.")
    response = client.auth.sign_in_with_password({"email": email, "password": password})
    user = getattr(response, "user", None)
    user_id = getattr(user, "id", None)
    if not user_id:
        raise ValueError("Supabase không trả về tài khoản giáo viên.")
    return SupabaseTeacherDocumentRepository(client, str(user_id))


def comma_values(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def drive_reference(value: str) -> tuple[str, str | None]:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Hãy nhập liên kết hoặc mã file Google Drive.")
    parsed = urlparse(normalized)
    if parsed.scheme in ("http", "https"):
        if parsed.hostname not in ("drive.google.com", "docs.google.com"):
            raise ValueError("Liên kết phải thuộc Google Drive hoặc Google Docs.")
        parts = [part for part in parsed.path.split("/") if part]
        file_id = parts[parts.index("d") + 1] if "d" in parts and parts.index("d") + 1 < len(parts) else normalized
        return file_id, normalized
    return normalized, None


def build_document(
    *,
    title: str,
    category: DocumentCategory,
    academic_year: str,
    subject: str,
    grade_level: str,
    class_name: str,
    file_name: str,
    mime_type: str,
    drive_link_or_id: str,
    description: str,
    tags: str,
) -> TeacherDocument:
    file_id, link = drive_reference(drive_link_or_id)
    return TeacherDocument(
        document_id=str(uuid4()),
        title=title,
        category=category,
        academic_year=academic_year,
        subject=subject,
        grade_level=grade_level,
        class_name=class_name,
        file_name=file_name,
        mime_type=mime_type,
        size_bytes=0,
        storage_provider="google_drive_manual",
        storage_file_id=file_id,
        web_view_link=link,
        description=description,
        tags=comma_values(tags),
    )


def document_rows(documents: tuple[TeacherDocument, ...]) -> list[dict[str, object]]:
    return [
        {
            "Tên tài liệu": item.title,
            "Loại": item.category_label,
            "Năm học": item.academic_year,
            "Môn": item.subject,
            "Khối": item.grade_level,
            "Lớp": item.class_name or "",
            "Tên file": item.file_name,
            "Nhãn": ", ".join(item.tags),
        }
        for item in documents
    ]


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Kho tài liệu giáo viên", page_icon="📚", layout="wide")
    st.title("Kho tài liệu cá nhân của giáo viên")
    st.caption("Supabase quản lý thông tin và quyền sở hữu · Google Drive lưu file")

    settings = supabase_settings()
    if settings is None:
        st.error("Chưa có SUPABASE_URL và SUPABASE_PUBLISHABLE_KEY.")
        return

    if "document_library_repository" not in st.session_state:
        st.sidebar.subheader("Đăng nhập giáo viên")
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Mật khẩu", type="password")
        if st.sidebar.button("Đăng nhập", use_container_width=True):
            try:
                client = create_supabase_client(*settings)
                st.session_state["document_library_client"] = client
                st.session_state["document_library_repository"] = authenticate(client, email, password)
                st.rerun()
            except Exception as error:
                st.sidebar.error(f"Không thể đăng nhập: {error}")
        st.info("Hãy đăng nhập để truy cập kho tài liệu của riêng bạn.")
        return

    repository = st.session_state["document_library_repository"]
    client = st.session_state["document_library_client"]
    catalog = TeacherDocumentCatalog(repository)
    st.sidebar.success("Đã kết nối kho tài liệu")
    if st.sidebar.button("Đăng xuất", use_container_width=True):
        client.auth.sign_out()
        st.session_state.pop("document_library_repository", None)
        st.session_state.pop("document_library_client", None)
        st.rerun()

    with st.expander("Đăng ký tài liệu từ Google Drive", expanded=False):
        st.info(
            "Bản này đăng ký file đã có trên Drive. Công cụ tải file trực tiếp bằng OAuth "
            "sẽ được bổ sung ở bước tiếp theo."
        )
        with st.form("new_teacher_document"):
            title = st.text_input("Tên tài liệu *")
            category_label = st.selectbox("Loại tài liệu *", tuple(DOCUMENT_CATEGORY_LABELS.values()))
            category = next(key for key, label in DOCUMENT_CATEGORY_LABELS.items() if label == category_label)
            left, middle, right = st.columns(3)
            academic_year = left.text_input("Năm học *", placeholder="2026-2027")
            subject = middle.text_input("Môn học *", placeholder="Toán")
            grade_level = right.text_input("Khối *", placeholder="6")
            class_name = st.text_input("Lớp", placeholder="6A1")
            file_name = st.text_input("Tên file *", placeholder="Giao-an-bai-1.docx")
            mime_label = st.selectbox("Định dạng", tuple(MIME_OPTIONS))
            drive_link = st.text_input("Liên kết hoặc mã file Google Drive *")
            description = st.text_area("Mô tả")
            tags = st.text_input("Nhãn (phân cách bằng dấu phẩy)", placeholder="học kỳ 1, đã chuẩn hóa")
            submitted = st.form_submit_button("Lưu vào kho", use_container_width=True)
            if submitted:
                try:
                    document = build_document(
                        title=title, category=category, academic_year=academic_year,
                        subject=subject, grade_level=grade_level, class_name=class_name,
                        file_name=file_name, mime_type=MIME_OPTIONS[mime_label],
                        drive_link_or_id=drive_link, description=description, tags=tags,
                    )
                    catalog.save(document)
                    st.success("Đã lưu tài liệu vào kho cá nhân.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Không thể lưu tài liệu: {error}")

    all_documents = catalog.search()
    st.subheader("Tìm kiếm tài liệu")
    query = st.text_input("Từ khóa", placeholder="Tên bài, mô tả hoặc nhãn")
    years = ("Tất cả", *sorted({item.academic_year for item in all_documents}))
    subjects = ("Tất cả", *sorted({item.subject for item in all_documents}))
    categories = ("Tất cả", *DOCUMENT_CATEGORY_LABELS.values())
    one, two, three = st.columns(3)
    year = one.selectbox("Năm học", years)
    subject_filter = two.selectbox("Môn học", subjects)
    category_filter = three.selectbox("Loại tài liệu", categories)
    category_value = next(
        (key for key, label in DOCUMENT_CATEGORY_LABELS.items() if label == category_filter), None
    )
    documents = catalog.search(
        DocumentFilter(
            query=query,
            academic_year=None if year == "Tất cả" else year,
            subject=None if subject_filter == "Tất cả" else subject_filter,
            category=category_value,
        )
    )
    st.caption(f"Tìm thấy {len(documents)} tài liệu")
    st.dataframe(document_rows(documents), use_container_width=True, hide_index=True)
    for document in documents:
        with st.expander(f"{document.category_label} · {document.title}"):
            st.write(document.description or "Không có mô tả.")
            st.caption(f"{document.subject} · Khối {document.grade_level} · {document.academic_year}")
            if document.web_view_link:
                st.link_button("Mở trên Google Drive", document.web_view_link)
            if st.button("Xóa thông tin khỏi kho", key=f"delete_{document.document_id}"):
                catalog.delete(document.document_id)
                st.success("Đã xóa thông tin tài liệu. File trên Google Drive không bị xóa.")
                st.rerun()


if __name__ == "__main__":
    main()
