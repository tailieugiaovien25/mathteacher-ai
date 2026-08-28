-- Assessment Curriculum Foundation V1
-- Canonical curriculum, learning requirements, mathematical competencies,
-- and regulatory-document data for the THCS Mathematics assessment module.

create table if not exists public.assessment_curriculum_programs (
    program_code text primary key
        check (char_length(program_code) between 1 and 100),

    program_name text not null
        check (char_length(program_name) between 1 and 300),

    subject_code text not null default 'MATH'
        check (char_length(subject_code) between 1 and 100),

    education_level text not null
        check (education_level in ('THCS', 'THPT', 'PRIMARY')),

    grade_min integer not null
        check (grade_min between 1 and 12),

    grade_max integer not null
        check (grade_max between 1 and 12),

    version_label text not null
        check (char_length(version_label) between 1 and 100),

    effective_from date null,
    effective_to date null,

    status text not null default 'ACTIVE'
        check (status in ('DRAFT', 'ACTIVE', 'INACTIVE', 'SUPERSEDED')),

    metadata jsonb not null default '{}'::jsonb,

    created_by uuid null
        references auth.users(id)
        on delete set null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (grade_min <= grade_max),
    check (
        effective_to is null
        or effective_from is null
        or effective_to >= effective_from
    )
);

create table if not exists public.assessment_curriculum_topics (
    topic_code text primary key
        check (char_length(topic_code) between 1 and 120),

    program_code text not null
        references public.assessment_curriculum_programs(program_code)
        on update cascade
        on delete restrict,

    parent_topic_code text null
        references public.assessment_curriculum_topics(topic_code)
        on update cascade
        on delete restrict,

    grade_level integer null
        check (grade_level between 1 and 12),

    domain_code text not null
        check (char_length(domain_code) between 1 and 100),

    topic_name text not null
        check (char_length(topic_name) between 1 and 300),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    status text not null default 'ACTIVE'
        check (status in ('DRAFT', 'ACTIVE', 'INACTIVE')),

    metadata jsonb not null default '{}'::jsonb,

    created_by uuid null
        references auth.users(id)
        on delete set null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (parent_topic_code is distinct from topic_code)
);

create table if not exists public.assessment_learning_requirements (
    requirement_code text primary key
        check (char_length(requirement_code) between 1 and 140),

    program_code text not null
        references public.assessment_curriculum_programs(program_code)
        on update cascade
        on delete restrict,

    topic_code text not null
        references public.assessment_curriculum_topics(topic_code)
        on update cascade
        on delete restrict,

    grade_level integer not null
        check (grade_level between 1 and 12),

    requirement_text text not null
        check (char_length(trim(requirement_text)) > 0),

    source_locator text null,

    version_number integer not null default 1
        check (version_number >= 1),

    replaces_requirement_code text null
        references public.assessment_learning_requirements(requirement_code)
        on update cascade
        on delete restrict,

    status text not null default 'DRAFT'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'INACTIVE',
                'SUPERSEDED'
            )
        ),

    metadata jsonb not null default '{}'::jsonb,

    created_by uuid null
        references auth.users(id)
        on delete set null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (
        replaces_requirement_code
        is distinct from requirement_code
    )
);

create table if not exists public.assessment_mathematical_competencies (
    competency_code text primary key
        check (char_length(competency_code) between 1 and 100),

    competency_name text not null
        check (char_length(competency_name) between 1 and 300),

    description text not null default '',

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    status text not null default 'ACTIVE'
        check (status in ('ACTIVE', 'INACTIVE')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_requirement_competency_links (
    requirement_code text not null
        references public.assessment_learning_requirements(requirement_code)
        on update cascade
        on delete cascade,

    competency_code text not null
        references public.assessment_mathematical_competencies(competency_code)
        on update cascade
        on delete restrict,

    emphasis text not null default 'PRIMARY'
        check (emphasis in ('PRIMARY', 'SECONDARY')),

    notes text not null default '',

    created_at timestamptz not null default now(),

    primary key (
        requirement_code,
        competency_code
    )
);

create table if not exists public.assessment_regulatory_documents (
    document_code text primary key
        check (char_length(document_code) between 1 and 120),

    document_type text not null
        check (
            document_type in (
                'LAW',
                'DECREE',
                'CIRCULAR',
                'OFFICIAL_LETTER',
                'GUIDANCE',
                'LOCAL_GUIDANCE',
                'SCHOOL_RULE'
            )
        ),

    document_number text not null
        check (char_length(document_number) between 1 and 150),

    document_title text not null
        check (char_length(document_title) between 1 and 500),

    issuer text not null
        check (char_length(issuer) between 1 and 300),

    issued_date date null,
    effective_date date null,
    expiry_date date null,

    application_scope text not null default '',
    source_url text null,

    status text not null default 'ACTIVE'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'PARTIALLY_ACTIVE',
                'INACTIVE',
                'SUPERSEDED',
                'REFERENCE'
            )
        ),

    metadata jsonb not null default '{}'::jsonb,

    created_by uuid null
        references auth.users(id)
        on delete set null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (
        expiry_date is null
        or effective_date is null
        or expiry_date >= effective_date
    )
);

