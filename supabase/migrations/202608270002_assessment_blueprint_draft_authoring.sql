begin;

create or replace function
public.activate_assessment_profile(
    target_profile_code text
)
returns table (
    profile_code text,
    status text,
    activated_at timestamptz
)
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
    selected_profile public.assessment_profiles%rowtype;
    section_total numeric;
    allocation_score_total numeric;
    allocation_percentage_total numeric;
begin
    if not public.current_user_is_portal_admin() then
        raise exception 'PORTAL_ADMIN_REQUIRED';
    end if;

    select profile.*
    into selected_profile
    from public.assessment_profiles profile
    where profile.profile_code = trim(target_profile_code)
    for update;

    if selected_profile.profile_code is null then
        raise exception 'ASSESSMENT_PROFILE_NOT_FOUND';
    end if;

    if selected_profile.status = 'ACTIVE' then
        return query
        select
            selected_profile.profile_code,
            selected_profile.status,
            now();
        return;
    end if;

    if selected_profile.status <> 'DRAFT' then
        raise exception 'ASSESSMENT_PROFILE_NOT_ACTIVATABLE';
    end if;

    select coalesce(sum(section.section_score), 0)
    into section_total
    from public.assessment_profile_sections section
    where section.profile_code = selected_profile.profile_code;

    if abs(section_total - selected_profile.total_score) > 0.0001 then
        raise exception 'ASSESSMENT_PROFILE_SECTION_TOTAL_MISMATCH';
    end if;

    select
        coalesce(sum(allocation.target_score), 0),
        coalesce(sum(allocation.target_percentage), 0)
    into
        allocation_score_total,
        allocation_percentage_total
    from public.assessment_profile_level_allocations allocation
    where allocation.profile_code = selected_profile.profile_code;

    if abs(
        allocation_score_total - selected_profile.total_score
    ) > 0.0001 then
        raise exception 'ASSESSMENT_PROFILE_LEVEL_SCORE_MISMATCH';
    end if;

    if abs(allocation_percentage_total - 100) > 0.0001 then
        raise exception 'ASSESSMENT_PROFILE_LEVEL_PERCENTAGE_MISMATCH';
    end if;

    if not exists (
        select 1
        from public.assessment_profile_regulatory_links regulatory_link
        where regulatory_link.profile_code = selected_profile.profile_code
            and regulatory_link.relationship_type = 'AUTHORITY'
    ) then
        raise exception 'ASSESSMENT_PROFILE_AUTHORITY_MISSING';
    end if;

    update public.assessment_profiles profile
    set
        status = 'ACTIVE',
        effective_from = coalesce(profile.effective_from, current_date),
        updated_at = now()
    where profile.profile_code = selected_profile.profile_code;

    return query
    select
        selected_profile.profile_code,
        'ACTIVE'::text,
        now();
end;
$$;

revoke all on function
public.activate_assessment_profile(text)
from public;

grant execute on function
public.activate_assessment_profile(text)
to authenticated;

comment on function
public.activate_assessment_profile(text)
is
'Explicit ADMIN activation for a complete data-configured assessment profile; validates section score, cognitive allocation and authority links.';

create or replace function
public.create_assessment_blueprint_draft(
    target_profile_code text,
    target_grade_level integer,
    target_blueprint_code text,
    target_blueprint_name text,
    target_academic_year text default null,
    target_semester_number integer default null
)
returns table (
    blueprint_id uuid,
    blueprint_version_id uuid,
    version_number integer,
    reused boolean
)
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
    current_user_id uuid := (select auth.uid());
    normalized_blueprint_code text :=
        upper(trim(coalesce(target_blueprint_code, '')));
    normalized_blueprint_name text :=
        trim(coalesce(target_blueprint_name, ''));
    normalized_academic_year text :=
        nullif(trim(coalesce(target_academic_year, '')), '');
    selected_profile public.assessment_profiles%rowtype;
    current_blueprint public.assessment_blueprints%rowtype;
    editable_version public.assessment_blueprint_versions%rowtype;
    next_version_number integer;
