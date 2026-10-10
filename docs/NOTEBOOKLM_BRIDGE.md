# NotebookLM Bridge — MathTeacher AI

## Phạm vi

Bridge tạo gói nguồn từ các tài liệu giáo viên đã chọn trong `teacher_document_library_v2`. Gói gồm bản sao file gốc, chỉ mục Markdown, manifest JSON/CSV, mã SHA-256 và các mẫu câu lệnh tiếng Việt cho NotebookLM.

**Đây là cầu nối xuất nguồn cho NotebookLM cá nhân**, không phải API tự động tạo notebook hoặc tải nguồn qua giao diện riêng tư. Giáo viên giải nén ZIP rồi thêm từng file trong `sources/` vào notebook trên https://notebooklm.google.com/.

## Dùng trong ứng dụng

1. Mở Thư viện học liệu từ MathTeacher AI.
2. Đăng nhập kho tài liệu và kết nối Google Drive như quy trình hiện tại.
3. Lọc danh sách theo môn, khối, sách hoặc bài học.
4. Mở `Tạo gói nguồn cho NotebookLM`, chọn tài liệu, bấm `Tạo gói nguồn NotebookLM`.
5. Tải ZIP, giải nén và thêm các file nguồn phù hợp vào NotebookLM.
6. Dùng `NOTEBOOKLM_PROMPTS_VI.md` để thử hỏi đáp theo nguồn, tạo hướng dẫn học tập, câu hỏi ôn tập, phân tích sai lầm, sơ đồ tư duy hoặc Audio Overview nếu chức năng đó có trong tài khoản.

## An toàn và giới hạn

- Bridge chỉ tải bản sao những tài liệu giáo viên đã chọn; không sửa/xóa file gốc hay metadata.
- Chỉ nguồn có `storage_provider` bắt đầu bằng `google_drive` mới được đưa qua adapter Google Drive đang kết nối.
- Từng nguồn tải lỗi được báo trong manifest/README; nếu tất cả nguồn đều lỗi thì không tạo gói.
- Gói có giới hạn tổng dữ liệu mặc định 100 MiB để tránh tạo file quá lớn trong phiên Streamlit.
- Trước khi thêm vào notebook, giáo viên cần kiểm tra nội dung, quyền sử dụng, thông tin cá nhân và mức phù hợp của nguồn.
- API Gemini Notebook/NotebookLM Enterprise không được dùng thay thế cho NotebookLM cá nhân trong bridge này.

## Kiểm thử

```powershell
$env:PYTHONPATH = "src"
python -m pytest src/tests/test_notebooklm_bridge_source_pack.py -q
```
