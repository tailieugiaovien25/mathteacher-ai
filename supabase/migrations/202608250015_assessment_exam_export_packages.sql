begin;

create table if not exists public.assessment_exam_export_packages (
    export_package_id uuid primary key default gen_random_uuid(),

    variant_id uuid not null
        references public.assessment_exam_variants(variant_id)
        on delete restrict,

    package_type text not null
        check (
            package_type in (
                'STUDENT_EXAM',
                'ANSWER_KEY',
                'SCORING_GUIDE'
            )
        ),

    target_format text not null
        check (
            target_format in (
                'DOCX',
                'PDF',
                'JSON'
            )
        ),

    template_code text not null
        check (char_length(template_code) between 1 and 140),

    template_version text not null
        check (char_length(template_version) between 1 and 100),

    package_schema_version integer not null default 1
        check (package_schema_version >= 1),

    package_payload jsonb not null
        check (jsonb_typeof(package_payload) = 'object'),

    package_hash text not null
        check (char_length(package_hash) = 64),

    package_status text not null default 'LOCKED'
        check (package_status = 'LOCKED'),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),

    unique (
        variant_id,
        package_type,
        target_format,
        template_code,
        template_version
    )
);

create or replace function
public.build_assessment_student_exam_payload(
    target_variant_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'package_schema_version', 1,
        'package_type', 'STUDENT_EXAM',
        'variant', jsonb_build_object(
            'variant_id',
                variant.variant_id,
            'variant_code',
                variant.variant_code,
            'generation_policy',
                variant.generation_policy,
            'variant_hash',
                variant.variant_hash
        ),
        'exam',
            snapshot.snapshot_document -> 'exam',
        'questions',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'display_number',
                                variant_question.variant_display_number,
                            'assigned_score',
                                variant_question.question_payload
                                    -> 'assigned_score',
                            'question_type_code',
                                variant_question.question_payload
                                    -> 'question_type_code',
                            'cognitive_level_code',
                                variant_question.question_payload
                                    -> 'cognitive_level_code',
                            'prompt_text',
                                variant_question.question_payload
                                    -> 'prompt_text',
                            'stimulus_text',
                                variant_question.question_payload
                                    -> 'stimulus_text',
                            'instruction_text',
                                variant_question.question_payload
                                    -> 'instruction_text',
                            'options',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            jsonb_build_object(
                                                'option_code',
                                                    option_mapping.variant_option_code,
                                                'option_text',
                                                    option_mapping.option_payload
                                                        -> 'option_text',
                                                'sequence_number',
                                                    option_mapping.variant_sequence_number
                                            )
                                            order by
                                                option_mapping.variant_sequence_number
                                        )
                                        from public.assessment_exam_variant_option_mappings
                                            option_mapping
                                        where
                                            option_mapping.variant_question_id =
                                                variant_question.variant_question_id
                                    ),
                                    '[]'::jsonb
                                ),
                            'statements',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            jsonb_build_object(
                                                'statement_code',
                                                    statement_element
                                                        -> 'statement_code',
                                                'statement_text',
                                                    statement_element
                                                        -> 'statement_text',
                                                'sequence_number',
                                                    statement_element
                                                        -> 'sequence_number'
                                            )
                                            order by (
                                                statement_element
                                                    ->> 'sequence_number'
                                            )::integer
                                        )
                                        from jsonb_array_elements(
                                            variant_question.question_payload
                                                -> 'statements'
                                        ) statement_element
                                    ),
                                    '[]'::jsonb
                                )
                        )
                        order by
                            variant_question.variant_display_number
                    )
                    from public.assessment_exam_variant_questions
                        variant_question
                    where
                        variant_question.variant_id =
                            variant.variant_id
                ),
                '[]'::jsonb
            )
    )
    from public.assessment_exam_variants variant
    join public.assessment_exam_snapshots snapshot
        on snapshot.snapshot_id = variant.snapshot_id
    where
        variant.variant_id = target_variant_id
        and variant.variant_status = 'LOCKED';
