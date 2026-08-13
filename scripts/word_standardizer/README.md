# Giao diện chuẩn hóa kế hoạch bài dạy

Cài thư viện và mở giao diện cục bộ:

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH="src;."; python -m streamlit run scripts/word_standardizer/app.py
```

Trình duyệt sẽ mở tại `http://localhost:8501`. Giáo án được xử lý trong thư mục tạm
trên máy tính, bản gốc không bị ghi đè và người dùng chủ động tải kết quả xuống ổ đĩa.
