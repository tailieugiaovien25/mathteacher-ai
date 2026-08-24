create table if not exists public.portal_roles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    role text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint portal_roles_role_check
        check (role in ('teacher', 'admin'))
);

alter table public.portal_roles
enable row level security;

drop policy if exists
"portal_roles_select_own"
on public.portal_roles;

create policy
"portal_roles_select_own"
on public.portal_roles
for select
to authenticated
using (
    (select auth.uid()) = user_id
);

revoke insert
on public.portal_roles
from authenticated;

revoke update
on public.portal_roles
from authenticated;

revoke delete
on public.portal_roles
from authenticated;

grant select
on public.portal_roles
to authenticated;

comment on table public.portal_roles is
'Server-governed portal authorization roles. Clients may read only their own role. Role mutation must be performed by trusted administrative/server operations.';

comment on column public.portal_roles.role is
'Supported values: teacher, admin. This field is authorization data and must not be user-editable.';
