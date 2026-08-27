MATHTEACHER-AI - V72 CANONICAL BLUEPRINT AUTHORING PORTAL

Nen ma nguon
------------
Branch: feature/math-assessment-generator-v1
Expected HEAD: 90ca9b9

Muc tieu
--------
Noi co so du lieu giao duc canonical vao giao dien soan Ma tran va Ban
dac ta. Giao vien khong nhap lai noi dung chuong trinh bang tay.

Luong ADMIN
-----------
1. Mo Quan tri bo mau de kiem tra.
2. Xem ho so cau truc de dang DRAFT.
3. Bam Kiem tra va kich hoat ho so.
4. RPC chi kich hoat khi:
   - tong diem cac phan bang tong diem ho so;
   - tong diem phan bo muc do bang tong diem ho so;
   - tong ty le muc do bang 100%;
   - co van ban can cu AUTHORITY.

Luong giao vien
---------------
1. Mo Ma tran & ban dac ta.
2. Chon ho so ACTIVE va khoi lop.
3. Tao hoac mo lai ban nhap theo ma ma tran.
4. Chon chu de canonical, co tuy chon mo rong chu de con tuong minh.
5. Chon YCCD ACTIVE + VERIFIED trong dung pham vi.
6. Nhap vai tro, so cau, diem, thu tu va ghi chu dac ta.
7. Luu nguyen tu toan bo tap lien ket qua RPC V71.1.

Nguyen tac
----------
- Khong doc truc tiep JSON canonical trong UI.
- Khong insert/update/delete bang lien ket truc tiep tu UI.
- Cau truc de lay tu assessment_profiles ACTIVE, khong ma hoa cung.
- Ma tran thuoc dung tai khoan giao vien.
- Decimal duoc bao toan khi gui diem sang Supabase.
- Selection phai finalized truoc khi ghi.

Migration
---------
202608270002_assessment_blueprint_draft_authoring.sql

Migration bo sung:
- activate_assessment_profile (chi ADMIN);
- create_assessment_blueprint_draft (giao vien da xac thuc).

Kiem thu khi dong goi
---------------------
- Target/integration: 89 passed.
- Assessment + canonical regression: 693 passed.

Ranh gio
--------
V72 luu pham vi YCCD va phan bo muc tieu cua ban dac ta. Buoc tiep theo
se noi cac o ma tran (section, dang cau hoi, muc do nhan thuc, diem) vao
cung workspace truoc khi gui duyet.
