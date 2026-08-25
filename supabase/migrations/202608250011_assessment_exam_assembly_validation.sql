begin;

create or replace function
public.enforce_assessment_exam_cell_capacity()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    maximum_question_count integer;
    maximum_target_score numeric(6,2);

    existing_question_count integer;
    existing_assigned_score numeric(6,2);
begin
    select
        blueprint_cell.question_count,
        blueprint_cell.target_score
    into
        maximum_question_count,
        maximum_target_score
    from public.assessment_blueprint_cells blueprint_cell
    join public.assessment_exam_versions exam_version
        on exam_version.blueprint_version_id =
            blueprint_cell.blueprint_version_id
    where
        blueprint_cell.blueprint_cell_id =
            new.blueprint_cell_id
        and exam_version.exam_version_id =
            new.exam_version_id;

    if maximum_question_count is null then
        raise exception
            'Blueprint cell does not belong to the exam blueprint.';
    end if;

    select
        count(*)::integer,
        coalesce(sum(exam_question.assigned_score), 0)
    into
        existing_question_count,
        existing_assigned_score
    from public.assessment_exam_questions exam_question
    where
        exam_question.exam_version_id =
            new.exam_version_id
        and exam_question.blueprint_cell_id =
            new.blueprint_cell_id
        and (
            tg_op = 'INSERT'
            or exam_question.exam_question_id
                is distinct from new.exam_question_id
        );

    if (
        existing_question_count + 1
        >
        maximum_question_count
    ) then
        raise exception
            'Exam question count exceeds blueprint cell capacity.';
    end if;

    if (
        existing_assigned_score + new.assigned_score
        >
        maximum_target_score + 0.0001
    ) then
        raise exception
            'Exam score exceeds blueprint cell target.';
    end if;

    return new;
end;
$$;

revoke all on function
public.enforce_assessment_exam_cell_capacity()
from public;

drop trigger if exists
assessment_exam_questions_capacity
on public.assessment_exam_questions;

create trigger assessment_exam_questions_capacity
before insert or update
on public.assessment_exam_questions
for each row
execute function
public.enforce_assessment_exam_cell_capacity();

create or replace function
public.invalidate_assessment_exam_assembly()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    target_exam_version_id uuid;
begin
    if tg_op = 'DELETE' then
        target_exam_version_id :=
            old.exam_version_id;
    else
        target_exam_version_id :=
            new.exam_version_id;
    end if;

    update public.assessment_exam_versions
    set
        assembly_status = case
            when origin_type = 'AI'
                then 'AI_PROPOSED'
            else 'DRAFT'
        end,
        updated_at = now()
    where
        exam_version_id = target_exam_version_id
        and assembly_status in (
            'ASSEMBLED',
            'REVISION_REQUIRED'
        )
        and locked_at is null;

    if (
        tg_op = 'UPDATE'
        and old.exam_version_id
            is distinct from new.exam_version_id
    ) then
        update public.assessment_exam_versions
        set
            assembly_status = case
                when origin_type = 'AI'
                    then 'AI_PROPOSED'
                else 'DRAFT'
            end,
            updated_at = now()
        where
            exam_version_id = old.exam_version_id
            and assembly_status in (
                'ASSEMBLED',
                'REVISION_REQUIRED'
            )
            and locked_at is null;
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke all on function
public.invalidate_assessment_exam_assembly()
from public;

drop trigger if exists
assessment_exam_questions_invalidate_assembly
on public.assessment_exam_questions;

create trigger assessment_exam_questions_invalidate_assembly
after insert or update or delete
on public.assessment_exam_questions
for each row
execute function
public.invalidate_assessment_exam_assembly();

create or replace function
public.assessment_exam_cell_allocation_matches(
    target_exam_version_id uuid,
    target_blueprint_cell_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_blueprint_cells blueprint_cell
        join public.assessment_exam_versions exam_version
            on exam_version.blueprint_version_id =
                blueprint_cell.blueprint_version_id
        where
            exam_version.exam_version_id =
                target_exam_version_id
            and blueprint_cell.blueprint_cell_id =
                target_blueprint_cell_id
            and (
                select count(*)::integer
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        target_exam_version_id
                    and exam_question.blueprint_cell_id =
                        target_blueprint_cell_id
            ) = blueprint_cell.question_count
            and abs(
                (
                    select coalesce(
                        sum(exam_question.assigned_score),
                        0
                    )
                    from public.assessment_exam_questions
                        exam_question
                    where
                        exam_question.exam_version_id =
                            target_exam_version_id
                        and exam_question.blueprint_cell_id =
                            target_blueprint_cell_id
                )
                -
                blueprint_cell.target_score
            ) <= 0.0001
    );
