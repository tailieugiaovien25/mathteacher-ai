begin;

-- Bibliographic and table-of-contents metadata only. No copyrighted full text.
with book_seed(grade_number,volume_number,title,publication_year,file_sha256,provenance_note) as (
    values
    (6,1,'Tiếng Anh 6 - Global Success - Sách học sinh - Tập một',2021,
     'a274e739065aa26dcbeee8f2fc5c5ed1ee30674e8cc1b86c2b84fda7da8ce9a1','User-provided reference PDF; publisher identity visible'),
    (6,2,'Tiếng Anh 6 - Global Success - Sách học sinh - Tập hai',2021,
     '7f90798c2749d09a319fc6ed59d07a08afee70a27cd5f91c0ebe9dd3c5bce806','User-provided reference PDF; publisher identity visible'),
    (7,0,'Tiếng Anh 7 - Global Success - Sách học sinh',2022,
     'aff8ccacae1a6818a9005ae9fbb30edc023b6af426ae994c76179209c89222bf','User-provided reference PDF; PDF24 metadata'),
    (8,0,'Tiếng Anh 8 - Global Success - Sách học sinh',2023,
     '9875ea146df5d9b9a71a7030dc8fd6aca44a8410c76803aec76fc6cacc8b63dc','User-provided reference PDF; third-party file metadata requires review'),
    (9,0,'Tiếng Anh 9 - Global Success - Sách học sinh',2024,
     '481abaf85a3e039affa2a234c50ccd3d61e1e25dc9aadeee15b40844b2e67ab8','User-provided reference PDF; file metadata requires review')
)
insert into public.educational_sources(
    source_id,code,name,source_kind,program_id,subject_id,grade_id,
    rights_status,access_scope,status,metadata
)
select
    'source-textbook-english-global-success-g'||grade_number||
        case when volume_number=0 then '' else '-v'||volume_number end,
    'TB-ENG-GS-G'||grade_number||case when volume_number=0 then '' else '-V'||volume_number end,
    title,'TEXTBOOK','program-vn-gdpt-2018','subject-english',
    'grade-'||lpad(grade_number::text,2,'0'),
    'RESTRICTED','AUTHORIZED_USERS','ACTIVE',
    jsonb_build_object(
        'textbook_family_code','ENGLISH-GLOBAL-SUCCESS',
        'publisher','Nhà xuất bản Giáo dục Việt Nam',
        'catalog_scope','bibliographic-and-table-of-contents-only',
        'copyrighted_full_text_included',false,
        'reference_file_sha256',file_sha256,
        'provenance_note',provenance_note,
        'requires_admin_source_review',true
    )
from book_seed
on conflict(source_id) do update set
    code=excluded.code,name=excluded.name,source_kind=excluded.source_kind,
    program_id=excluded.program_id,subject_id=excluded.subject_id,grade_id=excluded.grade_id,
    rights_status=excluded.rights_status,access_scope=excluded.access_scope,
    status=excluded.status,metadata=excluded.metadata,updated_at=now();

insert into public.educational_source_versions(
    source_version_id,source_id,version_number,edition_label,publication_year,
    publisher_name,source_locator,verification_status,publication_status,metadata
)
select source_id||'-version-1',source_id,1,'Bản tham chiếu do người dùng cung cấp',
       publication_year,
       'Nhà xuất bản Giáo dục Việt Nam','User-provided restricted reference PDF',
       'UNVERIFIED','PUBLISHED',
       jsonb_build_object('verification_scope','bibliographic-and-table-of-contents',
                          'requires_admin_source_review',true,'full_text_stored',false,
                          'reference_file_sha256',metadata->>'reference_file_sha256')
from (
    select source_id,metadata,
           case grade_id when 'grade-06' then 2021 when 'grade-07' then 2022
                         when 'grade-08' then 2023 when 'grade-09' then 2024 end as publication_year
    from public.educational_sources
    where source_id like 'source-textbook-english-global-success-g%'
) s
on conflict(source_version_id) do update set
    edition_label=excluded.edition_label,publication_year=excluded.publication_year,
    publisher_name=excluded.publisher_name,source_locator=excluded.source_locator,
    verification_status=excluded.verification_status,
    publication_status=excluded.publication_status,metadata=excluded.metadata;

