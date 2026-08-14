# Giao dien lich bao giang tu dong

## Chay tren Windows PowerShell

Tai thu muc goc cua du an:

```powershell
$env:PYTHONPATH = (Resolve-Path ".\\src").Path
streamlit run scripts/weekly_schedule/app.py
```

Trinh duyet se mo giao dien tai dia chi Streamlit thong bao. Tai tep
`templates/weekly_schedule/mau_du_lieu_lich_bao_giang_v2.xlsx` de thu nghiem.

## Pham vi V1

- Tai va kiem tra tep `.xlsx` toi da 20 MB.
- Xem bon bang nguon da duoc chuan hoa.
- Chon giao vien, nam hoc va tuan.
- Tao va xem truoc lich bao giang.
- Tai lich bao giang Excel da dinh dang va san sang de in.
- Khong sua hoac ghi de tep Excel nguon.
- Luu, cap nhat va mo lai lich theo giao vien, nam hoc va tuan.

Giao dien chi dieu phoi adapter va dich vu mien hien co. Thuat toan lap lich
khong phu thuoc Streamlit hay cach luu tru tep.

Ban thu nghiem luu du lieu tai `data/weekly_schedules`. Thu muc nay la du lieu
van hanh cua nguoi dung va khong dua vao Git. Adapter JSON co the duoc thay bang
Supabase ma khong sua dich vu lap lich.

## Luu tren Supabase

1. Cai cac goi trong `requirements.txt`.
2. Chay migration `supabase/migrations/202608140001_weekly_teaching_schedules.sql`.
3. Dat `SUPABASE_URL` va `SUPABASE_PUBLISHABLE_KEY` trong moi truong.
4. Khoi dong giao dien, chon `Supabase` va dang nhap tai khoan giao vien.

Khong dung secret key hoac service-role key trong giao dien giao vien.
