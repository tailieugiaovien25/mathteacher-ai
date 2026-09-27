begin;

create table if not exists public.assessment_blueprint_question_slots (
    slot_id uuid primary key default gen_random_uuid(),

    blueprint_version_id uuid not null
        references public.assessment_blueprint_versions(blueprint_version_id)
        on delete restrict,

    blueprint_cell_id uuid not null
        references public.assessment_blueprint_cells(blueprint_cell_id)
        on delete restrict,

    requirement_code text not null
        references public.assessment_learning_requirements(requirement_code)
        on update cascade
        on delete restrict,

    requirement_occurrence_number integer not null
        check (requirement_occurrence_number >= 1),

    slot_number integer not null
        check (slot_number >= 1),

    display_position integer not null
        check (display_position >= 1),

    section_code text not null,
    topic_code text not null,
    cognitive_level_code text not null,
    question_type_code text not null,

    target_score numeric(12,6) not null
        check (target_score > 0),

    slot_status text not null default 'READY_FOR_GENERATION'
        check (
            slot_status in (
                'READY_FOR_GENERATION',
                'FULFILLED',
                'RETIRED'
            )
        ),

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_at timestamptz not null default now(),

    unique (
        blueprint_version_id,
        display_position
    ),

    unique (
        blueprint_cell_id,
        slot_number
    ),

    unique (
        blueprint_version_id,
        requirement_code,
        requirement_occurrence_number
    )
);

create index if not exists
    assessment_blueprint_question_slots_blueprint_idx
on public.assessment_blueprint_question_slots (
    blueprint_version_id,
    display_position
);

create index if not exists
    assessment_blueprint_question_slots_cell_idx
on public.assessment_blueprint_question_slots (
    blueprint_cell_id,
    slot_number
);

create index if not exists
    assessment_blueprint_question_slots_requirement_idx
on public.assessment_blueprint_question_slots (
    requirement_code,
    blueprint_version_id
);

alter table public.assessment_blueprint_question_slots
    enable row level security;

revoke all on table
    public.assessment_blueprint_question_slots
from anon, authenticated;

grant select on table
    public.assessment_blueprint_question_slots
to authenticated;

drop policy if exists
    assessment_blueprint_question_slots_select_visible
on public.assessment_blueprint_question_slots;

create policy
    assessment_blueprint_question_slots_select_visible
on public.assessment_blueprint_question_slots
for select
to authenticated
using (
    public.assessment_blueprint_version_is_visible(
        blueprint_version_id
    )
);

create or replace function
public.materialize_assessment_blueprint_question_slots(
    target_blueprint_version_id uuid
)
returns setof public.assessment_blueprint_question_slots
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid;
    blueprint_owner_user_id uuid;
    blueprint_lifecycle_status text;
    blueprint_review_status text;
    blueprint_locked_at timestamptz;
    existing_slot_count integer;
    expected_question_count integer;
    inserted_slot_count integer;
