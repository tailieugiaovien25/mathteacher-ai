begin;

create or replace function public.replace_assessment_blueprint_cells(
    target_blueprint_version_id uuid,
    target_cells jsonb
)
returns setof public.assessment_blueprint_cells
language plpgsql
security definer
set search_path = ''
as $$
declare
    expected_profile_code text;
    expected_program_code text;
    expected_grade_level integer;
begin
    if target_cells is null
        or jsonb_typeof(target_cells) <> 'array'
        or jsonb_array_length(target_cells) = 0
    then
        raise exception 'BLUEPRINT_CELLS_MUST_BE_NON_EMPTY_ARRAY';
    end if;

    select
        version.profile_code,
        profile.program_code,
        blueprint.grade_level
    into
        expected_profile_code,
        expected_program_code,
        expected_grade_level
    from public.assessment_blueprint_versions version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id = version.blueprint_id
    join public.assessment_profiles profile
        on profile.profile_code = version.profile_code
    where version.blueprint_version_id = target_blueprint_version_id
    for update of version;

    if expected_profile_code is null then
        raise exception 'ASSESSMENT_BLUEPRINT_VERSION_NOT_FOUND';
    end if;

    if not public.assessment_blueprint_version_is_editable(
        target_blueprint_version_id
    ) then
        raise exception 'ASSESSMENT_BLUEPRINT_VERSION_NOT_EDITABLE';
    end if;

    if exists (
        select 1
        from jsonb_to_recordset(target_cells) as cell(
            section_code text,
            topic_code text,
            cognitive_level_code text,
            question_count integer,
            response_count integer,
            target_score numeric,
            sequence_number integer,
            specification_note text
        )
        where
            nullif(trim(cell.section_code), '') is null
            or nullif(trim(cell.topic_code), '') is null
            or nullif(trim(cell.cognitive_level_code), '') is null
            or cell.question_count is null
            or cell.question_count <= 0
            or cell.response_count is null
            or cell.response_count < cell.question_count
            or cell.target_score is null
            or cell.target_score <= 0
            or cell.sequence_number is null
            or cell.sequence_number < 0
    ) then
        raise exception 'INVALID_ASSESSMENT_BLUEPRINT_CELL';
    end if;

    if exists (
        select 1
        from jsonb_to_recordset(target_cells) as cell(
            section_code text,
            topic_code text,
            cognitive_level_code text
        )
        group by
            cell.section_code,
            cell.topic_code,
            cell.cognitive_level_code
        having count(*) > 1
    ) then
        raise exception 'DUPLICATE_ASSESSMENT_BLUEPRINT_CELL';
    end if;

    if exists (
        select 1
        from jsonb_to_recordset(target_cells) as cell(
            section_code text,
            topic_code text,
            cognitive_level_code text
        )
        left join public.assessment_profile_sections section
            on section.profile_code = expected_profile_code
            and section.section_code = cell.section_code
        left join public.assessment_curriculum_topics topic
            on topic.topic_code = cell.topic_code
            and topic.program_code = expected_program_code
            and topic.status = 'ACTIVE'
            and (
                topic.grade_level is null
                or topic.grade_level = expected_grade_level
            )
        left join public.assessment_cognitive_levels level
            on level.cognitive_level_code = cell.cognitive_level_code
            and level.status = 'ACTIVE'
        where
            section.section_code is null
            or topic.topic_code is null
            or level.cognitive_level_code is null
    ) then
        raise exception 'BLUEPRINT_CELL_SCOPE_INVALID';
    end if;

    if exists (
        select 1
        from public.assessment_profile_sections section
        left join (
            select
                cell.section_code,
                sum(cell.question_count)::integer as question_count,
                sum(cell.response_count)::integer as response_count,
                sum(cell.target_score)::numeric as target_score
            from jsonb_to_recordset(target_cells) as cell(
                section_code text,
                question_count integer,
                response_count integer,
                target_score numeric
            )
            group by cell.section_code
        ) supplied
            on supplied.section_code = section.section_code
        where
            section.profile_code = expected_profile_code
            and (
                supplied.section_code is null
                or supplied.question_count <> section.question_count
                or supplied.response_count <> section.response_count
                or abs(
                    supplied.target_score - section.section_score
                ) > 0.0001
            )
    ) then
        raise exception 'BLUEPRINT_CELL_SECTION_TOTALS_MISMATCH';
    end if;

    if exists (
        select 1
        from jsonb_to_recordset(target_cells) as cell(section_code text)
        left join public.assessment_profile_sections section
            on section.profile_code = expected_profile_code
            and section.section_code = cell.section_code
        where section.section_code is null
    ) then
        raise exception 'BLUEPRINT_CELL_SECTION_NOT_IN_PROFILE';
    end if;

    if exists (
        select 1
        from public.assessment_profile_level_allocations allocation
        left join (
            select
                cell.cognitive_level_code,
                sum(cell.target_score)::numeric as target_score
            from jsonb_to_recordset(target_cells) as cell(
                cognitive_level_code text,
                target_score numeric
            )
            group by cell.cognitive_level_code
        ) supplied
            on supplied.cognitive_level_code =
                allocation.cognitive_level_code
        where
            allocation.profile_code = expected_profile_code
            and abs(
                coalesce(supplied.target_score, 0)
                - allocation.target_score
            ) > 0.0001
    ) then
        raise exception 'BLUEPRINT_CELL_LEVEL_TOTALS_MISMATCH';
    end if;

    delete from public.assessment_blueprint_cells
    where blueprint_version_id = target_blueprint_version_id;

    insert into public.assessment_blueprint_cells (
        blueprint_version_id,
        profile_code,
        section_code,
        topic_code,
        cognitive_level_code,
        question_type_code,
        question_count,
        response_count,
        target_score,
        sequence_number,
        specification_note
    )
    select
        target_blueprint_version_id,
        expected_profile_code,
        cell.section_code,
        cell.topic_code,
        cell.cognitive_level_code,
        section.question_type_code,
        cell.question_count,
        cell.response_count,
        cell.target_score,
        cell.sequence_number,
        coalesce(cell.specification_note, '')
    from jsonb_to_recordset(target_cells) as cell(
        section_code text,
        topic_code text,
        cognitive_level_code text,
        question_count integer,
        response_count integer,
        target_score numeric,
        sequence_number integer,
        specification_note text
    )
    join public.assessment_profile_sections section
        on section.profile_code = expected_profile_code
        and section.section_code = cell.section_code;

    return query
    select stored.*
    from public.assessment_blueprint_cells stored
    where stored.blueprint_version_id = target_blueprint_version_id
    order by stored.sequence_number, stored.blueprint_cell_id;
