V75 - QUAN TRI NOI DUNG DAY HOC CANONICAL

Muc tieu
- Tao lop don vi noi dung canonical doc lap voi tung bo sach giao khoa.
- Anh xa noi dung canonical den vi tri Chuong/Unit/Bai/Muc trong SGK.
- Anh xa noi dung canonical den YCCD; tu YCCD co the truy vet den chi bao nang luc.
- Cung cap view assessment_content_context_catalog cho ma tran, ngan hang cau hoi va de kiem tra.
- Cung cap trang ADMIN "Noi dung day hoc" va RPC ghi du lieu co kiem soat.

Nguyen tac
- Thay doi bo sach khong lam thay doi YCCD, nang luc hay logic he thong.
- Noi dung SGK la nguon the hien; canonical_learning_content_units la dinh danh dung chung.
- Chi lien ket cac ban ghi cung mon va cung lop.
- Khong sao chep van ban, hinh anh hoac audio co ban quyen vao migration.
- Moi thay doi quan tri duoc ghi vao learning_content_change_log.

Tep cai dat
- supabase/migrations/202608280001_canonical_learning_content_governance.sql
- src/portal_v2/ui/admin_learning_content_catalog_streamlit.py
- src/portal_v2/ui/admin_navigation.py
- src/portal_v2/ui/admin_shell.py
- src/tests/test_canonical_learning_content_governance_v75.py

Buoc tiep theo
- V75.1 nap danh muc Toan Ket noi tri thuc lop 6-9 theo provenance.
- V75.2 nap danh muc Tieng Anh Global Success lop 6-9 va lien ket media.
- V75.3 ra soat, phe duyet lien ket SGK - noi dung - YCCD - nang luc.
