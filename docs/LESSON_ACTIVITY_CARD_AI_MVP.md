# Xưởng thẻ hoạt động có AI bản đầu

Trang `Thiết kế bài giảng` chỉ xuất hiện khi `MATHTEACHER_SLIDE_DESIGNER=1` trong khu vực giáo viên. Bản này phục vụ giáo viên soạn và xem trước tại máy, chưa công bố cho học sinh, chưa ghi vào Supabase. Bản nháp lưu trong phiên Streamlit và được tải ra JSON để mở lại.

## Luồng ba vòng

1. Giáo viên chọn môn, lớp, sách và bài SGK ACTIVE. Hệ thống lấy YCCĐ qua RPC đề xuất đã rà soát và lấy câu hỏi của chính giáo viên ở trạng thái `APPROVED`, có metadata nối đúng bài và sách. Nếu YCCĐ không có, giao diện nêu rõ; không tự gán YCCĐ từ tên bài. Danh sách câu hỏi có giới hạn 500 dòng; vượt giới hạn sẽ yêu cầu phân trang ở bước sau.
2. Giáo viên chọn YCCĐ, dán đoạn kiến thức đã đối chiếu với nguồn và xác nhận. AI chỉ nhận đoạn trích, YCCĐ đã chọn và tối đa 10 câu hỏi đã duyệt. AI đề xuất thẻ `TASK` (Giao nhiệm vụ), và nếu có câu phù hợp, thẻ `QUICK_CHECK` (Kiểm tra nhanh). Kết quả trả về bị kiểm tra ID bài, YCCĐ, phiên bản câu hỏi, loại hoạt động và nguồn trích dẫn. Nội dung câu hỏi được lấy lại từ bản đã duyệt, không dùng câu AI viết lại.
3. Giáo viên giữ, sửa hoặc bỏ từng đề xuất. Chỉ nút `Duyệt và thêm vào bài` đưa thẻ vào JSON của bài giảng. Đề xuất lại không sửa thẻ giáo viên đã duyệt. Bản xem trước của học sinh chỉ hiện tiêu đề và nhiệm vụ; ghi chú riêng không nằm trong HTML trình chiếu.

`GEMINI_API_KEY` được đọc ở máy chủ Streamlit từ secrets hoặc biến môi trường; `LESSON_CARD_GEMINI_MODEL` là tùy chọn. API chỉ được gọi khi giáo viên bấm tạo đề xuất. Không gửi dữ liệu học sinh, đáp án hay lời giải tới AI. Nếu thiếu cấu hình hoặc nguồn kiến thức đủ rõ, thông báo lỗi thay vì tự tạo liên kết dữ liệu.

## Việc chưa có trong bản này

- Lưu, phân quyền và công bố bản bài giảng trên Supabase; quản lý phiên bản chính thức.
- Tự đồng bộ lịch báo giảng/PPCT với bài đã chọn; hiện mới gắn ID bài SGK đã tra từ danh mục.
- Tạo hoặc kiểm định ảnh bằng AI, tìm giấy phép học liệu, tải lên kho ảnh; tránh tự đưa ảnh mạng vào bài giảng.
- Chạy nhiệm vụ và thu phản hồi từ học sinh; thẻ hiện chỉ tạo sản phẩm soạn bài và bản xem trước.
- Trình chiếu offline: reveal.js hiện tải từ CDN.

## Kiểm tra bằng bài Toán 6

1. Chọn sách và bài có trong danh mục; nhập đoạn kiến thức đã đối chiếu (tối thiểu 80 ký tự).
2. Bấm AI đề xuất; xác nhận mỗi thẻ có `lesson:<id>` và `teacher_excerpt:<hash>`. Nếu có câu phù hợp, thẻ Kiểm tra nhanh phải có `question:<version_id>`.
3. Sửa thẻ Giao nhiệm vụ, duyệt; đề xuất lại và xác nhận thẻ đã duyệt không thay đổi.
4. Xem trước: ghi chú giáo viên và đáp án không được xuất hiện. Tải JSON, mở lại, kiểm tra cùng ID bài SGK và nguồn trích.
