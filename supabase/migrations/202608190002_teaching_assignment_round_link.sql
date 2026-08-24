alter table
    public.teaching_assignments
add column if not exists
    assignment_round_id text null;

alter table
    public.teaching_assignments
drop constraint if exists
    teaching_assignments_assignment_round_fk;

alter table
    public.teaching_assignments
add constraint
    teaching_assignments_assignment_round_fk
foreign key (
    assignment_round_id
)
references public.assignment_rounds (
    round_id
)
on update cascade
on delete restrict;

create index if not exists
    teaching_assignments_round_idx
on public.teaching_assignments (
    assignment_round_id
);

create index if not exists
    teaching_assignments_year_round_idx
on public.teaching_assignments (
    academic_year,
    assignment_round_id
);

comment on column
public.teaching_assignments.assignment_round_id is
'Optional assignment round reference during migration. New ADMIN-managed assignments should reference assignment_rounds.round_id.';
