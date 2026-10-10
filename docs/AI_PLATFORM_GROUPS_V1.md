# MathTeacher AI — AI Platform Runtime

## Provider mặc định

AI Platform ưu tiên **Ollama local** để giảm phụ thuộc dịch vụ trả phí:

```text
MATH_TEACHER_AI_PROVIDER=ollama
MATH_TEACHER_AI_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

Có thể đổi model Ollama sang model phù hợp với máy chủ. Model cụ thể cần tuân thủ giấy phép của model đó.

## AI Quản trị hệ thống

Mặc định tắt:

```text
SYSTEM_ADMIN_AI_ENABLED=false
```

Khi bật, AI chỉ phân tích/giải thích trạng thái. Các thao tác có hậu quả như xóa dữ liệu, sửa production, migration, deploy hoặc khôi phục phải do người quản trị thực hiện và xác nhận.

## AI Marketing

Mặc định khóa cho tới khi hệ thống chuyển sang thương mại:

```text
MATH_TEACHER_COMMERCIAL_MODE=false
MARKETING_AI_ENABLED=false
```

Cả hai điều kiện phải đúng thì runtime marketing mới hoạt động.

AI Marketing hiện chỉ tạo **bản nháp**. Không có quyền tự gửi chiến dịch, thay đổi giá, cam kết thương mại hoặc công bố nội dung.

## Nguyên tắc kiến trúc

```text
AI Group
   ↓
AI Platform Contract
   ↓
Provider Layer
   ↓
Ollama / provider khác
```

Lesson Designer không phụ thuộc hai AI mới. Provider Layer cũng không thay thế `document_intelligence`; đây là lớp dùng chung cho các AI nhóm mới và có thể mở rộng dần.

## Giai đoạn tiếp theo

- thêm health check Ollama;
- thêm model registry/capability registry;
- thêm audit event cho các yêu cầu admin;
- thêm approval queue cho marketing;
- chỉ khi có yêu cầu thương mại mới kết nối CRM/campaign provider.