begin
    if current_user_id is null then
        raise exception 'AUTHENTICATION_REQUIRED';
    end if;

    if normalized_blueprint_code = ''
       or char_length(normalized_blueprint_code) > 140
    then
        raise exception 'INVALID_BLUEPRINT_CODE';
    end if;

    if normalized_blueprint_name = '' then
        raise exception 'INVALID_BLUEPRINT_NAME';
    end if;

    if target_grade_level not between 1 and 12 then
        raise exception 'INVALID_GRADE_LEVEL';
    end if;

    if target_semester_number is not null
       and target_semester_number not between 1 and 3
    then
        raise exception 'INVALID_SEMESTER_NUMBER';
    end if;

    select profile.*
    into selected_profile
    from public.assessment_profiles profile
    where profile.profile_code = trim(target_profile_code)
        and profile.status = 'ACTIVE';

    if selected_profile.profile_code is null then
        raise exception 'ACTIVE_ASSESSMENT_PROFILE_NOT_FOUND';
    end if;

    if target_grade_level not between
        selected_profile.grade_min and selected_profile.grade_max
    then
        raise exception 'GRADE_OUTSIDE_PROFILE_SCOPE';
    end if;

    select blueprint.*
    into current_blueprint
    from public.assessment_blueprints blueprint
    where blueprint.owner_user_id = current_user_id
        and blueprint.blueprint_code = normalized_blueprint_code
    for update;

    if current_blueprint.blueprint_id is null then
        insert into public.assessment_blueprints (
            blueprint_code,
            owner_user_id,
            subject_code,
            education_level,
            grade_level,
            current_version_number,
            lifecycle_status,
            metadata
        ) values (
            normalized_blueprint_code,
            current_user_id,
            selected_profile.subject_code,
            selected_profile.education_level,
            target_grade_level,
            0,
            'DRAFT',
            jsonb_build_object(
                'canonical_program_code',
                selected_profile.program_code,
                'created_by_workflow',
                'CANONICAL_BLUEPRINT_AUTHORING'
            )
        )
        returning * into current_blueprint;
    else
        if current_blueprint.lifecycle_status = 'ARCHIVED' then
            raise exception 'BLUEPRINT_IS_ARCHIVED';
        end if;

        if current_blueprint.subject_code is distinct from
            selected_profile.subject_code
           or current_blueprint.education_level is distinct from
            selected_profile.education_level
           or current_blueprint.grade_level is distinct from
            target_grade_level
        then
            raise exception 'BLUEPRINT_SCOPE_CONFLICT';
        end if;
    end if;

    select version.*
    into editable_version
    from public.assessment_blueprint_versions version
    where version.blueprint_id = current_blueprint.blueprint_id
        and version.review_status in (
            'DRAFT',
            'AI_PROPOSED',
            'REVISION_REQUIRED'
        )
        and version.locked_at is null
    order by version.version_number desc
    limit 1
    for update;

    if editable_version.blueprint_version_id is not null then
        if editable_version.profile_code is distinct from
            selected_profile.profile_code
        then
            raise exception 'EDITABLE_VERSION_PROFILE_CONFLICT';
        end if;

        return query
        select
            current_blueprint.blueprint_id,
            editable_version.blueprint_version_id,
            editable_version.version_number,
            true;
        return;
    end if;

    select coalesce(max(version.version_number), 0) + 1
    into next_version_number
    from public.assessment_blueprint_versions version
    where version.blueprint_id = current_blueprint.blueprint_id;

    insert into public.assessment_blueprint_versions (
        blueprint_id,
        version_number,
        profile_code,
        blueprint_name,
        academic_year,
        semester_number,
        total_score,
        duration_minutes,
        origin_type,
        review_status,
        metadata,
        created_by
    ) values (
        current_blueprint.blueprint_id,
        next_version_number,
        selected_profile.profile_code,
        normalized_blueprint_name,
        normalized_academic_year,
        target_semester_number,
        selected_profile.total_score,
        selected_profile.duration_minutes,
        'HUMAN',
        'DRAFT',
        jsonb_build_object(
            'canonical_program_code',
            selected_profile.program_code,
            'profile_version_number',
            selected_profile.version_number
        ),
        current_user_id
    )
    returning * into editable_version;

    return query
    select
        current_blueprint.blueprint_id,
        editable_version.blueprint_version_id,
        editable_version.version_number,
        false;
end;
$$;

revoke all on function
public.create_assessment_blueprint_draft(
    text,
    integer,
    text,
    text,
    text,
    integer
)
from public;

grant execute on function
public.create_assessment_blueprint_draft(
    text,
    integer,
    text,
    text,
    text,
    integer
)
to authenticated;

comment on function
public.create_assessment_blueprint_draft(
    text,
    integer,
    text,
    text,
    text,
    integer
)
is
'Creates or reuses one teacher-owned editable blueprint version from an ACTIVE data-configured assessment profile.';

commit;
