# Kho tai lieu giao vien V2

## Khoi dong

```powershell
$env:PYTHONPATH = (Resolve-Path ".\\src").Path
streamlit run scripts/document_library/app.py
```

Can co `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` va migration
`supabase/migrations/202608150002_teacher_documents.sql` da duoc chay.

Ung dung cho phep giao vien dang ky file da co tren Google Drive, tim kiem, loc
va xoa metadata. Xoa metadata khong xoa file goc.

De tai truc tiep Word, Excel hoac PDF len Drive, can them:

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID = Read-Host "Google OAuth Client ID"
$env:GOOGLE_OAUTH_CLIENT_SECRET = Read-Host "Google OAuth Client Secret"
$env:GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8501"
```

OAuth dung quyen toi thieu `drive.file`; token chi o trong phien Streamlit.
