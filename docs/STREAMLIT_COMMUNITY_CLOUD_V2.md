# Triển khai Teacher Portal trên Streamlit Community Cloud

## Thiết lập ứng dụng

1. Kết nối tài khoản Streamlit Community Cloud với GitHub.
2. Chọn repository `mathteacher-ai` và nhánh `main`.
3. Chọn entry point `streamlit_app.py`.
4. Chọn một địa chỉ dạng `https://YOUR_APP.streamlit.app`.
5. Mở **Advanced settings > Secrets** và khai báo các tên trong
   `.streamlit/secrets.toml.example` bằng giá trị thật.

Không đưa file `.streamlit/secrets.toml`, client secret hoặc mật khẩu vào Git.

## Google OAuth

Trong Google Cloud Console, sửa OAuth Web Client và thêm đúng URL ứng dụng vào
**Authorized redirect URIs**, ví dụ:

```text
https://YOUR_APP.streamlit.app
```

Đặt cùng URL đó cho `GOOGLE_OAUTH_REDIRECT_URI` trong Streamlit Secrets. Trong
giai đoạn Testing, tài khoản giáo viên phải nằm trong danh sách Test users.

## Chạy cục bộ

Entry point tự cấu hình đường dẫn import, vì vậy có thể chạy từ thư mục gốc:

```powershell
streamlit run streamlit_app.py
```

Các biến môi trường cục bộ vẫn được hỗ trợ và có ưu tiên hơn giá trị Secrets.

