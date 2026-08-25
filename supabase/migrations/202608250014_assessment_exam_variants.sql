begin;

create table if not exists public.assessment_exam_variants (
    variant_id uuid primary key default gen_random_uuid(),

    snapshot_id uuid not null
        references public.assessment_exam_snapshots(snapshot_id)
        on delete restrict,

    variant_code text not null
        check (char_length(variant_code) between 1 and 50),

    generation_seed text not null
        check (char_length(generation_seed) between 1 and 300),

    generation_policy text not null default 'SAFE_V1'
        check (generation_policy = 'SAFE_V1'),

    variant_status text not null default 'BUILDING'
        check (
            variant_status in (
                'BUILDING',
                'LOCKED'
            )
        ),

    variant_hash text null
        check (
            variant_hash is null
            or char_length(variant_hash) = 64
        ),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),

    unique (
        snapshot_id,
        variant_code
    ),

    check (
        variant_status <> 'LOCKED'
        or variant_hash is not null
    )
);

create table if not exists public.assessment_exam_variant_questions (
    variant_question_id uuid primary key default gen_random_uuid(),

    variant_id uuid not null
        references public.assessment_exam_variants(variant_id)
        on delete restrict,

    original_exam_question_id uuid not null,

    original_display_number integer not null
        check (original_display_number >= 1),

    variant_display_number integer not null
        check (variant_display_number >= 1),

    question_type_code text not null,

    question_payload jsonb not null
        check (jsonb_typeof(question_payload) = 'object'),

    question_shuffle_allowed boolean not null,

    question_order_key text not null,

    unique (
        variant_id,
        original_exam_question_id
    ),

    unique (
        variant_id,
        variant_display_number
    )
);

create table if not exists public.assessment_exam_variant_option_mappings (
    option_mapping_id uuid primary key default gen_random_uuid(),

    variant_question_id uuid not null
        references public.assessment_exam_variant_questions(
            variant_question_id
        )
        on delete restrict,

    original_option_code text not null,
    original_sequence_number integer not null
        check (original_sequence_number >= 1),

    variant_option_code text not null,
    variant_sequence_number integer not null
        check (variant_sequence_number >= 1),

    is_correct boolean not null,
    option_payload jsonb not null
        check (jsonb_typeof(option_payload) = 'object'),

    option_order_key text not null,

    unique (
        variant_question_id,
        original_option_code
    ),

    unique (
        variant_question_id,
        variant_sequence_number
    ),

    unique (
        variant_question_id,
        variant_option_code
    )
);

