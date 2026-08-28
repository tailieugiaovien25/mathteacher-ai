V74.2 - DU LIEU NANG LUC CANONICAL TOAN VA TIENG ANH

Muc tieu
- Nap bo khung mac dinh cho 5 nang luc thanh phan mon Toan.
- Nap bo khung mac dinh cho Nghe, Noi, Doc, Viet va Kien thuc ngon ngu mon Tieng Anh.
- Bo sung chi bao quan sat cap THCS (lop 6-9) va huong dan bang chung.
- Anh xa 5 ma nang luc Toan cu sang ma canonical bang canonical_entity_links.

Nguyen tac du lieu
- competency_components la chu so huu canonical.
- assessment_mathematical_competencies duoc giu lai de tuong thich, khong tao bo ma canh tranh.
- Moi thanh phan co provenance tu CT GDPT 2018 va Thong tu 32/2018/TT-BGDDT.
- Migration nay KHONG tu dong gan hang loat YCCD voi chi bao nang luc. Moi lien ket YCCD phai qua buoc ra soat ngu nghia va bang chung.

Tep cai dat
- supabase/migrations/202608270007_canonical_math_english_competency_seed.sql
- src/tests/test_canonical_math_english_competency_seed_v742.py

Thu tu kiem tra
1. python -m pytest -q src/tests/test_canonical_math_english_competency_seed_v742.py
2. Chay toan bo regression assessment/curriculum.
3. npx --yes supabase@latest db push --dry-run
4. Commit dung cac tep V74.2, push code, sau do moi db push.
