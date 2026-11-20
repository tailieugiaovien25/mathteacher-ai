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

## Bật AI Agent cho ADMIN

Trong **App settings > Secrets**, đặt `SYSTEM_ADMIN_AI_ENABLED = "true"`. Entry
point của Streamlit chuyển cờ này sang cấu hình runtime; khi lưu Secrets,
Streamlit Cloud khởi động lại ứng dụng. Chỉ bật sau khi đã cấu hình provider AI.
Nếu dùng Ollama Cloud, đặt thêm các khóa `MATH_TEACHER_AI_PROVIDER`,
`MATH_TEACHER_AI_MODEL`, `OLLAMA_BASE_URL` và `OLLAMA_API_KEY` như ví dụ trên.
Không dùng endpoint `127.0.0.1` trên Cloud vì endpoint đó trỏ tới chính máy chủ
của ứng dụng, không phải Ollama đang chạy trên máy cá nhân.

### Fallback Qwen 3 0.6B trên máy cá nhân

Fallback chỉ dùng được khi chạy Teacher Portal trên chính máy có Ollama. Cloud
không thể kết nối tới `localhost` của PC người dùng. Cài/chạy Ollama và tải model
`qwen3:0.6b`, rồi trên máy cá nhân đặt biến môi trường
`MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED=true` trước khi chạy Streamlit. Khi
Ollama Cloud trả HTTP 402, AI Agent sẽ dùng profile `qwen3-local-0.6b` nếu ADMIN
đã bật profile đó và Ollama local đang sẵn sàng. Fallback này chỉ áp dụng cho
Chief Engineer Agent; AI khác không tự đổi model.

Ví dụ trong Windows PowerShell:

```powershell
ollama pull qwen3:0.6b
$env:MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED = "true"
streamlit run streamlit_app.py
```

Nếu chạy portal local, đặt secrets cần thiết trong `.streamlit/secrets.toml`
trên máy đó; không commit file này. Trong **AI Runtime & Model Center**, giữ
profile `qwen3-local-0.6b` trong allow-list/fallback.

Sau khi ứng dụng khởi động lại, ADMIN mở **AI Agent**, nhập mục tiêu khảo sát
repository rồi chọn **Chạy AI Agent**. Trang chỉ cho phép thao tác đọc; nếu
provider chưa kết nối, kiểm tra **AI Runtime & Model Center** và cấu hình Secrets.

Để chạy AI hoàn toàn local trên một máy khác, cài Ollama và model trên máy đó rồi
chạy cả Streamlit app và Ollama trên cùng máy. Máy chỉ mở ứng dụng Cloud không thể
dùng Ollama cài trên máy cá nhân một cách tự động.

## Chạy cục bộ

Entry point tự cấu hình đường dẫn import, vì vậy có thể chạy từ thư mục gốc:

```powershell
streamlit run streamlit_app.py
```

Các biến môi trường cục bộ vẫn được hỗ trợ và có ưu tiên hơn giá trị Secrets.

