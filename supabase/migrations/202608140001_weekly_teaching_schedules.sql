create table if not exists public.weekly_teaching_schedules (
    user_id uuid not null references auth.users(id) on delete cascade,
    schedule_id text not null check (char_length(schedule_id) between 1 and 200),
    teacher_id text not null check (char_length(teacher_id) between 1 and 100),
    academic_year text not null check (char_length(academic_year) between 1 and 30),
    week_number integer not null check (week_number > 0),
    entry_count integer not null check (entry_count >= 0),
    schedule_data jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (user_id, schedule_id)
);

create index if not exists weekly_teaching_schedules_owner_teacher_idx
    on public.weekly_teaching_schedules (user_id, teacher_id, updated_at desc);

alter table public.weekly_teaching_schedules enable row level security;

revoke all on table public.weekly_teaching_schedules from anon;
grant select, insert, update, delete
    on table public.weekly_teaching_schedules to authenticated;

drop policy if exists "teachers_select_own_weekly_schedules"
    on public.weekly_teaching_schedules;
create policy "teachers_select_own_weekly_schedules"
    on public.weekly_teaching_schedules
    for select
    to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_insert_own_weekly_schedules"
    on public.weekly_teaching_schedules;
create policy "teachers_insert_own_weekly_schedules"
    on public.weekly_teaching_schedules
    for insert
    to authenticated
    with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_update_own_weekly_schedules"
    on public.weekly_teaching_schedules;
create policy "teachers_update_own_weekly_schedules"
    on public.weekly_teaching_schedules
    for update
    to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id)
    with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_delete_own_weekly_schedules"
    on public.weekly_teaching_schedules;
create policy "teachers_delete_own_weekly_schedules"
    on public.weekly_teaching_schedules
    for delete
    to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id);
