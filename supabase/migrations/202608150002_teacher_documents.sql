create table if not exists public.teacher_documents (
    user_id uuid not null references auth.users(id) on delete cascade,
    document_id uuid not null,
    title text not null check (char_length(title) between 1 and 250),
    category text not null check (category in (
        'lesson_plan', 'educational_plan', 'test_matrix',
        'test_specification', 'test_paper', 'marking_guide'
    )),
    academic_year text not null check (char_length(academic_year) between 1 and 30),
    subject text not null check (char_length(subject) between 1 and 100),
    grade_level text not null check (char_length(grade_level) between 1 and 50),
    class_name text check (class_name is null or char_length(class_name) between 1 and 100),
    file_name text not null check (char_length(file_name) between 1 and 255),
    mime_type text not null check (char_length(mime_type) between 1 and 150),
    size_bytes bigint not null default 0 check (size_bytes >= 0),
    storage_provider text not null check (char_length(storage_provider) between 1 and 50),
    storage_file_id text not null check (char_length(storage_file_id) between 1 and 500),
    web_view_link text check (web_view_link is null or char_length(web_view_link) <= 2000),
    description text check (description is null or char_length(description) <= 2000),
    tags text[] not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (user_id, document_id)
);

create index if not exists teacher_documents_owner_filters_idx
    on public.teacher_documents (user_id, academic_year, subject, category);

alter table public.teacher_documents enable row level security;
revoke all on table public.teacher_documents from anon;
grant select, insert, update, delete on table public.teacher_documents to authenticated;

drop policy if exists "teachers_select_own_documents" on public.teacher_documents;
create policy "teachers_select_own_documents" on public.teacher_documents
    for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "teachers_insert_own_documents" on public.teacher_documents;
create policy "teachers_insert_own_documents" on public.teacher_documents
    for insert to authenticated with check ((select auth.uid()) = user_id);

drop policy if exists "teachers_update_own_documents" on public.teacher_documents;
create policy "teachers_update_own_documents" on public.teacher_documents
    for update to authenticated using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists "teachers_delete_own_documents" on public.teacher_documents;
create policy "teachers_delete_own_documents" on public.teacher_documents
    for delete to authenticated using ((select auth.uid()) = user_id);
