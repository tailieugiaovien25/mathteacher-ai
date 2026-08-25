begin;

create extension if not exists pgcrypto
with schema extensions;

create table if not exists public.assessment_exam_snapshots (
    snapshot_id uuid primary key default gen_random_uuid(),

    publication_id uuid not null unique
        references public.assessment_exam_publications(
            publication_id
        )
        on delete restrict,

    exam_version_id uuid not null unique
        references public.assessment_exam_versions(
            exam_version_id
        )
        on delete restrict,

    snapshot_schema_version integer not null default 1
        check (snapshot_schema_version >= 1),

    snapshot_document jsonb not null
        check (jsonb_typeof(snapshot_document) = 'object'),

    snapshot_hash text not null
        check (char_length(snapshot_hash) = 64),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now()
);

create or replace function
public.build_assessment_exam_snapshot_document(
    target_exam_version_id uuid,
    target_publication_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'snapshot_schema_version', 1,
        'publication', jsonb_build_object(
            'publication_id',
                publication.publication_id,
            'publication_channel',
                publication.publication_channel,
            'publication_note',
                publication.publication_note,
            'published_at',
                publication.published_at
        ),
        'exam', jsonb_build_object(
            'exam_id',
                exam.exam_id,
            'exam_code',
                exam.exam_code,
            'subject_code',
                exam.subject_code,
            'education_level',
                exam.education_level,
            'grade_level',
                exam.grade_level,
            'exam_version_id',
                exam_version.exam_version_id,
            'version_number',
                exam_version.version_number,
            'exam_title',
                exam_version.exam_title,
            'exam_code_label',
                exam_version.exam_code_label,
            'academic_year',
                exam_version.academic_year,
            'semester_number',
                exam_version.semester_number,
            'scheduled_date',
                exam_version.scheduled_date,
            'total_score',
                exam_version.total_score,
            'duration_minutes',
                exam_version.duration_minutes,
            'instruction_text',
                exam_version.instruction_text
        ),
        'blueprint', jsonb_build_object(
            'blueprint_version_id',
                blueprint_version.blueprint_version_id,
            'blueprint_id',
                blueprint_version.blueprint_id,
            'version_number',
                blueprint_version.version_number,
            'blueprint_name',
                blueprint_version.blueprint_name,
            'profile_code',
                blueprint_version.profile_code,
            'total_score',
                blueprint_version.total_score,
            'duration_minutes',
                blueprint_version.duration_minutes
        ),
        'questions', coalesce(
            (
                select jsonb_agg(
                    jsonb_build_object(
                        'exam_question_id',
                            exam_question.exam_question_id,
                        'display_number',
                            exam_question.display_number,
                        'assigned_score',
                            exam_question.assigned_score,
                        'blueprint_cell_id',
                            exam_question.blueprint_cell_id,
                        'question_version_id',
                            question_version.question_version_id,
                        'question_id',
                            question_version.question_id,
                        'version_number',
                            question_version.version_number,
                        'question_type_code',
                            question_version.question_type_code,
                        'cognitive_level_code',
                            question_version.cognitive_level_code,
                        'prompt_text',
                            question_version.prompt_text,
                        'stimulus_text',
                            question_version.stimulus_text,
                        'instruction_text',
                            question_version.instruction_text,
                        'content_hash',
                            question_version.content_hash,
                        'options',
                            coalesce(
                                (
                                    select jsonb_agg(
                                        jsonb_build_object(
                                            'option_code',
                                                question_option.option_code,
                                            'option_text',
                                                question_option.option_text,
                                            'sequence_number',
                                                question_option.sequence_number,
                                            'is_correct',
                                                question_option.is_correct,
                                            'feedback_text',
                                                question_option.feedback_text
                                        )
                                        order by
                                            question_option.sequence_number
                                    )
                                    from public.assessment_question_options
                                        question_option
                                    where
                                        question_option.question_version_id =
                                            question_version.question_version_id
                                ),
                                '[]'::jsonb
                            ),
                        'statements',
                            coalesce(
                                (
                                    select jsonb_agg(
                                        jsonb_build_object(
                                            'statement_code',
                                                statement.statement_code,
                                            'statement_text',
                                                statement.statement_text,
                                            'sequence_number',
                                                statement.sequence_number,
                                            'correct_value',
                                                statement.correct_value,
                                            'explanation_text',
                                                statement.explanation_text
                                        )
                                        order by
                                            statement.sequence_number
                                    )
                                    from public.assessment_question_statements
                                        statement
                                    where
                                        statement.question_version_id =
                                            question_version.question_version_id
                                ),
                                '[]'::jsonb
                            ),
                        'answer',
                            coalesce(
                                (
                                    select jsonb_build_object(
                                        'answer_mode',
                                            answer.answer_mode,
                                        'exact_answer_text',
                                            answer.exact_answer_text,
                                        'accepted_answers',
                                            answer.accepted_answers,
                                        'numeric_answer',
                                            answer.numeric_answer,
                                        'tolerance',
                                            answer.tolerance,
                                        'unit_text',
                                            answer.unit_text,
                                        'rounding_rule',
                                            answer.rounding_rule,
                                        'answer_explanation',
                                            answer.answer_explanation
                                    )
                                    from public.assessment_question_answers
                                        answer
                                    where
                                        answer.question_version_id =
                                            question_version.question_version_id
                                ),
                                '{}'::jsonb
                            ),
                        'solutions',
                            coalesce(
                                (
                                    select jsonb_agg(
                                        jsonb_build_object(
                                            'solution_code',
                                                solution.solution_code,
                                            'solution_text',
                                                solution.solution_text,
                                            'sequence_number',
                                                solution.sequence_number,
                                            'is_primary',
                                                solution.is_primary,
                                            'alternative_method_note',
                                                solution.alternative_method_note,
                                            'scoring_steps',
                                                coalesce(
                                                    (
                                                        select jsonb_agg(
                                                            jsonb_build_object(
                                                                'step_code',
                                                                    scoring_step.step_code,
                                                                'step_description',
                                                                    scoring_step.step_description,
                                                                'sequence_number',
                                                                    scoring_step.sequence_number,
                                                                'step_score',
                                                                    scoring_step.step_score,
                                                                'acceptance_note',
                                                                    scoring_step.acceptance_note,
                                                                'allows_equivalent_method',
                                                                    scoring_step.allows_equivalent_method
                                                            )
                                                            order by
                                                                scoring_step.sequence_number
                                                        )
                                                        from public.assessment_question_scoring_steps
                                                            scoring_step
                                                        where
                                                            scoring_step.solution_id =
                                                                solution.solution_id
                                                    ),
                                                    '[]'::jsonb
                                                )
                                        )
                                        order by
                                            solution.sequence_number
                                    )
                                    from public.assessment_question_solutions
                                        solution
                                    where
                                        solution.question_version_id =
                                            question_version.question_version_id
                                ),
                                '[]'::jsonb
                            )
                    )
                    order by exam_question.display_number
                )
                from public.assessment_exam_questions exam_question
                join public.assessment_question_versions question_version
                    on question_version.question_version_id =
                        exam_question.question_version_id
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            ),
            '[]'::jsonb
        )
    )
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    join public.assessment_blueprint_versions blueprint_version
        on blueprint_version.blueprint_version_id =
            exam_version.blueprint_version_id
    join public.assessment_exam_publications publication
        on publication.publication_id =
            target_publication_id
        and publication.exam_version_id =
            exam_version.exam_version_id
    where
        exam_version.exam_version_id =
            target_exam_version_id;
