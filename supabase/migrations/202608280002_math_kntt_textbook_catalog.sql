begin;

-- V75.1 registers bibliographic and table-of-contents metadata only.
-- Copyrighted lesson text, images and exercises are not copied here.
insert into public.educational_sources(
    source_id,code,name,source_kind,program_id,subject_id,grade_id,
    rights_status,access_scope,status,metadata
)
select
    'source-textbook-math-kntt-g'||grade_number||'-v'||volume_number,
    'TB-MATH-KNTT-G'||grade_number||'-V'||volume_number,
    'Toán '||grade_number||' - Kết nối tri thức với cuộc sống - Tập '||volume_number,
    'TEXTBOOK','program-vn-gdpt-2018','subject-math',
    'grade-'||lpad(grade_number::text,2,'0'),
    'RESTRICTED','AUTHORIZED_USERS','ACTIVE',
    jsonb_build_object(
        'textbook_family_code','MATH-KNTT','publisher','Nhà xuất bản Giáo dục Việt Nam',
        'catalog_scope','bibliographic-and-table-of-contents-only',
        'copyrighted_full_text_included',false
    )
from generate_series(6,9) grade_number
cross join generate_series(1,2) volume_number
on conflict(source_id) do update set
    code=excluded.code,name=excluded.name,source_kind=excluded.source_kind,
    program_id=excluded.program_id,subject_id=excluded.subject_id,grade_id=excluded.grade_id,
    rights_status=excluded.rights_status,access_scope=excluded.access_scope,
    status=excluded.status,metadata=excluded.metadata,updated_at=now();

insert into public.educational_source_versions(
    source_version_id,source_id,version_number,edition_label,publication_year,
    publisher_name,source_locator,verification_status,publication_status,metadata
)
select
    source_id||'-version-1',source_id,1,'Bản danh mục đang sử dụng',
    case substring(source_id from 'g([0-9]+)')::integer
        when 6 then 2021 when 7 then 2022 when 8 then 2023 when 9 then 2024 end,
    'Nhà xuất bản Giáo dục Việt Nam','Mục lục bản sách giáo khoa',
    'UNVERIFIED','PUBLISHED',
    jsonb_build_object(
        'verification_scope','bibliographic-and-table-of-contents',
        'requires_admin_source_review',true,
        'full_text_stored',false
    )
from public.educational_sources
where source_id like 'source-textbook-math-kntt-g%-v%'
on conflict(source_version_id) do update set
    edition_label=excluded.edition_label,publication_year=excluded.publication_year,
    publisher_name=excluded.publisher_name,source_locator=excluded.source_locator,
    verification_status=excluded.verification_status,
    publication_status=excluded.publication_status,metadata=excluded.metadata;

insert into public.textbook_catalog(
    textbook_id,source_id,program_id,subject_id,grade_id,textbook_family_code,
    textbook_code,title,edition_label,publisher_name,publication_year,
    volume_code,status,display_order,metadata
)
select
    'textbook-math-kntt-g'||grade_number||'-v'||volume_number,
    'source-textbook-math-kntt-g'||grade_number||'-v'||volume_number,
    'program-vn-gdpt-2018','subject-math','grade-'||lpad(grade_number::text,2,'0'),
    'MATH-KNTT','MATH-KNTT-G'||grade_number||'-V'||volume_number,
    'Toán '||grade_number||' - Kết nối tri thức với cuộc sống - Tập '||volume_number,
    'Bản danh mục đang sử dụng','Nhà xuất bản Giáo dục Việt Nam',
    case grade_number when 6 then 2021 when 7 then 2022 when 8 then 2023 when 9 then 2024 end,
    'TAP_'||volume_number,'ACTIVE',grade_number*100+volume_number,
    jsonb_build_object(
        'source_version_id','source-textbook-math-kntt-g'||grade_number||'-v'||volume_number||'-version-1',
        'data_scope','table-of-contents','full_text_stored',false
    )
from generate_series(6,9) grade_number
cross join generate_series(1,2) volume_number
on conflict(textbook_id) do update set
    source_id=excluded.source_id,program_id=excluded.program_id,subject_id=excluded.subject_id,
    grade_id=excluded.grade_id,textbook_family_code=excluded.textbook_family_code,
    textbook_code=excluded.textbook_code,title=excluded.title,
    edition_label=excluded.edition_label,publisher_name=excluded.publisher_name,
    publication_year=excluded.publication_year,volume_code=excluded.volume_code,
    status=excluded.status,display_order=excluded.display_order,metadata=excluded.metadata,
    updated_at=now();

