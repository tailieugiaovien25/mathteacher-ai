# Google Drive OAuth cho kho tài liệu giáo viên V2

## Phạm vi

- Mỗi giáo viên đăng nhập Supabase và tự kết nối tài khoản Google của mình.
- Hệ thống chỉ xin quyền `drive.file`, áp dụng cho các file do ứng dụng tạo hoặc mở.
- File Word, Excel và PDF được tải vào thư mục `MathTeacher-AI` trên Google Drive.
- Supabase chỉ lưu metadata và quyền sở hữu; file thật vẫn ở Google Drive.
- Thông tin OAuth chỉ nằm trong phiên Streamlit hiện tại, không ghi vào Git hoặc Supabase.
- Tham số OAuth `state` có chữ ký và hết hạn sau 10 phút, nên callback vẫn an toàn khi
  Google quay về một phiên Streamlit mới.
- PKCE `code_verifier` được tái tạo từ `state` có chữ ký và Client Secret, không ghi
  ra đĩa hoặc phụ thuộc vào phiên Streamlit.

## Biến môi trường

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID = Read-Host "Google OAuth Client ID"
$env:GOOGLE_OAUTH_CLIENT_SECRET = Read-Host "Google OAuth Client Secret"
$env:GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8501"
```

Không dán Client Secret vào mã nguồn, ảnh chụp, GitHub hoặc cuộc trò chuyện.

## Cấu hình Google Cloud

1. Bật Google Drive API cho dự án.
2. Cấu hình màn hình đồng ý OAuth và thêm tài khoản kiểm thử nếu ứng dụng còn ở chế độ Testing.
3. Tạo OAuth Client loại **Web application**.
4. Thêm Authorized redirect URI chính xác: `http://localhost:8501`.
5. Khởi động lại Streamlit sau khi đặt biến môi trường.

## Luồng lưu tài liệu

1. Giáo viên kết nối Google Drive.
2. Chọn file `.docx`, `.xlsx` hoặc `.pdf`, tối đa 25 MB.
3. Adapter tải file lên Drive.
4. Dịch vụ lưu metadata vào Supabase.
5. Nếu bước 4 thất bại, hệ thống cố gắng xóa file vừa tải để tránh file rác.
