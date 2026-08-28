create or replace function public.replace_assessment_blueprint_requirement_links(
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
set search_path = pg_catalog, public
as $$
declare
    assignment jsonb;
    normalized_requirement_code text;
    normalized_coverage_role text;
    normalized_target_question_count integer;
    normalized_target_score numeric;
    normalized_sequence_number integer;
    normalized_specification_note text;
    unknown_keys text[];
    duplicate_count integer;
begin
    if target_blueprint_version_id is null then
        raise exception 'BLUEPRINT_VERSION_NOT_FOUND';
    end if;

    if not exists (
        select 1
        from public.assessment_blueprint_versions v
        where v.id = target_blueprint_version_id
    ) then
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

    create temporary table tmp_blueprint_requirement_assignments (
        requirement_code text not null,
        coverage_role text not null,
        target_question_count integer not null,
        target_score numeric null,
        sequence_number integer not null,
        specification_note text null
    ) on commit drop;

    for assignment in
        select value
        from jsonb_array_elements(requirement_assignments)
    loop
        if jsonb_typeof(assignment) is distinct from 'object' then
            raise exception 'ASSIGNMENT_NOT_OBJECT';
        end if;

        select array_agg(key order by key)
        into unknown_keys
        from jsonb_object_keys(assignment) as key
        where key not in (
            'requirement_code',
            'coverage_role',
            'target_question_count',
            'target_score',
            'sequence_number',
            'specification_note'
        );

        if unknown_keys is not null then
            raise exception 'ASSIGNMENT_UNKNOWN_FIELD: %',
                array_to_string(unknown_keys, ',');
        end if;

        if not (
            assignment ? 'requirement_code'
            and assignment ? 'coverage_role'
            and assignment ? 'target_question_count'
            and assignment ? 'sequence_number'
        ) then
            raise exception 'ASSIGNMENT_REQUIRED_FIELD_MISSING';
        end if;

        normalized_requirement_code =
            nullif(trim(assignment->>'requirement_code'), '');

        if normalized_requirement_code is null then
            raise exception 'ASSIGNMENT_REQUIRED_FIELD_MISSING';
        end if;

        normalized_coverage_role =
            upper(trim(assignment->>'coverage_role'));

        if normalized_coverage_role not in (
            'PRIMARY',
            'SUPPORTING'
        ) then
            raise exception 'INVALID_COVERAGE_ROLE';
        end if;

        begin
            normalized_target_question_count =
                (assignment->>'target_question_count')::integer;
        exception
            when others then
                raise exception 'INVALID_TARGET_QUESTION_COUNT';
        end;

        if normalized_target_question_count <= 0 then
            raise exception 'INVALID_TARGET_QUESTION_COUNT';
        end if;

        if assignment ? 'target_score'
           and jsonb_typeof(assignment->'target_score') <> 'null'
        then
            begin
                normalized_target_score =
                    (assignment->>'target_score')::numeric;
            exception
                when others then
                    raise exception 'INVALID_TARGET_SCORE';
            end;

            if normalized_target_score <= 0 then
                raise exception 'INVALID_TARGET_SCORE';
            end if;
        else
            normalized_target_score = null;
        end if;

        begin
            normalized_sequence_number =
                (assignment->>'sequence_number')::integer;
        exception
            when others then
                raise exception 'INVALID_SEQUENCE_NUMBER';
        end;

        if normalized_sequence_number < 0 then
            raise exception 'INVALID_SEQUENCE_NUMBER';
        end if;

        normalized_specification_note =
            nullif(
                trim(
                    coalesce(
                        assignment->>'specification_note',
                        ''
                    )
                ),
                ''
            );

        if not exists (
            select 1
            from public.assessment_learning_requirements r
            where r.requirement_code = normalized_requirement_code
        ) then
            raise exception 'REQUIREMENT_NOT_FOUND: %',
                normalized_requirement_code;
        end if;

        if not exists (
            select 1
            from public.assessment_learning_requirements r
            where r.requirement_code = normalized_requirement_code
              and r.status = 'ACTIVE'
        ) then
            raise exception 'REQUIREMENT_NOT_ACTIVE: %',
                normalized_requirement_code;
        end if;

        if not exists (
            select 1
            from public.assessment_learning_requirements r
            where r.requirement_code = normalized_requirement_code
              and coalesce(
                    r.metadata->>'canonical_status',
                    ''
                  ) = 'VERIFIED'
        ) then
            raise exception 'REQUIREMENT_NOT_VERIFIED: %',
                normalized_requirement_code;
        end if;

        insert into tmp_blueprint_requirement_assignments (
            requirement_code,
            coverage_role,
            target_question_count,
            target_score,
            sequence_number,
            specification_note
        )
        values (
            normalized_requirement_code,
            normalized_coverage_role,
            normalized_target_question_count,
            normalized_target_score,
            normalized_sequence_number,
            normalized_specification_note
        );
    end loop;

    select count(*) - count(distinct requirement_code)
    into duplicate_count
    from tmp_blueprint_requirement_assignments;

    if duplicate_count > 0 then
        raise exception 'DUPLICATE_REQUIREMENT_CODE';
    end if;

    delete from public.assessment_blueprint_requirement_links
    where assessment_blueprint_requirement_links.blueprint_version_id =
        target_blueprint_version_id;

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
        a.requirement_code,
        a.coverage_role,
        a.target_question_count,
        a.target_score,
        a.sequence_number,
        a.specification_note
    from tmp_blueprint_requirement_assignments a
    order by
        a.sequence_number,
        a.requirement_code;

    return query
    select
        l.blueprint_version_id,
        l.requirement_code,
        l.coverage_role,
        l.target_question_count,
        l.target_score,
        l.sequence_number,
        l.specification_note
    from public.assessment_blueprint_requirement_links l
    where l.blueprint_version_id =
        target_blueprint_version_id
    order by
        l.sequence_number,
        l.requirement_code;
end
$$;

revoke all on function public.replace_assessment_blueprint_requirement_links(
    uuid,
    jsonb
) from public;

revoke all on function public.replace_assessment_blueprint_requirement_links(
    uuid,
    jsonb
) from anon;

grant execute on function public.replace_assessment_blueprint_requirement_links(
    uuid,
    jsonb
) to authenticated;

comment on function public.replace_assessment_blueprint_requirement_links(
    uuid,
    jsonb
) is
'Atomically replaces the complete canonical learning-requirement assignment set for one editable assessment blueprint version.';
