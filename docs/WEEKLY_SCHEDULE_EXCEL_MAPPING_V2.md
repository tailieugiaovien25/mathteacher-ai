# Ánh xạ file Excel nguồn V2

## Mục tiêu

Công cụ cho phép giáo viên sử dụng mẫu Excel của trường mà không phải đổi mã
nguồn. Giáo viên chọn sheet, dòng tiêu đề và cột tương ứng với bốn bảng chuẩn:
Tuần học, Thời khóa biểu, PPCT và Tiết đã dạy.

## Nguyên tắc

- Excel chỉ là dữ liệu đầu vào và luôn được mở ở chế độ chỉ đọc.
- Ánh xạ chuyển tên bảng/cột thay đổi thành mô hình dữ liệu chuẩn.
- Dịch vụ lập lịch không biết tên sheet, dòng tiêu đề hoặc thư viện Excel.
- Trường không bắt buộc có thể được đánh dấu là không có cột tương ứng.
- Hồ sơ ánh xạ được lưu riêng tại `data/weekly_schedule_mappings` và không đưa
  vào Git.
- Mỗi lần áp dụng, toàn bộ dữ liệu được kiểm tra trước khi tạo lịch.

## Cách sử dụng

1. Tải file `.xlsx` của trường lên giao diện.
2. Mở **Ánh xạ file Excel nguồn**.
3. Với từng bảng, chọn sheet và dòng chứa tiêu đề.
4. Ghép từng trường chuẩn với cột nguồn, rồi xem trước dữ liệu.
5. Nhập tên ánh xạ và chọn **Kiểm tra và áp dụng ánh xạ**.
6. Những lần sau có thể chọn hồ sơ đã lưu và áp dụng lại.

Nếu mẫu trường thay đổi tên sheet hoặc cột, giáo viên chỉ cập nhật hồ sơ ánh
xạ; thuật toán tạo lịch báo giảng không thay đổi.