create or replace function
public.generate_assessment_exam_variant(
    target_snapshot_id uuid,
    target_variant_code text,
    target_generation_seed text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    source_exam_version_id uuid;
    source_snapshot_document jsonb;
    source_owner_user_id uuid;
    new_variant_id uuid;
    computed_variant_hash text;
begin
    if (
        target_variant_code is null
        or char_length(trim(target_variant_code))
            not between 1 and 50
    ) then
        raise exception
            'Assessment variant code is invalid.';
    end if;

    if (
        target_generation_seed is null
        or char_length(target_generation_seed)
            not between 1 and 300
    ) then
        raise exception
            'Assessment variant seed is invalid.';
    end if;

    select
        snapshot.exam_version_id,
        snapshot.snapshot_document,
        exam.owner_user_id
    into
        source_exam_version_id,
        source_snapshot_document,
        source_owner_user_id
    from public.assessment_exam_snapshots snapshot
    join public.assessment_exam_versions exam_version
        on exam_version.exam_version_id =
            snapshot.exam_version_id
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        snapshot.snapshot_id = target_snapshot_id;

    if source_exam_version_id is null then
        raise exception
            'Assessment exam snapshot does not exist.';
    end if;

    if source_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may generate variants.';
    end if;

    if not public.assessment_exam_snapshot_hash_matches(
        target_snapshot_id
    ) then
        raise exception
            'Assessment exam snapshot checksum is invalid.';
    end if;

    if (
        jsonb_typeof(
            source_snapshot_document -> 'questions'
        ) is distinct from 'array'
        or jsonb_array_length(
            source_snapshot_document -> 'questions'
        ) = 0
    ) then
        raise exception
            'Assessment exam snapshot contains no questions.';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(
            source_snapshot_document -> 'questions'
        ) question_element
        where
            jsonb_typeof(
                question_element -> 'options'
            ) = 'array'
            and jsonb_array_length(
                question_element -> 'options'
            ) > 26
    ) then
        raise exception
            'A multiple-choice question may not exceed 26 options.';
    end if;

    insert into public.assessment_exam_variants (
        snapshot_id,
        variant_code,
        generation_seed,
        generation_policy,
        variant_status,
        created_by
    )
    values (
        target_snapshot_id,
        trim(target_variant_code),
        target_generation_seed,
        'SAFE_V1',
        'BUILDING',
        (select auth.uid())
    )
    returning variant_id
    into new_variant_id;

    with question_source as (
        select
            question_element as question_payload,
            (
                question_element ->> 'blueprint_cell_id'
            )::uuid as blueprint_cell_id,
            (
                question_element ->> 'exam_question_id'
            )::uuid as original_exam_question_id,
            (
                question_element ->> 'display_number'
            )::integer as original_display_number,
            question_element ->> 'question_type_code'
                as question_type_code,
            (
                jsonb_typeof(
                    question_element -> 'options'
                ) = 'array'
                and jsonb_array_length(
                    question_element -> 'options'
                ) > 0
            ) as question_shuffle_allowed
        from jsonb_array_elements(
            source_snapshot_document -> 'questions'
        ) question_element
    ),
    ranked_questions as (
        select
            question_source.*,
            case
                when question_shuffle_allowed then
                    row_number() over (
                        partition by blueprint_cell_id
                        order by encode(
                            extensions.digest(
                                target_generation_seed
                                || ':QUESTION:'
                                || original_exam_question_id::text,
                                'sha256'
                            ),
                            'hex'
                        )
                    )
                else null
            end as shuffled_rank,
            encode(
                extensions.digest(
                    target_generation_seed
                    || ':QUESTION:'
                    || original_exam_question_id::text,
                    'sha256'
                ),
                'hex'
            ) as question_order_key
        from question_source
    ),
    shuffle_slots as (
        select
            blueprint_cell_id,
            array_agg(
                original_display_number
                order by original_display_number
            ) as display_numbers
        from question_source
        where question_shuffle_allowed
        group by blueprint_cell_id
    )
    insert into public.assessment_exam_variant_questions (
        variant_id,
        original_exam_question_id,
        original_display_number,
        variant_display_number,
        question_type_code,
        question_payload,
        question_shuffle_allowed,
        question_order_key
    )
    select
        new_variant_id,
        ranked_questions.original_exam_question_id,
        ranked_questions.original_display_number,
        case
            when ranked_questions.question_shuffle_allowed then
                shuffle_slots.display_numbers[
                    ranked_questions.shuffled_rank::integer
                ]
            else
                ranked_questions.original_display_number
        end,
        ranked_questions.question_type_code,
        ranked_questions.question_payload,
        ranked_questions.question_shuffle_allowed,
        ranked_questions.question_order_key
    from ranked_questions
    left join shuffle_slots
        on shuffle_slots.blueprint_cell_id =
            ranked_questions.blueprint_cell_id;

    insert into public.assessment_exam_variant_option_mappings (
        variant_question_id,
        original_option_code,
        original_sequence_number,
        variant_option_code,
        variant_sequence_number,
        is_correct,
        option_payload,
        option_order_key
    )
    select
        variant_question.variant_question_id,
        option_element ->> 'option_code',
        (
            option_element ->> 'sequence_number'
        )::integer,
        chr(
            64
            +
            row_number() over (
                partition by
                    variant_question.variant_question_id
                order by encode(
                    extensions.digest(
                        target_generation_seed
                        || ':OPTION:'
                        || variant_question.original_exam_question_id::text
                        || ':'
                        || (
                            option_element ->> 'option_code'
                        ),
                        'sha256'
                    ),
                    'hex'
                )
            )::integer
        ),
        row_number() over (
            partition by
                variant_question.variant_question_id
            order by encode(
                extensions.digest(
                    target_generation_seed
                    || ':OPTION:'
                    || variant_question.original_exam_question_id::text
                    || ':'
                    || (
                        option_element ->> 'option_code'
                    ),
                    'sha256'
                ),
                'hex'
            )
        )::integer,
        (
            option_element ->> 'is_correct'
        )::boolean,
        option_element,
        encode(
            extensions.digest(
                target_generation_seed
                || ':OPTION:'
                || variant_question.original_exam_question_id::text
                || ':'
                || (
                    option_element ->> 'option_code'
                ),
                'sha256'
            ),
            'hex'
        )
    from public.assessment_exam_variant_questions
        variant_question
    cross join lateral jsonb_array_elements(
        variant_question.question_payload -> 'options'
    ) option_element
    where
        variant_question.variant_id =
            new_variant_id
        and variant_question.question_shuffle_allowed;

    select encode(
        extensions.digest(
            jsonb_build_object(
                'variant_id',
                    variant.variant_id,
                'snapshot_id',
                    variant.snapshot_id,
                'variant_code',
                    variant.variant_code,
                'generation_seed',
                    variant.generation_seed,
                'generation_policy',
                    variant.generation_policy,
                'questions',
                    coalesce(
                        (
                            select jsonb_agg(
                                jsonb_build_object(
                                    'original_exam_question_id',
                                        variant_question.original_exam_question_id,
                                    'original_display_number',
                                        variant_question.original_display_number,
                                    'variant_display_number',
                                        variant_question.variant_display_number,
                                    'question_order_key',
                                        variant_question.question_order_key,
                                    'options',
                                        coalesce(
                                            (
                                                select jsonb_agg(
                                                    jsonb_build_object(
                                                        'original_option_code',
                                                            option_mapping.original_option_code,
                                                        'variant_option_code',
                                                            option_mapping.variant_option_code,
                                                        'variant_sequence_number',
                                                            option_mapping.variant_sequence_number,
                                                        'is_correct',
                                                            option_mapping.is_correct,
                                                        'option_order_key',
                                                            option_mapping.option_order_key
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
            )::text,
            'sha256'
        ),
        'hex'
    )
    into computed_variant_hash
    from public.assessment_exam_variants variant
    where
        variant.variant_id =
            new_variant_id;

    update public.assessment_exam_variants
    set
        variant_hash = computed_variant_hash,
        variant_status = 'LOCKED'
    where
        variant_id = new_variant_id;

    return new_variant_id;
end;
$$;

revoke all on function
public.generate_assessment_exam_variant(uuid, text, text)
from public;

grant execute on function
public.generate_assessment_exam_variant(uuid, text, text)
to authenticated;

create or replace function
public.prevent_assessment_exam_variant_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    old_parent_variant_id uuid;
    new_parent_variant_id uuid;
    old_parent_status text;
    new_parent_status text;
begin
    if tg_table_name = 'assessment_exam_variants' then
        if tg_op = 'DELETE' then
            raise exception
                'Generated assessment variants are immutable.';
        end if;

        if old.variant_status = 'LOCKED' then
            raise exception
                'Generated assessment variants are immutable.';
        end if;

        return new;
    end if;

    if tg_table_name = 'assessment_exam_variant_questions' then
        if tg_op in ('UPDATE', 'DELETE') then
            old_parent_variant_id := old.variant_id;
        end if;

        if tg_op = 'UPDATE' then
            new_parent_variant_id := new.variant_id;
        end if;

    elsif (
        tg_table_name =
            'assessment_exam_variant_option_mappings'
    ) then
        if tg_op in ('UPDATE', 'DELETE') then
            select variant_question.variant_id
            into old_parent_variant_id
            from public.assessment_exam_variant_questions
                variant_question
            where
                variant_question.variant_question_id =
                    old.variant_question_id;
        end if;

        if tg_op = 'UPDATE' then
            select variant_question.variant_id
            into new_parent_variant_id
            from public.assessment_exam_variant_questions
                variant_question
            where
                variant_question.variant_question_id =
                    new.variant_question_id;
        end if;
    else
        raise exception
            'Unsupported assessment variant mutation table.';
    end if;

    if old_parent_variant_id is not null then
        select variant.variant_status
        into old_parent_status
        from public.assessment_exam_variants variant
        where
            variant.variant_id =
                old_parent_variant_id;
    end if;

    if new_parent_variant_id is not null then
        select variant.variant_status
        into new_parent_status
        from public.assessment_exam_variants variant
        where
            variant.variant_id =
                new_parent_variant_id;
    end if;

    if (
        old_parent_status = 'LOCKED'
        or new_parent_status = 'LOCKED'
    ) then
        raise exception
            'Generated assessment variant mappings are immutable.';
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;
revoke all on function
public.prevent_assessment_exam_variant_mutation()
from public;

create trigger assessment_exam_variants_immutable
before update or delete
on public.assessment_exam_variants
for each row
execute function
public.prevent_assessment_exam_variant_mutation();

create trigger assessment_exam_variant_questions_immutable
before update or delete
on public.assessment_exam_variant_questions
for each row
execute function
public.prevent_assessment_exam_variant_mutation();

create trigger assessment_exam_variant_options_immutable
before update or delete
on public.assessment_exam_variant_option_mappings
for each row
execute function
public.prevent_assessment_exam_variant_mutation();

alter table public.assessment_exam_variants
    enable row level security;

alter table public.assessment_exam_variant_questions
    enable row level security;

alter table public.assessment_exam_variant_option_mappings
    enable row level security;

revoke all on table
    public.assessment_exam_variants,
    public.assessment_exam_variant_questions,
    public.assessment_exam_variant_option_mappings
from anon;

grant select
on table
    public.assessment_exam_variants,
    public.assessment_exam_variant_questions,
    public.assessment_exam_variant_option_mappings
to authenticated;

create policy assessment_exam_variants_select_visible
on public.assessment_exam_variants
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_exam_snapshots snapshot
        where
            snapshot.snapshot_id =
                assessment_exam_variants.snapshot_id
            and public.assessment_exam_version_is_visible(
                snapshot.exam_version_id
            )
    )
);

create policy assessment_exam_variant_questions_select_visible
on public.assessment_exam_variant_questions
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_exam_variants variant
        where
            variant.variant_id =
                assessment_exam_variant_questions.variant_id
    )
);

create policy assessment_exam_variant_options_select_visible
on public.assessment_exam_variant_option_mappings
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_exam_variant_questions
            variant_question
        where
            variant_question.variant_question_id =
                assessment_exam_variant_option_mappings.variant_question_id
    )
);

comment on table public.assessment_exam_variants is
'Locked deterministic exam variants generated from immutable snapshots.';

comment on table public.assessment_exam_variant_questions is
'Original-to-variant question position mappings and frozen payloads.';

comment on table
public.assessment_exam_variant_option_mappings is
'Original-to-variant option and correct-answer mappings.';

commit;