begin
    current_user_id := (select auth.uid());

    if current_user_id is null then
        raise exception 'AUTHENTICATION_REQUIRED';
    end if;

    select
        blueprint.owner_user_id,
        blueprint.lifecycle_status,
        version.review_status,
        version.locked_at
    into
        blueprint_owner_user_id,
        blueprint_lifecycle_status,
        blueprint_review_status,
        blueprint_locked_at
    from public.assessment_blueprint_versions version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id = version.blueprint_id
    where version.blueprint_version_id =
        target_blueprint_version_id;

    if blueprint_owner_user_id is null then
        raise exception 'ASSESSMENT_BLUEPRINT_VERSION_NOT_FOUND';
    end if;

    if blueprint_owner_user_id is distinct from current_user_id then
        raise exception 'ASSESSMENT_BLUEPRINT_OWNER_REQUIRED';
    end if;

    if (
        blueprint_lifecycle_status is distinct from 'ACTIVE'
        or blueprint_review_status is distinct from 'APPROVED'
        or blueprint_locked_at is null
    ) then
        raise exception 'APPROVED_ACTIVE_LOCKED_BLUEPRINT_REQUIRED';
    end if;

    -- Serialize calls for the same version before checking existing rows.
    perform pg_advisory_xact_lock(
        hashtextextended(target_blueprint_version_id::text, 0)
    );

    select coalesce(sum(cell.question_count), 0)::integer
    into expected_question_count
    from public.assessment_blueprint_cells cell
    where cell.blueprint_version_id = target_blueprint_version_id;

    if expected_question_count <= 0 then
        raise exception 'BLUEPRINT_HAS_NO_QUESTION_POSITIONS';
    end if;

    select count(*)
    into existing_slot_count
    from public.assessment_blueprint_question_slots slot
    where slot.blueprint_version_id =
        target_blueprint_version_id;

    if existing_slot_count > 0 then
        if existing_slot_count <> expected_question_count or exists (
            select 1
            from public.assessment_blueprint_cells cell
            left join public.assessment_blueprint_question_slots slot
                on slot.blueprint_cell_id = cell.blueprint_cell_id
                and slot.blueprint_version_id = target_blueprint_version_id
            where cell.blueprint_version_id = target_blueprint_version_id
            group by cell.blueprint_cell_id, cell.question_count,
                cell.target_score
            having count(slot.slot_id) <> cell.question_count
                or coalesce(min(slot.slot_number), 0) <> 1
                or coalesce(max(slot.slot_number), 0) <> cell.question_count
                or abs(coalesce(sum(slot.target_score), 0)
                    - cell.target_score) > 0.0001
        ) then
            raise exception 'EXISTING_QUESTION_SLOTS_INCOMPLETE';
        end if;
        return query
        select slot.*
        from public.assessment_blueprint_question_slots slot
        where slot.blueprint_version_id =
            target_blueprint_version_id
        order by slot.display_position;
        return;
    end if;

    if exists (
        with requirement_scope as (
            select
                link.requirement_code,
                link.target_question_count,
                link.target_score,
                requirement.topic_code
            from public.assessment_blueprint_requirement_links link
            join public.assessment_learning_requirements requirement
                on requirement.requirement_code =
                    link.requirement_code
            where
                link.blueprint_version_id =
                    target_blueprint_version_id
                and link.coverage_role = 'PRIMARY'
        )
        select 1
        from requirement_scope requirement
        where (
            select count(*)
            from public.assessment_blueprint_cells cell
            where
                cell.blueprint_version_id =
                    target_blueprint_version_id
                and cell.topic_code =
                    requirement.topic_code
                and abs(
                    (
                        cell.target_score
                        / cell.question_count
                    )
                    -
                    (
                        requirement.target_score
                        / requirement.target_question_count
                    )
                ) <= 0.0001
        ) <> 1
    ) then
        raise exception 'REQUIREMENT_TO_CELL_MAPPING_NOT_UNIQUE';
    end if;

    if exists (
        with requirement_scope as (
            select
                link.requirement_code,
                link.target_question_count,
                link.target_score,
                requirement.topic_code
            from public.assessment_blueprint_requirement_links link
            join public.assessment_learning_requirements requirement
                on requirement.requirement_code =
                    link.requirement_code
            where
                link.blueprint_version_id =
                    target_blueprint_version_id
                and link.coverage_role = 'PRIMARY'
        ),
        mapped as (
            select
                cell.blueprint_cell_id,
                requirement.requirement_code,
                requirement.target_question_count,
                requirement.target_score
            from requirement_scope requirement
            join public.assessment_blueprint_cells cell
                on cell.blueprint_version_id =
                    target_blueprint_version_id
                and cell.topic_code =
                    requirement.topic_code
                and abs(
                    (
                        cell.target_score
                        / cell.question_count
                    )
                    -
                    (
                        requirement.target_score
                        / requirement.target_question_count
                    )
                ) <= 0.0001
        ),
        totals as (
            select
                cell.blueprint_cell_id,
                cell.question_count,
                cell.target_score,
                coalesce(
                    sum(mapped.target_question_count),
                    0
                )::integer as mapped_question_count,
                coalesce(
                    sum(mapped.target_score),
                    0
                )::numeric as mapped_target_score
            from public.assessment_blueprint_cells cell
            left join mapped
                on mapped.blueprint_cell_id =
                    cell.blueprint_cell_id
            where
                cell.blueprint_version_id =
                    target_blueprint_version_id
            group by
                cell.blueprint_cell_id,
                cell.question_count,
                cell.target_score
        )
        select 1
        from totals
        where
            mapped_question_count <> question_count
            or abs(
                mapped_target_score - target_score
            ) > 0.0001
    ) then
        raise exception 'QUESTION_SLOT_PARTITION_MISMATCH';
    end if;

    insert into public.assessment_blueprint_question_slots (
        blueprint_version_id,
        blueprint_cell_id,
        requirement_code,
        requirement_occurrence_number,
        slot_number,
        display_position,
        section_code,
        topic_code,
        cognitive_level_code,
        question_type_code,
        target_score,
        slot_status,
        metadata
    )
    with requirement_scope as (
        select
            link.requirement_code,
            link.target_question_count,
            link.target_score,
            link.sequence_number as requirement_sequence,
            requirement.topic_code
        from public.assessment_blueprint_requirement_links link
        join public.assessment_learning_requirements requirement
            on requirement.requirement_code =
                link.requirement_code
        where
            link.blueprint_version_id =
                target_blueprint_version_id
            and link.coverage_role = 'PRIMARY'
    ),
    mapped as (
        select
            cell.blueprint_cell_id,
            cell.section_code,
            cell.topic_code,
            cell.cognitive_level_code,
            cell.question_type_code,
            cell.sequence_number as cell_sequence,
            requirement.requirement_code,
            requirement.target_question_count,
            requirement.target_score,
            requirement.requirement_sequence
        from requirement_scope requirement
        join public.assessment_blueprint_cells cell
            on cell.blueprint_version_id =
                target_blueprint_version_id
            and cell.topic_code =
                requirement.topic_code
            and abs(
                (
                    cell.target_score
                    / cell.question_count
                )
                -
                (
                    requirement.target_score
                    / requirement.target_question_count
                )
            ) <= 0.0001
    ),
    expanded as (
        select
            mapped.*,
            occurrence_number
        from mapped
        cross join lateral generate_series(
            1,
            mapped.target_question_count
        ) as occurrence_number
    ),
    numbered as (
        select
            expanded.*,
            row_number() over (
                partition by expanded.blueprint_cell_id
                order by
                    expanded.requirement_sequence,
                    expanded.requirement_code,
                    expanded.occurrence_number
            )::integer as slot_number,
            row_number() over (
                order by
                    expanded.cell_sequence,
                    expanded.blueprint_cell_id,
                    expanded.requirement_sequence,
                    expanded.requirement_code,
                    expanded.occurrence_number
            )::integer as display_position
        from expanded
    )
    select
        target_blueprint_version_id,
        numbered.blueprint_cell_id,
        numbered.requirement_code,
        numbered.occurrence_number,
        numbered.slot_number,
        numbered.display_position,
        numbered.section_code,
        numbered.topic_code,
        numbered.cognitive_level_code,
        numbered.question_type_code,
        (
            numbered.target_score
            / numbered.target_question_count
        )::numeric(12,6),
        'READY_FOR_GENERATION',
        jsonb_build_object(
            'materialization_rule',
            'topic_and_per_question_score_v1'
        )
    from numbered
    order by numbered.display_position;

    get diagnostics inserted_slot_count = row_count;

    if inserted_slot_count <> expected_question_count then
        raise exception 'QUESTION_SLOT_COUNT_MISMATCH';
    end if;

    if exists (
        select 1
        from public.assessment_blueprint_cells cell
        left join public.assessment_blueprint_question_slots slot
            on slot.blueprint_cell_id = cell.blueprint_cell_id
            and slot.blueprint_version_id = target_blueprint_version_id
        where cell.blueprint_version_id = target_blueprint_version_id
        group by cell.blueprint_cell_id, cell.question_count,
            cell.target_score
        having count(slot.slot_id) <> cell.question_count
            or abs(coalesce(sum(slot.target_score), 0)
                - cell.target_score) > 0.0001
    ) then
        raise exception 'QUESTION_SLOT_SCORE_MISMATCH';
    end if;

    return query
    select slot.*
    from public.assessment_blueprint_question_slots slot
    where slot.blueprint_version_id =
        target_blueprint_version_id
    order by slot.display_position;
end;
$$;

revoke all on function
public.materialize_assessment_blueprint_question_slots(uuid)
from public, anon;

grant execute on function
public.materialize_assessment_blueprint_question_slots(uuid)
to authenticated;

comment on table
public.assessment_blueprint_question_slots is
'Deterministic approved-blueprint question positions. AI may author content for a slot but may not change its canonical topic, requirement, level, type, or score.';

comment on function
public.materialize_assessment_blueprint_question_slots(uuid) is
'Materializes question positions only for the owning teacher from an ACTIVE APPROVED locked blueprint. Mapping fails closed unless each PRIMARY requirement maps uniquely by topic and per-question score and exactly partitions every matrix cell.';

commit;
