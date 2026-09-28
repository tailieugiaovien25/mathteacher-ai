-- Private, portable lesson drafts. All writes use the teacher's authenticated client.
create table if not exists public.teacher_lesson_drafts (
    draft_id uuid primary key,
    owner_user_id uuid not null references auth.users(id) on delete cascade,
    title text not null default '',
    draft_json jsonb not null,
    updated_at timestamptz not null default now(),
    constraint teacher_lesson_draft_title_limit check (char_length(title) <= 250),
    constraint teacher_lesson_draft_size_limit check (pg_column_size(draft_json) <= 2000000),
    constraint teacher_lesson_draft_shape check (jsonb_typeof(draft_json) = 'object')
);

create index if not exists teacher_lesson_drafts_owner_recent_idx
on public.teacher_lesson_drafts (owner_user_id, updated_at desc);

alter table public.teacher_lesson_drafts enable row level security;
revoke all on public.teacher_lesson_drafts from anon;
grant select, insert, update, delete on public.teacher_lesson_drafts to authenticated;

create policy teacher_lesson_drafts_select on public.teacher_lesson_drafts
for select to authenticated using (owner_user_id = (select auth.uid()));
create policy teacher_lesson_drafts_insert on public.teacher_lesson_drafts
for insert to authenticated with check (owner_user_id = (select auth.uid()));
create policy teacher_lesson_drafts_update on public.teacher_lesson_drafts
for update to authenticated using (owner_user_id = (select auth.uid()))
with check (owner_user_id = (select auth.uid()));
create policy teacher_lesson_drafts_delete on public.teacher_lesson_drafts
for delete to authenticated using (owner_user_id = (select auth.uid()));