with book_seed(grade_number,volume_number,title,publication_year) as (
    values
    (6,1,'Tiếng Anh 6 - Global Success - Sách học sinh - Tập một',2021),
    (6,2,'Tiếng Anh 6 - Global Success - Sách học sinh - Tập hai',2021),
    (7,0,'Tiếng Anh 7 - Global Success - Sách học sinh',2022),
    (8,0,'Tiếng Anh 8 - Global Success - Sách học sinh',2023),
    (9,0,'Tiếng Anh 9 - Global Success - Sách học sinh',2024)
)
insert into public.textbook_catalog(
    textbook_id,source_id,program_id,subject_id,grade_id,textbook_family_code,
    textbook_code,title,edition_label,publisher_name,publication_year,
    volume_code,status,display_order,metadata
)
select
    'textbook-english-global-success-g'||grade_number||case when volume_number=0 then '' else '-v'||volume_number end,
    'source-textbook-english-global-success-g'||grade_number||case when volume_number=0 then '' else '-v'||volume_number end,
    'program-vn-gdpt-2018','subject-english','grade-'||lpad(grade_number::text,2,'0'),
    'ENGLISH-GLOBAL-SUCCESS','ENG-GS-G'||grade_number||case when volume_number=0 then '' else '-V'||volume_number end,
    title,'Bản danh mục tham chiếu','Nhà xuất bản Giáo dục Việt Nam',publication_year,
    case when volume_number=0 then 'FULL_YEAR' else 'TAP_'||volume_number end,
    'ACTIVE',grade_number*100+volume_number,
    jsonb_build_object('source_version_id','source-textbook-english-global-success-g'||grade_number||
        case when volume_number=0 then '' else '-v'||volume_number end||'-version-1',
        'data_scope','table-of-contents','full_text_stored',false)
from book_seed
on conflict(textbook_id) do update set
    source_id=excluded.source_id,program_id=excluded.program_id,subject_id=excluded.subject_id,
    grade_id=excluded.grade_id,textbook_family_code=excluded.textbook_family_code,
    textbook_code=excluded.textbook_code,title=excluded.title,
    edition_label=excluded.edition_label,publisher_name=excluded.publisher_name,
    publication_year=excluded.publication_year,volume_code=excluded.volume_code,
    status=excluded.status,display_order=excluded.display_order,metadata=excluded.metadata,
    updated_at=now();

with unit_seed(grade_number,unit_number,title) as (
    values
    (6,1,'My New School'),(6,2,'My House'),(6,3,'My Friends'),
    (6,4,'My Neighbourhood'),(6,5,'Natural Wonders of Viet Nam'),(6,6,'Our Tet Holiday'),
    (6,7,'Television'),(6,8,'Sports and Games'),(6,9,'Cities of the World'),
    (6,10,'Our Houses in the Future'),(6,11,'Our Greener World'),(6,12,'Robots'),
    (7,1,'Hobbies'),(7,2,'Healthy Living'),(7,3,'Community Service'),
    (7,4,'Music and Arts'),(7,5,'Food and Drink'),(7,6,'A Visit to a School'),
    (7,7,'Traffic'),(7,8,'Films'),(7,9,'Festivals around the World'),
    (7,10,'Energy Sources'),(7,11,'Travelling in the Future'),(7,12,'English-speaking Countries'),
    (8,1,'Leisure Time'),(8,2,'Life in the Countryside'),(8,3,'Teenagers'),
    (8,4,'Ethnic Groups of Viet Nam'),(8,5,'Our Customs and Traditions'),(8,6,'Lifestyles'),
    (8,7,'Environmental Protection'),(8,8,'Shopping'),(8,9,'Natural Disasters'),
    (8,10,'Communication in the Future'),(8,11,'Science and Technology'),(8,12,'Life on Other Planets'),
    (9,1,'Local Community'),(9,2,'City Life'),(9,3,'Healthy Living for Teens'),
    (9,4,'Remembering the Past'),(9,5,'Our Experiences'),(9,6,'Vietnamese Lifestyle: Then and Now'),
    (9,7,'Natural Wonders of the World'),(9,8,'Tourism'),(9,9,'World Englishes'),
    (9,10,'Planet Earth'),(9,11,'Electronic Devices'),(9,12,'Career Choices')
)
insert into public.textbook_units(
    textbook_unit_id,textbook_id,parent_unit_id,unit_type,canonical_code,title,
    sequence_number,display_order,status,metadata
)
select
    'unit-english-global-success-g'||grade_number||'-unit-'||lpad(unit_number::text,2,'0'),
    'textbook-english-global-success-g'||grade_number||
        case when grade_number=6 then '-v'||case when unit_number<=6 then 1 else 2 end else '' end,
    null,'UNIT','ENG-GS-G'||grade_number||'-U'||lpad(unit_number::text,2,'0'),
    'Unit '||unit_number||'. '||title,unit_number,unit_number*10,'ACTIVE',
    jsonb_build_object('catalog_level','unit','source_scope','table-of-contents',
        'source_version_id','source-textbook-english-global-success-g'||grade_number||
            case when grade_number=6 then '-v'||case when unit_number<=6 then 1 else 2 end else '' end||'-version-1',
        'requires_requirement_alignment_review',true,'full_text_stored',false)
from unit_seed
on conflict(textbook_unit_id) do update set
    textbook_id=excluded.textbook_id,parent_unit_id=excluded.parent_unit_id,
    unit_type=excluded.unit_type,canonical_code=excluded.canonical_code,title=excluded.title,
    sequence_number=excluded.sequence_number,display_order=excluded.display_order,
    status=excluded.status,metadata=excluded.metadata,updated_at=now();

commit;