with chapter_seed(grade_number,volume_number,chapter_number,title) as (
    values
    (6,1,1,'Tập hợp các số tự nhiên'),
    (6,1,2,'Tính chia hết trong tập hợp các số tự nhiên'),
    (6,1,3,'Số nguyên'),
    (6,1,4,'Một số hình phẳng trong thực tiễn'),
    (6,1,5,'Tính đối xứng của hình phẳng trong tự nhiên'),
    (6,2,6,'Phân số'),
    (6,2,7,'Số thập phân'),
    (6,2,8,'Những hình hình học cơ bản'),
    (6,2,9,'Dữ liệu và xác suất thực nghiệm'),
    (7,1,1,'Số hữu tỉ'),
    (7,1,2,'Số thực'),
    (7,1,3,'Góc và đường thẳng song song'),
    (7,1,4,'Tam giác bằng nhau'),
    (7,1,5,'Thu thập và biểu diễn dữ liệu'),
    (7,2,6,'Tỉ lệ thức và đại lượng tỉ lệ'),
    (7,2,7,'Biểu thức đại số và đa thức một biến'),
    (7,2,8,'Làm quen với biến cố và xác suất của biến cố'),
    (7,2,9,'Quan hệ giữa các yếu tố trong một tam giác'),
    (7,2,10,'Một số hình khối trong thực tiễn'),
    (8,1,1,'Đa thức'),
    (8,1,2,'Hằng đẳng thức đáng nhớ và ứng dụng'),
    (8,1,3,'Tứ giác'),
    (8,1,4,'Định lí Thales'),
    (8,1,5,'Dữ liệu và biểu đồ'),
    (8,2,6,'Phân thức đại số'),
    (8,2,7,'Phương trình bậc nhất và hàm số bậc nhất'),
    (8,2,8,'Mở đầu về tính xác suất của biến cố'),
    (8,2,9,'Tam giác đồng dạng'),
    (8,2,10,'Một số hình khối trong thực tiễn'),
    (9,1,1,'Phương trình và hệ hai phương trình bậc nhất hai ẩn'),
    (9,1,2,'Phương trình và bất phương trình bậc nhất một ẩn'),
    (9,1,3,'Căn bậc hai và căn bậc ba'),
    (9,1,4,'Hệ thức lượng trong tam giác vuông'),
    (9,1,5,'Đường tròn'),
    (9,2,6,'Hàm số y = ax² (a ≠ 0). Phương trình bậc hai một ẩn'),
    (9,2,7,'Tần số và tần số tương đối'),
    (9,2,8,'Xác suất của biến cố trong một số mô hình xác suất đơn giản'),
    (9,2,9,'Đường tròn ngoại tiếp và đường tròn nội tiếp'),
    (9,2,10,'Một số hình khối trong thực tiễn')
)
insert into public.textbook_units(
    textbook_unit_id,textbook_id,parent_unit_id,unit_type,canonical_code,title,
    sequence_number,display_order,status,metadata
)
select
    'unit-math-kntt-g'||grade_number||'-chapter-'||lpad(chapter_number::text,2,'0'),
    'textbook-math-kntt-g'||grade_number||'-v'||volume_number,null,'CHAPTER',
    'MATH-KNTT-G'||grade_number||'-CH'||lpad(chapter_number::text,2,'0'),
    'Chương '||chapter_number||'. '||title,chapter_number,chapter_number*10,'ACTIVE',
    jsonb_build_object(
        'catalog_level','chapter','source_scope','table-of-contents',
        'source_version_id','source-textbook-math-kntt-g'||grade_number||'-v'||volume_number||'-version-1',
        'requires_requirement_alignment_review',true
    )
from chapter_seed
on conflict(textbook_unit_id) do update set
    textbook_id=excluded.textbook_id,parent_unit_id=excluded.parent_unit_id,
    unit_type=excluded.unit_type,canonical_code=excluded.canonical_code,title=excluded.title,
    sequence_number=excluded.sequence_number,display_order=excluded.display_order,
    status=excluded.status,metadata=excluded.metadata,updated_at=now();

commit;
