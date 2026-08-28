-- Assessment Profile Foundation V1
-- Configurable assessment types, question types, cognitive levels,
-- profile sections, level allocations, and regulatory links.

create table if not exists public.assessment_types (
    assessment_type_code text primary key
        check (char_length(assessment_type_code) between 1 and 100),

    assessment_type_name text not null
        check (char_length(assessment_type_name) between 1 and 300),

    assessment_category text not null
        check (
            assessment_category in (
                'REGULAR',
                'PERIODIC',
                'SURVEY',
                'PRACTICE',
                'COMPETITION',
                'ENTRANCE'
            )
        ),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    status text not null default 'ACTIVE'
        check (status in ('ACTIVE', 'INACTIVE')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_question_types (
    question_type_code text primary key
        check (char_length(question_type_code) between 1 and 100),

    question_type_name text not null
        check (char_length(question_type_name) between 1 and 300),

    answer_mode text not null
        check (
            answer_mode in (
                'SINGLE_CHOICE',
                'TRUE_FALSE_STATEMENTS',
                'SHORT_RESPONSE',
                'CONSTRUCTED_RESPONSE'
            )
        ),

    supports_options boolean not null default false,
    supports_statements boolean not null default false,
    requires_solution boolean not null default true,

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    status text not null default 'ACTIVE'
        check (status in ('ACTIVE', 'INACTIVE')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_cognitive_levels (
    cognitive_level_code text primary key
        check (char_length(cognitive_level_code) between 1 and 100),

    cognitive_level_name text not null
        check (char_length(cognitive_level_name) between 1 and 200),

    description text not null default '',

    sequence_number integer not null
        check (sequence_number >= 0),

    status text not null default 'ACTIVE'
        check (status in ('ACTIVE', 'INACTIVE')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_profiles (
    profile_code text primary key
        check (char_length(profile_code) between 1 and 140),

    profile_name text not null
        check (char_length(profile_name) between 1 and 400),

    program_code text not null
        references public.assessment_curriculum_programs(program_code)
        on update cascade
        on delete restrict,

    assessment_type_code text not null
        references public.assessment_types(assessment_type_code)
        on update cascade
        on delete restrict,

    subject_code text not null default 'MATH'
        check (char_length(subject_code) between 1 and 100),

    education_level text not null
        check (education_level in ('THCS', 'THPT', 'PRIMARY')),

    grade_min integer not null
        check (grade_min between 1 and 12),

    grade_max integer not null
        check (grade_max between 1 and 12),

    total_score numeric(6,2) not null default 10
        check (total_score > 0),

    duration_minutes integer not null
        check (duration_minutes > 0),

    version_number integer not null default 1
        check (version_number >= 1),

    replaces_profile_code text null
        references public.assessment_profiles(profile_code)
        on update cascade
        on delete restrict,

    effective_from date null,
    effective_to date null,

    status text not null default 'DRAFT'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'INACTIVE',
                'SUPERSEDED'
            )
        ),

    is_default boolean not null default false,
    metadata jsonb not null default '{}'::jsonb,

    created_by uuid null
        references auth.users(id)
        on delete set null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (grade_min <= grade_max),
    check (
        replaces_profile_code
        is distinct from profile_code
    ),
    check (
        effective_to is null
        or effective_from is null
        or effective_to >= effective_from
    )
);

create table if not exists public.assessment_profile_sections (
    profile_code text not null
        references public.assessment_profiles(profile_code)
        on update cascade
        on delete cascade,

    section_code text not null
        check (char_length(section_code) between 1 and 100),

    section_name text not null
        check (char_length(section_name) between 1 and 300),

    question_type_code text not null
        references public.assessment_question_types(question_type_code)
        on update cascade
        on delete restrict,

    sequence_number integer not null
        check (sequence_number >= 0),

    question_count integer not null
        check (question_count > 0),

    response_count integer not null
        check (response_count > 0),

    section_score numeric(6,2) not null
        check (section_score > 0),

    score_per_response numeric(8,4) null
        check (
            score_per_response is null
            or score_per_response > 0
        ),

    instructions text not null default '',
    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    primary key (
        profile_code,
        section_code
    ),

    unique (
        profile_code,
        sequence_number
    ),

    check (response_count >= question_count)
);

create table if not exists public.assessment_profile_level_allocations (
    profile_code text not null
        references public.assessment_profiles(profile_code)
        on update cascade
        on delete cascade,

    cognitive_level_code text not null
        references public.assessment_cognitive_levels(cognitive_level_code)
        on update cascade
        on delete restrict,

    target_score numeric(6,2) not null
        check (target_score >= 0),

    target_percentage numeric(5,2) not null
        check (
            target_percentage >= 0
            and target_percentage <= 100
        ),

    tolerance_percentage numeric(5,2) not null default 0
        check (
            tolerance_percentage >= 0
            and tolerance_percentage <= 100
        ),

    created_at timestamptz not null default now(),

    primary key (
        profile_code,
        cognitive_level_code
    )
);

create table if not exists public.assessment_profile_regulatory_links (
    profile_code text not null
        references public.assessment_profiles(profile_code)
        on update cascade
        on delete cascade,

    document_code text not null
        references public.assessment_regulatory_documents(document_code)
        on update cascade
        on delete restrict,

    relationship_type text not null
        check (
            relationship_type in (
                'AUTHORITY',
                'GUIDANCE',
                'REFERENCE',
                'LOCAL_OVERRIDE'
            )
        ),

    applicability_note text not null default '',

    created_at timestamptz not null default now(),

    primary key (
        profile_code,
        document_code
    )
);

create index if not exists
    assessment_profiles_scope_idx
on public.assessment_profiles (
    subject_code,
    education_level,
    grade_min,
    grade_max,
    assessment_type_code,
    status
);

create index if not exists
    assessment_profiles_replacement_idx
on public.assessment_profiles (
    replaces_profile_code
);

create index if not exists
    assessment_profile_sections_type_idx
on public.assessment_profile_sections (
    question_type_code
);

alter table public.assessment_types
    enable row level security;

alter table public.assessment_question_types
    enable row level security;

alter table public.assessment_cognitive_levels
    enable row level security;

alter table public.assessment_profiles
    enable row level security;

alter table public.assessment_profile_sections
    enable row level security;

alter table public.assessment_profile_level_allocations
    enable row level security;

alter table public.assessment_profile_regulatory_links
    enable row level security;

revoke all on table
    public.assessment_types,
    public.assessment_question_types,
    public.assessment_cognitive_levels,
    public.assessment_profiles,
    public.assessment_profile_sections,
    public.assessment_profile_level_allocations,
    public.assessment_profile_regulatory_links
from anon;

grant select, insert, update, delete on table
    public.assessment_types,
    public.assessment_question_types,
    public.assessment_cognitive_levels,
    public.assessment_profiles,
    public.assessment_profile_sections,
    public.assessment_profile_level_allocations,
    public.assessment_profile_regulatory_links
to authenticated;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_types',
        'assessment_question_types',
        'assessment_cognitive_levels',
        'assessment_profiles',
        'assessment_profile_sections',
        'assessment_profile_level_allocations',
        'assessment_profile_regulatory_links'
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

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_types',
        'assessment_question_types',
        'assessment_cognitive_levels',
        'assessment_profiles',
        'assessment_profile_sections',
        'assessment_profile_level_allocations',
        'assessment_profile_regulatory_links'
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

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_types',
        'assessment_question_types',
        'assessment_cognitive_levels',
        'assessment_profiles',
        'assessment_profile_sections'
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

insert into public.assessment_types (
    assessment_type_code,
    assessment_type_name,
    assessment_category,
    sequence_number,
    status
)
values
    (
        'MIDTERM',
        'Kiểm tra giữa học kỳ',
        'PERIODIC',
        10,
        'ACTIVE'
    ),
    (
        'FINAL',
        'Kiểm tra cuối học kỳ',
        'PERIODIC',
        20,
        'ACTIVE'
    )
on conflict (assessment_type_code) do nothing;

insert into public.assessment_question_types (
    question_type_code,
    question_type_name,
    answer_mode,
    supports_options,
    supports_statements,
    requires_solution,
    sequence_number,
    status
)
values
    (
        'MULTIPLE_CHOICE',
        'Trắc nghiệm nhiều lựa chọn',
        'SINGLE_CHOICE',
        true,
        false,
        true,
        10,
        'ACTIVE'
    ),
    (
        'TRUE_FALSE',
        'Trắc nghiệm đúng – sai',
        'TRUE_FALSE_STATEMENTS',
        false,
        true,
        true,
        20,
        'ACTIVE'
    ),
    (
        'SHORT_RESPONSE',
        'Trả lời ngắn',
        'SHORT_RESPONSE',
        false,
        false,
        true,
        30,
        'ACTIVE'
    ),
    (
        'ESSAY',
        'Tự luận',
        'CONSTRUCTED_RESPONSE',
        false,
        false,
        true,
        40,
        'ACTIVE'
    )
on conflict (question_type_code) do nothing;

insert into public.assessment_cognitive_levels (
    cognitive_level_code,
    cognitive_level_name,
    description,
    sequence_number,
    status
)
values
    (
        'KNOW',
        'Biết',
        'Nhận biết, nhắc lại hoặc thực hiện trực tiếp yêu cầu toán học.',
        10,
        'ACTIVE'
    ),
    (
        'UNDERSTAND',
        'Hiểu',
        'Giải thích, kết nối hoặc áp dụng trong tình huống quen thuộc.',
        20,
        'ACTIVE'
    ),
    (
        'APPLY',
        'Vận dụng',
        'Giải quyết tình huống mới, bài toán nhiều bước hoặc thực tiễn.',
        30,
        'ACTIVE'
    )
on conflict (cognitive_level_code) do nothing;

insert into public.assessment_profiles (
    profile_code,
    profile_name,
    program_code,
    assessment_type_code,
    subject_code,
    education_level,
    grade_min,
    grade_max,
    total_score,
    duration_minutes,
    version_number,
    status,
    is_default,
    metadata
)
values (
    'MATH-THCS-DEFAULT-3223-V1',
    'Đề Toán THCS tham khảo 3–2–2–3',
    'MOET-GDPT2018-MATH-THCS',
    'FINAL',
    'MATH',
    'THCS',
    6,
    9,
    10.00,
    90,
    1,
    'DRAFT',
    false,
    jsonb_build_object(
        'multiple_choice_score', 3,
        'true_false_score', 2,
        'short_response_score', 2,
        'essay_score', 3,
        'requires_local_approval', true,
        'not_nationally_mandatory_for_thcs', true
    )
)
on conflict (profile_code) do nothing;

insert into public.assessment_profile_sections (
    profile_code,
    section_code,
    section_name,
    question_type_code,
    sequence_number,
    question_count,
    response_count,
    section_score,
    score_per_response,
    instructions
)
values
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'MCQ',
        'Trắc nghiệm nhiều lựa chọn',
        'MULTIPLE_CHOICE',
        10,
        12,
        12,
        3.00,
        0.25,
        'Chọn một phương án đúng nhất cho mỗi câu.'
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'TF',
        'Trắc nghiệm đúng – sai',
        'TRUE_FALSE',
        20,
        2,
        8,
        2.00,
        0.25,
        'Mỗi câu gồm bốn ý; xác định từng ý đúng hoặc sai.'
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'SHORT',
        'Trả lời ngắn',
        'SHORT_RESPONSE',
        30,
        4,
        4,
        2.00,
        0.50,
        'Ghi đáp án ngắn gọn theo yêu cầu.'
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'ESSAY',
        'Tự luận',
        'ESSAY',
        40,
        2,
        2,
        3.00,
        null,
        'Trình bày đầy đủ lời giải.'
    )
on conflict (profile_code, section_code) do nothing;

insert into public.assessment_profile_level_allocations (
    profile_code,
    cognitive_level_code,
    target_score,
    target_percentage,
    tolerance_percentage
)
values
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'KNOW',
        4.00,
        40.00,
        0
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'UNDERSTAND',
        3.00,
        30.00,
        0
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'APPLY',
        3.00,
        30.00,
        0
    )
on conflict (
    profile_code,
    cognitive_level_code
) do nothing;

insert into public.assessment_profile_regulatory_links (
    profile_code,
    document_code,
    relationship_type,
    applicability_note
)
values
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'TT-22-2021-BGDDT',
        'AUTHORITY',
        'Căn cứ chung về kiểm tra, đánh giá học sinh THCS.'
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'TT-32-2018-BGDDT',
        'AUTHORITY',
        'Căn cứ xác định yêu cầu cần đạt môn Toán.'
    ),
    (
        'MATH-THCS-DEFAULT-3223-V1',
        'CV-7991-2024-BGDDT-GDTRH',
        'REFERENCE',
        'Chỉ sử dụng làm mẫu kỹ thuật khi phù hợp hướng dẫn địa phương.'
    )
on conflict (
    profile_code,
    document_code
) do nothing;

comment on table public.assessment_profiles is
'Versioned configurable assessment profiles; no exam structure is hard-coded in application code.';

comment on table public.assessment_profile_sections is
'Question sections and scores belonging to one assessment profile.';

comment on column
public.assessment_profile_sections.question_count is
'Number of question containers; a true-false question may contain multiple responses.';

comment on column
public.assessment_profile_sections.response_count is
'Number of individually scored responses or commands in the section.';

