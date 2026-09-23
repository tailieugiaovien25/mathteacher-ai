create or replace function
public.apply_assessment_blueprint_review()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    approved_version_number integer;
    current_blueprint_id uuid;
begin
    if not public.current_user_is_portal_admin() then
        raise exception
            'Only a portal administrator may review a blueprint.';
    end if;

    if new.reviewer_user_id is distinct from (select auth.uid()) then
        raise exception
            'Reviewer must match the authenticated user.';
    end if;

    select
        blueprint_version.review_status,
        blueprint_version.version_number,
        blueprint_version.blueprint_id
    into
        current_status,
        approved_version_number,
        current_blueprint_id
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            new.blueprint_version_id
    for update of blueprint_version, blueprint;

    if current_status is null then
        raise exception
            'Assessment blueprint version does not exist.';
    end if;

    if current_status is distinct from 'PENDING_REVIEW' then
        raise exception
            'Only a pending blueprint version may be reviewed.';
    end if;

    if new.decision = 'APPROVED' then
        if not public.assessment_blueprint_ready_for_review(
            new.blueprint_version_id
        ) then
            raise exception
                'Assessment blueprint is no longer ready for approval.';
        end if;

        update public.assessment_blueprint_versions
        set
            review_status = 'APPROVED',
            locked_at = now(),
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;

        update public.assessment_blueprints
        set
            current_version_number =
                approved_version_number,
            lifecycle_status = 'ACTIVE',
            updated_at = now()
        where
            blueprint_id = current_blueprint_id;

    elsif new.decision = 'REVISION_REQUIRED' then
        update public.assessment_blueprint_versions
        set
            review_status = 'REVISION_REQUIRED',
            locked_at = null,
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;

    elsif new.decision = 'REJECTED' then
        update public.assessment_blueprint_versions
        set
            review_status = 'REJECTED',
            locked_at = now(),
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;
    else
        raise exception
            'Unsupported assessment blueprint review decision.';
    end if;

    new.reviewed_at := now();

    return new;
end;
$$;


drop policy if exists assessment_blueprint_reviews_insert_admin on public.assessment_blueprint_reviews;
create policy assessment_blueprint_reviews_insert_admin on public.assessment_blueprint_reviews for insert to authenticated with check (public.current_user_is_portal_admin() and reviewer_user_id = (select auth.uid()) and exists (select 1 from public.assessment_blueprint_versions v where v.blueprint_version_id = assessment_blueprint_reviews.blueprint_version_id));
