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
    DocumentUploadMetadata,
    TeacherDocumentUploadService,
)
from teacher_document_library_v2.adapters import (
    GoogleDriveFileStorage,
    GoogleOAuthSettings,
    SupabaseTeacherDocumentRepository,
    create_authorization_request,
    credentials_from_dict,
    credentials_to_dict,
    exchange_authorization_code,
    validate_signed_oauth_state,
)


MIME_OPTIONS = {
    "Word (.docx)": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "Excel (.xlsx)": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "PDF (.pdf)": "application/pdf",
    "Tệp khác": "application/octet-stream",
}
MAX_DIRECT_UPLOAD_BYTES = 25 * 1024 * 1024


def supabase_settings(environment: Mapping[str, str] | None = None) -> tuple[str, str] | None:
    values = environment if environment is not None else os.environ
    url = values.get("SUPABASE_URL", "").strip()
    key = values.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    return (url, key) if url and key else None


def google_oauth_settings(
    environment: Mapping[str, str] | None = None,
) -> GoogleOAuthSettings | None:
    values = environment if environment is not None else os.environ
    return GoogleOAuthSettings.from_environment(values)


def validate_oauth_callback(
    *, incoming_state: str, signing_key: str, code: str
) -> None:
    try:
        validate_signed_oauth_state(incoming_state, signing_key)
    except ValueError as error:
        raise ValueError(
            "Trạng thái OAuth không hợp lệ hoặc đã hết hạn. Hãy kết nối lại Google Drive."
        ) from error
    if not code.strip():
        raise ValueError("Google không trả về mã cấp quyền.")


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


