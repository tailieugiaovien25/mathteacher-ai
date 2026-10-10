# MathTeacher AI — AI Skill Registry V4

AI Skill là hợp đồng chức năng nằm trên AI Kernel. Mỗi skill khai báo domain, capability và action được phép.

Nguyên tắc:

1. ADMIN là chủ quyền bật/tắt skill.
2. Skill không được tự tạo skill mới hoặc tự cấp quyền.
3. Chuẩn hóa giáo án dùng `document.standardization.audit`, chỉ READ_ONLY/ADVISORY.
4. Skill Marketing mặc định OFF.
5. Model/runtime thay đổi không làm thay đổi skill contract.
6. Code Kernel/Governance không được AI tự sửa.

Luồng chuẩn:

`User/System -> Skill Contract -> AI Kernel -> Model Router -> Provider -> Audit`
