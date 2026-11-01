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

## AI Trợ giảng dùng chung trên Streamlit Cloud

Streamlit Cloud chạy AI ở backend của ứng dụng. Nếu muốn người dùng ở nhiều máy
cùng dùng AI, hãy cấu hình một endpoint Ollama Cloud trong **App settings > Secrets**:

```toml
MATH_TEACHER_AI_PROVIDER = "ollama"
MATH_TEACHER_AI_MODEL = "gemma4:31b"
OLLAMA_BASE_URL = "https://ollama.com"
OLLAMA_API_KEY = "YOUR_OLLAMA_API_KEY"
```

`gemma4:31b` là model profile Ollama Cloud API có sẵn trong registry. API key chỉ
được dùng ở backend; không đưa key vào mã nguồn, trình duyệt hoặc Git. Tài khoản
Ollama có thể có giới hạn hoặc chi phí sử dụng theo gói. Sau khi lưu Secrets,
Streamlit Cloud sẽ khởi động lại ứng dụng. Khi các biến provider/model/endpoint
này được đặt, chúng là cấu hình runtime có thẩm quyền cho deployment Cloud.

Để chạy AI hoàn toàn local trên một máy khác, cài Ollama và model trên máy đó rồi
chạy cả Streamlit app và Ollama trên cùng máy. Máy chỉ mở ứng dụng Cloud không thể
dùng Ollama cài trên máy cá nhân một cách tự động.

## Chạy cục bộ

Entry point tự cấu hình đường dẫn import, vì vậy có thể chạy từ thư mục gốc:

```powershell
streamlit run streamlit_app.py
```

Các biến môi trường cục bộ vẫn được hỗ trợ và có ưu tiên hơn giá trị Secrets.

