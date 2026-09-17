-- MathTeacher-AI
-- Guarded cleanup of three legacy/orphan Mathematics 6 assessment topics.
--
-- Canonical curriculum identity remains:
--   canonical_subject_id = subject-mathematics
--
-- Subject/textbook catalog identity remains:
--   subject_id = subject-math
--
-- This migration intentionally DOES NOT modify either identity.
--
-- Supported entry states:
--
-- PRE_CLEAN:
--   168 math topics
--   exactly 3 legacy rows present
--
-- ALREADY_CLEAN:
--   165 math topics
--   zero legacy rows present
--
-- Both states must preserve:
--   290 learning requirements
--   290 ACTIVE learning requirements
--   165 canonical subject-mathematics topics
--   zero dangling requirement/topic references
--   zero dangling topic-parent references

do $migration$
declare
    v_program_count              bigint;
    v_topic_count                bigint;
    v_requirement_count          bigint;
    v_active_requirement_count   bigint;

    v_legacy_count               bigint;
    v_active_legacy_count        bigint;

    v_requirement_refs           bigint;
    v_blueprint_refs             bigint;
    v_child_refs                 bigint;

    v_canonical_count            bigint;

    v_requirements_without_topic bigint;
    v_topics_without_parent      bigint;

    v_deleted                    bigint := 0;

    v_post_topic_count           bigint;
    v_post_legacy_count          bigint;
    v_post_requirement_count     bigint;
    v_post_active_requirement_count bigint;
    v_post_canonical_count       bigint;
    v_post_requirements_without_topic bigint;
    v_post_topics_without_parent bigint;