$$;

revoke all on function
public.build_assessment_exam_snapshot_document(uuid, uuid)
from public;

create or replace function
public.capture_assessment_exam_publication_snapshot()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
    current_status text;
    snapshot_document_value jsonb;
    snapshot_hash_value text;
begin
    select
        exam.owner_user_id,
        exam_version.assembly_status
    into
        current_owner_user_id,
        current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            new.exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception
            'Assessment exam version does not exist.';
    end if;

    if current_status is distinct from 'APPROVED' then
        raise exception
            'Only an approved exam may be snapshotted.';
    end if;

    if new.published_by is distinct from current_owner_user_id then
        raise exception
            'Snapshot publisher must be the exam owner.';
    end if;

    if not public.assessment_exam_content_is_publishable(
        new.exam_version_id
    ) then
        raise exception
            'Assessment exam content is not publishable.';
    end if;

    snapshot_document_value :=
        public.build_assessment_exam_snapshot_document(
            new.exam_version_id,
            new.publication_id
        );

    if snapshot_document_value is null then
        raise exception
            'Assessment exam snapshot document could not be built.';
    end if;

    snapshot_hash_value := encode(
        extensions.digest(
            snapshot_document_value::text,
            'sha256'
        ),
        'hex'
    );

    insert into public.assessment_exam_snapshots (
        publication_id,
        exam_version_id,
        snapshot_schema_version,
        snapshot_document,
        snapshot_hash,
        created_by
    )
    values (
        new.publication_id,
        new.exam_version_id,
        1,
        snapshot_document_value,
        snapshot_hash_value,
        new.published_by
    );

    return new;
