# Lưu lịch báo giảng trên Supabase V2

## Nguyên tắc

- Ứng dụng giáo viên dùng `SUPABASE_PUBLISHABLE_KEY` và Supabase Auth.
- Không dùng secret key hoặc service-role key trong Streamlit.
- RLS giới hạn từng dòng theo `auth.uid()`.
- Repository vẫn lọc `user_id` trong truy vấn để tăng tính rõ ràng và hiệu năng.
- Lõi lập lịch không biết dữ liệu được lưu cục bộ hay trên Supabase.

## Tạo bảng

Mở SQL Editor của dự án Supabase và chạy toàn bộ tệp:

`supabase/migrations/202608140001_weekly_teaching_schedules.sql`

Migration tạo bảng, khóa chính `(user_id, schedule_id)`, chỉ mục, quyền cho vai
trò `authenticated` và bốn chính sách RLS cho đọc, thêm, sửa, xóa.

## Cấu hình PowerShell

Chỉ đặt biến trong cửa sổ PowerShell đang chạy:

```powershell
$env:SUPABASE_URL = "https://PROJECT_REF.supabase.co"
$env:SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."
$env:PYTHONPATH = (Resolve-Path ".\src").Path
streamlit run scripts/weekly_schedule/app.py
```

Không commit giá trị thật vào Git. `.env` đã nằm trong `.gitignore`.

## Chế độ hoạt động

- **Trên máy:** dùng `LocalWeeklyScheduleRepository` như trước.
- **Supabase:** đăng nhập bằng email và mật khẩu giáo viên; mọi thao tác dùng
  access token của giáo viên và chịu kiểm soát RLS.

Nếu chưa cấu hình Supabase, chế độ lưu trên máy vẫn hoạt động độc lập.
