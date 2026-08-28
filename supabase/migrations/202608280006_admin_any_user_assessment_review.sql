begin;

-- Governance change:
-- Any authenticated account with valid portal ADMIN authority may review
-- any PENDING_REVIEW assessment setting, including a setting owned by
-- the same account. Ownership remains unchanged and reviewer_user_id
-- continues to record the acting ADMIN for auditability.
--
-- This migration intentionally removes only the self-review prohibition.
-- It does not weaken the ADMIN authorization check, pending-review check,
-- ownership rules for draft editing, or review audit trail.
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

comment on function public.review_assessment_exam_setting(uuid,text,text) is
'ADMIN review workflow. Any valid portal ADMIN may review any pending assessment setting, including one owned by the same account. Owner and reviewer remain separately audited.';

commit;