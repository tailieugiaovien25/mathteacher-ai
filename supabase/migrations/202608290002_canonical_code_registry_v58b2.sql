-- V58-B2: ADMIN Canonical Code Registry + canonical teacher educational input
-- Additive foundation. Existing technical PK/FK values remain authoritative.

create table if not exists public.canonical_code_registry (
    code_id uuid primary key default gen_random_uuid(),
    namespace text not null,
    code text not null,
    label text not null,
    status text not null default 'ACTIVE'
        check (status in ('ACTIVE','INACTIVE')),
    rule_version integer not null default 1 check (rule_version >= 1),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(namespace, code)
);

create table if not exists public.canonical_code_mappings (
    mapping_id uuid primary key default gen_random_uuid(),
    namespace text not null,
    legacy_code text not null,
    canonical_code_id uuid not null
        references public.canonical_code_registry(code_id),
    valid_from timestamptz not null default now(),
    valid_to timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    unique(namespace, legacy_code, valid_from)
);

create table if not exists public.canonical_code_generation_rules (
    rule_id uuid primary key default gen_random_uuid(),
    namespace text not null,
    rule_version integer not null,
    template text not null,
    status text not null default 'ACTIVE'
        check (status in ('ACTIVE','INACTIVE')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique(namespace, rule_version)
);

create table if not exists public.canonical_teacher_educational_inputs (
    input_id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null,
    source_id uuid,
    source_version_id uuid,
    sheet_name text,
    row_position integer not null check (row_position >= 1),
    column_mapping jsonb not null default '{}'::jsonb,

    grade integer not null check (grade >= 1),
    mon text not null,
    pmon text,
    ppct integer not null check (ppct >= 1),
    bai text,
    ten_bai text,
    giao_an text,
    ten_tb text,
    sltb numeric,

    subject_business_id text not null,
    curriculum_business_id text not null,
    lesson_plan_business_id text,
    equipment_group_business_id text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique(owner_user_id, source_version_id, sheet_name, row_position)
);

create index if not exists idx_canonical_input_owner_curriculum
on public.canonical_teacher_educational_inputs(owner_user_id, curriculum_business_id);

create index if not exists idx_canonical_input_owner_lesson_plan
on public.canonical_teacher_educational_inputs(owner_user_id, lesson_plan_business_id);

-- Initial ADMIN-managed catalog. These are data rows, not application authority constants.
insert into public.canonical_code_registry(namespace, code, label)
values
 ('subject','T','Toán'),
 ('subject','A','Tiếng Anh'),
 ('subject','NT','Nghệ thuật'),
 ('component','TDS','Đại số'),
 ('component','THH','Hình học'),
 ('component','TXS','Xác suất thống kê'),
 ('component','NTN','Âm nhạc'),
 ('lesson_plan','GT','Giáo án Toán'),
 ('lesson_plan','GTDS','Giáo án Toán - Đại số'),
 ('lesson_plan','GTHH','Giáo án Toán - Hình học'),
 ('lesson_plan','GXS','Giáo án Toán - Xác suất thống kê'),
 ('lesson_plan','GTA','Giáo án Tiếng Anh'),
 ('equipment','TB','Thiết bị')
on conflict(namespace, code) do nothing;

insert into public.canonical_code_generation_rules(namespace, rule_version, template)
values
 ('subject',1,'{grade}{code}'),
 ('curriculum',1,'{grade}{code}{ppct:03d}'),
 ('lesson_plan',1,'{grade}{code}{ppct:03d}'),
 ('equipment',1,'{grade}{code}{ppct:03d}')
on conflict(namespace, rule_version) do nothing;


-- V58-B4A ADMIN RLS
alter table public.canonical_code_registry enable row level security;
alter table public.canonical_code_mappings enable row level security;
alter table public.canonical_code_generation_rules enable row level security;
alter table public.canonical_teacher_educational_inputs enable row level security;

-- Registry/rules are readable by authenticated users because runtime features
-- must resolve canonical codes. Mutations are ADMIN-only through the existing
-- portal role model.
create policy canonical_code_registry_authenticated_read
on public.canonical_code_registry for select to authenticated using (true);

create policy canonical_code_rules_authenticated_read
on public.canonical_code_generation_rules for select to authenticated using (true);

create policy canonical_code_mappings_authenticated_read
on public.canonical_code_mappings for select to authenticated using (true);

create policy canonical_code_registry_admin_write
on public.canonical_code_registry for all to authenticated
using (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ))
with check (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));

create policy canonical_code_rules_admin_write
on public.canonical_code_generation_rules for all to authenticated
using (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ))
with check (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));

create policy canonical_code_mappings_admin_write
on public.canonical_code_mappings for all to authenticated
using (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ))
with check (exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));

create policy canonical_teacher_input_owner_read
on public.canonical_teacher_educational_inputs for select to authenticated
using (owner_user_id = (select auth.uid()) or exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));

create policy canonical_teacher_input_owner_insert
on public.canonical_teacher_educational_inputs for insert to authenticated
with check (owner_user_id = (select auth.uid()) or exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));

create policy canonical_teacher_input_owner_update
on public.canonical_teacher_educational_inputs for update to authenticated
using (owner_user_id = (select auth.uid()) or exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ))
with check (owner_user_id = (select auth.uid()) or exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    ));
