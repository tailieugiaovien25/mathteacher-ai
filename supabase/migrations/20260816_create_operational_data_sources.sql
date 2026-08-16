create table if not exists public.operational_data_sources (
    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    source_id text not null,

    data_type text not null,

    origin text not null,

    owner_id text not null,

    academic_year text not null,

    status text not null,

    source_name text,

    source_version text,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    primary key (
        user_id,
        source_id
    ),

    constraint operational_data_sources_owner_matches_user
        check (
            owner_id = user_id::text
        ),

    constraint operational_data_sources_data_type_check
        check (
            data_type in (
                'PPCT',
                'TIMETABLE',
                'ACADEMIC_WEEK',
                'WEEKLY_SCHEDULE_TEMPLATE'
            )
        ),

    constraint operational_data_sources_origin_check
        check (
            origin in (
                'FILE_IMPORTED',
                'USER_ENTERED',
                'ADMIN_ENTERED',
                'SYSTEM_GENERATED'
            )
        ),

    constraint operational_data_sources_status_check
        check (
            status in (
                'UPLOADED',
                'MAPPED',
                'VALIDATED',
                'ACTIVE',
                'SUPERSEDED'
            )
        )
);

create index if not exists
    idx_operational_data_sources_workspace
on public.operational_data_sources (
    user_id,
    academic_year,
    data_type,
    status
);

alter table public.operational_data_sources
enable row level security;

drop policy if exists
    operational_data_sources_select_own
on public.operational_data_sources;

create policy
    operational_data_sources_select_own
on public.operational_data_sources
for select
using (
    auth.uid() = user_id
);

drop policy if exists
    operational_data_sources_insert_own
on public.operational_data_sources;

create policy
    operational_data_sources_insert_own
on public.operational_data_sources
for insert
with check (
    auth.uid() = user_id
    and owner_id = auth.uid()::text
);

drop policy if exists
    operational_data_sources_update_own
on public.operational_data_sources;

create policy
    operational_data_sources_update_own
on public.operational_data_sources
for update
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
    and owner_id = auth.uid()::text
);

drop policy if exists
    operational_data_sources_delete_own
on public.operational_data_sources;

create policy
    operational_data_sources_delete_own
on public.operational_data_sources
for delete
using (
    auth.uid() = user_id
);
