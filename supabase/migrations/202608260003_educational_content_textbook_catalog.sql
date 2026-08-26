-- EDU-DB-002
-- Educational Content Source & Textbook Catalog
--
-- Additive migration.
-- No operational data is deleted or rewritten.
--
-- Canonical foundation reused from EDU-DB-001:
--   public.education_programs
--   public.grades
--   public.education_program_scopes
--   public.educational_sources
--   public.educational_source_versions
--   public.subjects
--
-- New tables:
--   public.textbook_catalog
--   public.textbook_units
--   public.media_assets
--   public.educational_asset_links


-- ============================================================
-- 1. TEXTBOOK CATALOG
-- ============================================================

create table if not exists public.textbook_catalog (
    textbook_id text primary key,

    source_id text not null
        references public.educational_sources(
            source_id
        )
        on delete restrict,

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

    textbook_family_code text not null
        check (
            char_length(
                trim(textbook_family_code)
            ) between 1 and 120
        ),

    textbook_code text not null
        check (
            char_length(
                trim(textbook_code)
            ) between 1 and 160
        ),

    title text not null
        check (
            char_length(
                trim(title)
            ) between 1 and 300
        ),

    edition_label text,

    publisher_name text,

    publication_year integer
        check (
            publication_year is null
            or publication_year
                between 1900 and 2200
        ),

    volume_code text,

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'INACTIVE',
                'ARCHIVED'
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
        not null default now(),

    constraint
        textbook_catalog_scope_code_unique
    unique (
        program_id,
        subject_id,
        grade_id,
        textbook_code
    )
);


-- ============================================================
-- 2. TEXTBOOK UNITS
-- ============================================================

create table if not exists public.textbook_units (
    textbook_unit_id text primary key,

    textbook_id text not null
        references public.textbook_catalog(
            textbook_id
        )
        on delete cascade,

    parent_unit_id text,

    unit_type text not null
        check (
            char_length(
                trim(unit_type)
            ) between 1 and 80
        ),

    canonical_code text not null
        check (
            char_length(
                trim(canonical_code)
            ) between 1 and 180
        ),

    title text not null
        check (
            char_length(
                trim(title)
            ) between 1 and 300
        ),

    sequence_number integer
        check (
            sequence_number is null
            or sequence_number > 0
        ),

    display_order integer not null
        default 0
        check (
            display_order >= 0
        ),

    curriculum_period_from integer
        check (
            curriculum_period_from is null
            or curriculum_period_from > 0
        ),

    curriculum_period_to integer
        check (
            curriculum_period_to is null
            or curriculum_period_to > 0
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'DRAFT',
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

    constraint
        textbook_units_textbook_code_unique
    unique (
        textbook_id,
        canonical_code
    ),

    constraint
        textbook_units_textbook_unit_unique
    unique (
        textbook_id,
        textbook_unit_id
    ),

    constraint
        textbook_units_parent_not_self_check
    check (
        parent_unit_id is null
        or parent_unit_id <> textbook_unit_id
    ),

    constraint
        textbook_units_curriculum_period_check
    check (
        curriculum_period_from is null
        or curriculum_period_to is null
        or curriculum_period_to
            >= curriculum_period_from
    ),

    constraint
        textbook_units_parent_same_textbook_fk
    foreign key (
        textbook_id,
        parent_unit_id
    )
    references public.textbook_units(
        textbook_id,
        textbook_unit_id
    )
    on delete cascade
);


-- ============================================================
-- 3. MEDIA ASSETS
-- ============================================================

create table if not exists public.media_assets (
    media_asset_id text primary key,

    source_version_id text
        references public.educational_source_versions(
            source_version_id
        )
        on delete set null,

    media_type text not null
        check (
            media_type in (
                'PDF',
                'IMAGE',
                'AUDIO',
                'VIDEO',
                'TRANSCRIPT',
                'DOCUMENT',
                'WORKSHEET',
                'ARCHIVE',
                'EXTERNAL_LINK'
            )
        ),

    title text not null
        check (
            char_length(
                trim(title)
            ) between 1 and 300
        ),

    mime_type text,

    language_code text,

    duration_seconds numeric
        check (
            duration_seconds is null
            or duration_seconds >= 0
        ),

    page_number integer
        check (
            page_number is null
            or page_number > 0
        ),

    storage_provider text not null
        check (
            storage_provider in (
                'SUPABASE',
                'GOOGLE_DRIVE',
                'LOCAL_IMPORT',
                'EXTERNAL'
            )
        ),

    storage_locator text,

    external_url text,

    checksum_sha256 text
        check (
            checksum_sha256 is null
            or checksum_sha256
                ~ '^[A-Fa-f0-9]{64}$'
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'INACTIVE',
                'ARCHIVED',
                'BROKEN'
            )
        ),

    metadata jsonb not null
        default '{}'::jsonb,

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now(),

    constraint
        media_assets_locator_check
    check (
        nullif(
            trim(
                coalesce(
                    storage_locator,
                    ''
                )
            ),
            ''
        ) is not null
        or
        nullif(
            trim(
                coalesce(
                    external_url,
                    ''
                )
            ),
            ''
        ) is not null
    )
);


