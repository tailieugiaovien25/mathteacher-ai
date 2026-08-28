begin;

create or replace function
public.create_assessment_exam_draft(
    target_blueprint_version_id uuid,
    target_exam_code text,
    target_exam_title text,
    target_idempotency_key text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid;
    blueprint_owner_user_id uuid;
    blueprint_subject_code text;
    blueprint_education_level text;
    blueprint_grade_level integer;
    blueprint_lifecycle_status text;
    blueprint_review_status text;
    blueprint_locked_at timestamptz;
    blueprint_total_score numeric(6,2);
    blueprint_duration_minutes integer;
    blueprint_academic_year text;
    blueprint_semester_number integer;

    existing_exam_id uuid;
    existing_idempotency_key text;
    existing_exam_version_id uuid;

    new_exam_id uuid;
    new_exam_version_id uuid;
begin
    current_user_id := (select auth.uid());

    if current_user_id is null then
        raise exception
            'Authentication is required to create an exam draft.';
    end if;

    if target_blueprint_version_id is null then
        raise exception
            'Blueprint version id is required.';
    end if;

    if char_length(trim(coalesce(target_exam_code, ''))) = 0 then
        raise exception
            'Exam code is required.';
    end if;

    if char_length(trim(coalesce(target_exam_title, ''))) = 0 then
        raise exception
            'Exam title is required.';
    end if;

    if char_length(
        trim(coalesce(target_idempotency_key, ''))
    ) = 0 then
        raise exception
            'Idempotency key is required.';
    end if;

    perform pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            current_user_id::text
            ||
            ':'
            ||
            trim(target_exam_code),
            0
        )
    );

    select
        blueprint.owner_user_id,
        blueprint.subject_code,
        blueprint.education_level,
        blueprint.grade_level,
        blueprint.lifecycle_status,
        blueprint_version.review_status,
        blueprint_version.locked_at,
        blueprint_version.total_score,
        blueprint_version.duration_minutes,
        blueprint_version.academic_year,
        blueprint_version.semester_number
    into
        blueprint_owner_user_id,
        blueprint_subject_code,
        blueprint_education_level,
        blueprint_grade_level,
        blueprint_lifecycle_status,
        blueprint_review_status,
        blueprint_locked_at,
        blueprint_total_score,
        blueprint_duration_minutes,
        blueprint_academic_year,
        blueprint_semester_number
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            target_blueprint_version_id;

    if blueprint_owner_user_id is null then
        raise exception
            'Assessment blueprint version does not exist.';
    end if;

    if blueprint_owner_user_id is distinct from current_user_id then
        raise exception
            'Only the blueprint owner may generate an exam.';
    end if;

    if (
        blueprint_lifecycle_status is distinct from 'ACTIVE'
        or blueprint_review_status is distinct from 'APPROVED'
        or blueprint_locked_at is null
    ) then
        raise exception
            'Only an active approved locked blueprint may be used.';
    end if;

    if not exists (
        select 1
        from public.assessment_blueprint_cells blueprint_cell
        where
            blueprint_cell.blueprint_version_id =
                target_blueprint_version_id
    ) then
        raise exception
            'Assessment blueprint contains no cells.';
    end if;

    select
        exam.exam_id,
        exam.metadata ->> 'generation_idempotency_key'
    into
        existing_exam_id,
        existing_idempotency_key
    from public.assessment_exams exam
    where
        exam.owner_user_id = current_user_id
        and exam.exam_code = trim(target_exam_code)
    for update;

    if existing_exam_id is not null then
        if existing_idempotency_key
            is distinct from trim(target_idempotency_key)
        then
            raise exception
                'Exam code is already used by another request.';
        end if;

        select
            exam_version.exam_version_id
        into
            existing_exam_version_id
        from public.assessment_exam_versions exam_version
        where
            exam_version.exam_id = existing_exam_id
            and exam_version.blueprint_version_id =
                target_blueprint_version_id
            and exam_version.metadata
                ->> 'generation_idempotency_key'
                = trim(target_idempotency_key)
        order by
            exam_version.version_number desc
        limit 1;

        if existing_exam_version_id is null then
            raise exception
                'Existing exam does not match the generation request.';
        end if;

        return jsonb_build_object(
            'exam_id',
            existing_exam_id,
            'exam_version_id',
            existing_exam_version_id,
            'blueprint_version_id',
            target_blueprint_version_id,
            'reused',
            true
        );
    end if;

    insert into public.assessment_exams (
        exam_code,
        owner_user_id,
        subject_code,
        education_level,
        grade_level,
        current_version_number,
        lifecycle_status,
        metadata
    )
    values (
        trim(target_exam_code),
        current_user_id,
        blueprint_subject_code,
        blueprint_education_level,
        blueprint_grade_level,
        0,
        'DRAFT',
        jsonb_build_object(
            'generation_idempotency_key',
            trim(target_idempotency_key)
        )
    )
    returning exam_id
    into new_exam_id;

    insert into public.assessment_exam_versions (
        exam_id,
        version_number,
        blueprint_version_id,
        exam_title,
        exam_code_label,
        academic_year,
        semester_number,
        total_score,
        duration_minutes,
        origin_type,
        ai_generation_reference,
        assembly_status,
        metadata,
        created_by
    )
    values (
        new_exam_id,
        1,
        target_blueprint_version_id,
        trim(target_exam_title),
        trim(target_exam_code),
        blueprint_academic_year,
        blueprint_semester_number,
        blueprint_total_score,
        blueprint_duration_minutes,
        'AI',
        trim(target_idempotency_key),
        'AI_PROPOSED',
        jsonb_build_object(
            'generation_idempotency_key',
            trim(target_idempotency_key)
        ),
        current_user_id
    )
    returning exam_version_id
    into new_exam_version_id;

    update public.assessment_exams
    set
        current_version_number = 1,
        updated_at = now()
    where
        exam_id = new_exam_id;

    return jsonb_build_object(
        'exam_id',
        new_exam_id,
        'exam_version_id',
        new_exam_version_id,
        'blueprint_version_id',
        target_blueprint_version_id,
        'reused',
        false
    );
