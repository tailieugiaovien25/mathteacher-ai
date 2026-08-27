MATHTEACHER-AI - V71.1 CANONICAL BLUEPRINT REQUIREMENT SCOPE

Nen ma nguon
------------
Branch: feature/math-assessment-generator-v1
Expected HEAD: aad8d99

Muc tieu
--------
Noi lua chon YCCD canonical da xac thuc vao ma tran de kiem tra bang
mot phep ghi nguyen tu, dong thoi ngan lien ket sai mon, sai khoi, sai
chuong trinh, sai chu de hoac YCCD chua VERIFIED.

Sua loi du lieu
---------------
Migration 202608270001 sua tham chieu khoa chinh RPC tu cot khong ton tai
assessment_blueprint_versions.id sang blueprint_version_id.

Bao ve toan cuc
---------------
Trigger moi ap dung cho ca RPC va thao tac ghi truc tiep vao bang
assessment_blueprint_requirement_links. Moi lien ket bat buoc khop:
- subject_code cua ma tran va chuong trinh;
- grade_level cua ma tran, YCCD va chu de;
- program_code cua YCCD va chu de;
- trang thai ACTIVE cua program, topic, requirement;
- metadata.canonical_status = VERIFIED.

Lop ung dung
------------
- BlueprintRequirementLinkService chi nhan selection da finalized.
- Assignment phai khop chinh xac tap YCCD da chon.
- Gateway goi RPC replace_assessment_blueprint_requirement_links.
- Decimal duoc gui bang chuoi de khong mat do chinh xac diem.
- Ket qua RPC duoc doi chieu day du voi yeu cau da gui.

Kiem thu khi dong goi
---------------------
- Target/integration: 63 passed.
- Assessment + canonical regression: 667 passed.

Ranh gio
--------
V71.1 chua them giao dien Streamlit. Sau khi migration va gateway duoc
nghiem thu tren Supabase that, buoc tiep theo moi noi bo chon YCCD vao
trang soan ma tran/ban dac ta.
