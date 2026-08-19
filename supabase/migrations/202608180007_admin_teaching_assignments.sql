-- ADMIN-owned Teaching Assignment authorization boundary.
--
-- TeachingAssignment is an administrative school assignment.
--
-- Teachers:
--   - may read only their own assignments
--   - may not create, update, or delete assignments
--
-- ADMIN:
--   - may read all assignments
--   - may create, update, and delete assignments
--
-- Existing teacher SELECT ownership policy is preserved.

-- ---------------------------------------------------------
-- REMOVE TEACHER WRITE POLICIES
-- ---------------------------------------------------------

drop policy if exists
    "teachers_insert_own_assignments"
on public.teaching_assignments;

drop policy if exists
    "teachers_update_own_assignments"
on public.teaching_assignments;

drop policy if exists
    "teachers_delete_own_assignments"
on public.teaching_assignments;


-- ---------------------------------------------------------
-- ADMIN: SELECT ALL
-- ---------------------------------------------------------

drop policy if exists
    "admins_select_teaching_assignments"
on public.teaching_assignments;

create policy
    "admins_select_teaching_assignments"
on public.teaching_assignments
for select
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: INSERT
-- ---------------------------------------------------------

drop policy if exists
    "admins_insert_teaching_assignments"
on public.teaching_assignments;

create policy
    "admins_insert_teaching_assignments"
on public.teaching_assignments
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE
-- ---------------------------------------------------------

drop policy if exists
    "admins_update_teaching_assignments"
on public.teaching_assignments;

create policy
    "admins_update_teaching_assignments"
on public.teaching_assignments
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: DELETE
-- ---------------------------------------------------------

drop policy if exists
    "admins_delete_teaching_assignments"
on public.teaching_assignments;

create policy
    "admins_delete_teaching_assignments"
on public.teaching_assignments
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.teaching_assignments is
'Canonical teaching and homeroom assignments administered by portal ADMIN. Teachers may read only their own assignments.';