end;
$$;

revoke all on function
public.create_assessment_exam_draft(
    uuid,
    text,
    text,
    text
)
from public;

grant execute on function
public.create_assessment_exam_draft(
    uuid,
    text,
    text,
    text
)
to authenticated;


create or replace function
public.assemble_assessment_exam_from_blueprint(
    target_exam_version_id uuid,
    target_selection_seed text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid;
    current_owner_user_id uuid;
    current_blueprint_version_id uuid;
    current_assembly_status text;
    current_subject_code text;
    current_education_level text;
    current_grade_level integer;

    blueprint_lifecycle_status text;
    blueprint_review_status text;
    blueprint_locked_at timestamptz;

    blueprint_cell record;
    inserted_count integer;
    display_number_value integer := 0;
    total_inserted_count integer := 0;
begin
    current_user_id := (select auth.uid());

    if current_user_id is null then
        raise exception
            'Authentication is required to assemble an exam.';
    end if;

    if char_length(
        trim(coalesce(target_selection_seed, ''))
    ) = 0 then
        raise exception
            'Selection seed is required.';
    end if;

    select
        exam.owner_user_id,
        exam_version.blueprint_version_id,
        exam_version.assembly_status,
        exam.subject_code,
        exam.education_level,
        exam.grade_level
    into
        current_owner_user_id,
        current_blueprint_version_id,
        current_assembly_status,
        current_subject_code,
        current_education_level,
        current_grade_level
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

    if current_owner_user_id is distinct from current_user_id then
        raise exception
            'Only the exam owner may assemble it.';
    end if;

    if current_assembly_status not in (
        'DRAFT',
        'AI_PROPOSED',
        'REVISION_REQUIRED',
        'ASSEMBLED'
    ) then
        raise exception
            'Assessment exam version is not available for assembly.';
    end if;

    if not public.assessment_exam_version_is_editable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam version is not editable.';
    end if;

    select
        blueprint.lifecycle_status,
        blueprint_version.review_status,
        blueprint_version.locked_at
    into
        blueprint_lifecycle_status,
        blueprint_review_status,
        blueprint_locked_at
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            current_blueprint_version_id;

    if (
        blueprint_lifecycle_status is distinct from 'ACTIVE'
        or blueprint_review_status is distinct from 'APPROVED'
        or blueprint_locked_at is null
    ) then
        raise exception
            'Exam blueprint is not active, approved, and locked.';
    end if;

    delete from public.assessment_exam_questions
    where
        exam_version_id = target_exam_version_id;

    for blueprint_cell in
        select
            cell.blueprint_cell_id,
            cell.topic_code,
            cell.question_type_code,
            cell.cognitive_level_code,
            cell.question_count,
            cell.target_score,
            cell.sequence_number
        from public.assessment_blueprint_cells cell
        where
            cell.blueprint_version_id =
                current_blueprint_version_id
        order by
            cell.sequence_number,
            cell.blueprint_cell_id
    loop
        insert into public.assessment_exam_questions (
            exam_version_id,
            blueprint_cell_id,
            question_version_id,
            display_number,
            assigned_score,
            selection_origin,
            ai_selection_reference,
            selection_note,
            metadata
        )
        select
            target_exam_version_id,
            blueprint_cell.blueprint_cell_id,
            candidate.question_version_id,
            display_number_value
                + candidate.selection_number,
            candidate.default_score,
            'AI_SUGGESTED',
            trim(target_selection_seed),
            'Deterministic blueprint assembly.',
            jsonb_build_object(
                'selection_seed',
                trim(target_selection_seed)
            )
        from (
            select
                question_version.question_version_id,
                question_version.default_score,
                row_number() over (
                    order by
                        md5(
                            question_version.question_version_id::text
                            ||
                            trim(target_selection_seed)
                            ||
                            blueprint_cell.blueprint_cell_id::text
                        ),
                        question_version.question_version_id
                )::integer as selection_number
            from public.assessment_question_versions question_version
            join public.assessment_question_items question
                on question.question_id =
                    question_version.question_id
            where
                question.lifecycle_status = 'ACTIVE'
                and question.subject_code =
                    current_subject_code
                and question.education_level =
                    current_education_level
                and question.grade_level =
                    current_grade_level
                and question.current_version_number =
                    question_version.version_number
                and question_version.review_status = 'APPROVED'
                and question_version.locked_at is not null
                and question_version.question_type_code =
                    blueprint_cell.question_type_code
                and question_version.cognitive_level_code =
                    blueprint_cell.cognitive_level_code
                and question_version.default_score =
                    (
                        blueprint_cell.target_score
                        /
                        blueprint_cell.question_count
                    )
                and exists (
                    select 1
                    from public.assessment_question_requirement_links
                        question_requirement
                    join public.assessment_learning_requirements
                        requirement
                        on requirement.requirement_code =
                            question_requirement.requirement_code
                    where
                        question_requirement.question_version_id =
                            question_version.question_version_id
                        and question_requirement.link_role = 'PRIMARY'
                        and requirement.topic_code =
                            blueprint_cell.topic_code
                )
                and not exists (
                    select 1
                    from public.assessment_exam_questions
                        existing_question
                    where
                        existing_question.exam_version_id =
                            target_exam_version_id
                        and existing_question.question_version_id =
                            question_version.question_version_id
                )
            order by
                md5(
                    question_version.question_version_id::text
                    ||
                    trim(target_selection_seed)
                    ||
                    blueprint_cell.blueprint_cell_id::text
                ),
                question_version.question_version_id
            limit blueprint_cell.question_count
        ) candidate;

        get diagnostics inserted_count = row_count;

        if inserted_count <> blueprint_cell.question_count then
            raise exception
                'Insufficient approved questions for blueprint cell %.',
                blueprint_cell.blueprint_cell_id;
        end if;

        display_number_value :=
            display_number_value + inserted_count;

        total_inserted_count :=
            total_inserted_count + inserted_count;
    end loop;

    if total_inserted_count = 0 then
        raise exception
            'Assessment blueprint contains no assemblable cells.';
    end if;

    perform public.mark_assessment_exam_assembled(
        target_exam_version_id
    );

    return jsonb_build_object(
        'exam_version_id',
        target_exam_version_id,
        'blueprint_version_id',
        current_blueprint_version_id,
        'question_count',
        total_inserted_count,
        'assembly_status',
        'ASSEMBLED',
        'selection_seed',
        trim(target_selection_seed)
    );
end;
$$;

revoke all on function
public.assemble_assessment_exam_from_blueprint(
    uuid,
    text
)
from public;

grant execute on function
public.assemble_assessment_exam_from_blueprint(
    uuid,
    text
)
to authenticated;


create or replace function
public.assessment_exam_validation_report(
    target_exam_version_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
    current_user_id uuid;
    current_owner_user_id uuid;
    current_blueprint_version_id uuid;
    question_count_value integer;
    expected_question_count integer;
    assigned_score_value numeric(10,4);
    expected_score_value numeric(10,4);
    matched_cell_count integer;
    expected_cell_count integer;
    assembly_matches boolean;
begin
    current_user_id := (select auth.uid());

    select
        exam.owner_user_id,
        exam_version.blueprint_version_id,
        exam_version.total_score
    into
        current_owner_user_id,
        current_blueprint_version_id,
        expected_score_value
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            target_exam_version_id;

    if current_owner_user_id is null then
        raise exception
            'Assessment exam version does not exist.';
    end if;

    if (
        current_owner_user_id is distinct from current_user_id
        and not public.current_user_is_portal_admin()
    ) then
        raise exception
            'Assessment exam validation report is not visible.';
    end if;

    select
        count(*)::integer,
        coalesce(sum(cell.question_count), 0)::integer
    into
        expected_cell_count,
        expected_question_count
    from public.assessment_blueprint_cells cell
    where
        cell.blueprint_version_id =
            current_blueprint_version_id;

    select
        count(*)::integer,
        coalesce(sum(exam_question.assigned_score), 0)
    into
        question_count_value,
        assigned_score_value
    from public.assessment_exam_questions exam_question
    where
        exam_question.exam_version_id =
            target_exam_version_id;

    select
        count(*)::integer
    into
        matched_cell_count
    from public.assessment_blueprint_cells cell
    where
        cell.blueprint_version_id =
            current_blueprint_version_id
        and public.assessment_exam_cell_allocation_matches(
            target_exam_version_id,
            cell.blueprint_cell_id
        );

    assembly_matches :=
        public.assessment_exam_assembly_matches_blueprint(
            target_exam_version_id
        );

    return jsonb_build_object(
        'is_valid',
        assembly_matches,
        'violations',
        case
            when assembly_matches
                then '[]'::jsonb
            else jsonb_build_array(
                'Assessment exam does not completely match its blueprint.'
            )
        end,
        'metrics',
        jsonb_build_object(
            'question_count',
            question_count_value,
            'expected_question_count',
            expected_question_count,
            'assigned_score',
            assigned_score_value,
            'expected_score',
            expected_score_value,
            'matched_cell_count',
            matched_cell_count,
            'expected_cell_count',
            expected_cell_count
        )
    );
end;
$$;

revoke all on function
public.assessment_exam_validation_report(uuid)
from public;

grant execute on function
public.assessment_exam_validation_report(uuid)
to authenticated;

comment on function
public.create_assessment_exam_draft(
    uuid,
    text,
    text,
    text
) is
'Creates or reuses one idempotent exam draft from an active approved blueprint.';

comment on function
public.assemble_assessment_exam_from_blueprint(
    uuid,
    text
) is
'Deterministically assembles an editable exam using active approved current question versions.';

comment on function
public.assessment_exam_validation_report(uuid) is
'Returns a structured blueprint-validation report for one visible exam version.';

commit;
