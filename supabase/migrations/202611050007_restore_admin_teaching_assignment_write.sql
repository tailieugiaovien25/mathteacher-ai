-- Ensure authenticated ADMIN can manage teaching assignments while teachers
-- retain read-only access to their own rows.
grant select, insert, update, delete
on public.teaching_assignments
to authenticated;

drop policy if exists teachers_insert_own_assignments
on public.teaching_assignments;
drop policy if exists teachers_update_own_assignments
on public.teaching_assignments;
drop policy if exists teachers_delete_own_assignments
on public.teaching_assignments;

drop policy if exists admins_select_teaching_assignments
on public.teaching_assignments;
create policy admins_select_teaching_assignments
on public.teaching_assignments
for select to authenticated
using ((select public.current_user_is_portal_admin()));

drop policy if exists admins_insert_teaching_assignments
on public.teaching_assignments;
create policy admins_insert_teaching_assignments
on public.teaching_assignments
for insert to authenticated
with check ((select public.current_user_is_portal_admin()));

drop policy if exists admins_update_teaching_assignments
on public.teaching_assignments;
create policy admins_update_teaching_assignments
on public.teaching_assignments
for update to authenticated
using ((select public.current_user_is_portal_admin()))
with check ((select public.current_user_is_portal_admin()));

drop policy if exists admins_delete_teaching_assignments
on public.teaching_assignments;
create policy admins_delete_teaching_assignments
on public.teaching_assignments
for delete to authenticated
using ((select public.current_user_is_portal_admin()));
