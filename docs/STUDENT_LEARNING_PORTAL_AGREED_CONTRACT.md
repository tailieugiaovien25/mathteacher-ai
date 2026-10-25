# Hợp đồng triển khai giao diện học tập MathTeacherAI

Nguồn: *Biên bản thống nhất xây dựng giao diện học tập*, ngày 28/09/2026, do người dùng cung cấp. Tài liệu này chuyển quyết định trong biên bản thành phạm vi có thể kiểm tra trong mã nguồn; không thay thế biên bản.

## Quyết định đã thống nhất

- Cổng học sinh tách khỏi khu vực giáo viên và Admin. Hai không gian **Lớp học** và **Cá nhân tự học** dùng chung danh mục lớp, môn, TKB đang hoạt động, PPCT, SGK, YCCĐ, học liệu và nhiệm vụ. Toán và Tiếng Anh là hai môn đầu tiên; thêm môn không cần tạo cấu trúc dữ liệu riêng.
- Giáo viên quyết định nội dung và phạm vi công bố. Học sinh chỉ đọc phiên bản đã công bố cho lớp hoặc cá nhân của mình. Nội dung mới hoặc bản nháp không đi thẳng sang giao diện học sinh.
- Kho học liệu giữ bản gốc của PDF, DOCX, ảnh, âm thanh, video và PPTX. Bản xem nhanh, video hoặc ảnh slide là các phiên bản dẫn xuất, không ghi đè file gốc. Câu hỏi và tiến độ học là dữ liệu có cấu trúc độc lập với hiệu ứng PPTX.
- PPTX giữ được đường mở file gốc; trình chiếu có hiệu ứng qua PowerPoint Online/Live được xem xét theo điều kiện tài khoản và hạ tầng. Video xuất từ PPTX phục vụ tự học; PDF hoặc ảnh slide là bản xem nhẹ. ONLYOFFICE, H5P và SCORM là các lựa chọn nghiên cứu sau.
- Bài giảng HTML5 do MathTeacherAI tạo là **một loại học liệu**, không thay thế hoặc chuyển đổi bắt buộc các PPTX có sẵn. Khối soạn và trình chiếu HTML5 được dùng lại trong hai không gian khi có quyền công bố.

## Ranh giới hiện tại

`lesson_slide_designer.py` là bản nháp dành cho giáo viên: bốn hoạt động, slide, khối nội dung, bản xem trước reveal.js và nhập/xuất JSON. Mã SGK nhập thủ công hiện chỉ là tham chiếu chưa được xác thực. Bản xem trước tải reveal.js từ CDN và cần mạng. Không dùng JSON tải xuống làm căn cứ cấp quyền xem cho học sinh, không coi bản xem trước là một bản đã công bố.

Ứng dụng hiện chỉ có vai trò `teacher` và `admin` trong `portal_v2.authorization`. Vì vậy không mở route học sinh hoặc truy vấn học liệu bằng vai trò giáo viên rồi lọc ở giao diện. Trước khi có Student Portal phải thiết kế danh tính học sinh, liên kết lớp, kiểm soát đọc ở CSDL và Storage, cùng kiểm thử quyền theo tài khoản thực.

## Thứ tự triển khai tiếp

| Bước | Công việc | Điều kiện hoàn thành |
| --- | --- | --- |
| 1 | Ổn định đề kiểm tra và ngân hàng câu hỏi Toán 6–9 | Luồng duyệt và dữ liệu nguồn kiểm thử được trên canonical. |
| 2 | Mô hình bài giảng và học liệu dùng chung | Bài, hoạt động, slide, asset, nguồn, phiên bản; giữ file gốc và liên kết PPCT/SGK/YCCĐ hợp lệ. |
| 3 | Lưu nháp và công bố của giáo viên | Có quyền sở hữu, kiểm tra bản phát hành, lịch sử phiên bản, thu hồi và nhật ký; không lộ ghi chú/đáp án giáo viên. |
| 4 | Danh tính học sinh và hai không gian | Học sinh chỉ thấy đúng lớp và bản được giao; trang chủ lấy TKB/PPCT và nhiệm vụ từ nguồn có thẩm quyền. |
| 5 | Tiến độ và câu hỏi nhanh | Lưu lần học, vị trí tiếp tục; một câu từ ngân hàng đã duyệt không mang đáp án trong payload học sinh. |
| 6 | Nhiều định dạng và AI Tutor | PPTX nhiều cách xem, video, tương tác; AI chỉ dùng tài liệu đã được giáo viên công bố. |

## Dữ liệu bài giảng tối thiểu trước khi lưu CSDL

`subject_id`, `grade_id`, `textbook_id`, `textbook_unit_id`, `ppct_period_id`, `requirement_codes`, `owner_user_id`, `lesson_type`, `activity_type`, `slide_order`, `block_kind`, `display_rule`, `asset_id`, `version_number`, `status`, `published_at`. Mỗi khóa ngoại phải được đối chiếu với nguồn đang hoạt động và quyền sở hữu tương ứng; không suy ra danh tính từ chuỗi do giáo viên tự nhập. Trạng thái cần phân biệt nháp, đang duyệt nếu có, đã công bố và thu hồi.

## Kiểm tra trước khi công bố cho học sinh

1. Giáo viên chỉ sửa bài của mình; bản đã công bố bất biến, sửa tạo phiên bản mới.
2. Tài khoản học sinh ngoài lớp hoặc chưa được giao không xem được bài, file gốc và bản dẫn xuất, kể cả khi biết ID.
3. Payload học sinh không có đáp án, lời giải, ghi chú nội bộ hoặc nội dung chưa mở.
4. Thay đổi TKB hoặc PPCT không tự thay đổi bản bài học đã công bố; giáo viên xem lại việc gắn nguồn.
5. Có đường dùng khi mạng yếu: bản xem nhẹ và khả năng tiếp tục học sau gián đoạn; giới hạn lưu offline cần quyết định riêng.