begin

    -- --------------------------------------------------------
    -- Exact program identity
    -- --------------------------------------------------------

    select count(*)
      into v_program_count
      from public.assessment_curriculum_programs
     where program_code = 'MOET-GDPT2018-MATH-THCS'
       and subject_code = 'MATH'
       and education_level = 'THCS'
       and grade_min = 6
       and grade_max = 9
       and status = 'ACTIVE';

    if v_program_count <> 1 then
        raise exception
            'R27_PROGRAM_IDENTITY_PRECONDITION_FAILED: %',
            v_program_count;
    end if;

    -- --------------------------------------------------------
    -- Pre-state counts
    -- --------------------------------------------------------

    select count(*)
      into v_topic_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS';

    select
        count(*),
        count(*) filter (where status = 'ACTIVE')
      into
        v_requirement_count,
        v_active_requirement_count
      from public.assessment_learning_requirements
     where program_code = 'MOET-GDPT2018-MATH-THCS';

    select
        count(*),
        count(*) filter (where status = 'ACTIVE')
      into
        v_legacy_count,
        v_active_legacy_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS'
       and topic_code in (
            'M6-HH',
            'M6-SH',
            'M6-TKXS'
       );

    select count(*)
      into v_requirement_refs
      from public.assessment_learning_requirements
     where topic_code in (
            'M6-HH',
            'M6-SH',
            'M6-TKXS'
       );

    select count(*)
      into v_blueprint_refs
      from public.assessment_blueprint_cells
     where topic_code in (
            'M6-HH',
            'M6-SH',
            'M6-TKXS'
       );

    select count(*)
      into v_child_refs
      from public.assessment_curriculum_topics
     where parent_topic_code in (
            'M6-HH',
            'M6-SH',
            'M6-TKXS'
       );

    select count(*)
      into v_canonical_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS'
       and metadata->>'canonical_subject_id'
             = 'subject-mathematics';

    select count(*)
      into v_requirements_without_topic
      from public.assessment_learning_requirements r
     where r.program_code = 'MOET-GDPT2018-MATH-THCS'
       and not exists (
            select 1
              from public.assessment_curriculum_topics t
             where t.topic_code = r.topic_code
       );

    select count(*)
      into v_topics_without_parent
      from public.assessment_curriculum_topics t
     where t.program_code = 'MOET-GDPT2018-MATH-THCS'
       and t.parent_topic_code is not null
       and not exists (
            select 1
              from public.assessment_curriculum_topics p
             where p.topic_code = t.parent_topic_code
       );

    -- --------------------------------------------------------
    -- Global invariant checks
    -- --------------------------------------------------------

    if v_requirement_count <> 290 then
        raise exception
            'R27_REQUIREMENT_COUNT_PRECONDITION_FAILED: %',
            v_requirement_count;
    end if;

    if v_active_requirement_count <> 290 then
        raise exception
            'R27_ACTIVE_REQUIREMENT_COUNT_PRECONDITION_FAILED: %',
            v_active_requirement_count;
    end if;

    if v_canonical_count <> 165 then
        raise exception
            'R27_CANONICAL_TOPIC_COUNT_PRECONDITION_FAILED: %',
            v_canonical_count;
    end if;

    if v_requirement_refs <> 0 then
        raise exception
            'R27_LEGACY_REQUIREMENT_REFERENCE_BLOCK: %',
            v_requirement_refs;
    end if;

    if v_blueprint_refs <> 0 then
        raise exception
            'R27_LEGACY_BLUEPRINT_REFERENCE_BLOCK: %',
            v_blueprint_refs;
    end if;

    if v_child_refs <> 0 then
        raise exception
            'R27_LEGACY_CHILD_REFERENCE_BLOCK: %',
            v_child_refs;
    end if;

    if v_requirements_without_topic <> 0 then
        raise exception
            'R27_PRE_REQUIREMENT_TOPIC_INTEGRITY_FAILED: %',
            v_requirements_without_topic;
    end if;

    if v_topics_without_parent <> 0 then
        raise exception
            'R27_PRE_TOPIC_PARENT_INTEGRITY_FAILED: %',
            v_topics_without_parent;
    end if;

    -- --------------------------------------------------------
    -- Two allowed starting states
    -- --------------------------------------------------------

    if v_legacy_count = 3 then

        if v_topic_count <> 168 then
            raise exception
                'R27_PRE_CLEAN_TOPIC_COUNT_FAILED: %',
                v_topic_count;
        end if;

        if v_active_legacy_count <> 3 then
            raise exception
                'R27_LEGACY_ROWS_NOT_ALL_ACTIVE: %',
                v_active_legacy_count;
        end if;

        delete from public.assessment_curriculum_topics
         where program_code = 'MOET-GDPT2018-MATH-THCS'
           and topic_code in (
                'M6-HH',
                'M6-SH',
                'M6-TKXS'
           );

        get diagnostics v_deleted = row_count;

        if v_deleted <> 3 then
            raise exception
                'R27_DELETE_COUNT_FAILED: %',
                v_deleted;
        end if;

    elsif v_legacy_count = 0 then

        if v_topic_count <> 165 then
            raise exception
                'R27_ALREADY_CLEAN_TOPIC_COUNT_FAILED: %',
                v_topic_count;
        end if;

        -- R26 Test cleanup has already produced the exact
        -- target state. Migration becomes a guarded no-op.
        v_deleted := 0;

    else

        raise exception
            'R27_UNEXPECTED_LEGACY_ROW_COUNT: %',
            v_legacy_count;

    end if;

    -- --------------------------------------------------------
    -- Postconditions
    -- --------------------------------------------------------

    select count(*)
      into v_post_topic_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS';

    select count(*)
      into v_post_legacy_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS'
       and topic_code in (
            'M6-HH',
            'M6-SH',
            'M6-TKXS'
       );

    select
        count(*),
        count(*) filter (where status = 'ACTIVE')
      into
        v_post_requirement_count,
        v_post_active_requirement_count
      from public.assessment_learning_requirements
     where program_code = 'MOET-GDPT2018-MATH-THCS';

    select count(*)
      into v_post_canonical_count
      from public.assessment_curriculum_topics
     where program_code = 'MOET-GDPT2018-MATH-THCS'
       and metadata->>'canonical_subject_id'
             = 'subject-mathematics';

    select count(*)
      into v_post_requirements_without_topic
      from public.assessment_learning_requirements r
     where r.program_code = 'MOET-GDPT2018-MATH-THCS'
       and not exists (
            select 1
              from public.assessment_curriculum_topics t
             where t.topic_code = r.topic_code
       );

    select count(*)
      into v_post_topics_without_parent
      from public.assessment_curriculum_topics t
     where t.program_code = 'MOET-GDPT2018-MATH-THCS'
       and t.parent_topic_code is not null
       and not exists (
            select 1
              from public.assessment_curriculum_topics p
             where p.topic_code = t.parent_topic_code
       );

    if v_post_topic_count <> 165 then
        raise exception
            'R27_POST_TOPIC_COUNT_FAILED: %',
            v_post_topic_count;
    end if;

    if v_post_legacy_count <> 0 then
        raise exception
            'R27_POST_LEGACY_COUNT_FAILED: %',
            v_post_legacy_count;
    end if;

    if v_post_requirement_count <> 290 then
        raise exception
            'R27_POST_REQUIREMENT_COUNT_FAILED: %',
            v_post_requirement_count;
    end if;

    if v_post_active_requirement_count <> 290 then
        raise exception
            'R27_POST_ACTIVE_REQUIREMENT_COUNT_FAILED: %',
            v_post_active_requirement_count;
    end if;

    if v_post_canonical_count <> 165 then
        raise exception
            'R27_POST_CANONICAL_COUNT_FAILED: %',
            v_post_canonical_count;
    end if;

    if v_post_requirements_without_topic <> 0 then
        raise exception
            'R27_POST_REQUIREMENT_TOPIC_INTEGRITY_FAILED: %',
            v_post_requirements_without_topic;
    end if;

    if v_post_topics_without_parent <> 0 then
        raise exception
            'R27_POST_TOPIC_PARENT_INTEGRITY_FAILED: %',
            v_post_topics_without_parent;
    end if;

    raise notice
        'R27_LEGACY_TOPIC_CLEANUP_PASS deleted=% topics=165 requirements=290 canonical=165',
        v_deleted;

end
$migration$;