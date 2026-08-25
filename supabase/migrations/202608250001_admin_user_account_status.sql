-- ADMIN-managed teacher account lifecycle.

alter table public.portal_roles
add column if not exists is_active boolean not null default true;

comment on column public.portal_roles.is_active is
'Controls whether a portal account may enter MathTeacher-AI. Only ADMIN may change another teacher account status.';

create or replace function public.current_user_is_portal_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
            and pr.is_active = true
    );
$$;

revoke all on function public.current_user_is_portal_admin() from public;
grant execute on function public.current_user_is_portal_admin() to authenticated;

grant update (is_active) on public.portal_roles to authenticated;

drop policy if exists "admins_update_teacher_account_status" on public.portal_roles;
create policy "admins_update_teacher_account_status"
on public.portal_roles
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
    and role = 'teacher'
)
with check (
    (select public.current_user_is_portal_admin())
    and role = 'teacher'
);

drop policy if exists "admins_update_teacher_profiles" on public.teacher_profiles;
create policy "admins_update_teacher_profiles"
on public.teacher_profiles
for update
to authenticated
using ((select public.current_user_is_portal_admin()))
with check ((select public.current_user_is_portal_admin()));
