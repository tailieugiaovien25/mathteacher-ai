create table if not exists public.lesson_plan_workspace_drafts (
    draft_id text not null,
    teacher_user_id uuid not null
        references auth.users(id)
        on delete cascade,

    academic_year text not null,
    week_number integer not null,
    subject_ref text not null,
    selection_mode text not null,
    selection_unit_id text not null,

    objectives_text text not null default '',
    materials_text text not null default '',
    teaching_process_text text not null default '',

    class_or_grade_ref text null,
    lesson_id text null,
    title text not null default '',

    status text not null default 'DRAFT',
    metadata jsonb not null default '{}'::jsonb,

    updated_at timestamptz not null default now(),

    primary key (
        teacher_user_id,
        draft_id
    )
);

create index if not exists
    lesson_plan_workspace_drafts_teacher_idx
on public.lesson_plan_workspace_drafts (
    teacher_user_id
);

create index if not exists
    lesson_plan_workspace_drafts_context_idx
on public.lesson_plan_workspace_drafts (
    teacher_user_id,
    academic_year,
    week_number,
    subject_ref
);

alter table public.lesson_plan_workspace_drafts
    enable row level security;

revoke all
on table public.lesson_plan_workspace_drafts
from anon;

grant select, insert, update, delete
on table public.lesson_plan_workspace_drafts
to authenticated;

drop policy if exists
    lesson_plan_workspace_drafts_select_own
on public.lesson_plan_workspace_drafts;

create policy
    lesson_plan_workspace_drafts_select_own
on public.lesson_plan_workspace_drafts
for select
to authenticated
using (
    teacher_user_id = auth.uid()
);

drop policy if exists
    lesson_plan_workspace_drafts_insert_own
on public.lesson_plan_workspace_drafts;

create policy
    lesson_plan_workspace_drafts_insert_own
on public.lesson_plan_workspace_drafts
for insert
to authenticated
with check (
    teacher_user_id = auth.uid()
);

drop policy if exists
    lesson_plan_workspace_drafts_update_own
on public.lesson_plan_workspace_drafts;

create policy
    lesson_plan_workspace_drafts_update_own
on public.lesson_plan_workspace_drafts
for update
to authenticated
using (
    teacher_user_id = auth.uid()
)
with check (
    teacher_user_id = auth.uid()
);

drop policy if exists
    lesson_plan_workspace_drafts_delete_own
on public.lesson_plan_workspace_drafts;

create policy
    lesson_plan_workspace_drafts_delete_own
on public.lesson_plan_workspace_drafts
for delete
to authenticated
using (
    teacher_user_id = auth.uid()
);

create or replace function
public.set_lesson_plan_workspace_draft_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists
    lesson_plan_workspace_drafts_set_updated_at
on public.lesson_plan_workspace_drafts;

create trigger
    lesson_plan_workspace_drafts_set_updated_at
before update
on public.lesson_plan_workspace_drafts
for each row
execute function
    public.set_lesson_plan_workspace_draft_updated_at();

