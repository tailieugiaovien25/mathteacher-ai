# MathTeacher AI — AI Knowledge Governance V5

## Mục tiêu

Tạo lớp tri thức có phiên bản để AI có thể ngày càng hữu ích mà không được tự phát hành tri thức dùng chung.

## Nguyên tắc bất biến

> Dữ liệu đổi nhưng hệ thống không đổi.

> AI có thể đề xuất tri thức; ADMIN quyết định tri thức nào trở thành tri thức dùng chung.

## Vòng đời

`CANDIDATE -> APPROVED`

Các nhánh kiểm soát:

- `CANDIDATE -> REJECTED`
- `APPROVED -> REVOKED`
- `APPROVED -> SUPERSEDED` khi ADMIN phát hành phiên bản mới

## Bảo đảm

- Mỗi record có `content_hash` để kiểm tra toàn vẹn.
- Chỉ `APPROVED` được trả về từ lớp context dùng chung.
- Store local-first dùng JSON atomic replace; backend lưu trữ có thể đổi sang Supabase mà không đổi Kernel contract.
- `KnowledgeRegistry` không cấp quyền cho AI tự approve.
- Skill `knowledge.curator` chỉ tạo candidate/advisory; phát hành vẫn thuộc ADMIN.

## V5 chưa làm

- Chưa tự động đưa toàn bộ knowledge vào prompt của mọi skill.
- Chưa thực hiện semantic/vector search.
- Chưa tự động học từ dữ liệu production.

Ba phần trên chỉ thực hiện sau khi có evaluation/quality gate và policy rõ ràng.
