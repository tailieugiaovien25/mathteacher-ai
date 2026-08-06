# AI Teacher Platform

AI Teacher Platform là nền tảng trợ lý AI chuyên môn hỗ trợ trực tiếp giáo viên trong việc đọc dữ liệu, hiểu bài học, thiết kế, kiểm tra và cải tiến các sản phẩm giáo dục.

## Trạng thái hiện tại

- Project Baseline: 1.0
- AI Core Module: AI-101 LessonModelBuilder v1.0
- BaseModel Foundation: hoàn thành
- Repository Branch: `main`

## Phạm vi dự án

AI Teacher Platform tập trung hỗ trợ công việc chuyên môn của giáo viên.

Hệ thống không cung cấp chức năng quản lý dành cho tổ chuyên môn, nhà trường, ban giám hiệu hoặc cán bộ quản lý giáo dục.

## Chức năng hiện có

- Đọc Workbook Excel.
- Phân tích Worksheet.
- Phát hiện vùng dữ liệu.
- Phát hiện hàng tiêu đề.
- Phân tích cột.
- Phát hiện bảng.
- Xuất báo cáo JSON.
- Đọc cấu trúc worksheet `LuuBG`.
- Chuyển dữ liệu Excel thành `LessonModel`.
- Nhận diện môn học, lớp, tên bài, phân môn và số tiết.
- Kiểm thử `LessonModelBuilder` trên nhiều hàng dữ liệu.
- Cung cấp `BaseModel` dùng chung cho các model của hệ thống.

## Yêu cầu hệ thống

- Windows 10 hoặc Windows 11.
- Git.
- Python 3.13 hoặc phiên bản tương thích.
- Visual Studio Code.
- Kết nối Internet để clone repository và cài thư viện.

## Khôi phục dự án trên máy tính mới

### 1. Cài Git

Cài Git cho Windows, sau đó kiểm tra:

```powershell
git --version
```

### 2. Cài Python

Cài Python, sau đó kiểm tra:

```powershell
python --version
```

### 3. Cài Visual Studio Code

Cài Visual Studio Code và mở Terminal PowerShell.

### 4. Clone repository

Di chuyển đến thư mục muốn lưu dự án:

```powershell
cd D:\Projects
```

Clone repository:

```powershell
git clone https://github.com/tailieugiaovien25/mathteacher-ai.git
```

Mở thư mục dự án:

```powershell
cd mathteacher-ai
```

### 5. Tạo môi trường ảo

```powershell
python -m venv .venv
```

### 6. Cho phép kích hoạt môi trường trong phiên PowerShell hiện tại

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### 7. Kích hoạt môi trường ảo

```powershell
.\.venv\Scripts\Activate.ps1
```

Khi thành công, Terminal sẽ có tiền tố:

```text
(.venv)
```

### 8. Cài thư viện

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 9. Khôi phục dữ liệu đầu vào

Sao chép file Excel nguồn từ Google Drive vào:

```text
data/input/
```

File đang dùng trong giai đoạn hiện tại:

```text
LBG-TUYEN_chuan_VBA_macro.xlsm
```

Đường dẫn dự kiến:

```text
data/input/LBG-TUYEN_chuan_VBA_macro.xlsm
```

Không đưa file dữ liệu nguồn có thông tin cần bảo vệ lên repository công khai.

### 10. Chạy Robot01

Đặt mã hóa UTF-8:

```powershell
$env:PYTHONIOENCODING="utf-8"
```

Chạy ứng dụng:

```powershell
python src\main.py
```

Kết quả mong muốn:

- Robot01 chạy hoàn tất.
- Không có `Traceback`.
- Báo cáo được tạo tại:

```text
output/reports/workbook_report.json
```

### 11. Chạy kiểm thử BaseModel

```powershell
python .\src\tests\test_base_model.py
```

Kết quả mong muốn:

```text
KẾT QUẢ: 7/7 TEST PASS
```

### 12. Chạy kiểm thử LessonModelBuilder

```powershell
python .\src\tests\test_lesson_model_builder.py
```

Kết quả mong muốn:

```text
KẾT QUẢ: 5/5 TEST PASS
```

### 13. Kiểm tra Git

```powershell
git status
```

Kết quả mong muốn:

```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

## Tiêu chí khôi phục thành công

Dự án được xem là khôi phục thành công khi:

- Repository clone thành công.
- Môi trường `.venv` được tạo.
- Các thư viện cài đặt thành công.
- File Excel nguồn được đặt đúng vị trí.
- Robot01 chạy không lỗi.
- Báo cáo JSON được tạo.
- BaseModel test đạt 7/7.
- LessonModelBuilder test đạt 5/5.
- Git working tree sạch.

## Cấu trúc mã nguồn chính

```text
src/
├── config/
├── excel_engine/
├── intelligence/
├── mapping_engine/
├── models/
├── robots/
├── tests/
├── utils/
├── word_engine/
└── main.py
```

## Các file quan trọng

```text
requirements.txt
README.md
src/main.py
src/models/base_model.py
src/models/lesson_model.py
src/intelligence/lesson_model_builder.py
src/tests/test_base_model.py
src/tests/test_lesson_model_builder.py
```

## Dữ liệu và tài liệu ngoài GitHub

Các tài sản sau được quản lý trên Google Drive:

- tài liệu quản lý dự án;
- đặc tả phần mềm;
- tài liệu kiến trúc;
- tài liệu kỹ thuật;
- Prompt Library;
- các phiên bản phát hành;
- dữ liệu Excel nguồn;
- mẫu Word, PowerPoint và học liệu;
- Recovery Guide.

## Quy tắc an toàn

- Không làm việc trực tiếp trong thư mục Google Drive đồng bộ nếu có thể gây xung đột Git.
- Không commit `.venv`, `__pycache__`, file đầu ra hoặc file audit.
- Không commit dữ liệu cá nhân hoặc tài liệu nhạy cảm vào repository công khai.
- Luôn chạy test trước khi commit.
- Luôn push lên GitHub sau khi commit ổn định.
- Luôn sao lưu dữ liệu nguồn và tài liệu trên Google Drive.

## Quy trình phát triển chuẩn

```text
Design
  ↓
Implementation
  ↓
Testing
  ↓
Documentation
  ↓
Commit
  ↓
Push
  ↓
Release
  ↓
Recovery Verification
```

## Repository

```text
https://github.com/tailieugiaovien25/mathteacher-ai
```