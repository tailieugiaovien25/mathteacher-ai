# Teacher Portal UI V2

## Mục tiêu

Cung cấp một điểm truy cập thống nhất cho các công cụ của giáo viên, dùng một
phiên đăng nhập Supabase và giữ nguyên ranh giới giữa giao diện, adapter và dịch vụ lõi.

## Các trang

- Tổng quan.
- Lịch báo giảng.
- Kho tài liệu và Google Drive.
- Chuẩn hóa giáo án Word.
- Hồ sơ giáo viên.

## Nguyên tắc

- Cổng chỉ điều phối giao diện và phiên đăng nhập.
- Mỗi tính năng tiếp tục dùng repository/adapter riêng.
- Không đưa khóa bí mật vào mã nguồn.
- Các ứng dụng thành phần tiếp tục chạy độc lập.

