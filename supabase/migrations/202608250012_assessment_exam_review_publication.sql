begin;

create table if not exists public.assessment_exam_reviews (
    review_id uuid primary key default gen_random_uuid(),

    exam_version_id uuid not null
        references public.assessment_exam_versions(exam_version_id)
        on delete restrict,

    reviewer_user_id uuid not null
        references auth.users(id)
        on delete restrict,

    decision text not null
        check (
            decision in (
                'APPROVED',
                'REVISION_REQUIRED',
                'REJECTED'
            )
        ),

    review_note text not null default '',

    checklist jsonb not null default '{}'::jsonb
        check (jsonb_typeof(checklist) = 'object'),

    reviewed_at timestamptz not null default now()
);

create table if not exists public.assessment_exam_publications (
    publication_id uuid primary key default gen_random_uuid(),

    exam_version_id uuid not null unique
        references public.assessment_exam_versions(exam_version_id)
        on delete restrict,

    published_by uuid not null
        references auth.users(id)
        on delete restrict,

    publication_channel text not null default 'INTERNAL'
        check (
            publication_channel in (
                'INTERNAL',
                'PRINT',
                'DIGITAL',
                'EXPORT'
            )
        ),

    publication_note text not null default '',
    published_at timestamptz not null default now()
);

create index if not exists
assessment_exam_reviews_version_idx
on public.assessment_exam_reviews (
    exam_version_id,
    reviewed_at desc
);

create or replace function
public.assessment_exam_content_is_publishable(
    target_exam_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_exam_versions exam_version
        join public.assessment_blueprint_versions blueprint_version
            on blueprint_version.blueprint_version_id =
                exam_version.blueprint_version_id
        where
            exam_version.exam_version_id =
                target_exam_version_id

            and blueprint_version.review_status = 'APPROVED'
            and blueprint_version.locked_at is not null

            and public.assessment_exam_assembly_matches_blueprint(
                exam_version.exam_version_id
            )

            and exists (
                select 1
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            )

            and not exists (
                select 1
                from public.assessment_exam_questions exam_question
                join public.assessment_question_versions question_version
                    on question_version.question_version_id =
                        exam_question.question_version_id
                join public.assessment_question_items question
                    on question.question_id =
                        question_version.question_id
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
                    and (
                        question_version.review_status
                            is distinct from 'APPROVED'
                        or question_version.locked_at is null
                        or question.lifecycle_status
                            is distinct from 'ACTIVE'
                    )
            )
    );
$$;

revoke all on function
public.assessment_exam_content_is_publishable(uuid)
from public;

grant execute on function
public.assessment_exam_content_is_publishable(uuid)
to authenticated;