$$;

revoke all on function
public.assessment_exam_cell_allocation_matches(uuid, uuid)
from public;

grant execute on function
public.assessment_exam_cell_allocation_matches(uuid, uuid)
to authenticated;

create or replace function
public.assessment_exam_assembly_matches_blueprint(
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
        where
            exam_version.exam_version_id =
                target_exam_version_id

            and exists (
                select 1
                from public.assessment_blueprint_cells blueprint_cell
                where
                    blueprint_cell.blueprint_version_id =
                        exam_version.blueprint_version_id
            )

            and not exists (
                select 1
                from public.assessment_blueprint_cells blueprint_cell
                where
                    blueprint_cell.blueprint_version_id =
                        exam_version.blueprint_version_id
                    and not public.assessment_exam_cell_allocation_matches(
                        exam_version.exam_version_id,
                        blueprint_cell.blueprint_cell_id
                    )
            )

            and not exists (
                select 1
                from public.assessment_exam_questions exam_question
                join public.assessment_blueprint_cells blueprint_cell
                    on blueprint_cell.blueprint_cell_id =
                        exam_question.blueprint_cell_id
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
                    and blueprint_cell.blueprint_version_id
                        is distinct from
                        exam_version.blueprint_version_id
            )

            and abs(
                (
                    select coalesce(
                        sum(exam_question.assigned_score),
                        0
                    )
                    from public.assessment_exam_questions
                        exam_question
                    where
                        exam_question.exam_version_id =
                            exam_version.exam_version_id
                )
                -
                exam_version.total_score
            ) <= 0.0001

            and (
                select count(*)::integer
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            ) > 0

            and (
                select min(exam_question.display_number)
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            ) = 1

            and (
                select max(exam_question.display_number)
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            ) = (
                select count(*)::integer
                from public.assessment_exam_questions exam_question
                where
                    exam_question.exam_version_id =
                        exam_version.exam_version_id
            )
    );
$$;

revoke all on function
public.assessment_exam_assembly_matches_blueprint(uuid)
from public;

grant execute on function
public.assessment_exam_assembly_matches_blueprint(uuid)
to authenticated;

create or replace function
public.mark_assessment_exam_assembled(
    target_exam_version_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    if not public.assessment_exam_version_is_editable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam version is not editable.';
    end if;

    if not public.assessment_exam_assembly_matches_blueprint(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam does not completely match its blueprint.';
    end if;

    update public.assessment_exam_versions
    set
        assembly_status = 'ASSEMBLED',
        updated_at = now()
    where
        exam_version_id =
            target_exam_version_id;
end;
$$;

revoke all on function
public.mark_assessment_exam_assembled(uuid)
from public;

grant execute on function
public.mark_assessment_exam_assembled(uuid)
to authenticated;

create or replace function
public.assessment_exam_ready_for_review(
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
            and exam_version.assembly_status in (
                'ASSEMBLED',
                'PENDING_REVIEW'
            )
            and exam_version.locked_at is null
            and blueprint_version.review_status = 'APPROVED'
            and blueprint_version.locked_at is not null
            and public.assessment_exam_assembly_matches_blueprint(
                exam_version.exam_version_id
            )
    );
$$;

revoke all on function
public.assessment_exam_ready_for_review(uuid)
from public;

grant execute on function
public.assessment_exam_ready_for_review(uuid)
to authenticated;

comment on function
public.assessment_exam_cell_allocation_matches(uuid, uuid) is
'Checks question count and score for one exam blueprint cell.';

comment on function
public.assessment_exam_assembly_matches_blueprint(uuid) is
'Checks every matrix cell, total score, and continuous question numbering.';

comment on function
public.mark_assessment_exam_assembled(uuid) is
'Marks an exam assembled only when it completely matches its approved blueprint.';

commit;

