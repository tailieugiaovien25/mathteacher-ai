create table if not exists public.operational_payloads (
    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    source_id text not null,

    data_type text not null,

    payload_version text not null
        default '',

    payload jsonb not null,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    primary key (
        user_id,
        source_id,
        data_type,
        payload_version
    )
);

create index if not exists
    idx_operational_payloads_source
on public.operational_payloads (
    user_id,
    source_id,
    data_type
);

grant select, insert, update, delete
on table public.operational_payloads
to authenticated;

alter table public.operational_payloads
enable row level security;

drop policy if exists
    operational_payloads_select_own
on public.operational_payloads;

create policy
    operational_payloads_select_own
on public.operational_payloads
for select
using (
    auth.uid() = user_id
);

drop policy if exists
    operational_payloads_insert_own
on public.operational_payloads;

create policy
    operational_payloads_insert_own
on public.operational_payloads
for insert
with check (
    auth.uid() = user_id
);

drop policy if exists
    operational_payloads_update_own
on public.operational_payloads;

create policy
    operational_payloads_update_own
on public.operational_payloads
for update
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
);

drop policy if exists
    operational_payloads_delete_own
on public.operational_payloads;

create policy
    operational_payloads_delete_own
on public.operational_payloads
for delete
using (
    auth.uid() = user_id
);