$$;

revoke all on function
public.build_assessment_student_exam_payload(uuid)
from public;

create or replace function
public.build_assessment_answer_key_payload(
    target_variant_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'package_schema_version', 1,
        'package_type', 'ANSWER_KEY',
        'variant', jsonb_build_object(
            'variant_id',
                variant.variant_id,
            'variant_code',
                variant.variant_code,
            'variant_hash',
                variant.variant_hash
        ),
        'exam',
            snapshot.snapshot_document -> 'exam',
        'answers',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'display_number',
                                variant_question.variant_display_number,
                            'assigned_score',
                                variant_question.question_payload
                                    -> 'assigned_score',
                            'question_type_code',
                                variant_question.question_payload
                                    -> 'question_type_code',
                            'correct_options',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            option_mapping.variant_option_code
                                            order by
                                                option_mapping.variant_sequence_number
                                        )
                                        from public.assessment_exam_variant_option_mappings
                                            option_mapping
                                        where
                                            option_mapping.variant_question_id =
                                                variant_question.variant_question_id
                                            and option_mapping.is_correct
                                    ),
                                    '[]'::jsonb
                                ),
                            'statement_answers',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            jsonb_build_object(
                                                'statement_code',
                                                    statement_element
                                                        -> 'statement_code',
                                                'correct_value',
                                                    statement_element
                                                        -> 'correct_value'
                                            )
                                            order by (
                                                statement_element
                                                    ->> 'sequence_number'
                                            )::integer
                                        )
                                        from jsonb_array_elements(
                                            variant_question.question_payload
                                                -> 'statements'
                                        ) statement_element
                                    ),
                                    '[]'::jsonb
                                ),
                            'answer',
                                coalesce(
                                    variant_question.question_payload
                                        -> 'answer',
                                    '{}'::jsonb
                                )
                        )
                        order by
                            variant_question.variant_display_number
                    )
                    from public.assessment_exam_variant_questions
                        variant_question
                    where
                        variant_question.variant_id =
                            variant.variant_id
                ),
                '[]'::jsonb
            )
    )
    from public.assessment_exam_variants variant
    join public.assessment_exam_snapshots snapshot
        on snapshot.snapshot_id = variant.snapshot_id
    where
        variant.variant_id = target_variant_id
        and variant.variant_status = 'LOCKED';
$$;

revoke all on function
public.build_assessment_answer_key_payload(uuid)
from public;

create or replace function
public.build_assessment_scoring_guide_payload(
    target_variant_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'package_schema_version', 1,
        'package_type', 'SCORING_GUIDE',
        'variant', jsonb_build_object(
            'variant_id',
                variant.variant_id,
            'variant_code',
                variant.variant_code,
            'variant_hash',
                variant.variant_hash
        ),
        'exam',
            snapshot.snapshot_document -> 'exam',
        'scoring_items',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'display_number',
                                variant_question.variant_display_number,
                            'assigned_score',
                                variant_question.question_payload
                                    -> 'assigned_score',
                            'question_type_code',
                                variant_question.question_payload
                                    -> 'question_type_code',
                            'correct_options',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            option_mapping.variant_option_code
                                            order by
                                                option_mapping.variant_sequence_number
                                        )
                                        from public.assessment_exam_variant_option_mappings
                                            option_mapping
                                        where
                                            option_mapping.variant_question_id =
                                                variant_question.variant_question_id
                                            and option_mapping.is_correct
                                    ),
                                    '[]'::jsonb
                                ),
                            'statements',
                                coalesce(
                                    variant_question.question_payload
                                        -> 'statements',
                                    '[]'::jsonb
                                ),
                            'answer',
                                coalesce(
                                    variant_question.question_payload
                                        -> 'answer',
                                    '{}'::jsonb
                                ),
                            'solutions',
                                coalesce(
                                    variant_question.question_payload
                                        -> 'solutions',
                                    '[]'::jsonb
                                )
                        )
                        order by
                            variant_question.variant_display_number
                    )
                    from public.assessment_exam_variant_questions
                        variant_question
                    where
                        variant_question.variant_id =
                            variant.variant_id
                ),
                '[]'::jsonb
            )
    )
    from public.assessment_exam_variants variant
    join public.assessment_exam_snapshots snapshot
        on snapshot.snapshot_id = variant.snapshot_id
    where
        variant.variant_id = target_variant_id
        and variant.variant_status = 'LOCKED';
