-- V58-C5B7D: canonical lesson-plan grouping policy configuration.
create table if not exists public.lesson_plan_grouping_policy_config (
    id uuid primary key default gen_random_uuid(),
    subject_ref text not null,
    component_ref text not null default '',
    grouping_mode text not null check (
        grouping_mode in ('BY_PERIOD', 'BY_LESSON', 'BY_WEEK')
    ),
    status text not null default 'ACTIVE' check (
        status in ('ACTIVE', 'INACTIVE')
    ),
    rule_version integer not null default 1 check (rule_version >= 1),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (subject_ref, component_ref)
);

alter table public.lesson_plan_grouping_policy_config enable row level security;

drop policy if exists lesson_plan_grouping_policy_read_authenticated
on public.lesson_plan_grouping_policy_config;
create policy lesson_plan_grouping_policy_read_authenticated
on public.lesson_plan_grouping_policy_config
for select to authenticated
using (true);

drop policy if exists lesson_plan_grouping_policy_admin_insert
on public.lesson_plan_grouping_policy_config;
create policy lesson_plan_grouping_policy_admin_insert
on public.lesson_plan_grouping_policy_config
for insert to authenticated
with check (
    exists (
        select 1
        from public.portal_roles pr
        where pr.user_id = (select auth.uid())
          and pr.role = 'admin'
          and pr.is_active = true
    )
);

drop policy if exists lesson_plan_grouping_policy_admin_update
on public.lesson_plan_grouping_policy_config;
create policy lesson_plan_grouping_policy_admin_update
on public.lesson_plan_grouping_policy_config
for update to authenticated
using (
    exists (
        select 1
        from public.portal_roles pr
        where pr.user_id = (select auth.uid())
          and pr.role = 'admin'
          and pr.is_active = true
    )
)
with check (
    exists (
        select 1
        from public.portal_roles pr
        where pr.user_id = (select auth.uid())
          and pr.role = 'admin'
          and pr.is_active = true
    )
);

grant select, insert, update
on public.lesson_plan_grouping_policy_config
to authenticated;
