-- Reviewed textbook teaching excerpts, scoped to the teacher and exact catalog lesson.
create table if not exists public.teacher_textbook_lesson_sources (
    source_id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references auth.users(id) on delete cascade,
    textbook_id text not null,
    textbook_unit_id text not null,
    source_label text not null default '',
    knowledge_excerpt text not null,
    pdf_sha256 text,
    pdf_page integer,
    review_status text not null default 'TEACHER_REVIEWED'
        check (review_status in ('TEACHER_REVIEWED', 'RETIRED')),
    updated_at timestamptz not null default now(),
    unique (owner_user_id, textbook_unit_id, source_label),
    foreign key (textbook_id, textbook_unit_id)
        references public.textbook_units(textbook_id, textbook_unit_id) on delete restrict,
    check (char_length(source_label) between 1 and 160),
    check (char_length(knowledge_excerpt) between 80 and 4000),
    check (pdf_page is null or pdf_page > 0),
    check (pdf_sha256 is null or pdf_sha256 ~ '^[a-f0-9]{64}$')
);
create index if not exists teacher_textbook_sources_lesson_idx
on public.teacher_textbook_lesson_sources (owner_user_id, textbook_unit_id, review_status);
alter table public.teacher_textbook_lesson_sources enable row level security;
revoke all on public.teacher_textbook_lesson_sources from anon;
grant select, insert, update on public.teacher_textbook_lesson_sources to authenticated;
create policy teacher_textbook_sources_select on public.teacher_textbook_lesson_sources
for select to authenticated using (owner_user_id = (select auth.uid()));
create policy teacher_textbook_sources_insert on public.teacher_textbook_lesson_sources
for insert to authenticated with check (owner_user_id = (select auth.uid()));
create policy teacher_textbook_sources_update on public.teacher_textbook_lesson_sources
for update to authenticated using (owner_user_id = (select auth.uid()))
with check (owner_user_id = (select auth.uid()));