$$;

revoke all on function
public.build_assessment_scoring_guide_payload(uuid)
from public;

create or replace function
public.assessment_student_payload_has_forbidden_keys(
    target_payload jsonb
)
returns boolean
language sql
immutable
set search_path = ''
as $$
    select
        jsonb_path_exists(
            target_payload,
            '$.**.answer'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.solutions'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.scoring_steps'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.is_correct'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.correct_value'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.feedback_text'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.answer_explanation'
        )
        or jsonb_path_exists(
            target_payload,
            '$.**.acceptance_note'
        );
$$;

revoke all on function
public.assessment_student_payload_has_forbidden_keys(jsonb)
from public;

create or replace function
public.create_assessment_exam_export_package(
    target_variant_id uuid,
    target_package_type text,
    target_format text,
    target_template_code text,
    target_template_version text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    source_snapshot_id uuid;
    source_exam_version_id uuid;
    source_owner_user_id uuid;
    source_variant_status text;
    package_payload_value jsonb;
    package_hash_value text;
    new_export_package_id uuid;
begin
    select
        variant.snapshot_id,
        snapshot.exam_version_id,
        exam.owner_user_id,
        variant.variant_status
    into
        source_snapshot_id,
        source_exam_version_id,
        source_owner_user_id,
        source_variant_status
    from public.assessment_exam_variants variant
    join public.assessment_exam_snapshots snapshot
        on snapshot.snapshot_id = variant.snapshot_id
    join public.assessment_exam_versions exam_version
        on exam_version.exam_version_id =
            snapshot.exam_version_id
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        variant.variant_id = target_variant_id;

    if source_snapshot_id is null then
        raise exception
            'Assessment exam variant does not exist.';
    end if;

    if source_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may create export packages.';
    end if;

    if source_variant_status is distinct from 'LOCKED' then
        raise exception
            'Only a locked exam variant may be exported.';
    end if;

    if not public.assessment_exam_snapshot_hash_matches(
        source_snapshot_id
    ) then
        raise exception
            'Assessment exam snapshot checksum is invalid.';
    end if;

    if target_package_type not in (
        'STUDENT_EXAM',
        'ANSWER_KEY',
        'SCORING_GUIDE'
    ) then
        raise exception
            'Unsupported assessment export package type.';
    end if;

    if target_format not in (
        'DOCX',
        'PDF',
        'JSON'
    ) then
        raise exception
            'Unsupported assessment export format.';
    end if;

    if (
        target_template_code is null
        or char_length(trim(target_template_code))
            not between 1 and 140
    ) then
        raise exception
            'Assessment export template code is invalid.';
    end if;

    if (
        target_template_version is null
        or char_length(trim(target_template_version))
            not between 1 and 100
    ) then
        raise exception
            'Assessment export template version is invalid.';
    end if;

    case target_package_type
        when 'STUDENT_EXAM' then
            package_payload_value :=
                public.build_assessment_student_exam_payload(
                    target_variant_id
                );
        when 'ANSWER_KEY' then
            package_payload_value :=
                public.build_assessment_answer_key_payload(
                    target_variant_id
                );
        when 'SCORING_GUIDE' then
            package_payload_value :=
                public.build_assessment_scoring_guide_payload(
                    target_variant_id
                );
    end case;

    if package_payload_value is null then
        raise exception
            'Assessment export payload could not be built.';
    end if;

    if (
        target_package_type = 'STUDENT_EXAM'
        and public.assessment_student_payload_has_forbidden_keys(
            package_payload_value
        )
    ) then
        raise exception
            'Student exam payload contains forbidden answer data.';
    end if;

    package_payload_value :=
        package_payload_value
        || jsonb_build_object(
            'target_format',
                target_format,
            'template_code',
                trim(target_template_code),
            'template_version',
                trim(target_template_version)
        );

    package_hash_value := encode(
        extensions.digest(
            package_payload_value::text,
            'sha256'
        ),
        'hex'
    );

    insert into public.assessment_exam_export_packages (
        variant_id,
        package_type,
        target_format,
        template_code,
        template_version,
        package_schema_version,
        package_payload,
        package_hash,
        package_status,
        created_by
    )
    values (
        target_variant_id,
        target_package_type,
        target_format,
        trim(target_template_code),
        trim(target_template_version),
        1,
        package_payload_value,
        package_hash_value,
        'LOCKED',
        (select auth.uid())
    )
    returning export_package_id
    into new_export_package_id;

    return new_export_package_id;
end;
$$;

revoke all on function
public.create_assessment_exam_export_package(
    uuid,
    text,
    text,
    text,
    text
)
from public;

grant execute on function
public.create_assessment_exam_export_package(
    uuid,
    text,
    text,
    text,
    text
)
to authenticated;

create or replace function
public.assessment_exam_export_package_hash_matches(
    target_export_package_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_exam_export_packages export_package
        where
            export_package.export_package_id =
                target_export_package_id
            and exists (
                select 1
                from public.assessment_exam_variants variant
                join public.assessment_exam_snapshots snapshot
                    on snapshot.snapshot_id =
                        variant.snapshot_id
                where
                    variant.variant_id =
                        export_package.variant_id
                    and public.assessment_exam_version_is_visible(
                        snapshot.exam_version_id
                    )
            )
            and export_package.package_hash = encode(
                extensions.digest(
                    export_package.package_payload::text,
                    'sha256'
                ),
                'hex'
            )
    );
$$;

revoke all on function
public.assessment_exam_export_package_hash_matches(uuid)
from public;

grant execute on function
public.assessment_exam_export_package_hash_matches(uuid)
to authenticated;

create or replace function
public.prevent_assessment_exam_export_package_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    raise exception
        'Assessment exam export packages are immutable.';
end;
$$;

revoke all on function
public.prevent_assessment_exam_export_package_mutation()
from public;

create trigger assessment_exam_export_packages_immutable
before update or delete
on public.assessment_exam_export_packages
for each row
execute function
public.prevent_assessment_exam_export_package_mutation();

alter table public.assessment_exam_export_packages
    enable row level security;

revoke all on table
public.assessment_exam_export_packages
from anon;

grant select
on table public.assessment_exam_export_packages
to authenticated;

create policy assessment_exam_export_packages_select_visible
on public.assessment_exam_export_packages
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_exam_variants variant
        join public.assessment_exam_snapshots snapshot
            on snapshot.snapshot_id =
                variant.snapshot_id
        where
            variant.variant_id =
                assessment_exam_export_packages.variant_id
            and public.assessment_exam_version_is_visible(
                snapshot.exam_version_id
            )
    )
);

comment on table public.assessment_exam_export_packages is
'Immutable student, answer-key, and scoring-guide payloads for DOCX, PDF, or JSON rendering.';

comment on function
public.build_assessment_student_exam_payload(uuid) is
'Builds a student-safe payload without answers, correctness flags, solutions, or scoring steps.';

comment on function
public.assessment_student_payload_has_forbidden_keys(jsonb) is
'Rejects student payloads containing answers, correctness flags, solutions, feedback, or scoring data at any JSON depth.';

comment on function
public.create_assessment_exam_export_package(
    uuid,
    text,
    text,
    text,
    text
) is
'Creates and locks a checksummed export payload using a named template version.';

commit;