-- ============================================================
-- 4. EDUCATIONAL ASSET LINKS
-- ============================================================

create table if not exists public.educational_asset_links (
    asset_link_id text primary key,

    media_asset_id text not null
        references public.media_assets(
            media_asset_id
        )
        on delete cascade,

    entity_type text not null
        check (
            entity_type in (
                'TEXTBOOK',
                'TEXTBOOK_UNIT',
                'SOURCE',
                'SOURCE_VERSION',
                'PROGRAM_SCOPE',
                'CANONICAL_ENTITY'
            )
        ),

    entity_id text not null
        check (
            char_length(
                trim(entity_id)
            ) between 1 and 240
        ),

    relation_type text not null
        check (
            char_length(
                trim(relation_type)
            ) between 1 and 120
        ),

    display_order integer not null
        default 0
        check (
            display_order >= 0
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

    constraint
        educational_asset_links_semantic_unique
    unique (
        media_asset_id,
        entity_type,
        entity_id,
        relation_type
    )
);


-- ============================================================
-- 5. INDEXES
-- ============================================================

create index if not exists
    textbook_catalog_program_idx
on public.textbook_catalog (
    program_id
);

create index if not exists
    textbook_catalog_subject_idx
on public.textbook_catalog (
    subject_id
);

create index if not exists
    textbook_catalog_grade_idx
on public.textbook_catalog (
    grade_id
);

create index if not exists
    textbook_catalog_source_idx
on public.textbook_catalog (
    source_id
);

create index if not exists
    textbook_catalog_status_idx
on public.textbook_catalog (
    status
);

create index if not exists
    textbook_catalog_scope_idx
on public.textbook_catalog (
    program_id,
    subject_id,
    grade_id
);

create index if not exists
    textbook_catalog_family_idx
on public.textbook_catalog (
    textbook_family_code
);


create index if not exists
    textbook_units_textbook_idx
on public.textbook_units (
    textbook_id
);

create index if not exists
    textbook_units_parent_idx
on public.textbook_units (
    parent_unit_id
);

create index if not exists
    textbook_units_type_idx
on public.textbook_units (
    unit_type
);

create index if not exists
    textbook_units_status_idx
on public.textbook_units (
    status
);

create index if not exists
    textbook_units_display_idx
on public.textbook_units (
    textbook_id,
    display_order
);

create index if not exists
    textbook_units_parent_display_idx
on public.textbook_units (
    textbook_id,
    parent_unit_id,
    display_order
);


create index if not exists
    media_assets_source_version_idx
on public.media_assets (
    source_version_id
);

create index if not exists
    media_assets_type_idx
on public.media_assets (
    media_type
);

create index if not exists
    media_assets_storage_provider_idx
on public.media_assets (
    storage_provider
);

create index if not exists
    media_assets_status_idx
on public.media_assets (
    status
);

create index if not exists
    media_assets_checksum_idx
on public.media_assets (
    checksum_sha256
);


create index if not exists
    educational_asset_links_media_idx
on public.educational_asset_links (
    media_asset_id
);

create index if not exists
    educational_asset_links_entity_type_idx
on public.educational_asset_links (
    entity_type
);

create index if not exists
    educational_asset_links_entity_id_idx
on public.educational_asset_links (
    entity_id
);

create index if not exists
    educational_asset_links_relation_idx
on public.educational_asset_links (
    relation_type
);

create index if not exists
    educational_asset_links_status_idx
on public.educational_asset_links (
    status
);

create index if not exists
    educational_asset_links_entity_idx
on public.educational_asset_links (
    entity_type,
    entity_id
);

create index if not exists
    educational_asset_links_entity_display_idx
on public.educational_asset_links (
    entity_type,
    entity_id,
    display_order
);


-- ============================================================
-- 6. UPDATED_AT
-- ============================================================

create or replace function
    public.set_educational_catalog_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


drop trigger if exists
    textbook_catalog_set_updated_at
on public.textbook_catalog;

create trigger
    textbook_catalog_set_updated_at
before update
on public.textbook_catalog
for each row
execute function
    public.set_educational_catalog_updated_at();


drop trigger if exists
    textbook_units_set_updated_at
on public.textbook_units;

create trigger
    textbook_units_set_updated_at
before update
on public.textbook_units
for each row
execute function
    public.set_educational_catalog_updated_at();


drop trigger if exists
    media_assets_set_updated_at
on public.media_assets;

create trigger
    media_assets_set_updated_at
before update
on public.media_assets
for each row
execute function
    public.set_educational_catalog_updated_at();


drop trigger if exists
    educational_asset_links_set_updated_at
on public.educational_asset_links;

create trigger
    educational_asset_links_set_updated_at
before update
on public.educational_asset_links
for each row
execute function
    public.set_educational_catalog_updated_at();


-- ============================================================
-- 7. ROW LEVEL SECURITY
-- ============================================================

alter table public.textbook_catalog
    enable row level security;

alter table public.textbook_units
    enable row level security;

alter table public.media_assets
    enable row level security;

alter table public.educational_asset_links
    enable row level security;


-- ============================================================
-- 8. PRIVILEGES
-- ============================================================

revoke all
on table public.textbook_catalog
from anon, authenticated;

revoke all
on table public.textbook_units
from anon, authenticated;

revoke all
on table public.media_assets
from anon, authenticated;

revoke all
on table public.educational_asset_links
from anon, authenticated;


grant select
on table public.textbook_catalog
to authenticated;

grant select
on table public.textbook_units
to authenticated;

grant select
on table public.media_assets
to authenticated;

grant select
on table public.educational_asset_links
to authenticated;


-- ============================================================
-- 9. AUTHENTICATED READ POLICIES
-- ============================================================

drop policy if exists
    "authenticated_read_textbook_catalog"
on public.textbook_catalog;

create policy
    "authenticated_read_textbook_catalog"
on public.textbook_catalog
for select
to authenticated
using (true);


drop policy if exists
    "authenticated_read_textbook_units"
on public.textbook_units;

create policy
    "authenticated_read_textbook_units"
on public.textbook_units
for select
to authenticated
using (true);


drop policy if exists
    "authenticated_read_media_assets"
on public.media_assets;

create policy
    "authenticated_read_media_assets"
on public.media_assets
for select
to authenticated
using (true);


drop policy if exists
    "authenticated_read_educational_asset_links"
on public.educational_asset_links;

create policy
    "authenticated_read_educational_asset_links"
on public.educational_asset_links
for select
to authenticated
using (true);


-- ============================================================
-- 10. FUNCTION PRIVILEGES
-- ============================================================

revoke all
on function
    public.set_educational_catalog_updated_at()
from public;

-- No direct EXECUTE grant is required for application clients.
-- The function is invoked by table triggers.


-- ============================================================
-- END EDU-DB-002
-- ============================================================