create index if not exists
    assessment_curriculum_topics_program_grade_idx
on public.assessment_curriculum_topics (
    program_code,
    grade_level,
    domain_code
);

create index if not exists
    assessment_learning_requirements_scope_idx
on public.assessment_learning_requirements (
    program_code,
    grade_level,
    topic_code,
    status
);

create index if not exists
    assessment_learning_requirements_replacement_idx
on public.assessment_learning_requirements (
    replaces_requirement_code
);

create index if not exists
    assessment_regulatory_documents_status_idx
on public.assessment_regulatory_documents (
    status,
    issued_date
);

alter table public.assessment_curriculum_programs
    enable row level security;

alter table public.assessment_curriculum_topics
    enable row level security;

alter table public.assessment_learning_requirements
    enable row level security;

alter table public.assessment_mathematical_competencies
    enable row level security;

alter table public.assessment_requirement_competency_links
    enable row level security;

alter table public.assessment_regulatory_documents
    enable row level security;

revoke all on table
    public.assessment_curriculum_programs,
    public.assessment_curriculum_topics,
    public.assessment_learning_requirements,
    public.assessment_mathematical_competencies,
    public.assessment_requirement_competency_links,
    public.assessment_regulatory_documents
from anon;

grant select, insert, update, delete on table
    public.assessment_curriculum_programs,
    public.assessment_curriculum_topics,
    public.assessment_learning_requirements,
    public.assessment_mathematical_competencies,
    public.assessment_requirement_competency_links,
    public.assessment_regulatory_documents
to authenticated;

-- Authenticated users may read canonical assessment data.
do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_curriculum_programs',
        'assessment_curriculum_topics',
        'assessment_learning_requirements',
        'assessment_mathematical_competencies',
        'assessment_requirement_competency_links',
        'assessment_regulatory_documents'
    ]
    loop
        execute format(
            'drop policy if exists %I on public.%I',
            'authenticated_select_' || table_name,
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for select to authenticated
             using ((select auth.uid()) is not null)',
            'authenticated_select_' || table_name,
            table_name
        );
    end loop;
end
$$;

-- Only an active portal administrator may mutate canonical data.
do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_curriculum_programs',
        'assessment_curriculum_topics',
        'assessment_learning_requirements',
        'assessment_mathematical_competencies',
        'assessment_requirement_competency_links',
        'assessment_regulatory_documents'
    ]
    loop
        execute format(
            'drop policy if exists %I on public.%I',
            'admins_insert_' || table_name,
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for insert to authenticated
             with check (
                 (select public.current_user_is_portal_admin())
             )',
            'admins_insert_' || table_name,
            table_name
        );

        execute format(
            'drop policy if exists %I on public.%I',
            'admins_update_' || table_name,
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for update to authenticated
             using (
                 (select public.current_user_is_portal_admin())
             )
             with check (
                 (select public.current_user_is_portal_admin())
             )',
            'admins_update_' || table_name,
            table_name
        );

        execute format(
            'drop policy if exists %I on public.%I',
            'admins_delete_' || table_name,
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for delete to authenticated
             using (
                 (select public.current_user_is_portal_admin())
             )',
            'admins_delete_' || table_name,
            table_name
        );
    end loop;
end
$$;

create or replace function
public.set_assessment_canonical_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_curriculum_programs',
        'assessment_curriculum_topics',
        'assessment_learning_requirements',
        'assessment_mathematical_competencies',
        'assessment_regulatory_documents'
    ]
    loop
        execute format(
            'drop trigger if exists %I on public.%I',
            table_name || '_set_updated_at',
            table_name
        );

        execute format(
            'create trigger %I
             before update on public.%I
             for each row
             execute function
                 public.set_assessment_canonical_updated_at()',
            table_name || '_set_updated_at',
            table_name
        );
    end loop;
end
$$;

insert into public.assessment_curriculum_programs (
    program_code,
    program_name,
    subject_code,
    education_level,
    grade_min,
    grade_max,
    version_label,
    effective_from,
    status,
    metadata
)
values (
    'MOET-GDPT2018-MATH-THCS',
    'Chương trình Giáo dục phổ thông 2018 môn Toán cấp THCS',
    'MATH',
    'THCS',
    6,
    9,
    'GDPT-2018-CURRENT',
    date '2021-09-05',
    'ACTIVE',
    jsonb_build_object(
        'canonical_source', true,
        'book_independent', true
    )
)
on conflict (program_code) do nothing;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status
)
values
    (
        'M6-SH',
        'MOET-GDPT2018-MATH-THCS',
        null,
        6,
        'NUMBER_AND_ALGEBRA',
        'Số và Đại số',
        10,
        'ACTIVE'
    ),
    (
        'M6-HH',
        'MOET-GDPT2018-MATH-THCS',
        null,
        6,
        'GEOMETRY_AND_MEASUREMENT',
        'Hình học và Đo lường',
        20,
        'ACTIVE'
    ),
    (
        'M6-TKXS',
        'MOET-GDPT2018-MATH-THCS',
        null,
        6,
        'STATISTICS_AND_PROBABILITY',
        'Thống kê và Xác suất',
        30,
        'ACTIVE'
    )
