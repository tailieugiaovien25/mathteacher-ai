-- ADMIN Teacher Directory read boundary.
--
-- Teachers retain ownership-based access to their own profiles.
-- ADMIN receives read-only access to teacher profiles.
-- Portal role mutation remains server-governed.

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
    );
$$;

revoke all
on function public.current_user_is_portal_admin()
from public;

grant execute
on function public.current_user_is_portal_admin()
to authenticated;

comment on function public.current_user_is_portal_admin() is
'Returns true only when the authenticated user has canonical portal role admin. Used as a narrow RLS authorization helper.';

drop policy if exists
"admins_select_teacher_profiles"
on public.teacher_profiles;

create policy
"admins_select_teacher_profiles"
on public.teacher_profiles
for select
to authenticated
using (
    (select public.current_user_is_portal_admin())
);

comment on policy
"admins_select_teacher_profiles"
on public.teacher_profiles is
'Allows authenticated portal ADMIN users to read teacher profiles for administrative directory and assignment workflows. Does not grant profile mutation rights.';
