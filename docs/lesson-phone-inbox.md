# Hộp nhận ảnh điện thoại giáo viên (thử nghiệm tại lớp)

Ứng dụng chạy trên **máy giáo viên**, điện thoại/iPad chỉ gửi ảnh vào hàng chờ.
Học sinh không cần điện thoại. Nội dung chỉ hiện trên slide sau khi giáo viên duyệt.

1. Mở bài giảng bằng tài khoản giáo viên khi còn mạng, lưu bản nháp lên tài khoản.
2. Cho máy tính kết nối hotspot do điện thoại giáo viên phát.
3. Bật `MATHTEACHER_LOCAL_PHONE_INBOX=1` trước khi chạy Streamlit.
4. Trong thẻ ghi nhận, chọn **Nhận ảnh từ điện thoại / iPad giáo viên qua hotspot** rồi bấm **Bật hộp nhận ảnh nội bộ**.
5. Trên điện thoại mở địa chỉ IP/cổng hiển thị trên máy tính, nhập mã ghép cặp, chụp hoặc chọn ảnh, bấm **Gửi vào hộp chờ giáo viên**.
6. Trên máy tính bấm **Làm mới hộp chờ**, xem ảnh, chọn **Duyệt và đưa ảnh vào thẻ**. Lưu bản nháp/kiểm tra trạng thái tự lưu trước khi đóng ứng dụng.
7. Cuối tiết bấm **Dừng hộp nhận ảnh**.

Nếu điện thoại không mở được địa chỉ gợi ý, chạy `ipconfig` trên máy tính và thay phần IP trong địa chỉ bằng IPv4 của kết nối Wi-Fi/hotspot. Giữ nguyên cổng `8515`. `localhost:8514` trên điện thoại không phải là máy tính.

Ảnh được thu nhỏ trên điện thoại thành JPEG tối đa 450 KB. Mã ghép cặp có hạn 20 phút và có thể tạo lại. Chỉ một hộp nhận chạy trên máy giáo viên; tối đa 10 ảnh chờ. Nếu Windows Firewall hỏi, chỉ cho phép kết nối trên mạng riêng của hotspot.

Đây là đường truyền nội bộ HTTP trong hotspot giáo viên. Không mở cổng nhận cho mạng công cộng hoặc Internet. Trang nhận ảnh không thể tự đăng nhập hay sửa bài giảng. Kết nối điện thoại không biến toàn bộ Streamlit/Gemini/Supabase thành ứng dụng ngoại tuyến: cần mở bài học trước khi mất Internet, và lưu bản nháp khi có kết nối trở lại. Phiên bản này nhận **ảnh**, chưa nhận video trực tiếp hoặc âm thanh trực tiếp.
