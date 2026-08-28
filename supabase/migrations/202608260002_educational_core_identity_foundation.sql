-- Educational Core identity/source foundation.
-- Additive migration: does not replace existing domain tables.

create table if not exists public.education_programs (
    program_id text primary key,

    code text not null unique
        check (
            char_length(trim(code))
            between 1 and 80
        ),

    name text not null
        check (
            char_length(trim(name))
            between 1 and 200
        ),

    country_code text not null
        default 'VN'
        check (
            char_length(trim(country_code))
            between 2 and 3
        ),

    program_type text not null
        default 'GENERAL_EDUCATION'
        check (
            char_length(trim(program_type))
            between 1 and 80
        ),

    effective_from date,
    effective_to date,

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE',
                'ARCHIVED'
            )
        ),

    metadata jsonb not null
        default '{}'::jsonb,

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now(),

    created_by uuid,
    updated_by uuid,

    constraint
        education_programs_effective_range_check
    check (
        effective_to is null
        or effective_from is null
        or effective_to >= effective_from
    )
);


create table if not exists public.grades (
    grade_id text primary key,

    code text not null unique
        check (
            char_length(trim(code))
            between 1 and 50
        ),

    name text not null
        check (
            char_length(trim(name))
            between 1 and 100
        ),

    grade_number smallint
        not null unique
        check (
            grade_number between 1 and 12
        ),

    school_level text not null
        check (
            school_level in (
                'PRIMARY',
                'LOWER_SECONDARY',
                'UPPER_SECONDARY'
            )
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    display_order integer not null
        default 0
        check (
            display_order >= 0
        ),

    metadata jsonb not null
        default '{}'::jsonb,

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now()
);


create table if not exists
    public.education_program_scopes (
        program_scope_id text primary key,

        program_id text not null
            references public.education_programs(
                program_id
            )
            on delete restrict,

        subject_id text not null
            references public.subjects(
                subject_id
            )
            on delete restrict,

        grade_id text not null
            references public.grades(
                grade_id
            )
            on delete restrict,

        status text not null
            default 'ACTIVE'
            check (
                status in (
                    'ACTIVE',
                    'INACTIVE'
                )
            ),

        metadata jsonb not null
            default '{}'::jsonb,

        created_at timestamptz
            not null default now(),

        updated_at timestamptz
            not null default now(),

        constraint
            education_program_scopes_program_subject_grade_unique
        unique (
            program_id,
            subject_id,
            grade_id
        )
    );


create table if not exists
    public.educational_sources (
        source_id text primary key,

        code text not null unique
            check (
                char_length(trim(code))
                between 1 and 120
            ),

        name text not null
            check (
                char_length(trim(name))
                between 1 and 250
            ),

        source_kind text not null
            check (
                char_length(trim(source_kind))
                between 1 and 80
            ),

        program_id text
            references public.education_programs(
                program_id
            )
            on delete restrict,

        subject_id text
            references public.subjects(
                subject_id
            )
            on delete restrict,

        grade_id text
            references public.grades(
                grade_id
            )
            on delete restrict,

        rights_status text not null
            default 'UNKNOWN'
            check (
                rights_status in (
                    'VERIFIED_ALLOWED',
                    'RESTRICTED',
                    'INTERNAL_REFERENCE',
                    'UNKNOWN'
                )
            ),

        access_scope text not null
            default 'SYSTEM_INTERNAL'
            check (
                access_scope in (
                    'SYSTEM_INTERNAL',
                    'AUTHORIZED_USERS',
                    'PUBLIC'
                )
            ),

        status text not null
            default 'ACTIVE'
            check (
                status in (
                    'ACTIVE',
                    'INACTIVE',
                    'ARCHIVED'
                )
            ),

        metadata jsonb not null
            default '{}'::jsonb,

        created_at timestamptz
            not null default now(),

        updated_at timestamptz
            not null default now(),

        created_by uuid,
        updated_by uuid
    );


create table if not exists
    public.educational_source_versions (
        source_version_id text primary key,

        source_id text not null
            references public.educational_sources(
                source_id
            )
            on delete restrict,

        version_number integer not null
            check (
                version_number > 0
            ),

        edition_label text,

        publication_year integer
            check (
                publication_year is null
                or publication_year
                    between 1900 and 2200
            ),

        publisher_name text,
        publisher_reference text,
        source_locator text,

        checksum_sha256 text
            check (
                checksum_sha256 is null
                or checksum_sha256
                    ~ '^[A-Fa-f0-9]{64}$'
            ),

        verification_status text not null
            default 'UNVERIFIED'
            check (
                verification_status in (
                    'UNVERIFIED',
                    'VERIFIED',
                    'REJECTED'
                )
            ),

        publication_status text not null
            default 'DRAFT'
            check (
                publication_status in (
                    'DRAFT',
                    'REVIEW',
                    'VERIFIED',
                    'PUBLISHED',
                    'DEPRECATED',
                    'ARCHIVED'
                )
            ),

        metadata jsonb not null
            default '{}'::jsonb,

        created_at timestamptz
            not null default now(),

        created_by uuid,

        verified_at timestamptz,
        verified_by uuid,

        constraint
            educational_source_versions_source_version_unique
        unique (
            source_id,
            version_number
        ),

        constraint
            educational_source_versions_verification_actor_check
        check (
            verification_status <> 'VERIFIED'
            or (
                verified_at is not null
                and verified_by is not null
            )
        )
    );


create table if not exists
    public.canonical_entity_links (
        link_id text primary key,

        canonical_entity_type text not null
            check (
                char_length(
                    trim(canonical_entity_type)
                )
                between 1 and 80
            ),

        canonical_entity_code text not null
            check (
                char_length(
                    trim(canonical_entity_code)
                )
                between 1 and 160
            ),

        domain_name text not null
            check (
                char_length(trim(domain_name))
                between 1 and 80
            ),

        domain_entity_type text not null
            check (
                char_length(
                    trim(domain_entity_type)
                )
                between 1 and 120
            ),

        domain_entity_key text not null
            check (
                char_length(
                    trim(domain_entity_key)
                )
                between 1 and 240
            ),

        link_type text not null
            default 'COMPATIBILITY'
            check (
                link_type in (
                    'COMPATIBILITY',
                    'MIGRATION',
                    'TRACEABILITY'
                )
            ),

        status text not null
            default 'ACTIVE'
            check (
                status in (
                    'ACTIVE',
                    'INACTIVE',
                    'ARCHIVED'
                )
            ),

        metadata jsonb not null
            default '{}'::jsonb,

        created_at timestamptz
            not null default now(),

        created_by uuid,

        constraint
            canonical_entity_links_unique_mapping
        unique (
            canonical_entity_type,
            canonical_entity_code,
            domain_name,
            domain_entity_type,
            domain_entity_key
        )
    );


create index if not exists
    education_program_scopes_subject_grade_idx
on public.education_program_scopes (
    subject_id,
    grade_id
);


create index if not exists
    educational_sources_subject_grade_idx
on public.educational_sources (
    subject_id,
    grade_id
);


create index if not exists
    educational_source_versions_source_status_idx
on public.educational_source_versions (
    source_id,
    publication_status,
    version_number
);


create index if not exists
    canonical_entity_links_canonical_idx
on public.canonical_entity_links (
    canonical_entity_type,
    canonical_entity_code
);


create index if not exists
    canonical_entity_links_domain_idx
on public.canonical_entity_links (
    domain_name,
    domain_entity_type,
    domain_entity_key
);


/*
English is a first-class subject.

Preserve the existing stable subject identity so current
teacher assignment, timetable and portal relationships
remain valid.

Listening, Speaking, Reading, Writing, Grammar,
Vocabulary and Pronunciation are not subject components.
*/

update public.subjects
set
    name = 'Tiếng Anh',
    component_policy = 'NONE',
    updated_at = now()
where
    subject_id = 'subject-foreign-language-1';


insert into public.education_programs (
    program_id,
    code,
    name,
    country_code,
    program_type,
    status
)
values (
    'program-vn-gdpt-2018',
    'VN_GDPT_2018',
    'Chương trình giáo dục phổ thông 2018',
    'VN',
    'GENERAL_EDUCATION',
    'ACTIVE'
)
on conflict (
    program_id
)
do update
set
    code = excluded.code,
    name = excluded.name,
    country_code = excluded.country_code,
    program_type = excluded.program_type,
    status = excluded.status,
    updated_at = now();


insert into public.grades (
    grade_id,
    code,
    name,
    grade_number,
    school_level,
    status,
    display_order
)
select
    'grade-' ||
        lpad(gs::text, 2, '0'),

    'GRADE_' ||
        lpad(gs::text, 2, '0'),

    'Lớp ' || gs::text,

    gs,

    case
        when gs between 1 and 5
            then 'PRIMARY'
        when gs between 6 and 9
            then 'LOWER_SECONDARY'
        else 'UPPER_SECONDARY'
    end,

    'ACTIVE',

    gs * 10
from generate_series(1, 12) as gs
on conflict (
    grade_id
)
do update
set
    code = excluded.code,
    name = excluded.name,
    grade_number = excluded.grade_number,
    school_level = excluded.school_level,
    status = excluded.status,
    display_order = excluded.display_order,
    updated_at = now();


insert into public.education_program_scopes (
    program_scope_id,
    program_id,
    subject_id,
    grade_id,
    status
)
select
    'scope-gdpt2018-math-' ||
        lpad(gs::text, 2, '0'),

    'program-vn-gdpt-2018',

    'subject-math',

    'grade-' ||
        lpad(gs::text, 2, '0'),

    'ACTIVE'
from generate_series(6, 9) as gs
where exists (
    select 1
    from public.subjects s
    where
        s.subject_id = 'subject-math'
)
on conflict (
    program_id,
    subject_id,
    grade_id
)
do update
set
    status = excluded.status,
    updated_at = now();


insert into public.education_program_scopes (
    program_scope_id,
    program_id,
    subject_id,
    grade_id,
    status
)
select
    'scope-gdpt2018-english-' ||
        lpad(gs::text, 2, '0'),

    'program-vn-gdpt-2018',

    'subject-foreign-language-1',

    'grade-' ||
        lpad(gs::text, 2, '0'),

    'ACTIVE'
from generate_series(6, 9) as gs
where exists (
    select 1
    from public.subjects s
    where
        s.subject_id =
            'subject-foreign-language-1'
)
on conflict (
    program_id,
    subject_id,
    grade_id
)
do update
set
    status = excluded.status,
    updated_at = now();


alter table
    public.education_programs
enable row level security;

alter table
    public.grades
enable row level security;

alter table
    public.education_program_scopes
enable row level security;

alter table
    public.educational_sources
enable row level security;

alter table
    public.educational_source_versions
enable row level security;

alter table
    public.canonical_entity_links
enable row level security;


revoke all
on table public.education_programs
from anon;

revoke all
on table public.grades
from anon;

revoke all
on table public.education_program_scopes
from anon;

revoke all
on table public.educational_sources
from anon;

revoke all
on table public.educational_source_versions
from anon;

revoke all
on table public.canonical_entity_links
from anon;


grant select
on table public.education_programs
to authenticated;

grant select
on table public.grades
to authenticated;

grant select
on table public.education_program_scopes
to authenticated;

grant select
on table public.educational_sources
to authenticated;

grant select
on table public.educational_source_versions
to authenticated;

grant select
on table public.canonical_entity_links
to authenticated;


grant
    insert,
    update,
    delete
on table public.education_programs
to authenticated;

grant
    insert,
    update,
    delete
on table public.grades
to authenticated;

grant
    insert,
    update,
    delete
on table public.education_program_scopes
to authenticated;

grant
    insert,
    update,
    delete
on table public.educational_sources
to authenticated;

grant
    insert,
    update,
    delete
on table public.educational_source_versions
to authenticated;

grant
    insert,
    update,
    delete
on table public.canonical_entity_links
to authenticated;


create policy
    "authenticated_read_education_programs"
on public.education_programs
for select
to authenticated
using (
    (select auth.uid()) is not null
);


create policy
    "authenticated_read_grades"
on public.grades
for select
to authenticated
using (
    (select auth.uid()) is not null
);


create policy
    "authenticated_read_education_program_scopes"
on public.education_program_scopes
for select
to authenticated
using (
    (select auth.uid()) is not null
);


create policy
    "authenticated_read_educational_sources"
on public.educational_sources
for select
to authenticated
using (
    (select auth.uid()) is not null
    and status = 'ACTIVE'
    and access_scope in (
        'AUTHORIZED_USERS',
        'PUBLIC',
        'SYSTEM_INTERNAL'
    )
);


create policy
    "authenticated_read_educational_source_versions"
on public.educational_source_versions
for select
to authenticated
using (
    (select auth.uid()) is not null
    and exists (
        select 1
        from public.educational_sources s
        where
            s.source_id =
                educational_source_versions.source_id
            and s.status = 'ACTIVE'
            and s.access_scope in (
                'AUTHORIZED_USERS',
                'PUBLIC',
                'SYSTEM_INTERNAL'
            )
    )
);


create policy
    "authenticated_read_canonical_entity_links"
on public.canonical_entity_links
for select
to authenticated
using (
    (select auth.uid()) is not null
    and status = 'ACTIVE'
);


create policy
    "admin_manage_education_programs"
on public.education_programs
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


create policy
    "admin_manage_grades"
on public.grades
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


create policy
    "admin_manage_education_program_scopes"
on public.education_program_scopes
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


create policy
    "admin_manage_educational_sources"
on public.educational_sources
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


create policy
    "admin_manage_educational_source_versions"
on public.educational_source_versions
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


create policy
    "admin_manage_canonical_entity_links"
on public.canonical_entity_links
for all
to authenticated
using (
    (
        select
            public.current_user_is_portal_admin()
    )
)
with check (
    (
        select
            public.current_user_is_portal_admin()
    )
);


comment on table public.education_programs is
'Canonical education-program registry shared by all MathTeacher-AI tools.';

comment on table public.grades is
'Canonical grade registry shared across subjects and tools.';

comment on table public.education_program_scopes is
'Program + first-class subject + grade scopes. English remains a subject, not a component.';

comment on table public.educational_sources is
'Canonical source identity; file/media representations are modeled separately in later packages.';

comment on table public.educational_source_versions is
'Versioned source/provenance boundary for curriculum, textbook and multimedia ingestion.';

comment on table public.canonical_entity_links is
'Transitional compatibility bridge only; not a replacement for domain foreign keys.';
