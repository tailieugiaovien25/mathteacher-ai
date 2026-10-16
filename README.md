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