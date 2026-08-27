begin;

create or replace function
public.enforce_assessment_blueprint_requirement_scope()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    if not exists (
        select 1
        from public.assessment_blueprint_versions version
        join public.assessment_blueprints blueprint
            on blueprint.blueprint_id = version.blueprint_id
        join public.assessment_learning_requirements requirement
            on requirement.requirement_code = new.requirement_code
        join public.assessment_curriculum_programs program
            on program.program_code = requirement.program_code
        join public.assessment_curriculum_topics topic
            on topic.topic_code = requirement.topic_code
        where version.blueprint_version_id = new.blueprint_version_id
            and blueprint.subject_code = program.subject_code
            and blueprint.grade_level = requirement.grade_level
            and topic.program_code = requirement.program_code
            and topic.grade_level = requirement.grade_level
            and requirement.status = 'ACTIVE'
            and topic.status = 'ACTIVE'
            and program.status = 'ACTIVE'
            and coalesce(
                requirement.metadata ->> 'canonical_status',
                ''
            ) = 'VERIFIED'
    ) then
        raise exception
            'REQUIREMENT_OUTSIDE_BLUEPRINT_CANONICAL_SCOPE';
    end if;

    return new;
end;
$$;

revoke all on function
public.enforce_assessment_blueprint_requirement_scope()
from public;

drop trigger if exists
assessment_blueprint_requirement_scope_guard
on public.assessment_blueprint_requirement_links;

create trigger assessment_blueprint_requirement_scope_guard
before insert or update
on public.assessment_blueprint_requirement_links
for each row
execute function
public.enforce_assessment_blueprint_requirement_scope();

