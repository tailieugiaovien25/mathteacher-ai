begin;

create table if not exists public.notebooklm_notebooks (
    user_id uuid not null references auth.users(id) on delete cascade,
    notebook_id uuid not null default gen_random_uuid(),
    notebook_name text not null check (char_length(notebook_name) between 1 and 250),
    notebook_url text check (notebook_url is null or char_length(notebook_url) <= 2000),
    external_notebook_id text check (external_notebook_id is null or char_length(external_notebook_id) <= 500),
    status text not null default 'ACTIVE' check (status in ('ACTIVE', 'ARCHIVED')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (user_id, notebook_id)
);

create index if not exists notebooklm_notebooks_owner_status_idx
    on public.notebooklm_notebooks (user_id, status);

create table if not exists public.notebooklm_sources (
    user_id uuid not null references auth.users(id) on delete cascade,
    source_id uuid not null default gen_random_uuid(),
    notebook_id uuid not null,
    document_id uuid not null,
    status text not null default 'PENDING'
        check (status in ('PENDING', 'SYNCED', 'FAILED', 'REMOVED')),
    external_source_id text
        check (external_source_id is null or char_length(external_source_id) <= 500),
    last_synced_at timestamptz,
    last_error text
        check (last_error is null or char_length(last_error) <= 4000),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (user_id, source_id),

    constraint notebooklm_sources_notebook_fk
        foreign key (user_id, notebook_id)
        references public.notebooklm_notebooks(user_id, notebook_id)
        on delete cascade,

    constraint notebooklm_sources_document_fk
        foreign key (user_id, document_id)
        references public.teacher_documents(user_id, document_id)
        on delete cascade,

    constraint notebooklm_sources_notebook_document_unique
        unique (user_id, notebook_id, document_id)
);

create index if not exists notebooklm_sources_notebook_status_idx
    on public.notebooklm_sources (user_id, notebook_id, status);

create index if not exists notebooklm_sources_document_idx
    on public.notebooklm_sources (user_id, document_id);

create table if not exists public.notebooklm_sync_runs (
    user_id uuid not null references auth.users(id) on delete cascade,
    sync_run_id uuid not null default gen_random_uuid(),
    notebook_id uuid not null,
    status text not null
        check (status in ('RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED')),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    source_count integer not null default 0 check (source_count >= 0),
    success_count integer not null default 0 check (success_count >= 0),
    failure_count integer not null default 0 check (failure_count >= 0),
    error_message text
        check (error_message is null or char_length(error_message) <= 4000),
    created_at timestamptz not null default now(),

    constraint notebooklm_sync_runs_notebook_fk
        foreign key (user_id, notebook_id)
        references public.notebooklm_notebooks(user_id, notebook_id)
        on delete cascade
);

create index if not exists notebooklm_sync_runs_notebook_started_idx
    on public.notebooklm_sync_runs (user_id, notebook_id, started_at desc);

revoke all on table public.notebooklm_notebooks from anon;
revoke all on table public.notebooklm_sources from anon;
revoke all on table public.notebooklm_sync_runs from anon;

grant select, insert, update, delete
on table public.notebooklm_notebooks to authenticated;

grant select, insert, update, delete
on table public.notebooklm_sources to authenticated;

grant select, insert, update, delete
on table public.notebooklm_sync_runs to authenticated;

alter table public.notebooklm_notebooks enable row level security;
alter table public.notebooklm_sources enable row level security;
alter table public.notebooklm_sync_runs enable row level security;

drop policy if exists notebooklm_notebooks_select_own
    on public.notebooklm_notebooks;
create policy notebooklm_notebooks_select_own
    on public.notebooklm_notebooks
    for select to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists notebooklm_notebooks_insert_own
    on public.notebooklm_notebooks;
create policy notebooklm_notebooks_insert_own
    on public.notebooklm_notebooks
    for insert to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_notebooks_update_own
    on public.notebooklm_notebooks;
create policy notebooklm_notebooks_update_own
    on public.notebooklm_notebooks
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_notebooks_delete_own
    on public.notebooklm_notebooks;
create policy notebooklm_notebooks_delete_own
    on public.notebooklm_notebooks
    for delete to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sources_select_own
    on public.notebooklm_sources;
create policy notebooklm_sources_select_own
    on public.notebooklm_sources
    for select to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sources_insert_own
    on public.notebooklm_sources;
create policy notebooklm_sources_insert_own
    on public.notebooklm_sources
    for insert to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sources_update_own
    on public.notebooklm_sources;
create policy notebooklm_sources_update_own
    on public.notebooklm_sources
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sources_delete_own
    on public.notebooklm_sources;
create policy notebooklm_sources_delete_own
    on public.notebooklm_sources
    for delete to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sync_runs_select_own
    on public.notebooklm_sync_runs;
create policy notebooklm_sync_runs_select_own
    on public.notebooklm_sync_runs
    for select to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sync_runs_insert_own
    on public.notebooklm_sync_runs;
create policy notebooklm_sync_runs_insert_own
    on public.notebooklm_sync_runs
    for insert to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sync_runs_update_own
    on public.notebooklm_sync_runs;
create policy notebooklm_sync_runs_update_own
    on public.notebooklm_sync_runs
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists notebooklm_sync_runs_delete_own
    on public.notebooklm_sync_runs;
create policy notebooklm_sync_runs_delete_own
    on public.notebooklm_sync_runs
    for delete to authenticated
    using ((select auth.uid()) = user_id);

commit;
