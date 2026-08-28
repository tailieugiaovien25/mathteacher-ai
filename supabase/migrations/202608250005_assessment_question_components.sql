-- Assessment Question Components V1
-- Multiple-choice options, true-false statements,
-- learning-requirement links, and competency links.

create table if not exists public.assessment_question_options (
    option_id uuid primary key default gen_random_uuid(),

    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    option_code text not null
        check (char_length(option_code) between 1 and 20),

    option_text text not null
        check (char_length(trim(option_text)) > 0),

    sequence_number integer not null
        check (sequence_number >= 1),

    is_correct boolean not null default false,
    feedback_text text not null default '',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        question_version_id,
        option_code
    ),

    unique (
        question_version_id,
        sequence_number
    )
);

create table if not exists public.assessment_question_statements (
    statement_id uuid primary key default gen_random_uuid(),

    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    statement_code text not null
        check (char_length(statement_code) between 1 and 20),

    statement_text text not null
        check (char_length(trim(statement_text)) > 0),

    sequence_number integer not null
        check (sequence_number >= 1),

    correct_value boolean not null,
    explanation_text text not null default '',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        question_version_id,
        statement_code
    ),

    unique (
        question_version_id,
        sequence_number
    )
);

create table if not exists public.assessment_question_requirement_links (
    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    requirement_code text not null
        references public.assessment_learning_requirements(requirement_code)
        on update cascade
        on delete restrict,

    link_role text not null default 'SECONDARY'
        check (link_role in ('PRIMARY', 'SECONDARY')),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    notes text not null default '',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    primary key (
        question_version_id,
        requirement_code
    )
);

create table if not exists public.assessment_question_competency_links (
    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    competency_code text not null
        references public.assessment_mathematical_competencies(competency_code)
        on update cascade
        on delete restrict,

    link_role text not null default 'SECONDARY'
        check (link_role in ('PRIMARY', 'SECONDARY')),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    notes text not null default '',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    primary key (
        question_version_id,
        competency_code
    )
);

create unique index if not exists
    assessment_question_options_one_correct_idx
on public.assessment_question_options (
    question_version_id
)
where is_correct = true;

create unique index if not exists
    assessment_question_requirements_one_primary_idx
on public.assessment_question_requirement_links (
    question_version_id
)
where link_role = 'PRIMARY';

create unique index if not exists
    assessment_question_competencies_one_primary_idx
on public.assessment_question_competency_links (
    question_version_id
)
where link_role = 'PRIMARY';

create index if not exists
    assessment_question_options_version_idx
on public.assessment_question_options (
    question_version_id,
    sequence_number
);

create index if not exists
    assessment_question_statements_version_idx
on public.assessment_question_statements (
    question_version_id,
    sequence_number
);

create index if not exists
    assessment_question_requirement_code_idx
on public.assessment_question_requirement_links (
    requirement_code,
    question_version_id
);

create index if not exists
    assessment_question_competency_code_idx
on public.assessment_question_competency_links (
    competency_code,
    question_version_id
);

create or replace function
public.assessment_question_version_is_visible(
    target_question_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_question_versions question_version
        join public.assessment_question_items question_item
            on question_item.question_id =
                question_version.question_id
        where
            question_version.question_version_id =
                target_question_version_id
            and (
                question_item.owner_user_id = (
                    select auth.uid()
                )
                or (
                    select
                        public.current_user_is_portal_admin()
                )
            )
    );
$$;

revoke all on function
public.assessment_question_version_is_visible(uuid)
from public;

grant execute on function
public.assessment_question_version_is_visible(uuid)
to authenticated;

create or replace function
public.validate_assessment_question_component_type()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    actual_question_type text;
begin
    select question_version.question_type_code
    into actual_question_type
    from public.assessment_question_versions question_version
    where
        question_version.question_version_id =
            new.question_version_id;

    if actual_question_type is null then
        raise exception
            'Assessment question version does not exist.';
    end if;

    if tg_table_name = 'assessment_question_options'
       and actual_question_type <> 'MULTIPLE_CHOICE'
    then
        raise exception
            'Question options require MULTIPLE_CHOICE type.';
    end if;

    if tg_table_name = 'assessment_question_statements'
       and actual_question_type <> 'TRUE_FALSE'
    then
        raise exception
            'Question statements require TRUE_FALSE type.';
    end if;

    return new;
