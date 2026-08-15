# Kho tai lieu giao vien V2

## Khoi dong

```powershell
$env:PYTHONPATH = (Resolve-Path ".\\src").Path
streamlit run scripts/document_library/app.py
```

Can co `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` va migration
`supabase/migrations/202608150002_teacher_documents.sql` da duoc chay.

Ban dau cho phep giao vien dang ky file da co tren Google Drive, tim kiem, loc
va xoa metadata. Xoa metadata khong xoa file goc. OAuth tai file truc tiep se
duoc bo sung qua adapter rieng, khong thay doi mo hinh va dich vu kho tai lieu.