create or replace function
public.replace_assessment_blueprint_requirement_links(
    target_blueprint_version_id uuid,
    requirement_assignments jsonb
)
returns table (
    blueprint_version_id uuid,
    requirement_code text,
    coverage_role text,
    target_question_count integer,
    target_score numeric,
    sequence_number integer,
    specification_note text
)
language plpgsql
volatile
security definer
set search_path = ''
as $$
begin
    if target_blueprint_version_id is null
       or not exists (
            select 1
            from public.assessment_blueprint_versions version
            where version.blueprint_version_id =
                target_blueprint_version_id
       )
    then
        raise exception 'BLUEPRINT_VERSION_NOT_FOUND';
    end if;

    if not public.assessment_blueprint_version_is_editable(
        target_blueprint_version_id
    ) then
        raise exception 'BLUEPRINT_VERSION_NOT_EDITABLE';
    end if;

    if jsonb_typeof(requirement_assignments) is distinct from 'array' then
        raise exception 'ASSIGNMENTS_NOT_ARRAY';
    end if;

    if jsonb_array_length(requirement_assignments) = 0 then
        raise exception 'EMPTY_ASSIGNMENT_SET';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(requirement_assignments) item
        where jsonb_typeof(item) is distinct from 'object'
    ) then
        raise exception 'ASSIGNMENT_NOT_OBJECT';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(requirement_assignments) item
        cross join lateral jsonb_object_keys(item) key
        where key not in (
            'requirement_code',
            'coverage_role',
            'target_question_count',
            'target_score',
            'sequence_number',
            'specification_note'
        )
    ) then
        raise exception 'ASSIGNMENT_UNKNOWN_FIELD';
    end if;

    create temporary table tmp_blueprint_requirement_assignments (
        requirement_code text not null,
        coverage_role text not null,
        target_question_count integer not null,
        target_score numeric null,
        sequence_number integer not null,
        specification_note text not null
    ) on commit drop;

    begin
        insert into tmp_blueprint_requirement_assignments (
            requirement_code,
            coverage_role,
            target_question_count,
            target_score,
            sequence_number,
            specification_note
        )
        select
            trim(item.requirement_code),
            upper(trim(item.coverage_role)),
            item.target_question_count,
            item.target_score,
            item.sequence_number,
            trim(coalesce(item.specification_note, ''))
        from jsonb_to_recordset(requirement_assignments) as item (
            requirement_code text,
            coverage_role text,
            target_question_count integer,
            target_score numeric,
            sequence_number integer,
            specification_note text
        );
    exception
        when not_null_violation
            or invalid_text_representation
            or numeric_value_out_of_range
        then
            raise exception 'ASSIGNMENT_INVALID_VALUE';
    end;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where assignment.requirement_code = ''
    ) then
        raise exception 'ASSIGNMENT_REQUIRED_FIELD_MISSING';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where assignment.coverage_role not in ('PRIMARY', 'SUPPORTING')
    ) then
        raise exception 'INVALID_COVERAGE_ROLE';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where assignment.target_question_count <= 0
    ) then
        raise exception 'INVALID_TARGET_QUESTION_COUNT';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where assignment.target_score is not null
            and assignment.target_score <= 0
    ) then
        raise exception 'INVALID_TARGET_SCORE';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where assignment.sequence_number < 0
    ) then
        raise exception 'INVALID_SEQUENCE_NUMBER';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        group by assignment.requirement_code
        having count(*) > 1
    ) then
        raise exception 'DUPLICATE_REQUIREMENT_CODE';
    end if;

    if exists (
        select 1
        from tmp_blueprint_requirement_assignments assignment
        where not exists (
            select 1
            from public.assessment_blueprint_versions version
            join public.assessment_blueprints blueprint
                on blueprint.blueprint_id = version.blueprint_id
            join public.assessment_learning_requirements requirement
                on requirement.requirement_code =
                    assignment.requirement_code
            join public.assessment_curriculum_programs program
                on program.program_code = requirement.program_code
            join public.assessment_curriculum_topics topic
                on topic.topic_code = requirement.topic_code
            where version.blueprint_version_id =
                    target_blueprint_version_id
                and blueprint.subject_code = program.subject_code
                and blueprint.grade_level = requirement.grade_level
                and topic.program_code = requirement.program_code
                and topic.grade_level = requirement.grade_level
                and requirement.status = 'ACTIVE'
                and topic.status = 'ACTIVE'
                and program.status = 'ACTIVE'
                and coalesce(
                    requirement.metadata ->> 'canonical_status',
                    ''
                ) = 'VERIFIED'
        )
    ) then
        raise exception
            'REQUIREMENT_OUTSIDE_BLUEPRINT_CANONICAL_SCOPE';
    end if;

    delete from public.assessment_blueprint_requirement_links link
    where link.blueprint_version_id = target_blueprint_version_id;

    insert into public.assessment_blueprint_requirement_links (
        blueprint_version_id,
        requirement_code,
        coverage_role,
        target_question_count,
        target_score,
        sequence_number,
        specification_note
    )
    select
        target_blueprint_version_id,
        assignment.requirement_code,
        assignment.coverage_role,
        assignment.target_question_count,
        assignment.target_score,
        assignment.sequence_number,
        assignment.specification_note
    from tmp_blueprint_requirement_assignments assignment
    order by
        assignment.sequence_number,
        assignment.requirement_code;

    return query
    select
        link.blueprint_version_id,
        link.requirement_code,
        link.coverage_role,
        link.target_question_count,
        link.target_score,
        link.sequence_number,
        link.specification_note
    from public.assessment_blueprint_requirement_links link
    where link.blueprint_version_id = target_blueprint_version_id
    order by
        link.sequence_number,
        link.requirement_code;
end;
$$;

revoke all on function
public.replace_assessment_blueprint_requirement_links(uuid, jsonb)
from public;

grant execute on function
public.replace_assessment_blueprint_requirement_links(uuid, jsonb)
to authenticated;

comment on function
public.replace_assessment_blueprint_requirement_links(uuid, jsonb)
is
'Atomically replaces canonical requirement coverage for an editable blueprint version and enforces subject, grade, program, topic and VERIFIED scope.';

commit;
