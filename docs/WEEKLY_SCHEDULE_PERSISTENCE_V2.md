# Lưu lịch báo giảng V2

## Mục tiêu

Lưu và mở lại lịch báo giảng theo giáo viên, năm học và tuần mà không làm lõi
lập lịch phụ thuộc vào nơi lưu dữ liệu.

## Thiết kế

- `WeeklyScheduleRepository` là cổng lưu trữ của hệ thống.
- `LocalWeeklyScheduleRepository` là adapter JSON dùng trong giai đoạn thử nghiệm.
- Cùng một `schedule_id` được cập nhật, không tạo bản trùng.
- Ghi tệp theo cơ chế thay thế nguyên tử để hạn chế tệp dở dang.
- Tên tệp được kiểm tra để ngăn đường dẫn không an toàn.
- Mỗi giáo viên chỉ xem danh sách lịch của chính mã giáo viên đó.

Supabase repository trong giai đoạn sau sẽ triển khai cùng contract. Dịch vụ
`WeeklyTeachingScheduleService` và mô hình lịch không cần thay đổi.

## Dữ liệu cục bộ

Giao diện mặc định lưu tại `data/weekly_schedules`. Đây là dữ liệu vận hành của
người dùng, không phải mã nguồn và không nên đưa vào Git.
