create table if not exists public.teacher_profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    teacher_code text not null check (char_length(teacher_code) between 1 and 100),
    full_name text not null check (char_length(full_name) between 1 and 200),
    school_name text not null check (char_length(school_name) between 1 and 250),
    subjects text[] not null check (cardinality(subjects) > 0),
    grade_levels text[] not null check (cardinality(grade_levels) > 0),
    default_academic_year text not null check (char_length(default_academic_year) between 1 and 30),
    show_teacher_name boolean not null default true,
    show_school_name boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.teacher_profiles enable row level security;
revoke all on table public.teacher_profiles from anon;
grant select, insert, update, delete on table public.teacher_profiles to authenticated;

drop policy if exists "teachers_select_own_profile" on public.teacher_profiles;
create policy "teachers_select_own_profile" on public.teacher_profiles
    for select to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_insert_own_profile" on public.teacher_profiles;
create policy "teachers_insert_own_profile" on public.teacher_profiles
    for insert to authenticated
    with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_update_own_profile" on public.teacher_profiles;
create policy "teachers_update_own_profile" on public.teacher_profiles
    for update to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id)
    with check ((select auth.uid()) is not null and (select auth.uid()) = user_id);

drop policy if exists "teachers_delete_own_profile" on public.teacher_profiles;
create policy "teachers_delete_own_profile" on public.teacher_profiles
    for delete to authenticated
    using ((select auth.uid()) is not null and (select auth.uid()) = user_id);