create or replace function
public.submit_assessment_exam_for_review(
    target_exam_version_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
    current_status text;
begin
    select
        exam.owner_user_id,
        exam_version.assembly_status
    into
        current_owner_user_id,
        current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            target_exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception
            'Assessment exam version does not exist.';
    end if;

    if current_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may submit it for review.';
    end if;

    if current_status is distinct from 'ASSEMBLED' then
        raise exception
            'Only an assembled exam may be submitted for review.';
    end if;

    if not public.assessment_exam_ready_for_review(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam is not ready for review.';
    end if;

    if not public.assessment_exam_content_is_publishable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam contains unavailable content.';
    end if;

    update public.assessment_exam_versions
    set
        assembly_status = 'PENDING_REVIEW',
        updated_at = now()
    where
        exam_version_id =
            target_exam_version_id;
end;
$$;

revoke all on function
public.submit_assessment_exam_for_review(uuid)
from public;

grant execute on function
public.submit_assessment_exam_for_review(uuid)
to authenticated;

create or replace function
public.apply_assessment_exam_review()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    approved_version_number integer;
    current_exam_id uuid;
    current_owner_user_id uuid;
begin
    if not public.current_user_is_portal_admin() then
        raise exception
            'Only a portal administrator may review an exam.';
    end if;

    if new.reviewer_user_id is distinct from (select auth.uid()) then
        raise exception
            'Reviewer must match the authenticated user.';
    end if;

    select
        exam_version.assembly_status,
        exam_version.version_number,
        exam_version.exam_id,
        exam.owner_user_id
    into
        current_status,
        approved_version_number,
        current_exam_id,
        current_owner_user_id
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            new.exam_version_id
    for update of exam_version, exam;

    if current_status is null then
        raise exception
            'Assessment exam version does not exist.';
    end if;

    if current_owner_user_id = (select auth.uid()) then
        raise exception
            'A reviewer may not review their own exam.';
    end if;

    if current_status is distinct from 'PENDING_REVIEW' then
        raise exception
            'Only a pending exam version may be reviewed.';
    end if;

    if new.decision = 'APPROVED' then
        if not public.assessment_exam_ready_for_review(
            new.exam_version_id
        ) then
            raise exception
                'Assessment exam no longer matches its blueprint.';
        end if;

        if not public.assessment_exam_content_is_publishable(
            new.exam_version_id
        ) then
            raise exception
                'Assessment exam contains unavailable content.';
        end if;

        update public.assessment_exam_versions
        set
            assembly_status = 'APPROVED',
            locked_at = now(),
            updated_at = now()
        where
            exam_version_id = new.exam_version_id;

        update public.assessment_exams
        set
            current_version_number =
                approved_version_number,
            lifecycle_status = 'ACTIVE',
            updated_at = now()
        where
            exam_id = current_exam_id;

    elsif new.decision = 'REVISION_REQUIRED' then
        update public.assessment_exam_versions
        set
            assembly_status = 'REVISION_REQUIRED',
            locked_at = null,
            updated_at = now()
        where
            exam_version_id = new.exam_version_id;

    elsif new.decision = 'REJECTED' then
        update public.assessment_exam_versions
        set
            assembly_status = 'REJECTED',
            locked_at = now(),
            updated_at = now()
        where
            exam_version_id = new.exam_version_id;
    else
        raise exception
            'Unsupported assessment exam review decision.';
    end if;

    new.reviewed_at := now();

    return new;
end;
$$;

revoke all on function
public.apply_assessment_exam_review()
from public;

drop trigger if exists
assessment_exam_reviews_apply
on public.assessment_exam_reviews;

create trigger assessment_exam_reviews_apply
before insert
on public.assessment_exam_reviews
for each row
execute function
public.apply_assessment_exam_review();

create or replace function
public.publish_assessment_exam(
    target_exam_version_id uuid,
    target_publication_channel text default 'INTERNAL',
    target_publication_note text default ''
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_exam_id uuid;
    current_version_number integer;
    current_owner_user_id uuid;
    current_status text;
    new_publication_id uuid;
begin
    select
        exam_version.exam_id,
        exam_version.version_number,
        exam.owner_user_id,
        exam_version.assembly_status
    into
        current_exam_id,
        current_version_number,
        current_owner_user_id,
        current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            target_exam_version_id
    for update of exam_version, exam;

    if current_exam_id is null then
        raise exception
            'Assessment exam version does not exist.';
    end if;

    if current_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may publish it.';
    end if;

    if current_status is distinct from 'APPROVED' then
        raise exception
            'Only an approved exam may be published.';
    end if;

    if not exists (
        select 1
        from public.assessment_exams exam
        where
            exam.exam_id = current_exam_id
            and exam.current_version_number =
                current_version_number
    ) then
        raise exception
            'Only the current approved exam version may be published.';
    end if;

    if target_publication_channel not in (
        'INTERNAL',
        'PRINT',
        'DIGITAL',
        'EXPORT'
    ) then
        raise exception
            'Unsupported assessment publication channel.';
    end if;

    if not public.assessment_exam_content_is_publishable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam content is no longer publishable.';
    end if;

    insert into public.assessment_exam_publications (
        exam_version_id,
        published_by,
        publication_channel,
        publication_note
    )
    values (
        target_exam_version_id,
        (select auth.uid()),
        target_publication_channel,
        coalesce(target_publication_note, '')
    )
    returning publication_id
    into new_publication_id;

    update public.assessment_exam_versions
    set
        assembly_status = 'PUBLISHED',
        locked_at = coalesce(locked_at, now()),
        updated_at = now()
    where
        exam_version_id =
            target_exam_version_id;

    return new_publication_id;
end;
$$;

revoke all on function
public.publish_assessment_exam(uuid, text, text)
from public;

grant execute on function
public.publish_assessment_exam(uuid, text, text)
to authenticated;

alter table public.assessment_exam_reviews
    enable row level security;

alter table public.assessment_exam_publications
    enable row level security;

revoke all on table
    public.assessment_exam_reviews,
    public.assessment_exam_publications
from anon;

grant select, insert
on table public.assessment_exam_reviews
to authenticated;

grant select
on table public.assessment_exam_publications
to authenticated;

revoke update
on table public.assessment_exams
from authenticated;

grant update (
    exam_code,
    metadata,
    updated_at
)
on table public.assessment_exams
to authenticated;

drop policy if exists
assessment_exam_reviews_select_visible
on public.assessment_exam_reviews;

create policy assessment_exam_reviews_select_visible
on public.assessment_exam_reviews
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(
        exam_version_id
    )
);

drop policy if exists
assessment_exam_reviews_insert_admin
on public.assessment_exam_reviews;

create policy assessment_exam_reviews_insert_admin
on public.assessment_exam_reviews
for insert
to authenticated
with check (
    public.current_user_is_portal_admin()
    and reviewer_user_id = (select auth.uid())
    and exists (
        select 1
        from public.assessment_exam_versions exam_version
        join public.assessment_exams exam
            on exam.exam_id = exam_version.exam_id
        where
            exam_version.exam_version_id =
                assessment_exam_reviews.exam_version_id
            and exam.owner_user_id
                is distinct from (select auth.uid())
    )
);

drop policy if exists
assessment_exam_publications_select_visible
on public.assessment_exam_publications;

create policy assessment_exam_publications_select_visible
on public.assessment_exam_publications
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(
        exam_version_id
    )
);

comment on table public.assessment_exam_reviews is
'Immutable administrative review history for exam versions.';

comment on table public.assessment_exam_publications is
'Immutable publication record for each published exam version.';

comment on function
public.assessment_exam_content_is_publishable(uuid) is
'Rechecks the approved blueprint and every approved active question.';

comment on function
public.publish_assessment_exam(uuid, text, text) is
'Publishes only the current approved exam version owned by the teacher.';

commit;

