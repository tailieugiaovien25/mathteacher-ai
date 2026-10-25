# MathTeacher AI

**Nền tảng AI hỗ trợ giáo viên Toán THCS — ưu tiên mã nguồn mở, chạy cục bộ và quản trị tập trung.**

## Phiên bản

**v0.1.0 — First Public Checkpoint**

Checkpoint này xác nhận nền tảng đã có:
- Teacher Document Library
- Shared Knowledge Library
- Cầu nối Teacher Document → Shared Knowledge
- Quản lý trạng thái đồng bộ theo từng đích
- Local Knowledge Sync dry-run
- NotebookLM adapter tùy chọn
- Kiểm thử tích hợp Shared Knowledge + NotebookLM
- Quản trị AI tập trung bởi ADMIN

## Kiến trúc tri thức

```text
Teacher Document Library
          |
          v
Shared Knowledge Library
       /       \
      v         v
  Local KB   NotebookLM
```

## Vertical slice MVP tạo đề Toán 6

Luồng tham chiếu hỗ trợ nhập và chỉnh sửa câu hỏi, ADMIN duyệt và khóa, duyệt ma trận, tạo và duyệt đề, xuất bản snapshot, khóa mã đề và tạo ZIP.

Chi tiết: [docs/math6-mvp-vertical-slice.md](docs/math6-mvp-vertical-slice.md).

## NotebookLM Bridge (tùy chọn)

NotebookLM Bridge hỗ trợ chuẩn bị gói tài liệu để giáo viên đưa vào NotebookLM cá nhân. Đây là adapter tùy chọn, không phải thành phần cốt lõi bắt buộc của nền tảng.

Bridge không gọi API riêng tư hoặc tự động điều khiển giao diện NotebookLM cá nhân.

Chi tiết: [docs/NOTEBOOKLM_BRIDGE.md](docs/NOTEBOOKLM_BRIDGE.md).

## Quy tắc an toàn khi phát triển

- Không commit môi trường ảo, thư mục `__pycache__`, file đầu ra hoặc audit không phù hợp.
- Không đưa dữ liệu cá nhân hay tài liệu nhạy cảm vào repository công khai.
- Chạy kiểm thử trước khi commit.
- AI Kernel và AI Platform thuộc quyền quản trị của ADMIN. AI chức năng không tự ý thay đổi kiến trúc lõi, quyền truy cập, cấu hình quản trị hoặc dữ liệu production ngoài cơ chế được ADMIN phê duyệt.