def main(*, embedded: bool = False) -> None:
    import streamlit as st

    if not embedded:
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
    if not embedded:
        st.sidebar.success("Đã kết nối kho tài liệu")
    if not embedded and st.sidebar.button("Đăng xuất", use_container_width=True):
        client.auth.sign_out()
        st.session_state.pop("document_library_repository", None)
        st.session_state.pop("document_library_client", None)
        st.session_state.pop("google_drive_credentials", None)
        st.session_state.pop("google_oauth_state", None)
        st.session_state.pop("google_oauth_url", None)
        st.rerun()

    oauth_settings = google_oauth_settings()
    callback_code = str(st.query_params.get("code", ""))
    callback_state = str(st.query_params.get("state", ""))
    callback_error = str(st.query_params.get("error", ""))
    if callback_error:
        st.error(f"Google Drive từ chối kết nối: {callback_error}")
        st.query_params.clear()
    elif callback_code:
        try:
            if oauth_settings is None:
                raise ValueError("Chưa cấu hình Google OAuth trên máy chủ.")
            validate_oauth_callback(
                incoming_state=callback_state,
                signing_key=oauth_settings.client_secret,
                code=callback_code,
            )
            st.session_state["google_drive_credentials"] = exchange_authorization_code(
                oauth_settings, code=callback_code, state=callback_state
            )
            st.session_state.pop("google_oauth_url", None)
            st.query_params.clear()
            st.rerun()
        except Exception as error:
            st.query_params.clear()
            st.error(f"Không thể hoàn tất kết nối Google Drive: {error}")

    st.sidebar.subheader("Google Drive")
    if oauth_settings is None:
        st.sidebar.warning(
            "Chưa có GOOGLE_OAUTH_CLIENT_ID và GOOGLE_OAUTH_CLIENT_SECRET."
        )
    elif "google_drive_credentials" not in st.session_state:
        if st.sidebar.button("Tạo liên kết kết nối", use_container_width=True):
            try:
                url, state = create_authorization_request(oauth_settings)
                st.session_state["google_oauth_url"] = url
            except Exception as error:
                st.sidebar.error(f"Không thể tạo liên kết OAuth: {error}")
        if st.session_state.get("google_oauth_url"):
            st.sidebar.link_button(
                "Kết nối tài khoản Google",
                st.session_state["google_oauth_url"],
                use_container_width=True,
            )
    else:
        st.sidebar.success("Đã kết nối Google Drive")
        if st.sidebar.button("Ngắt kết nối Drive", use_container_width=True):
            st.session_state.pop("google_drive_credentials", None)
            st.rerun()

    if "google_drive_credentials" in st.session_state:
        with st.expander("Tải file trực tiếp lên Google Drive", expanded=True):
            st.caption(
                "Chấp nhận Word, Excel và PDF tối đa 25 MB. File được đặt trong "
                "thư mục MathTeacher-AI trên Drive của giáo viên."
            )
            with st.form("direct_google_drive_upload"):
                uploaded = st.file_uploader(
                    "Chọn file *", type=["docx", "xlsx", "pdf"]
                )
                upload_title = st.text_input("Tên tài liệu *", key="upload_title")
                upload_category_label = st.selectbox(
                    "Loại tài liệu *",
                    tuple(DOCUMENT_CATEGORY_LABELS.values()),
                    key="upload_category",
                )
                upload_category = next(
                    key for key, label in DOCUMENT_CATEGORY_LABELS.items()
                    if label == upload_category_label
                )
                upload_left, upload_middle, upload_right = st.columns(3)
                upload_year = upload_left.text_input("Năm học *", key="upload_year")
                upload_subject = upload_middle.text_input("Môn học *", key="upload_subject")
                upload_grade = upload_right.text_input("Khối *", key="upload_grade")
                upload_class = st.text_input("Lớp", key="upload_class")
                upload_description = st.text_area("Mô tả", key="upload_description")
                upload_tags = st.text_input(
                    "Nhãn (phân cách bằng dấu phẩy)", key="upload_tags"
                )
                upload_submitted = st.form_submit_button(
                    "Tải lên Drive và lưu vào kho", use_container_width=True
                )
                if upload_submitted:
                    try:
                        if uploaded is None:
                            raise ValueError("Hãy chọn một file Word, Excel hoặc PDF.")
                        content = uploaded.getvalue()
                        if len(content) > MAX_DIRECT_UPLOAD_BYTES:
                            raise ValueError("File vượt quá giới hạn 25 MB.")
                        credentials = credentials_from_dict(
                            st.session_state["google_drive_credentials"]
                        )
                        storage = GoogleDriveFileStorage(credentials)
                        service = TeacherDocumentUploadService(catalog, storage)
                        service.upload(
                            content=content,
                            file_name=uploaded.name,
                            mime_type=uploaded.type or "application/octet-stream",
                            metadata=DocumentUploadMetadata(
                                title=upload_title,
                                category=upload_category,
                                academic_year=upload_year,
                                subject=upload_subject,
                                grade_level=upload_grade,
                                class_name=upload_class,
                                description=upload_description,
                                tags=comma_values(upload_tags),
                            ),
                        )
                        st.session_state["google_drive_credentials"] = credentials_to_dict(credentials)
                        st.success("Đã tải file lên Drive và lưu metadata vào Supabase.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Không thể tải tài liệu: {error}")

    with st.expander("Đăng ký tài liệu đã có trên Google Drive", expanded=False):
        st.info(
            "Dùng mục này khi file đã có sẵn trên Drive và bạn muốn đăng ký bằng liên kết."
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




    # NOTEBOOKLM_BRIDGE_UI_V1
    st.divider()
    with st.expander(
        "\u0054\u1ea1o g\u00f3i ngu\u1ed3n cho NotebookLM",
        expanded=False,
    ):
        st.write(
            "Ch\u1ecdn c\u00e1c h\u1ecdc li\u1ec7u trong danh s\u00e1ch "
            "hi\u1ec7n t\u1ea1i \u0111\u1ec3 t\u1ea1o g\u00f3i ngu\u1ed3n "
            "cho NotebookLM c\u00e1 nh\u00e2n."
        )
        st.caption(
            "G\u00f3i ZIP ch\u1ee9a b\u1ea3n sao t\u1ec7p ngu\u1ed3n, "
            "ch\u1ec9 m\u1ee5c, manifest SHA-256 v\u00e0 m\u1eabu "
            "c\u00e2u l\u1ec7nh ti\u1ebfng Vi\u1ec7t. "
            "Sau khi gi\u1ea3i n\u00e9n, gi\u00e1o vi\u00ean th\u00eam "
            "t\u1eebng t\u1ec7p trong sources/ v\u00e0o NotebookLM."
        )

        bridge_storage = None
        credentials = st.session_state.get("google_drive_credentials")
        if credentials:
            try:
                bridge_storage = GoogleDriveFileStorage(
                    credentials_from_dict(credentials)
                )
            except Exception as error:
                st.error(
                    f"Kh\u00f4ng kh\u1edfi t\u1ea1o \u0111\u01b0\u1ee3c "
                    f"k\u1ebft n\u1ed1i Google Drive: {error}"
                )

        if bridge_storage is None:
            st.info(
                "H\u00e3y k\u1ebft n\u1ed1i Google Drive "
                "\u1edf thanh b\u00ean \u0111\u1ec3 t\u1ea1o g\u00f3i ngu\u1ed3n."
            )
        elif not documents:
            st.info(
                "Kh\u00f4ng c\u00f3 t\u00e0i li\u1ec7u "
                "ph\u00f9 h\u1ee3p b\u1ed9 l\u1ecdc hi\u1ec7n t\u1ea1i."
            )
        else:
            label_to_document = {
                f"{item.title} | {item.file_name} | {item.document_id[:8]}": item
                for item in documents
            }
            selected_labels = st.multiselect(
                "Ch\u1ecdn h\u1ecdc li\u1ec7u \u0111\u01b0a v\u00e0o g\u00f3i",
                options=list(label_to_document),
                key="notebooklm_bridge_selected_sources_v1",
                help=(
                    "Ch\u1ec9 c\u00e1c t\u00e0i li\u1ec7u "
                    "\u0111\u01b0\u1ee3c ch\u1ecdn m\u1edbi "
                    "\u0111\u01b0\u1ee3c t\u1ea3i xu\u1ed1ng v\u00e0 "
                    "\u0111\u00f3ng g\u00f3i."
                ),
            )

            if st.button(
                "T\u1ea1o g\u00f3i ngu\u1ed3n NotebookLM",
                key="notebooklm_bridge_build_package_v1",
                disabled=not selected_labels,
                use_container_width=True,
            ):
                try:
                    from notebooklm_bridge import build_notebooklm_source_pack

                    selected_documents = tuple(
                        label_to_document[label] for label in selected_labels
                    )

                    def download_selected(document):
                        if (
                            str(document.storage_provider).casefold()
                            != "google_drive_oauth"
                        ):
                            raise ValueError(
                                "T\u00e0i li\u1ec7u n\u00e0y "
                                "kh\u00f4ng \u0111\u01b0\u1ee3c l\u01b0u "
                                "b\u1eb1ng k\u1ebft n\u1ed1i Google Drive "
                                "hi\u1ec7n t\u1ea1i."
                            )
                        return bridge_storage.download(document.storage_file_id)

                    with st.spinner(
                        "\u0110ang t\u1ea1o g\u00f3i ngu\u1ed3n NotebookLM..."
                    ):
                        pack = build_notebooklm_source_pack(
                            selected_documents, download_selected
                        )

                    st.session_state["notebooklm_bridge_pack_v1"] = {
                        "filename": pack.filename,
                        "content": pack.content,
                        "included_count": len(pack.included_sources),
                        "failed_sources": [
                            dict(row) for row in pack.failed_sources
                        ],
                    }
                except Exception as error:
                    st.error(
                        f"Kh\u00f4ng t\u1ea1o \u0111\u01b0\u1ee3c "
                        f"g\u00f3i NotebookLM: {error}"
                    )

        pack_state = st.session_state.get("notebooklm_bridge_pack_v1")
        if pack_state:
            st.success(
                f"\u0110\u00e3 \u0111\u00f3ng g\u00f3i "
                f"{pack_state['included_count']} ngu\u1ed3n."
            )
            st.download_button(
                "T\u1ea3i g\u00f3i ngu\u1ed3n NotebookLM (.zip)",
                data=pack_state["content"],
                file_name=pack_state["filename"],
                mime="application/zip",
                key="notebooklm_bridge_download_package_v1",
                use_container_width=True,
            )
            if pack_state["failed_sources"]:
                st.warning(
                    f"C\u00f3 {len(pack_state['failed_sources'])} "
                    "ngu\u1ed3n ch\u01b0a t\u1ea3i \u0111\u01b0\u1ee3c."
                )
                with st.expander(
                    "Chi ti\u1ebft ngu\u1ed3n ch\u01b0a \u0111\u00f3ng g\u00f3i"
                ):
                    for failed in pack_state["failed_sources"]:
                        st.write(
                            f"- {failed.get('title', '')} "
                            f"({failed.get('file_name', '')}): "
                            f"{failed.get('error', '')}"
                        )
if __name__ == "__main__":
    main()
