-- Fix PL/pgSQL ambiguity in save_assessment_exam_setting_draft.
--
-- The function returns TABLE columns named setting_set_id,
-- setting_version_id, and version_number. Those output names are PL/pgSQL
-- variables inside the function, so unqualified table-column references with
-- the same names are ambiguous (SQLSTATE 42702).
--
-- This migration preserves the function signature and business logic and only
-- qualifies the affected table columns with explicit aliases.
create or replace function public.save_assessment_exam_setting_draft(
    target_setting_code text,
    target_setting_name text,
    target_visibility text,
    target_profile_code text,
    target_subject_code text,
    target_grade_level integer,
    target_assessment_name text,
    target_academic_year text,
    target_semester_number integer,
    target_duration_minutes integer,
    target_total_score numeric,
    target_textbook_id text,
    target_ppct_reference text,
    target_teaching_cutoff_date date,
    target_class_codes jsonb,
    target_textbook_unit_ids jsonb,
    target_requirement_codes jsonb,
    target_teaching_scope_policy jsonb,
    target_competency_targets jsonb,
    target_question_selection_policy jsonb,
    target_export_policy jsonb
)
returns table(setting_set_id uuid, setting_version_id uuid, version_number integer)
language plpgsql security definer set search_path = ''
as $$
declare
    selected_set_id uuid;
    selected_version_id uuid;
    selected_version_number integer;
    existing_owner uuid;