end;
$$;

drop trigger if exists
    assessment_question_options_validate_type
on public.assessment_question_options;

create trigger
    assessment_question_options_validate_type
before insert or update
on public.assessment_question_options
for each row
execute function
    public.validate_assessment_question_component_type();

drop trigger if exists
    assessment_question_statements_validate_type
on public.assessment_question_statements;

create trigger
    assessment_question_statements_validate_type
before insert or update
on public.assessment_question_statements
for each row
execute function
    public.validate_assessment_question_component_type();

alter table public.assessment_question_options
    enable row level security;

alter table public.assessment_question_statements
    enable row level security;

alter table public.assessment_question_requirement_links
    enable row level security;

alter table public.assessment_question_competency_links
    enable row level security;

revoke all on table
    public.assessment_question_options,
    public.assessment_question_statements,
    public.assessment_question_requirement_links,
    public.assessment_question_competency_links
from anon;

grant select, insert, update, delete on table
    public.assessment_question_options,
    public.assessment_question_statements,
    public.assessment_question_requirement_links,
    public.assessment_question_competency_links
to authenticated;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_question_options',
        'assessment_question_statements',
        'assessment_question_requirement_links',
        'assessment_question_competency_links'
    ]
    loop
        execute format(
            'drop policy if exists %I on public.%I',
            table_name || '_select_authorized',
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for select to authenticated
             using (
                 (
                     select
                         public.assessment_question_version_is_visible(
                             question_version_id
                         )
                 )
             )',
            table_name || '_select_authorized',
            table_name
        );

        execute format(
            'drop policy if exists %I on public.%I',
            table_name || '_insert_editable',
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for insert to authenticated
             with check (
                 (
                     select
                         public.assessment_question_version_is_editable(
                             question_version_id
                         )
                 )
             )',
            table_name || '_insert_editable',
            table_name
        );

        execute format(
            'drop policy if exists %I on public.%I',
            table_name || '_update_editable',
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for update to authenticated
             using (
                 (
                     select
                         public.assessment_question_version_is_editable(
                             question_version_id
                         )
                 )
             )
             with check (
                 (
                     select
                         public.assessment_question_version_is_editable(
                             question_version_id
                         )
                 )
             )',
            table_name || '_update_editable',
            table_name
        );

        execute format(
            'drop policy if exists %I on public.%I',
            table_name || '_delete_editable',
            table_name
        );

        execute format(
            'create policy %I on public.%I
             for delete to authenticated
             using (
                 (
                     select
                         public.assessment_question_version_is_editable(
                             question_version_id
                         )
                 )
             )',
            table_name || '_delete_editable',
            table_name
        );
    end loop;
end
$$;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_question_options',
        'assessment_question_statements',
        'assessment_question_requirement_links',
        'assessment_question_competency_links'
    ]
    loop
        execute format(
            'drop trigger if exists %I on public.%I',
            table_name || '_set_updated_at',
            table_name
        );

        execute format(
            'create trigger %I
             before update on public.%I
             for each row
             execute function
                 public.set_assessment_question_updated_at()',
            table_name || '_set_updated_at',
            table_name
        );
    end loop;
end
$$;

comment on table public.assessment_question_options is
'Ordered answer options for one editable multiple-choice question version.';

comment on table public.assessment_question_statements is
'Ordered true-false statements with independent correct values.';

comment on table public.assessment_question_requirement_links is
'Version-specific links to canonical learning requirements, with at most one primary link.';

comment on table public.assessment_question_competency_links is
'Version-specific links to mathematical competencies, with at most one primary link.';

comment on index
public.assessment_question_options_one_correct_idx is
'Ensures at most one correct option; completeness is validated before review submission.';

