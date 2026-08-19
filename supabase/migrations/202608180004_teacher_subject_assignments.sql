-- Canonical ADMIN-managed subject assignments for teachers.
--
-- This table represents:
--
--   ADMIN assigns a canonical Subject to a Teacher
--   for one Academic Year.
--
-- It intentionally does NOT contain class_id or component_id.
--
-- Class-level teaching belongs to teaching_assignments.
-- Component selection belongs to teacher subject registration.

create table if not exists
public.teacher_subject_assignments (
    assignment_id text primary key
        check (
            char_length(assignment_id)
            between 1 and 120
        ),

    teacher_id uuid not null
        references auth.users(id)
        on delete cascade,

    academic_year text not null
        check (
            char_length(academic_year)
            between 1 and 30
        ),

    subject_id text not null
        references public.subjects(subject_id)
        on update cascade
        on delete restrict,

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint teacher_subject_assignments_scope_unique
        unique (
            teacher_id,
            academic_year,
            subject_id
        )
);

create index if not exists
teacher_subject_assignments_teacher_year_idx
on public.teacher_subject_assignments (
    teacher_id,
    academic_year
);

alter table
public.teacher_subject_assignments
enable row level security;

revoke all
on table public.teacher_subject_assignments
from anon;

grant
select,
insert,
update,
delete
on table public.teacher_subject_assignments
to authenticated;


-- ---------------------------------------------------------
-- TEACHER: READ OWN ASSIGNMENTS
-- ---------------------------------------------------------

drop policy if exists
"teachers_select_own_subject_assignments"
on public.teacher_subject_assignments;

create policy
"teachers_select_own_subject_assignments"
on public.teacher_subject_assignments
for select
to authenticated
using (
    (select auth.uid()) = teacher_id
);


-- ---------------------------------------------------------
-- ADMIN: READ ALL ASSIGNMENTS
-- ---------------------------------------------------------

drop policy if exists
"admins_select_teacher_subject_assignments"
on public.teacher_subject_assignments;

create policy
"admins_select_teacher_subject_assignments"
on public.teacher_subject_assignments
for select
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: CREATE ASSIGNMENTS
-- ---------------------------------------------------------

drop policy if exists
"admins_insert_teacher_subject_assignments"
on public.teacher_subject_assignments;

create policy
"admins_insert_teacher_subject_assignments"
on public.teacher_subject_assignments
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE ASSIGNMENTS
-- ---------------------------------------------------------

drop policy if exists
"admins_update_teacher_subject_assignments"
on public.teacher_subject_assignments;

create policy
"admins_update_teacher_subject_assignments"
on public.teacher_subject_assignments
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: DELETE ASSIGNMENTS
-- ---------------------------------------------------------

drop policy if exists
"admins_delete_teacher_subject_assignments"
on public.teacher_subject_assignments;

create policy
"admins_delete_teacher_subject_assignments"
on public.teacher_subject_assignments
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.teacher_subject_assignments is
'ADMIN-managed canonical Subject assignments for teachers. '
'Class-level teaching and SubjectComponent selection are '
'owned by separate domain contracts.';
