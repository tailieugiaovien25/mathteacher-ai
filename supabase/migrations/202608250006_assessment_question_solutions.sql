-- Assessment Question Solutions V1
-- Canonical answers, alternative solutions, scoring steps,
-- equivalent short answers, tolerances, units, and grading rules.

create table if not exists public.assessment_question_answers (
    answer_id uuid primary key default gen_random_uuid(),

    question_version_id uuid not null unique
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    answer_mode text not null
        check (
            answer_mode in (
                'SINGLE_CHOICE',
                'TRUE_FALSE_STATEMENTS',
                'SHORT_RESPONSE',
                'CONSTRUCTED_RESPONSE'
            )
        ),

    exact_answer_text text null,

    accepted_answers jsonb not null default '[]'::jsonb
        check (jsonb_typeof(accepted_answers) = 'array'),

    numeric_answer numeric null,

    tolerance numeric null
        check (
            tolerance is null
            or tolerance >= 0
        ),

    unit_text text null,
    rounding_rule text null,

    answer_explanation text not null default '',
    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (
        numeric_answer is not null
        or tolerance is null
    )
);

create table if not exists public.assessment_question_solutions (
    solution_id uuid primary key default gen_random_uuid(),

    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete cascade,

    solution_code text not null
        check (char_length(solution_code) between 1 and 50),

    solution_text text not null
        check (char_length(trim(solution_text)) > 0),

    sequence_number integer not null default 1
        check (sequence_number >= 1),

    is_primary boolean not null default false,

    alternative_method_note text not null default '',

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        solution_id,
        question_version_id
    ),

    unique (
        question_version_id,
        solution_code
    ),

    unique (
        question_version_id,
        sequence_number
    )
);

create table if not exists public.assessment_question_scoring_steps (
    scoring_step_id uuid primary key default gen_random_uuid(),

    solution_id uuid not null,
    question_version_id uuid not null,

    step_code text not null
        check (char_length(step_code) between 1 and 50),

    step_description text not null
        check (char_length(trim(step_description)) > 0),

    sequence_number integer not null
        check (sequence_number >= 1),

    step_score numeric(6,2) not null
        check (step_score > 0),

    acceptance_note text not null default '',
    allows_equivalent_method boolean not null default true,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    foreign key (
        solution_id,
        question_version_id
    )
    references public.assessment_question_solutions (
        solution_id,
        question_version_id
    )
    on delete cascade,

    unique (
        solution_id,
        step_code
    ),

    unique (
        solution_id,
        sequence_number
    )
);

create unique index if not exists
    assessment_question_solutions_one_primary_idx
on public.assessment_question_solutions (
    question_version_id
)
where is_primary = true;

create index if not exists
    assessment_question_answers_version_idx
on public.assessment_question_answers (
    question_version_id
);

create index if not exists
    assessment_question_solutions_version_idx
on public.assessment_question_solutions (
    question_version_id,
    sequence_number
);

create index if not exists
    assessment_question_scoring_steps_version_idx
on public.assessment_question_scoring_steps (
    question_version_id,
    solution_id,
    sequence_number
);

create or replace function
public.validate_assessment_question_answer_mode()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    expected_answer_mode text;
begin
    select question_type.answer_mode
    into expected_answer_mode
    from public.assessment_question_versions question_version
    join public.assessment_question_types question_type
        on question_type.question_type_code =
            question_version.question_type_code
    where
        question_version.question_version_id =
            new.question_version_id;

    if expected_answer_mode is null then
        raise exception
            'Assessment question version does not exist.';
    end if;

    if new.answer_mode <> expected_answer_mode then
        raise exception
            'Answer mode does not match question type.';
    end if;

    return new;
end;
$$;

drop trigger if exists
    assessment_question_answers_validate_mode
on public.assessment_question_answers;

create trigger
    assessment_question_answers_validate_mode
before insert or update
on public.assessment_question_answers
for each row
execute function
    public.validate_assessment_question_answer_mode();

create or replace function
public.assessment_question_scoring_total_matches(
    target_question_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select not exists (
        select 1
        from public.assessment_question_solutions solution
        join public.assessment_question_versions question_version
            on question_version.question_version_id =
                solution.question_version_id
        join public.assessment_question_scoring_steps scoring_step
            on scoring_step.solution_id =
                solution.solution_id
            and scoring_step.question_version_id =
                solution.question_version_id
        where
            solution.question_version_id =
                target_question_version_id
        group by
            solution.solution_id,
            question_version.default_score
        having abs(
            sum(scoring_step.step_score)
            -
            question_version.default_score
        ) > 0.0001
    );
$$;
revoke all on function
public.assessment_question_scoring_total_matches(uuid)
from public;

grant execute on function
public.assessment_question_scoring_total_matches(uuid)
to authenticated;

alter table public.assessment_question_answers
    enable row level security;

alter table public.assessment_question_solutions
    enable row level security;

alter table public.assessment_question_scoring_steps
    enable row level security;

revoke all on table
    public.assessment_question_answers,
    public.assessment_question_solutions,
    public.assessment_question_scoring_steps
from anon;

grant select, insert, update, delete on table
    public.assessment_question_answers,
    public.assessment_question_solutions,
    public.assessment_question_scoring_steps
to authenticated;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'assessment_question_answers',
        'assessment_question_solutions',
        'assessment_question_scoring_steps'
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
        'assessment_question_answers',
        'assessment_question_solutions',
        'assessment_question_scoring_steps'
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

comment on table public.assessment_question_answers is
'One canonical answer definition for each question version.';

comment on column
public.assessment_question_answers.accepted_answers is
'Equivalent accepted answers, especially for short-response questions.';

comment on column
public.assessment_question_answers.tolerance is
'Allowed non-negative numeric tolerance; valid only with a numeric answer.';

comment on table public.assessment_question_solutions is
'Primary and alternative mathematically valid solutions for a question version.';

comment on table public.assessment_question_scoring_steps is
'Ordered scoring steps supporting equivalent mathematical methods.';

comment on function
public.assessment_question_scoring_total_matches(uuid) is
'Validates that scoring-step totals match the default question score before review.';

