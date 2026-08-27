begin;

create table if not exists public.assessment_exam_setting_presets (
    preset_code text primary key,
    preset_name text not null,
    profile_code text not null references
        public.assessment_profiles(profile_code) on update cascade on delete restrict,
    version_number integer not null default 1 check (version_number >= 1),
    is_default boolean not null default false,
    status text not null default 'ACTIVE'
        check (status in ('DRAFT', 'ACTIVE', 'INACTIVE', 'SUPERSEDED')),
    default_values jsonb not null default '{}'::jsonb
        check (jsonb_typeof(default_values) = 'object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_exam_setting_sets (
    setting_set_id uuid primary key default gen_random_uuid(),
    setting_code text not null unique
        check (char_length(trim(setting_code)) between 1 and 140),
    setting_name text not null
        check (char_length(trim(setting_name)) between 1 and 400),
    owner_user_id uuid not null references auth.users(id) on delete restrict,
    visibility text not null default 'PERSONAL'
        check (visibility in ('PERSONAL', 'SHARED')),
    lifecycle_status text not null default 'DRAFT'
        check (lifecycle_status in ('DRAFT', 'ACTIVE', 'RETIRED')),
    current_version_number integer not null default 0
        check (current_version_number >= 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_exam_setting_versions (
    setting_version_id uuid primary key default gen_random_uuid(),
    setting_set_id uuid not null references
        public.assessment_exam_setting_sets(setting_set_id) on delete restrict,
    version_number integer not null check (version_number >= 1),
    profile_code text not null references
        public.assessment_profiles(profile_code) on update cascade on delete restrict,
    subject_code text not null,
    grade_level integer not null check (grade_level between 1 and 12),
    assessment_name text not null,
    academic_year text not null,
    semester_number integer null check (semester_number between 1 and 3),
    duration_minutes integer not null check (duration_minutes > 0),
    total_score numeric(6,2) not null check (total_score > 0),
    textbook_id text null references
        public.textbook_catalog(textbook_id) on delete restrict,
    ppct_reference text not null default '',
    teaching_cutoff_date date null,
    class_codes jsonb not null default '[]'::jsonb
        check (jsonb_typeof(class_codes) = 'array'),
    textbook_unit_ids jsonb not null default '[]'::jsonb
        check (jsonb_typeof(textbook_unit_ids) = 'array'),
    requirement_codes jsonb not null default '[]'::jsonb
        check (jsonb_typeof(requirement_codes) = 'array'),
    teaching_scope_policy jsonb not null default '{}'::jsonb
        check (jsonb_typeof(teaching_scope_policy) = 'object'),
    competency_targets jsonb not null default '[]'::jsonb
        check (jsonb_typeof(competency_targets) = 'array'),
    question_selection_policy jsonb not null default '{}'::jsonb
        check (jsonb_typeof(question_selection_policy) = 'object'),
    export_policy jsonb not null default '{}'::jsonb
        check (jsonb_typeof(export_policy) = 'object'),
    review_status text not null default 'DRAFT'
        check (review_status in (
            'DRAFT', 'PENDING_REVIEW', 'REVISION_REQUIRED',
            'APPROVED', 'REJECTED'
        )),
    locked_at timestamptz null,
    created_by uuid not null references auth.users(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (setting_set_id, version_number),
    check (
        review_status not in ('APPROVED', 'REJECTED')
        or locked_at is not null
    )
);

create table if not exists public.assessment_exam_setting_reviews (
    review_id uuid primary key default gen_random_uuid(),
    setting_version_id uuid not null references
        public.assessment_exam_setting_versions(setting_version_id)
        on delete restrict,
    reviewer_user_id uuid not null references auth.users(id) on delete restrict,
    decision text not null check (
        decision in ('APPROVED', 'REVISION_REQUIRED', 'REJECTED')
    ),
    review_note text not null default '',
    reviewed_at timestamptz not null default now()
);

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

    select setting_set_id, owner_user_id
      into selected_set_id, existing_owner
    from public.assessment_exam_setting_sets
    where setting_code = trim(target_setting_code)
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
        select coalesce(max(version_number), 0) + 1
          into selected_version_number
        from public.assessment_exam_setting_versions
        where assessment_exam_setting_versions.setting_set_id = selected_set_id;
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

create or replace function public.submit_assessment_exam_setting_for_review(
    target_setting_version_id uuid
) returns void language plpgsql security definer set search_path = '' as $$
begin
    update public.assessment_exam_setting_versions version
    set review_status='PENDING_REVIEW', updated_at=now()
    from public.assessment_exam_setting_sets setting_set
    where version.setting_version_id=target_setting_version_id
      and setting_set.setting_set_id=version.setting_set_id
      and setting_set.owner_user_id=(select auth.uid())
      and version.review_status in ('DRAFT','REVISION_REQUIRED')
      and version.locked_at is null;
    if not found then raise exception 'EDITABLE_ASSESSMENT_SETTING_NOT_FOUND'; end if;
end; $$;

create or replace function public.review_assessment_exam_setting(
    target_setting_version_id uuid,
    target_decision text,
    target_review_note text default ''
) returns uuid language plpgsql security definer set search_path = '' as $$
declare target_owner uuid; target_set uuid; target_number integer; review_key uuid;
begin
    if not public.current_user_is_portal_admin() then raise exception 'PORTAL_ADMIN_REQUIRED'; end if;
    if target_decision not in ('APPROVED','REVISION_REQUIRED','REJECTED') then
        raise exception 'ASSESSMENT_SETTING_REVIEW_DECISION_INVALID'; end if;
    select setting_set.owner_user_id, version.setting_set_id, version.version_number
      into target_owner, target_set, target_number
    from public.assessment_exam_setting_versions version
    join public.assessment_exam_setting_sets setting_set
      on setting_set.setting_set_id=version.setting_set_id
    where version.setting_version_id=target_setting_version_id
      and version.review_status='PENDING_REVIEW' for update of version, setting_set;
    if target_owner is null then raise exception 'PENDING_ASSESSMENT_SETTING_NOT_FOUND'; end if;
    if target_owner=(select auth.uid()) then raise exception 'ASSESSMENT_SETTING_SELF_REVIEW_FORBIDDEN'; end if;
    insert into public.assessment_exam_setting_reviews(
        setting_version_id, reviewer_user_id, decision, review_note
    ) values (target_setting_version_id,(select auth.uid()),target_decision,coalesce(target_review_note,''))
    returning review_id into review_key;
    update public.assessment_exam_setting_versions set
        review_status=target_decision,
        locked_at=case when target_decision in ('APPROVED','REJECTED') then now() else null end,
        updated_at=now()
    where setting_version_id=target_setting_version_id;
    if target_decision='APPROVED' then
        update public.assessment_exam_setting_sets set
            lifecycle_status='ACTIVE', current_version_number=target_number, updated_at=now()
        where setting_set_id=target_set;
    end if;
    return review_key;
end; $$;

create or replace function public.assessment_settings_current_user_is_admin()
returns boolean language sql stable security definer set search_path='' as $$
    select public.current_user_is_portal_admin();
$$;

alter table public.assessment_exam_setting_sets enable row level security;
alter table public.assessment_exam_setting_versions enable row level security;
alter table public.assessment_exam_setting_reviews enable row level security;
alter table public.assessment_exam_setting_presets enable row level security;

grant select on public.assessment_exam_setting_sets,
    public.assessment_exam_setting_versions,
    public.assessment_exam_setting_reviews,
    public.assessment_exam_setting_presets to authenticated;
revoke all on public.assessment_exam_setting_sets,
    public.assessment_exam_setting_versions,
    public.assessment_exam_setting_reviews,
    public.assessment_exam_setting_presets from anon;

create policy assessment_setting_presets_active_read
on public.assessment_exam_setting_presets
for select to authenticated using (status = 'ACTIVE');

create policy assessment_setting_sets_visible on public.assessment_exam_setting_sets
for select to authenticated using (
    owner_user_id=(select auth.uid()) or visibility='SHARED'
    or public.current_user_is_portal_admin()
);
create policy assessment_setting_versions_visible on public.assessment_exam_setting_versions
for select to authenticated using (exists (
    select 1 from public.assessment_exam_setting_sets setting_set
    where setting_set.setting_set_id=assessment_exam_setting_versions.setting_set_id
      and (setting_set.owner_user_id=(select auth.uid()) or setting_set.visibility='SHARED'
           or public.current_user_is_portal_admin())
));
create policy assessment_setting_reviews_visible on public.assessment_exam_setting_reviews
for select to authenticated using (public.current_user_is_portal_admin() or exists (
    select 1 from public.assessment_exam_setting_versions version
    join public.assessment_exam_setting_sets setting_set on setting_set.setting_set_id=version.setting_set_id
    where version.setting_version_id=assessment_exam_setting_reviews.setting_version_id
      and setting_set.owner_user_id=(select auth.uid())
));

revoke all on function public.save_assessment_exam_setting_draft(
    text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,
    jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb) from public;
grant execute on function public.save_assessment_exam_setting_draft(
    text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,
    jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb) to authenticated;
revoke all on function public.submit_assessment_exam_setting_for_review(uuid) from public;
grant execute on function public.submit_assessment_exam_setting_for_review(uuid) to authenticated;
revoke all on function public.review_assessment_exam_setting(uuid,text,text) from public;
grant execute on function public.review_assessment_exam_setting(uuid,text,text) to authenticated;
revoke all on function public.assessment_settings_current_user_is_admin() from public;
grant execute on function public.assessment_settings_current_user_is_admin() to authenticated;

insert into public.assessment_exam_setting_presets(
    preset_code,
    preset_name,
    profile_code,
    version_number,
    is_default,
    status,
    default_values
)
values (
    'MATH-THCS-PERIODIC-DEFAULT-V1',
    'Thiết đặt mặc định đề kiểm tra định kỳ môn Toán THCS',
    'MATH-THCS-DEFAULT-3223-V1',
    1,
    true,
    'ACTIVE',
    jsonb_build_object(
        'assessment_name', 'Kiểm tra định kỳ môn Toán THCS',
        'semester_number', 1,
        'teaching_scope_policy', jsonb_build_object(
            'only_taught_content', true,
            'multi_class_scope', 'INTERSECTION',
            'include_topic_descendants', true,
            'require_ppct_reference', true,
            'require_teaching_cutoff_date', true,
            'textbook_is_context_not_authority', true
        ),
        'competency_targets', jsonb_build_array(
            jsonb_build_object(
                'domain_type', 'SUBJECT_SPECIFIC',
                'indicator_code', 'MATH_COMPETENCY_FROM_YCCD',
                'evidence_strength', 'DIRECT',
                'coverage_role', 'PRIMARY'
            ),
            jsonb_build_object(
                'domain_type', 'GENERAL',
                'indicator_code', 'PROBLEM_SOLVING_AND_CREATIVITY',
                'evidence_strength', 'INDIRECT',
                'coverage_role', 'SUPPORTING'
            ),
            jsonb_build_object(
                'domain_type', 'DIGITAL',
                'indicator_code', 'ONLY_WHEN_DIGITAL_TASK_EXISTS',
                'evidence_strength', 'CONTEXTUAL',
                'coverage_role', 'SUPPORTING'
            ),
            jsonb_build_object(
                'domain_type', 'QUALITY',
                'indicator_code', 'NO_TRAIT_CONCLUSION_FROM_SCORE_ONLY',
                'evidence_strength', 'CONTEXTUAL',
                'coverage_role', 'SUPPORTING'
            )
        ),
        'question_selection_policy', jsonb_build_object(
            'approved_and_locked_only', true,
            'avoid_recent_reuse', true,
            'avoid_cross_variant_duplicates', true,
            'variant_count', 2,
            'require_solution_and_scoring', true
        ),
        'export_policy', jsonb_build_object(
            'export_matrix', true,
            'export_specification', true,
            'export_exam', true,
            'export_answer_key', true,
            'export_marking_guide', true
        )
    )
)
on conflict (preset_code) do update set
    preset_name = excluded.preset_name,
    profile_code = excluded.profile_code,
    version_number = excluded.version_number,
    is_default = excluded.is_default,
    status = excluded.status,
    default_values = excluded.default_values,
    updated_at = now();

commit;
