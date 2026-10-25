# MathTeacher AI — Open Source AI V11: Runtime & Model Center

## Mục tiêu

V11 đưa lớp **AI Runtime/Model Center** về đúng quyền quản trị của ADMIN.

## Nguyên tắc bất biến

- AI Kernel/Governance không tự sửa.
- AI không tự đổi model/provider.
- AI không tự pull/xóa/cập nhật model local.
- Chỉ ADMIN được thay đổi active profile, allow-list và fallback profile.
- Runtime inspection là quan sát; không tạo side effect trên Ollama.

## Runtime flow

```text
ADMIN Runtime Center
  -> Model Registry
  -> Allow-list
  -> Active Profile
  -> Fallback Profiles
  -> Ollama Health
  -> Local Model Inventory
  -> AI Kernel Router
```

## Persistence

Cấu hình runtime được lưu local-first tại `.mathteacher_ai/runtime_config.json` hoặc đường dẫn từ `MATH_TEACHER_AI_RUNTIME_CONFIG`.

## Quy tắc an toàn

`active_profile_id` phải thuộc allow-list. Một profile đang active không thể bị tắt trước khi ADMIN chọn profile khác. Fallback chỉ được lấy từ profile đang bật và không trùng active.

## Chuẩn bị cho production

V11 chưa thực hiện pull/delete model tự động, chưa thay đổi Supabase schema và chưa coi runtime status là bằng chứng deployment production. Khi triển khai production, có thể thay persistence local bằng backend ADMIN-owned mà không thay đổi hợp đồng Kernel.
