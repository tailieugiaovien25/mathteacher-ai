# MathTeacher AI — AI Open-Source Kernel V2

## Mục tiêu

Xây AI platform tự chạy, local-first và do ADMIN quản trị, trong đó model/runtime thay đổi được nhưng nghiệp vụ MathTeacher AI không phụ thuộc trực tiếp vào một model.

## Quy tắc bất biến

> Dữ liệu đổi nhưng hệ thống không đổi.

- AI Kernel không tự sửa code lõi.
- AI không tự nâng quyền.
- USER không được yêu cầu AI thực hiện hành động MUTATING/GOVERNANCE.
- ADMIN là chủ thể cấu hình model/provider/profile/policy.
- AI chỉ là advisory trong `Chuẩn hóa giáo án`; deterministic transformer vẫn là chủ thể sửa DOCX.
- Mỗi lần gọi AI qua Kernel phải có `audit_id`.

## Local-first model profiles hiện tại

- `qwen3:8b`: tác vụ tổng quát/tiếng Việt/toán/coding/agent nhẹ.
- `qwen3:30b`: tác vụ suy luận/agent nặng hơn.
- `deepseek-r1:32b`: chuyên suy luận/toán.
- `mistral-small3.1:24b`: tài liệu/đa phương thức.

Các model ID chỉ là profile mặc định; ADMIN có thể thay bằng profile đã duyệt mà không sửa nghiệp vụ.

## Chuẩn hóa giáo án

`DOCX -> Inventory/Fingerprint -> AI diagnosis -> Deterministic standardization -> Independent validation -> Before/After evidence`

AI không tự sửa file Word và không được tạo tiêu chí hình thức ngoài profile ADMIN.