end;
$$;

revoke all on function
public.capture_assessment_exam_publication_snapshot()
from public;

drop trigger if exists
assessment_exam_publications_capture_snapshot
on public.assessment_exam_publications;

create trigger assessment_exam_publications_capture_snapshot
after insert
on public.assessment_exam_publications
for each row
execute function
public.capture_assessment_exam_publication_snapshot();

create or replace function
public.prevent_assessment_exam_snapshot_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    raise exception
        'Published assessment exam snapshots are immutable.';
end;
$$;

revoke all on function
public.prevent_assessment_exam_snapshot_mutation()
from public;

drop trigger if exists
assessment_exam_snapshots_immutable
on public.assessment_exam_snapshots;

create trigger assessment_exam_snapshots_immutable
before update or delete
on public.assessment_exam_snapshots
for each row
execute function
public.prevent_assessment_exam_snapshot_mutation();

create or replace function
public.assessment_exam_snapshot_hash_matches(
    target_snapshot_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_exam_snapshots snapshot
        where
            snapshot.snapshot_id =
                target_snapshot_id
            and public.assessment_exam_version_is_visible(
                snapshot.exam_version_id
            )
            and snapshot.snapshot_hash = encode(
                extensions.digest(
                    snapshot.snapshot_document::text,
                    'sha256'
                ),
                'hex'
            )
    );
$$;

revoke all on function
public.assessment_exam_snapshot_hash_matches(uuid)
from public;

grant execute on function
public.assessment_exam_snapshot_hash_matches(uuid)
to authenticated;

alter table public.assessment_exam_snapshots
    enable row level security;

revoke all on table
public.assessment_exam_snapshots
from anon;

grant select
on table public.assessment_exam_snapshots
to authenticated;

drop policy if exists
assessment_exam_snapshots_select_visible
on public.assessment_exam_snapshots;

create policy assessment_exam_snapshots_select_visible
on public.assessment_exam_snapshots
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(
        exam_version_id
    )
);

comment on table public.assessment_exam_snapshots is
'Immutable JSON snapshots captured atomically when an exam is published.';

comment on function
public.build_assessment_exam_snapshot_document(uuid, uuid) is
'Builds a complete immutable document including questions, answers, and scoring guides.';

comment on function
public.capture_assessment_exam_publication_snapshot() is
'Captures and hashes the published exam within the publication transaction.';

comment on function
public.assessment_exam_snapshot_hash_matches(uuid) is
'Recomputes SHA-256 from the stored canonical JSONB document and verifies snapshot integrity.';

commit;

