-- ADMIN read boundary for portal role directory.
--
-- Role mutation remains server-governed.
-- ADMIN receives read-only access required to build
-- the teacher directory.

drop policy if exists
"admins_select_portal_roles"
on public.portal_roles;

create policy
"admins_select_portal_roles"
on public.portal_roles
for select
to authenticated
using (
    (select public.current_user_is_portal_admin())
);

comment on policy
"admins_select_portal_roles"
on public.portal_roles is
'Allows authenticated portal ADMIN users to read portal roles for administrative directory workflows. Does not grant role mutation rights.';