end;
$$;

revoke all on function
public.replace_assessment_blueprint_cells(uuid, jsonb)
from public;

grant execute on function
public.replace_assessment_blueprint_cells(uuid, jsonb)
to authenticated;

comment on function
public.replace_assessment_blueprint_cells(uuid, jsonb) is
'Atomically replaces a teacher-owned editable blueprint cell set and enforces profile section, cognitive-level and curriculum scope totals.';

create or replace function public.review_assessment_blueprint(
    target_blueprint_version_id uuid,
    target_decision text,
    target_review_note text default ''
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    created_review_id uuid;
begin
    if not public.current_user_is_portal_admin() then
        raise exception 'PORTAL_ADMIN_REQUIRED';
    end if;

    if target_decision not in (
        'APPROVED',
        'REVISION_REQUIRED',
        'REJECTED'
    ) then
        raise exception 'UNSUPPORTED_BLUEPRINT_REVIEW_DECISION';
    end if;

    insert into public.assessment_blueprint_reviews (
        blueprint_version_id,
        reviewer_user_id,
        decision,
        review_note,
        checklist
    )
    values (
        target_blueprint_version_id,
        (select auth.uid()),
        target_decision,
        coalesce(target_review_note, ''),
        jsonb_build_object(
            'canonical_scope_checked', true,
            'profile_totals_checked', true,
            'reviewed_in_portal', true
        )
    )
    returning review_id into created_review_id;

    return created_review_id;
end;
$$;

revoke all on function
public.review_assessment_blueprint(uuid, text, text)
from public;

grant execute on function
public.review_assessment_blueprint(uuid, text, text)
to authenticated;

comment on function
public.review_assessment_blueprint(uuid, text, text) is
'Records one ADMIN decision through the immutable blueprint review trigger; self-review and pending-state rules remain enforced by the database.';

commit;
