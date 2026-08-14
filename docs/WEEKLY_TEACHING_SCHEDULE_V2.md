# Lịch báo giảng tự động theo tuần V2

## Phạm vi bản đầu

Lõi V2 nhận dữ liệu chuẩn đã được hệ thống xác thực:

- tuần năm học;
- thời khóa biểu có khoảng hiệu lực;
- PPCT theo từng lớp, môn và phân môn;
- nhật ký các tiết đã hoàn thành trước tuần cần tạo.

Lõi không đọc trực tiếp file Excel, không biết tên worksheet và không truy cập
Google Drive hoặc Supabase. Những nguồn này phải được chuyển thành các hợp đồng
dữ liệu chuẩn bởi adapter ở lớp ngoài.

## Quy tắc xác định tiết PPCT

Với mỗi bộ khóa `(lớp, môn, phân môn)`:

1. Đếm các bản ghi nhật ký có trạng thái `COMPLETED` và ngày dạy trước ngày đầu
   tuần.
2. Sắp xếp các tiết của tuần theo ngày và tiết thời khóa biểu.
3. Tiết PPCT cần lấy bằng số tiết đã hoàn thành cộng thứ tự xuất hiện trong
   tuần.
4. Tra PPCT để lấy tên bài, mã bài, thứ tự tiết trong bài và thiết bị.
5. Dừng với lỗi rõ ràng nếu không tìm thấy tiết PPCT hoặc có dữ liệu PPCT trùng.

## Điểm mở rộng tiếp theo

- adapter nhập tuần học, thời khóa biểu và PPCT từ giao diện/Excel;
- ngoại lệ ngày nghỉ, đổi tiết và dạy bù;
- giao diện chọn tuần và xem trước;
- exporter ghi lịch vào mẫu Excel/Word của giáo viên;
- lưu phiên bản và lịch sử xác nhận.

## Kiểm thử

Từ thư mục gốc dự án, chạy:

```powershell
$env:PYTHONPATH="src"
python -m pytest src/educational_planning_v2/tests/test_weekly_teaching_schedule_service.py -v
```

