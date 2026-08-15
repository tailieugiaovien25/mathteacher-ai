# Kho tài liệu cá nhân của giáo viên V2

## Phạm vi đầu tiên

- Mỗi tài liệu thuộc đúng một tài khoản giáo viên.
- Phân loại theo năm học, môn, khối/lớp và loại tài liệu.
- Sáu loại tài liệu: giáo án, kế hoạch giáo dục, ma trận, bản đặc tả, đề kiểm
  tra và hướng dẫn chấm.
- Supabase lưu metadata; file thực tế nằm trên Google Drive.
- Tìm kiếm theo tên, mô tả, nhãn và lọc theo các trường chuẩn.

## Ranh giới kiến trúc

`TeacherDocument` và `TeacherDocumentCatalog` không phụ thuộc Supabase,
Google Drive hay Streamlit. `SupabaseTeacherDocumentRepository` chỉ là adapter
metadata. Việc tải file trực tiếp bằng OAuth sẽ dùng một adapter lưu trữ riêng.

Migration bật RLS và chỉ cho phép tài khoản đã xác thực đọc, thêm, sửa hoặc xóa
bản ghi có `user_id` của chính tài khoản đó. Giao diện chỉ dùng publishable key,
không dùng secret key hay service-role key.
