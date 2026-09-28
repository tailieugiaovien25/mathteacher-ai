"""Teacher-reviewed source library tied to a catalog textbook lesson."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
import unicodedata


def _searchable(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def find_lesson_pages(pdf_bytes: bytes, lesson_title: str) -> list[int]:
    """Suggest text-layer PDF pages; teacher must verify page and lesson identity."""
    if len(pdf_bytes) > 100 * 1024 * 1024:
        raise ValueError("PDF vượt quá 100 MB.")
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(pdf_bytes))
    if len(reader.pages) > 500:
        raise ValueError("PDF vượt quá 500 trang.")
    title = _searchable(lesson_title)
    if len(title) < 8:
        raise ValueError("Tên bài quá ngắn để tìm trong PDF.")
    pages = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if len(text.strip()) < 120 or "muc luc" in _searchable(text[:200]):
            continue
        if title in _searchable(text[:2400]):
            pages.append(index + 1)
            if len(pages) == 10:
                break
    return pages


def extract_pdf_page(pdf_bytes: bytes, page: int) -> tuple[str, int]:
    """Extract exactly the page chosen by the teacher; never infer the lesson from OCR."""
    if len(pdf_bytes) > 100 * 1024 * 1024:
        raise ValueError("PDF vượt quá 100 MB. Hãy chọn tệp nhỏ hơn hoặc nhập đoạn kiến thức.")
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(pdf_bytes))
    if not 1 <= len(reader.pages) <= 500 or not 1 <= page <= len(reader.pages):
        raise ValueError("Trang PDF không hợp lệ hoặc sách vượt quá 500 trang.")
    return (reader.pages[page - 1].extract_text() or "").strip()[:4000], len(reader.pages)


def load_reviewed_sources(client, *, user_id: str, book_id: str, lesson_id: str) -> list[dict]:
    result = (client.table("teacher_textbook_lesson_sources")
              .select("source_id,source_label,knowledge_excerpt,pdf_page,pdf_sha256")
              .eq("owner_user_id", user_id).eq("textbook_id", book_id)
              .eq("textbook_unit_id", lesson_id).eq("review_status", "TEACHER_REVIEWED")
              .limit(51).execute().data)
    if not isinstance(result, list) or len(result) > 50:
        raise ValueError("Danh sách nguồn vượt giới hạn 50 đoạn; cần rà soát.")
    return result


def save_reviewed_source(client, *, user_id: str, book_id: str, lesson_id: str,
                         label: str, excerpt: str, pdf_bytes: bytes | None,
                         pdf_page: int | None) -> None:
    label, excerpt = label.strip(), excerpt.strip()
    if not 1 <= len(label) <= 160 or not 80 <= len(excerpt) <= 4000:
        raise ValueError("Cần tên nguồn và đoạn kiến thức đã kiểm tra từ 80 đến 4000 ký tự.")
    if pdf_bytes is not None:
        if pdf_page is None:
            raise ValueError("Cần số trang PDF cho đoạn trích.")
        extract_pdf_page(pdf_bytes, pdf_page)
    client.table("teacher_textbook_lesson_sources").upsert({
        "owner_user_id": user_id, "textbook_id": book_id, "textbook_unit_id": lesson_id,
        "source_label": label, "knowledge_excerpt": excerpt,
        "pdf_sha256": sha256(pdf_bytes).hexdigest() if pdf_bytes is not None else None,
        "pdf_page": pdf_page if pdf_bytes is not None else None,
        "review_status": "TEACHER_REVIEWED",
    }, on_conflict="owner_user_id,textbook_unit_id,source_label").execute()


def render_lesson_source_picker(st, *, client, user_id: str, book_id: str,
                                lesson_id: str, lesson_title: str) -> tuple[str, str]:
    """Return only a reviewed excerpt and a stable source ID for the AI boundary."""
    sources = load_reviewed_sources(client, user_id=user_id, book_id=book_id,
                                    lesson_id=lesson_id)
    if sources:
        selected = st.selectbox("Đoạn kiến thức đã kiểm tra của đúng bài",
                                sources, format_func=lambda row: row["source_label"],
                                key="lesson_source_" + lesson_id)
        st.caption("Trang PDF: " + (str(selected["pdf_page"]) if selected["pdf_page"] else "Giáo viên nhập"))
        st.text_area("Kiến thức nguồn đã duyệt", selected["knowledge_excerpt"],
                     disabled=True, height=160, key="lesson_source_text_" + str(selected["source_id"]))
        excerpt = str(selected["knowledge_excerpt"])
        ref = "teacher_excerpt:" + sha256(excerpt.encode("utf-8")).hexdigest()[:20]
    else:
        st.info("Bài này chưa có đoạn kiến thức đã kiểm tra. Hãy tạo nguồn bên dưới.")
        excerpt, ref = "", ""
    with st.expander("Thêm hoặc cập nhật nguồn kiến thức của bài", expanded=not sources):
        st.caption("Chọn đúng bài SGK phía trên. Trích PDF chỉ là văn bản nháp; giáo viên cần sửa lỗi và xác nhận.")
        label = st.text_input("Tên mục hoặc đoạn kiến thức", key="source_label_" + lesson_id)
        pdf = st.file_uploader("PDF đúng tập SGK (tùy chọn, tối đa 100 MB)", type=["pdf"],
                               key="source_pdf_" + lesson_id)
        pdf_bytes = pdf.getvalue() if pdf else None
        page = None
        extracted = ""
        if pdf_bytes:
            try:
                if len(pdf_bytes) > 100 * 1024 * 1024:
                    raise ValueError("PDF vượt quá 100 MB.")
                from pypdf import PdfReader
                count = len(PdfReader(BytesIO(pdf_bytes)).pages)
                if not 1 <= count <= 500:
                    raise ValueError("PDF phải có từ 1 đến 500 trang.")
                if st.button("Tìm trang theo tên bài", key="source_find_" + lesson_id):
                    matches = find_lesson_pages(pdf_bytes, lesson_title)
                    st.session_state["source_page_matches_" + lesson_id] = (
                        sha256(pdf_bytes).hexdigest(), matches)
                cached_matches = st.session_state.get("source_page_matches_" + lesson_id)
                matches = cached_matches[1] if cached_matches and cached_matches[0] == sha256(pdf_bytes).hexdigest() else []
                if matches:
                    st.caption("Trang có tên bài (cần đối chiếu): " + ", ".join(map(str, matches)))
                else:
                    st.caption("Nếu PDF là ảnh quét, tìm chữ có thể không thấy bài. Hãy chọn trang thủ công.")
                page = st.number_input("Trang trong tệp PDF", min_value=1, max_value=count,
                                       value=1, key="source_page_" + lesson_id)
                if st.button("Lấy chữ của trang này", key="source_extract_" + lesson_id):
                    extracted, _ = extract_pdf_page(pdf_bytes, int(page))
                    st.session_state["source_editor_" + lesson_id] = extracted
            except Exception as exc:
                st.error(f"Không đọc được PDF: {exc}")
                return excerpt, ref
        reviewed = st.text_area("Sửa và kiểm tra đoạn kiến thức trước khi lưu", height=180,
                                max_chars=4000, key="source_editor_" + lesson_id)
        confirmed = st.checkbox("Tôi đã đối chiếu đoạn này với đúng bài SGK đã chọn",
                                key="source_confirm_" + lesson_id)
        if st.button("Lưu nguồn đã kiểm tra", key="source_save_" + lesson_id):
            try:
                if not confirmed:
                    raise ValueError("Giáo viên cần xác nhận đã đối chiếu đúng bài.")
                save_reviewed_source(client, user_id=user_id, book_id=book_id,
                                     lesson_id=lesson_id, label=label, excerpt=reviewed,
                                     pdf_bytes=pdf_bytes, pdf_page=int(page) if pdf_bytes else None)
                st.success("Đã lưu kiến thức nguồn theo đúng bài SGK.")
                st.rerun()
            except Exception as exc:
                st.error(f"Chưa lưu được nguồn: {exc}")
    return excerpt, ref
