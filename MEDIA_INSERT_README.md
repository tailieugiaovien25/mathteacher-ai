# Công cụ chèn ảnh/video vào slide hiện tại

## Tệp trong gói
- `src/portal_v2/ui/lesson_slide_designer.py`: thêm nút xanh nhạt trên thanh công cụ, hộp chọn ảnh/video, hiển thị media trên slide, kéo để di chuyển, kéo góc dưới-phải để đổi kích thước và nút `×` để xóa.
- `src/tests/test_lesson_slide_designer_media.py`: ba kiểm thử mới cho thêm, di chuyển, đổi kích thước, xóa và xuất HTML.

## Cài đặt
Giải nén gói tại thư mục gốc dự án, giữ nguyên cấu trúc thư mục. Chạy:

```powershell
python -m py_compile src\portal_v2\ui\lesson_slide_designer.py
python -m pytest src\tests\test_lesson_slide_designer.py src\tests\test_lesson_slide_designer_media.py -q
```

## Giới hạn dung lượng
Mã ứng dụng không đặt ngưỡng byte riêng cho nội dung ảnh/video. Tuy vậy, cấu hình Streamlit hiện tại giới hạn mỗi file tải lên ở 2 GiB và thông điệp ở 4 GiB; trình duyệt, bộ nhớ, database và hệ thống triển khai vẫn có giới hạn. Media đang được lưu inline dưới dạng base64 trong bản nháp JSON, vì vậy tệp video nhiều GB có thể tiêu tốn nhiều RAM và vượt giới hạn database. Để hỗ trợ video cực lớn một cách ổn định, cần chuyển media sang object storage (ví dụ bucket lưu trữ riêng) và chỉ lưu đường dẫn media trong bản nháp.
