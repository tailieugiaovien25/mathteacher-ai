begin;

alter table public.assessment_blueprint_versions
    add column if not exists setting_version_id uuid null references
        public.assessment_exam_setting_versions(setting_version_id)
        on delete restrict;

alter table public.assessment_exam_versions
    add column if not exists setting_version_id uuid null references
        public.assessment_exam_setting_versions(setting_version_id)
        on delete restrict,
    add column if not exists setting_snapshot jsonb null;

create index if not exists assessment_blueprint_versions_setting_idx
on public.assessment_blueprint_versions(setting_version_id);

create index if not exists assessment_exam_versions_setting_idx
on public.assessment_exam_versions(setting_version_id);

create or replace function public.bind_assessment_setting_to_blueprint(
    target_blueprint_version_id uuid,
    target_setting_version_id uuid
)
returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare
    current_user_id uuid := (select auth.uid());
    blueprint_row record;
    setting_row record;
begin
    if current_user_id is null then
        raise exception 'AUTHENTICATION_REQUIRED';
    end if;

    select v.*, b.owner_user_id, b.subject_code as blueprint_subject_code,
           b.grade_level as blueprint_grade_level
      into blueprint_row
      from public.assessment_blueprint_versions v
      join public.assessment_blueprints b on b.blueprint_id = v.blueprint_id
     where v.blueprint_version_id = target_blueprint_version_id
     for update;

    if blueprint_row.blueprint_version_id is null then
        raise exception 'BLUEPRINT_VERSION_NOT_FOUND';
    end if;
    if blueprint_row.owner_user_id is distinct from current_user_id then
        raise exception 'BLUEPRINT_OWNER_REQUIRED';
    end if;
    if blueprint_row.locked_at is not null
       or blueprint_row.review_status not in ('DRAFT','AI_PROPOSED','REVISION_REQUIRED') then
        raise exception 'BLUEPRINT_VERSION_NOT_EDITABLE';
    end if;

    select v.*, s.owner_user_id, s.lifecycle_status
      into setting_row
      from public.assessment_exam_setting_versions v
      join public.assessment_exam_setting_sets s on s.setting_set_id = v.setting_set_id
     where v.setting_version_id = target_setting_version_id;

    if setting_row.setting_version_id is null then
        raise exception 'SETTING_VERSION_NOT_FOUND';
    end if;
    if setting_row.review_status <> 'APPROVED'
       or setting_row.locked_at is null
       or setting_row.lifecycle_status <> 'ACTIVE' then
        raise exception 'SETTING_VERSION_NOT_GOVERNED';
    end if;
    if setting_row.owner_user_id is distinct from current_user_id
       and not public.current_user_is_portal_admin() then
        raise exception 'SETTING_VERSION_NOT_VISIBLE';
    end if;
    if setting_row.profile_code <> blueprint_row.profile_code
       or setting_row.subject_code <> blueprint_row.blueprint_subject_code
       or setting_row.grade_level <> blueprint_row.blueprint_grade_level
       or setting_row.academic_year <> blueprint_row.academic_year
       or setting_row.semester_number is distinct from blueprint_row.semester_number
       or setting_row.duration_minutes <> blueprint_row.duration_minutes
       or setting_row.total_score <> blueprint_row.total_score then
        raise exception 'SETTING_BLUEPRINT_SCOPE_MISMATCH';
    end if;

    if exists (
        select 1
          from public.assessment_blueprint_requirement_links link
         where link.blueprint_version_id = target_blueprint_version_id
           and not (setting_row.requirement_codes ? link.requirement_code)
    ) then
        raise exception 'BLUEPRINT_REQUIREMENT_OUTSIDE_SETTING_SCOPE';
    end if;

    update public.assessment_blueprint_versions
       set setting_version_id = target_setting_version_id,
           updated_at = now()
     where blueprint_version_id = target_blueprint_version_id;

    return jsonb_build_object(
        'blueprint_version_id', target_blueprint_version_id,
        'setting_version_id', target_setting_version_id
    );
end;
$$;

create or replace function public.enforce_blueprint_setting_before_review()
returns trigger language plpgsql set search_path = ''
as $$
declare
    governed_requirement_codes jsonb;
