"""Learning material catalog UI using the existing teacher document store."""
from __future__ import annotations

from dataclasses import replace
from pathlib import PurePath
from datetime import date
from teacher_document_library_v2 import DocumentCategory, DocumentUploadMetadata, TeacherDocument

MAX_BYTES = 25 * 1024 * 1024
FORMATS = {
    'png': ('Ảnh', 'image/png'), 'jpg': ('Ảnh', 'image/jpeg'), 'jpeg': ('Ảnh', 'image/jpeg'),
    'gif': ('Ảnh', 'image/gif'), 'webp': ('Ảnh', 'image/webp'), 'bmp': ('Ảnh', 'image/bmp'),
    'mp3': ('Âm thanh', 'audio/mpeg'), 'wav': ('Âm thanh', 'audio/wav'),
    'ogg': ('Âm thanh', 'audio/ogg'), 'm4a': ('Âm thanh', 'audio/mp4'),
    'mp4': ('Video', 'video/mp4'), 'webm': ('Video', 'video/webm'), 'mov': ('Video', 'video/quicktime'),
    'ppt': ('PowerPoint', 'application/vnd.ms-powerpoint'),
    'pptx': ('PowerPoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'),
    'pps': ('PowerPoint', 'application/vnd.ms-powerpoint'),
    'ppsx': ('PowerPoint', 'application/vnd.openxmlformats-officedocument.presentationml.slideshow'),
    'pptm': ('PowerPoint', 'application/vnd.ms-powerpoint.presentation.macroEnabled.12'),
    'pdf': ('Tài liệu', 'application/pdf'), 'doc': ('Tài liệu', 'application/msword'),
    'docx': ('Tài liệu', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    'xls': ('Tài liệu', 'application/vnd.ms-excel'),
    'xlsx': ('Tài liệu', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    'txt': ('Tài liệu', 'text/plain'),
}
PREFIX = 'mt_material_v1:'
FIELDS = ('book', 'lesson', 'activity', 'origin')
ORIGINS = ('Giáo viên tải lên', 'AI', 'Internet')


def file_format(name):
    name = str(name)
    if not name or '/' in name or '\\' in name or len(name) > 255:
        raise ValueError('Tên tệp không hợp lệ.')
    extension = PurePath(name).suffix.lower().lstrip('.')
    if extension not in FORMATS:
        raise ValueError('Định dạng tệp chưa được hỗ trợ.')
    return FORMATS[extension]


def read_metadata(document):
    result = {field: '' for field in FIELDS}
    labels = []
    for tag in document.tags:
        if tag.startswith(PREFIX):
            key, separator, value = tag[len(PREFIX):].partition('=')
            if separator and key in FIELDS:
                result[key] = value
        else:
            labels.append(tag)
    result['labels'] = ', '.join(labels)
    return result


def make_tags(labels='', **values):
    tags = []
    for tag in str(labels).split(','):
        tag = tag.strip()
        if tag.startswith(PREFIX):
            raise ValueError('Nhãn không được bắt đầu bằng mt_material_v1:.')
        if tag:
            tags.append(tag)
    for key in FIELDS:
        value = str(values.get(key, '')).strip()
        if value:
            tags.append(f'{PREFIX}{key}={value}')
    if any(len(tag) > 100 for tag in tags):
        raise ValueError('Thông tin SGK, bài, hoạt động hoặc nhãn quá dài (tối đa 100 ký tự mỗi nhãn).')
    return tuple(dict.fromkeys(tags))


def material_kind(document):
    try:
        return file_format(document.file_name)[0]
    except ValueError:
        return 'Tài liệu'


def filter_materials(documents, *, query='', subject='', grade='', kind='', book='', lesson=''):
    result = []
    for item in documents:
        meta = read_metadata(item)
        if subject and item.subject != subject or grade and item.grade_level != grade:
            continue
        if kind and material_kind(item) != kind or book and meta['book'] != book or lesson and meta['lesson'] != lesson:
            continue
        haystack = ' '.join((item.title, item.file_name, item.description or '', item.subject, item.grade_level, *item.tags))
        if query.strip().casefold() not in haystack.casefold():
            continue
        result.append(item)
    return tuple(result)


def metadata_inputs(st, key, document=None):
    meta = read_metadata(document) if document else dict.fromkeys((*FIELDS, 'labels'), '')
    left, right = st.columns(2)
    title = left.text_input('Tên học liệu *', value=document.title if document else '', key=key+'title')
    subject = right.text_input('Môn *', value=document.subject if document else 'Toán', key=key+'subject')
    left, right = st.columns(2)
    grade = left.text_input('Khối *', value=document.grade_level if document else '6', key=key+'grade')
    today = date.today()
    year = today.year if today.month >= 8 else today.year - 1
    academic_year = right.text_input('Năm học *', value=document.academic_year if document else f'{year}-{year+1}', key=key+'year')
    book = st.text_input('Sách giáo khoa', value=meta['book'], key=key+'book')
    lesson = st.text_input('Bài học', value=meta['lesson'], key=key+'lesson')
    activity = st.text_input('Hoạt động', value=meta['activity'], key=key+'activity')
    origin_value = meta['origin'] if meta['origin'] in ORIGINS else ORIGINS[0]
    origin = st.selectbox('Nguồn học liệu', ORIGINS, index=ORIGINS.index(origin_value), key=key+'origin')
    description = st.text_area('Mô tả / nguồn tham khảo', value=(document.description or '') if document else '', key=key+'description')
    labels = st.text_input('Nhãn (cách nhau bằng dấu phẩy)', value=meta['labels'], key=key+'labels')
    return dict(title=title, subject=subject, grade_level=grade, academic_year=academic_year,
                description=description, labels=labels, book=book, lesson=lesson, activity=activity, origin=origin)


def validated_metadata(values, document=None):
    tags = make_tags(**{key: values[key] for key in ('labels', *FIELDS)})
    fields = {key: values[key] for key in ('title', 'subject', 'grade_level', 'academic_year', 'description')}
    # Validate before uploading bytes, so invalid metadata cannot leave an orphan file.
    candidate = replace(document, **fields, tags=tags) if document else TeacherDocument(
        document_id='00000000-0000-0000-0000-000000000001', category=DocumentCategory.LESSON_PLAN,
        class_name=None, file_name='validation.txt', mime_type='text/plain', size_bytes=0,
        storage_provider='google_drive', storage_file_id='validation', tags=tags, **fields)
    return candidate, DocumentUploadMetadata(category=candidate.category, class_name=candidate.class_name, tags=tags, **fields)


def render_library(st, catalog, storage=None):
    st.subheader('📚 Thư viện học liệu')
    notice = st.session_state.pop('material_notice', '')
    if notice:
        st.success(notice)
    with st.expander('⬆ Tải học liệu lên', expanded=False):
        if storage is None:
            st.info('Kết nối Google Drive ở thanh bên để tải lên và xem trước học liệu.')
        else:
            with st.form('material_upload'):
                uploaded = st.file_uploader('Chọn ảnh, âm thanh, video, PowerPoint hoặc tài liệu', type=list(FORMATS))
                st.caption('Tối đa 25 MB/tệp. PowerPoint được giữ nguyên tệp gốc và hiệu ứng.')
                values = metadata_inputs(st, 'material_new_')
                submit = st.form_submit_button('⬆ Tải lên và lưu học liệu')
            if submit:
                try:
                    if uploaded is None:
                        raise ValueError('Hãy chọn tệp học liệu.')
                    content = uploaded.getvalue()
                    if not content or len(content) > MAX_BYTES:
                        raise ValueError('Tệp phải có nội dung và không vượt quá 25 MB.')
                    _, mime = file_format(uploaded.name)
                    _, metadata = validated_metadata(values)
                    from teacher_document_library_v2 import TeacherDocumentUploadService
                    TeacherDocumentUploadService(catalog, storage).upload(content=content, file_name=uploaded.name, mime_type=mime, metadata=metadata)
                    st.session_state['material_notice'] = 'Đã lưu học liệu vào thư viện.'
                    st.rerun()
                except Exception as error:
                    st.error(f'Không thể tải lên: {error}')
    try:
        all_items = catalog.search()
    except Exception as error:
        st.error(f'Không thể đọc thư viện: {error}')
        return
    query = st.text_input('🔎 Tìm học liệu', placeholder='Tên, bài học, hoạt động hoặc nhãn', key='material_query')
    def choose(container, label, values, key):
        selected = container.selectbox(label, ('Tất cả', *sorted(set(value for value in values if value))), key=key)
        return '' if selected == 'Tất cả' else selected
    a, b, c = st.columns(3)
    subject = choose(a, 'Môn', [item.subject for item in all_items], 'material_filter_subject')
    subject_items = filter_materials(all_items, subject=subject)
    grade = choose(b, 'Khối', [item.grade_level for item in subject_items], 'material_filter_grade')
    kind = choose(c, 'Loại học liệu', [material_kind(item) for item in all_items], 'material_filter_kind')
    context_items = filter_materials(subject_items, grade=grade)
    a, b = st.columns(2)
    book = choose(a, 'Sách giáo khoa', [read_metadata(item)['book'] for item in context_items], 'material_filter_book')
    lesson_items = filter_materials(context_items, book=book)
    lesson = choose(b, 'Bài học', [read_metadata(item)['lesson'] for item in lesson_items], 'material_filter_lesson')
    items = filter_materials(all_items, query=query, subject=subject, grade=grade, kind=kind, book=book, lesson=lesson)
    st.caption(f'{len(items)} học liệu')
    for item in items:
        meta = read_metadata(item)
        with st.expander(f'{material_kind(item)} · {item.title}'):
            st.caption(' · '.join(str(value) for value in (item.subject, 'Khối '+item.grade_level, meta['book'], meta['lesson'], meta['activity']) if value))
            st.write(item.description or 'Chưa có mô tả.')
            if meta['labels']:
                st.caption('Nhãn: '+meta['labels'])
            st.caption(f'{item.file_name} · {item.size_bytes / 1024 / 1024:.2f} MB · {meta["origin"] or "Chưa ghi nguồn"}')
            if item.web_view_link:
                st.link_button('↗ Mở tệp trên Drive', item.web_view_link)
            if storage and item.storage_provider == 'google_drive_oauth':
                if st.button('▶ Xem trước / tải xuống', key='material_preview_'+item.document_id):
                    try:
                        content = storage.download(item.storage_file_id)
                        kind_value = material_kind(item)
                        if kind_value == 'Ảnh':
                            st.image(content)
                        elif kind_value == 'Âm thanh':
                            st.audio(content, format=item.mime_type)
                        elif kind_value == 'Video':
                            st.video(content, format=item.mime_type)
                        elif kind_value == 'PowerPoint':
                            st.info('Tải tệp và mở bằng PowerPoint để giữ hiệu ứng và âm thanh gốc.')
                        else:
                            st.info('Tải tệp để xem bằng ứng dụng tương ứng.')
                        st.download_button('⬇ Tải tệp gốc', content, file_name=item.file_name, mime=item.mime_type, key='material_download_'+item.document_id)
                    except Exception as error:
                        st.error(f'Không thể mở tệp: {error}')
            with st.form('material_edit_'+item.document_id):
                values = metadata_inputs(st, 'material_edit_'+item.document_id, item)
                save = st.form_submit_button('💾 Lưu thông tin')
            if save:
                try:
                    updated, _ = validated_metadata(values, item)
                    catalog.save(updated)
                    st.session_state['material_notice'] = 'Đã cập nhật thông tin học liệu.'
                    st.rerun()
                except Exception as error:
                    st.error(f'Không thể lưu: {error}')
            confirm = st.checkbox('Xác nhận xóa học liệu khỏi thư viện', key='material_confirm_'+item.document_id)
            if st.button('🗑 Xóa khỏi thư viện', key='material_delete_'+item.document_id, disabled=not confirm):
                try:
                    if not catalog.delete(item.document_id):
                        raise ValueError('Học liệu không còn trong thư viện hoặc chưa xóa được.')
                    st.session_state['material_notice'] = 'Đã xóa khỏi thư viện. Tệp gốc vẫn được giữ trên Drive.'
                    st.rerun()
                except Exception as error:
                    st.error(f'Không thể xóa: {error}')

    # NOTEBOOKLM_BRIDGE_V1: prepare a portable source pack for personal NotebookLM.
    # This does not call or automate NotebookLM's private consumer interface.
    st.divider()
    with st.expander('🧠 Tạo gói nguồn cho NotebookLM', expanded=False):
        st.write(
            'Chọn các học liệu phù hợp với một bài học/chủ đề. MathTeacher AI sẽ tải bản sao từ Google Drive '
            'và đóng gói tệp gốc cùng chỉ mục, metadata và mẫu câu lệnh tiếng Việt.'
        )
        st.caption(
            'Gói ZIP là gói trung chuyển: cần giải nén, sau đó thêm từng tệp nguồn vào NotebookLM. '
            'Tài liệu gốc trong kho không bị sửa hoặc xóa.'
        )
        if storage is None:
            st.info('Hãy kết nối Google Drive ở thanh bên để tạo gói nguồn.')
        elif not items:
            st.info('Không có học liệu phù hợp bộ lọc hiện tại.')
        else:
            label_to_document = {
                f'{item.title} · {item.file_name} · {item.document_id[:8]}': item
                for item in items
            }
            selected_labels = st.multiselect(
                'Chọn nguồn đưa vào gói',
                options=list(label_to_document),
                key='notebooklm_bridge_selected_sources_v1',
                help='Chỉ các tài liệu bạn chọn mới được tải xuống và đóng gói.',
            )
            if st.button(
                '📦 Tạo gói nguồn NotebookLM',
                key='notebooklm_bridge_build_package_v1',
                disabled=not selected_labels,
                use_container_width=True,
            ):
                try:
                    from notebooklm_bridge import build_notebooklm_source_pack

                    selected_documents = tuple(label_to_document[label] for label in selected_labels)

                    def download_selected(document):
                        if not str(document.storage_provider).casefold().startswith('google_drive'):
                            raise ValueError(
                                'Tài liệu không thuộc Google Drive đã kết nối; hãy tải lên Drive hoặc chọn nguồn Drive.'
                            )
                        return storage.download(document.storage_file_id)

                    with st.spinner('Đang tải bản sao các nguồn và tạo gói…'):
                        pack = build_notebooklm_source_pack(
                            selected_documents,
                            download_selected,
                        )
                    st.session_state['notebooklm_bridge_pack_v1'] = {
                        'filename': pack.filename,
                        'content': pack.content,
                        'included_count': len(pack.included_sources),
                        'failed_sources': [dict(row) for row in pack.failed_sources],
                    }
                except Exception as error:
                    st.error(f'Không tạo được gói NotebookLM: {error}')

            pack_state = st.session_state.get('notebooklm_bridge_pack_v1')
            if pack_state:
                st.success(
                    f"Đã chuẩn bị {pack_state['included_count']} nguồn. "
                    'Gói có chỉ mục, metadata, mã kiểm tra tệp và các mẫu câu lệnh tiếng Việt.'
                )
                st.download_button(
                    '⬇ Tải gói nguồn NotebookLM (.zip)',
                    data=pack_state['content'],
                    file_name=pack_state['filename'],
                    mime='application/zip',
                    key='notebooklm_bridge_download_package_v1',
                    use_container_width=True,
                )
                if pack_state['failed_sources']:
                    st.warning(
                        f"Có {len(pack_state['failed_sources'])} nguồn không tải được; "
                        'hãy kiểm tra quyền Drive hoặc cấu hình kho tài liệu.'
                    )
                    with st.expander('Chi tiết nguồn chưa đóng gói'):
                        for failed in pack_state['failed_sources']:
                            st.write(f"- {failed['title']} ({failed['file_name']}): {failed['error']}")
