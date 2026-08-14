# Hồ sơ giáo viên Supabase V2

## Mục tiêu

Thông tin giáo viên được nhập trong giao diện và lưu theo tài khoản đã đăng
nhập. Excel tiếp tục chỉ cung cấp các bảng dữ liệu như thời khóa biểu và PPCT.

## Trường dữ liệu

- Mã giáo viên.
- Họ và tên.
- Trường công tác.
- Môn giảng dạy.
- Khối/lớp phụ trách.
- Năm học mặc định.
- Tùy chọn hiển thị họ tên và trường trên lịch báo giảng.

Không lưu email đăng nhập, mật khẩu hoặc khóa API trong bảng hồ sơ.

## Bảo mật

Migration `supabase/migrations/202608150001_teacher_profiles.sql` tạo bảng có
khóa chính `user_id`, bật RLS và giới hạn mọi thao tác theo `auth.uid()`.
Ứng dụng vẫn dùng publishable key và access token của giáo viên.

## Luồng giao diện

1. Giáo viên đăng nhập Supabase.
2. Nếu chưa có hồ sơ, hệ thống yêu cầu tạo hồ sơ trước khi lập lịch.
3. Mã giáo viên trong hồ sơ phải trùng mã trong bảng Thời khóa biểu.
4. Năm học mặc định được chọn tự động nếu có trong dữ liệu nguồn.
5. Tùy chọn hiển thị được đưa vào metadata của lịch và tệp Excel xuất ra.

Nhờ repository contract, mô hình hồ sơ không phụ thuộc Supabase và có thể dùng
với bộ lưu khác sau này.