begin
    if new.review_status = 'PENDING_REVIEW'
       and old.review_status is distinct from 'PENDING_REVIEW' then
        if new.setting_version_id is null or not exists (
            select 1
              from public.assessment_exam_setting_versions setting_version
              join public.assessment_exam_setting_sets setting_set
                on setting_set.setting_set_id = setting_version.setting_set_id
             where setting_version.setting_version_id = new.setting_version_id
               and setting_version.review_status = 'APPROVED'
               and setting_version.locked_at is not null
               and setting_set.lifecycle_status = 'ACTIVE'
        ) then
            raise exception 'APPROVED_ACTIVE_SETTING_REQUIRED';
        end if;

        select requirement_codes into governed_requirement_codes
          from public.assessment_exam_setting_versions
         where setting_version_id = new.setting_version_id;

        if exists (
            select 1
              from public.assessment_blueprint_requirement_links link
             where link.blueprint_version_id = new.blueprint_version_id
               and not (governed_requirement_codes ? link.requirement_code)
        ) then
            raise exception 'BLUEPRINT_REQUIREMENT_OUTSIDE_SETTING_SCOPE';
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists assessment_blueprint_setting_review_guard
on public.assessment_blueprint_versions;
create trigger assessment_blueprint_setting_review_guard
before update of review_status on public.assessment_blueprint_versions
for each row execute function public.enforce_blueprint_setting_before_review();

create or replace function public.capture_exam_setting_snapshot()
returns trigger language plpgsql set search_path = ''
as $$
declare
    linked_setting_id uuid;
    setting_document jsonb;
begin
    select setting_version_id into linked_setting_id
      from public.assessment_blueprint_versions
     where blueprint_version_id = new.blueprint_version_id;

    if linked_setting_id is null then
        raise exception 'BLUEPRINT_SETTING_REQUIRED_FOR_EXAM';
    end if;

    select jsonb_build_object(
        'setting_version_id', v.setting_version_id,
        'setting_set_id', v.setting_set_id,
        'version_number', v.version_number,
        'profile_code', v.profile_code,
        'subject_code', v.subject_code,
        'grade_level', v.grade_level,
        'assessment_name', v.assessment_name,
        'academic_year', v.academic_year,
        'semester_number', v.semester_number,
        'duration_minutes', v.duration_minutes,
        'total_score', v.total_score,
        'textbook_id', v.textbook_id,
        'ppct_reference', v.ppct_reference,
        'teaching_cutoff_date', v.teaching_cutoff_date,
        'class_codes', v.class_codes,
        'textbook_unit_ids', v.textbook_unit_ids,
        'requirement_codes', v.requirement_codes,
        'teaching_scope_policy', v.teaching_scope_policy,
        'competency_targets', v.competency_targets,
        'question_selection_policy', v.question_selection_policy,
        'export_policy', v.export_policy,
        'review_status', v.review_status,
        'locked_at', v.locked_at
    ) into setting_document
      from public.assessment_exam_setting_versions v
      join public.assessment_exam_setting_sets s on s.setting_set_id = v.setting_set_id
     where v.setting_version_id = linked_setting_id
       and v.review_status = 'APPROVED'
       and v.locked_at is not null
       and s.lifecycle_status = 'ACTIVE';

    if setting_document is null then
        raise exception 'GOVERNED_SETTING_UNAVAILABLE_FOR_EXAM';
    end if;

    new.setting_version_id := linked_setting_id;
    new.setting_snapshot := setting_document;
    return new;
end;
$$;

drop trigger if exists assessment_exam_setting_snapshot_capture
on public.assessment_exam_versions;
create trigger assessment_exam_setting_snapshot_capture
before insert on public.assessment_exam_versions
for each row execute function public.capture_exam_setting_snapshot();

create or replace function public.protect_exam_setting_snapshot()
returns trigger language plpgsql set search_path = ''
as $$
begin
    if new.setting_version_id is distinct from old.setting_version_id
       or new.setting_snapshot is distinct from old.setting_snapshot then
        raise exception 'EXAM_SETTING_SNAPSHOT_IS_IMMUTABLE';
    end if;
    return new;
end;
$$;

drop trigger if exists assessment_exam_setting_snapshot_immutable
on public.assessment_exam_versions;
create trigger assessment_exam_setting_snapshot_immutable
before update of setting_version_id, setting_snapshot
on public.assessment_exam_versions
for each row execute function public.protect_exam_setting_snapshot();

revoke all on function public.bind_assessment_setting_to_blueprint(uuid, uuid)
from public;
grant execute on function public.bind_assessment_setting_to_blueprint(uuid, uuid)
to authenticated;

comment on column public.assessment_blueprint_versions.setting_version_id is
'Approved locked exam-setting version governing this blueprint.';
comment on column public.assessment_exam_versions.setting_snapshot is
'Immutable JSON snapshot of the governed setting captured at exam creation.';

commit;