on conflict (topic_code) do nothing;

insert into public.assessment_mathematical_competencies (
    competency_code,
    competency_name,
    description,
    sequence_number,
    status
)
values
    (
        'MATH-REASONING',
        'Tư duy và lập luận toán học',
        'Thực hiện các thao tác tư duy, lập luận và giải thích toán học.',
        10,
        'ACTIVE'
    ),
    (
        'MATH-MODELING',
        'Mô hình hóa toán học',
        'Thiết lập và sử dụng mô hình toán học để giải quyết vấn đề.',
        20,
        'ACTIVE'
    ),
    (
        'MATH-PROBLEM-SOLVING',
        'Giải quyết vấn đề toán học',
        'Nhận biết, lựa chọn và thực hiện giải pháp toán học.',
        30,
        'ACTIVE'
    ),
    (
        'MATH-COMMUNICATION',
        'Giao tiếp toán học',
        'Đọc, viết, trình bày và trao đổi thông tin toán học.',
        40,
        'ACTIVE'
    ),
    (
        'MATH-TOOLS',
        'Sử dụng công cụ, phương tiện học toán',
        'Lựa chọn và sử dụng công cụ, phương tiện trong học toán.',
        50,
        'ACTIVE'
    )
on conflict (competency_code) do nothing;

insert into public.assessment_regulatory_documents (
    document_code,
    document_type,
    document_number,
    document_title,
    issuer,
    issued_date,
    effective_date,
    application_scope,
    source_url,
    status,
    metadata
)
values
    (
        'TT-32-2018-BGDDT',
        'CIRCULAR',
        '32/2018/TT-BGDĐT',
        'Ban hành Chương trình giáo dục phổ thông',
        'Bộ Giáo dục và Đào tạo',
        date '2018-12-26',
        date '2019-02-15',
        'Căn cứ xác định nội dung và yêu cầu cần đạt của Chương trình GDPT.',
        'https://vanban.chinhphu.vn/',
        'ACTIVE',
        jsonb_build_object('canonical_for_requirements', true)
    ),
    (
        'TT-22-2021-BGDDT',
        'CIRCULAR',
        '22/2021/TT-BGDĐT',
        'Quy định về đánh giá học sinh THCS và học sinh THPT',
        'Bộ Giáo dục và Đào tạo',
        date '2021-07-20',
        date '2021-09-05',
        'Quy định trực tiếp hoạt động kiểm tra, đánh giá học sinh THCS.',
        'https://vanban.chinhphu.vn/?docid=203926&pageid=27160',
        'ACTIVE',
        jsonb_build_object('assessment_authority', true)
    ),
    (
        'TT-17-2025-BGDDT',
        'CIRCULAR',
        '17/2025/TT-BGDĐT',
        'Sửa đổi, bổ sung một số nội dung trong Chương trình giáo dục phổ thông',
        'Bộ Giáo dục và Đào tạo',
        date '2025-09-12',
        date '2025-09-12',
        'Văn bản sửa đổi Chương trình GDPT cần được đối chiếu theo phiên bản.',
        'https://vanban.chinhphu.vn/?docid=215347&pageid=27160',
        'ACTIVE',
        jsonb_build_object('amends_program', 'TT-32-2018-BGDDT')
    ),
    (
        'CV-7991-2024-BGDDT-GDTRH',
        'OFFICIAL_LETTER',
        '7991/BGDĐT-GDTrH',
        'Về việc thực hiện kiểm tra, đánh giá đối với cấp THCS, THPT',
        'Bộ Giáo dục và Đào tạo',
        date '2024-12-17',
        null,
        'Tài liệu tham khảo kỹ thuật; phạm vi áp dụng cho THCS phải được xác định theo hướng dẫn địa phương.',
        'https://luatvietnam.vn/',
        'REFERENCE',
        jsonb_build_object(
            'do_not_assume_mandatory_for_thcs', true,
            'requires_local_guidance', true
        )
    )
on conflict (document_code) do nothing;

comment on table public.assessment_curriculum_programs is
'Versioned canonical curriculum programs used by the assessment module.';

comment on table public.assessment_curriculum_topics is
'Book-independent curriculum domains, topics, and units.';

comment on table public.assessment_learning_requirements is
'Canonical learning requirements imported from verified official sources.';

comment on table public.assessment_mathematical_competencies is
'Canonical mathematical competencies defined by the Mathematics curriculum.';

comment on table public.assessment_requirement_competency_links is
'Reviewed links between learning requirements and mathematical competencies.';

comment on table public.assessment_regulatory_documents is
'Versioned regulatory and guidance documents governing assessment profiles.';

