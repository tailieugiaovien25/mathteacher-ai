# Weekly Schedule Excel Adapter V2

## Muc tieu

Excel chi la nguon du lieu do giao vien nhap. Adapter doc bon bang va chuyen
chung thanh cac mo hinh mien on dinh; dich vu lap lich khong biet ten file,
ten sheet, vi tri o hay thu vien doc bang tinh.

## Bon bang du lieu

1. `Tuan_hoc`: nam hoc, so tuan, ngay bat dau va ngay ket thuc.
2. `Thoi_khoa_bieu`: giao vien, lop, mon/phan mon, thu, tiet va khoang hieu luc.
3. `PPCT`: thu tu tiet, bai hoc, so tiet trong bai va thiet bi day hoc.
4. `Tiet_da_day`: lich su thuc hien de tinh tiet PPCT tiep theo.

Dong trong duoc bo qua. Ngay chap nhan gia tri ngay cua Excel hoac chuoi
`yyyy-mm-dd`, `dd/mm/yyyy`, `dd-mm-yyyy`. Thiet bi cach nhau boi dau cham
phay. Trang thai `COMPLETED`, `Da day`/`Da day` co dau, hoac `Hoan thanh`
duoc chuan hoa thanh trang thai da hoan thanh.

## Du lieu doi nhung he thong khong doi

`WeeklyScheduleWorkbookSchema` la hop dong anh xa. Neu ten sheet hoac ten
cot cua mot file nguon thay doi, giao dien/cau hinh chi can tao schema khac;
khong sua `WeeklyTeachingScheduleService` va cac mo hinh mien.

## Su dung

```python
from educational_planning_v2.adapters import WeeklyScheduleExcelAdapter
from educational_planning_v2.services import WeeklyTeachingScheduleService

data = WeeklyScheduleExcelAdapter().load("du-lieu-lich-bao-giang.xlsx")
week = data.week(5, "2026-2027")

schedule = WeeklyTeachingScheduleService().build(
    schedule_id="GV001-2026-2027-W05",
    teacher_id="GV001",
    academic_week=week,
    timetable_slots=data.timetable_slots,
    curriculum_periods=data.curriculum_periods,
    execution_records=data.execution_records,
)
```

Loi du lieu co vi tri sheet, dong va cot de giao dien huong dan giao vien sua
truc tiep trong bang nguon.
