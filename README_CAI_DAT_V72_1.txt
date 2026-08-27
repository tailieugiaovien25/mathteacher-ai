MATHTEACHER-AI — V72.1
HOÀN THIỆN GỬI DUYỆT VÀ PHÊ DUYỆT MA TRẬN

Mục tiêu
1. Lưu nguyên tử các ô ma trận theo hồ sơ đánh giá đang hoạt động.
2. Bảo đảm tổng số câu, số ý, điểm từng phần và điểm từng mức độ khớp hồ sơ.
3. Giáo viên gửi phiên bản ma trận hoàn chỉnh để duyệt.
4. ADMIN khác chủ sở hữu phê duyệt, yêu cầu sửa hoặc từ chối.
5. Khi phê duyệt, trigger hiện có khóa phiên bản và kích hoạt ma trận.

Migration mới
supabase/migrations/202608270003_assessment_blueprint_cell_authoring.sql

RPC mới
- replace_assessment_blueprint_cells(uuid, jsonb)
- review_assessment_blueprint(uuid, text, text)

Luồng vận hành
Giáo viên lưu YCCĐ -> lưu ô ma trận -> gửi duyệt -> ADMIN ghi quyết định.
Quyết định APPROVED tự chuyển phiên bản sang APPROVED, đặt locked_at và
chuyển assessment_blueprints.lifecycle_status sang ACTIVE.

Không sử dụng service_role trong giao diện. Không ghi trực tiếp các bảng
ma trận hoặc duyệt từ UI; toàn bộ thay đổi đi qua RPC/trigger được quản trị.
