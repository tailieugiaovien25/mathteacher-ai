-- Restore ADMIN read access for the portal user directory.
-- The helper is SECURITY DEFINER to avoid recursive RLS evaluation.
create or replace function public.current_user_is_portal_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $admin_check$
    select exists (
        select 1
        from public.portal_roles pr
        where pr.user_id = (select auth.uid())
          and lower(pr.role) = 'admin'
          and pr.is_active = true
    );
$admin_check$;

revoke all on function public.current_user_is_portal_admin() from public;
grant execute on function public.current_user_is_portal_admin() to authenticated;

grant select on public.portal_roles, public.teacher_profiles to authenticated;

drop policy if exists admins_select_portal_roles on public.portal_roles;
create policy admins_select_portal_roles
on public.portal_roles
for select to authenticated
using ((select public.current_user_is_portal_admin()));

drop policy if exists admins_select_teacher_profiles on public.teacher_profiles;
create policy admins_select_teacher_profiles
on public.teacher_profiles
for select to authenticated
using ((select public.current_user_is_portal_admin()));