begin
    if nullif(trim(target_setting_code), '') is null
        or nullif(trim(target_setting_name), '') is null
        or nullif(trim(target_assessment_name), '') is null
        or nullif(trim(target_academic_year), '') is null
    then raise exception 'ASSESSMENT_SETTING_REQUIRED_TEXT_MISSING'; end if;

    if target_visibility not in ('PERSONAL', 'SHARED') then
        raise exception 'ASSESSMENT_SETTING_VISIBILITY_INVALID';
    end if;
    if target_visibility = 'SHARED'
        and not public.current_user_is_portal_admin()
    then raise exception 'SHARED_ASSESSMENT_SETTING_REQUIRES_ADMIN'; end if;

    if jsonb_typeof(coalesce(target_class_codes, '[]'::jsonb)) <> 'array'
        or jsonb_typeof(coalesce(target_textbook_unit_ids, '[]'::jsonb)) <> 'array'
        or jsonb_typeof(coalesce(target_requirement_codes, '[]'::jsonb)) <> 'array'
        or jsonb_typeof(coalesce(target_competency_targets, '[]'::jsonb)) <> 'array'
        or jsonb_typeof(coalesce(target_teaching_scope_policy, '{}'::jsonb)) <> 'object'
        or jsonb_typeof(coalesce(target_question_selection_policy, '{}'::jsonb)) <> 'object'
        or jsonb_typeof(coalesce(target_export_policy, '{}'::jsonb)) <> 'object'
    then raise exception 'ASSESSMENT_SETTING_JSON_SHAPE_INVALID'; end if;

    if not exists (
        select 1 from public.assessment_profiles profile
        where profile.profile_code = target_profile_code
          and profile.status = 'ACTIVE'
          and profile.subject_code = target_subject_code
          and target_grade_level between profile.grade_min and profile.grade_max
    ) then raise exception 'ACTIVE_ASSESSMENT_PROFILE_SCOPE_INVALID'; end if;

    if target_textbook_id is not null and not exists (
        select 1 from public.textbook_catalog textbook
        where textbook.textbook_id = target_textbook_id
          and textbook.status = 'ACTIVE'
    ) then raise exception 'ACTIVE_TEXTBOOK_NOT_FOUND'; end if;

    if exists (
        select 1 from jsonb_array_elements_text(
            coalesce(target_textbook_unit_ids, '[]'::jsonb)
        ) as selected_unit(unit_id)
        where not exists (
            select 1 from public.textbook_units unit
            where unit.textbook_unit_id = selected_unit.unit_id
              and unit.textbook_id = target_textbook_id
              and unit.status = 'ACTIVE'
        )
    ) then raise exception 'TEXTBOOK_UNIT_SCOPE_INVALID'; end if;

    if exists (
        select 1 from jsonb_array_elements_text(
            coalesce(target_requirement_codes, '[]'::jsonb)
        ) as selected_requirement(requirement_code)
        where not exists (
            select 1 from public.assessment_learning_requirements requirement
            join public.assessment_curriculum_programs program
              on program.program_code = requirement.program_code
            where requirement.requirement_code =
                selected_requirement.requirement_code
              and requirement.grade_level = target_grade_level
              and requirement.status = 'ACTIVE'
              and program.subject_code = target_subject_code
        )
    ) then raise exception 'LEARNING_REQUIREMENT_SCOPE_INVALID'; end if;

    select setting_set.setting_set_id, setting_set.owner_user_id
      into selected_set_id, existing_owner
    from public.assessment_exam_setting_sets as setting_set
    where setting_set.setting_code = trim(target_setting_code)
    for update;

    if selected_set_id is null then
        insert into public.assessment_exam_setting_sets(
            setting_code, setting_name, owner_user_id, visibility
        ) values (
            trim(target_setting_code), trim(target_setting_name),
            (select auth.uid()), target_visibility
        ) returning assessment_exam_setting_sets.setting_set_id
          into selected_set_id;
    elsif existing_owner is distinct from (select auth.uid()) then
        raise exception 'ASSESSMENT_SETTING_OWNER_REQUIRED';
    else
        update public.assessment_exam_setting_sets
        set setting_name = trim(target_setting_name),
            visibility = target_visibility,
            updated_at = now()
        where assessment_exam_setting_sets.setting_set_id = selected_set_id;
    end if;

    select version.setting_version_id, version.version_number
      into selected_version_id, selected_version_number
    from public.assessment_exam_setting_versions version
    where version.setting_set_id = selected_set_id
      and version.review_status in ('DRAFT', 'REVISION_REQUIRED')
      and version.locked_at is null
    order by version.version_number desc limit 1 for update;

    if selected_version_id is null then
        select coalesce(max(setting_version.version_number), 0) + 1
          into selected_version_number
        from public.assessment_exam_setting_versions as setting_version
        where setting_version.setting_set_id = selected_set_id;
        selected_version_id := gen_random_uuid();
        insert into public.assessment_exam_setting_versions(
            setting_version_id, setting_set_id, version_number,
            profile_code, subject_code, grade_level, assessment_name,
            academic_year, semester_number, duration_minutes, total_score,
            textbook_id, ppct_reference, teaching_cutoff_date,
            class_codes, textbook_unit_ids, requirement_codes,
            teaching_scope_policy, competency_targets,
            question_selection_policy, export_policy, created_by
        ) values (
            selected_version_id, selected_set_id, selected_version_number,
            target_profile_code, target_subject_code, target_grade_level,
            trim(target_assessment_name), trim(target_academic_year),
            target_semester_number, target_duration_minutes, target_total_score,
            target_textbook_id, coalesce(target_ppct_reference, ''),
            target_teaching_cutoff_date, coalesce(target_class_codes, '[]'),
            coalesce(target_textbook_unit_ids, '[]'),
            coalesce(target_requirement_codes, '[]'),
            coalesce(target_teaching_scope_policy, '{}'),
            coalesce(target_competency_targets, '[]'),
            coalesce(target_question_selection_policy, '{}'),
            coalesce(target_export_policy, '{}'), (select auth.uid())
        );
    else
        update public.assessment_exam_setting_versions set
            profile_code=target_profile_code, subject_code=target_subject_code,
            grade_level=target_grade_level, assessment_name=trim(target_assessment_name),
            academic_year=trim(target_academic_year), semester_number=target_semester_number,
            duration_minutes=target_duration_minutes, total_score=target_total_score,
            textbook_id=target_textbook_id,
            ppct_reference=coalesce(target_ppct_reference, ''),
            teaching_cutoff_date=target_teaching_cutoff_date,
            class_codes=coalesce(target_class_codes, '[]'),
            textbook_unit_ids=coalesce(target_textbook_unit_ids, '[]'),
            requirement_codes=coalesce(target_requirement_codes, '[]'),
            teaching_scope_policy=coalesce(target_teaching_scope_policy, '{}'),
            competency_targets=coalesce(target_competency_targets, '[]'),
            question_selection_policy=coalesce(target_question_selection_policy, '{}'),
            export_policy=coalesce(target_export_policy, '{}'), updated_at=now()
        where assessment_exam_setting_versions.setting_version_id = selected_version_id;
    end if;

    return query select selected_set_id, selected_version_id, selected_version_number;
end; $$;

