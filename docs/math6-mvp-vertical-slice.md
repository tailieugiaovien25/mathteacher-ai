# Vertical slice MVP tạo đề Toán 6

Vertical slice này chứng minh luồng nghiệp vụ nhỏ nhất mà không cần credential
và không truy cập Supabase:

1. Tạo hoặc import câu hỏi Toán 6 vào kho in-memory.
2. Chỉnh sửa câu hỏi khi còn ở `DRAFT` hoặc `REVISION_REQUIRED`.
3. Gửi câu hỏi vào hàng đợi, ADMIN duyệt và khóa.
4. Tạo ma trận, gửi vào hàng đợi và ADMIN duyệt/khóa.
5. Lắp ráp đề xác định từ các câu hỏi đã duyệt và khóa.
6. Gửi đề vào hàng đợi và ADMIN duyệt.
7. ADMIN xuất bản snapshot bất biến, tạo mã đề `LOCKED`.
8. Kiểm tra hash snapshot và xuất ZIP để tải về.

## Phạm vi an toàn

- Toàn bộ trạng thái chỉ nằm trong bộ nhớ của tiến trình.
- Không đọc hoặc ghi database.
- Không gọi dịch vụ AI, Supabase, Google Drive hoặc API bên ngoài.
- Không thay thế workflow Supabase hiện hữu; đây là lát cắt tham chiếu và test
  hồi quy cho chuỗi trạng thái end-to-end.
- Gói ZIP tham chiếu dùng TXT/JSON. Luồng production hiện hữu tiếp tục chịu
  trách nhiệm render DOCX bằng bộ mẫu đã duyệt.

## Chạy màn hình Streamlit demo

Từ thư mục gốc repository:

```powershell
$env:PYTHONPATH = (Resolve-Path "src").Path
streamlit run scripts\math6_mvp_streamlit.py
```

Màn hình cho phép nạp/import JSON hoặc tạo câu hỏi, chỉnh sửa và gửi duyệt;
ADMIN duyệt/khóa câu hỏi và ma trận; tạo/duyệt/xuất bản đề; cuối cùng tải ZIP.
Các nút không hợp lệ được ẩn hoặc vô hiệu hóa theo trạng thái hiện tại.

## Chạy demo CLI

```powershell
$env:PYTHONPATH = (Resolve-Path "src").Path
python scripts\math6_mvp_demo.py
```

Kết quả được ghi vào:

```text
output/math6_mvp/math6-mvp-demo.zip
```

ZIP gồm:

- `de-kiem-tra.txt`
- `dap-an-huong-dan-cham.txt`
- `ma-tran-ban-dac-ta.json`
- `snapshot.json`
- `manifest.json` chứa hash của từng tệp và snapshot

## Chạy test không credential

```powershell
$env:PYTHONPATH = (Resolve-Path "src").Path
python -m pytest -q src\tests\test_math6_mvp_vertical_slice.py
```

Kiểm tra compile:

```powershell
python -m py_compile `
  src\assessment_generation_v2\services\math6_mvp_workflow.py `
  scripts\math6_mvp_demo.py `
  scripts\math6_mvp_streamlit.py `
  src\portal_v2\ui\math6_mvp_demo_streamlit.py `
  src\tests\test_math6_mvp_vertical_slice.py
```

## Điểm tích hợp production còn lại

Lát cắt này cố ý không thay đổi schema hoặc migration. Để đưa cùng workflow
vào portal Supabase, cần ánh xạ các thao tác in-memory sang bảng/RPC đã được
quản trị và RLS bảo vệ, sau đó nối các hàng đợi câu hỏi, ma trận và đề vào
navigation ADMIN. Chỉ thực hiện bước đó trong một thay đổi persistence được
phê duyệt riêng và có môi trường thử nghiệm Supabase.
