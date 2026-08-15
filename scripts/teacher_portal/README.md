# Cổng giáo viên MathTeacher-AI

Chạy từ thư mục gốc dự án:

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path
streamlit run scripts/teacher_portal/app.py
```

Cổng dùng chung phiên đăng nhập Supabase cho lịch báo giảng, kho tài liệu,
chuẩn hóa Word và hồ sơ giáo viên. Các ứng dụng thành phần vẫn có thể chạy độc lập.

