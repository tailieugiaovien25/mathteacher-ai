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

Giao dien chi dieu phoi adapter va dich vu mien hien co. Thuat toan lap lich
khong phu thuoc Streamlit hay cach luu tru tep.
