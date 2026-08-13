# Công cụ vận hành workbook

Thư mục này chứa các công cụ hỗ trợ workbook, tách biệt khỏi mã nguồn
sản phẩm và bộ kiểm thử tự động.

## Nguyên tắc

1. Dữ liệu có thể thay đổi nhưng kiến trúc hệ thống không thay đổi.
2. Luôn chạy công cụ từ thư mục gốc của dự án.
3. Không chỉnh sửa trực tiếp workbook nguồn trong `data/input/`.
4. Mọi thao tác ghi phải dùng bản sao làm việc và có bản sao lưu.
5. Chạy công cụ kiểm tra hoặc mô phỏng trước công cụ bảo trì.
6. Không bật khóa ghi nếu chưa kiểm tra đầu vào, đầu ra và báo cáo dự kiến.

## Cấu trúc

### `audits/`

Kiểm kê cấu trúc, VBA, control, button và tính toàn vẹn của workbook. Một số
công cụ có thể tạo báo cáo văn bản trong `output/reports/`, nhưng không sửa
workbook nguồn.

### `inspectors/`

Đọc và hiển thị chi tiết về PPCT, TKB, LưuBG, YCCD, công thức, liên kết và
VBA. Các công cụ này phục vụ chẩn đoán thủ công.

### `validation/`

Tạo manifest hoặc báo cáo, mô phỏng thay đổi và xác minh kết quả. Nên chạy
nhóm này trước và sau một hoạt động bảo trì.

### `maintenance/`

Tạo bản sao làm việc, nhập dữ liệu hoặc áp dụng thay đổi lên bản sao. Các
công cụ này mặc định không ghi dữ liệu:

- Hai script nhập YCCD dùng `DRY_RUN = True`.
- Hai script áp dụng cleanup dùng `APPLY_CHANGES = False`.
- Script chuẩn bị workbook dùng `CREATE_COPIES = False`.

Chỉ đổi khóa tương ứng sau khi đã xem xét tệp nguồn, tệp đích, bản sao lưu và
kết quả validation. Sau khi hoàn tất, đưa khóa về giá trị an toàn mặc định.

## Cách chạy

Từ thư mục gốc dự án:

```bash
PYTHONPATH=src python scripts/workbook/<nhóm>/<tên_script>.py
```

Ví dụ kiểm tra cú pháp mà không thực thi nghiệp vụ:

```bash
python -m py_compile scripts/workbook/audits/*.py
python -m py_compile scripts/workbook/inspectors/*.py
python -m py_compile scripts/workbook/validation/*.py
python -m py_compile scripts/workbook/maintenance/*.py
```

## Kiểm tra an toàn

Các giá trị mặc định của script có khả năng ghi được bảo vệ bởi:

```bash
pytest -q src/tests/test_operational_scripts_safe_defaults.py
```

Không commit thay đổi bật chế độ ghi. Bộ kiểm thử phải trở về trạng thái đạt
trước khi tạo commit hoặc phát hành.
