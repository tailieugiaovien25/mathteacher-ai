-- Edit an owned, unlocked draft atomically. Published and queued versions remain immutable.
create or replace function public.edit_owned_assessment_question_draft(
    target_question_version_id uuid, target_candidate jsonb
) returns void language plpgsql security invoker set search_path = '' as $$
declare
    v public.assessment_question_versions%rowtype;
    answer_row public.assessment_question_answers%rowtype;
    solution_row public.assessment_question_solutions%rowtype;
    entry jsonb;
    idx integer;
    correct_count integer := 0;
    correct_letter text;
    total_score numeric := 0;
    answer_text text;
begin
    if (select auth.uid()) is null then
        raise exception 'Authentication required';
    end if;
    select qv.* into v
    from public.assessment_question_versions qv
    join public.assessment_question_items qi on qi.question_id = qv.question_id
    where qv.question_version_id = target_question_version_id
      and qi.owner_user_id = (select auth.uid())
      and qv.review_status in ('DRAFT','AI_PROPOSED','REVISION_REQUIRED')
      and qv.locked_at is null
    for update of qv;
    if not found then
        raise exception 'Question is not owned or is locked for review';
    end if;
    if jsonb_typeof(target_candidate) <> 'object'
       or length(trim(coalesce(target_candidate->>'prompt_text',''))) = 0
       or length(trim(coalesce(target_candidate->>'answer',''))) = 0
       or length(trim(coalesce(target_candidate->>'solution',''))) = 0 then
        raise exception 'Question, answer and solution are required';
    end if;
    answer_text := trim(target_candidate->>'answer');
    if v.question_type_code = 'MULTIPLE_CHOICE' then
        if jsonb_typeof(target_candidate->'options') <> 'array'
           or jsonb_array_length(target_candidate->'options') <> 4 then
            raise exception 'Exactly four choices are required';
        end if;
        idx := 0;
        for entry in select value from jsonb_array_elements(target_candidate->'options') loop
            if length(trim(coalesce(entry->>'text',''))) = 0
               or jsonb_typeof(entry->'is_correct') <> 'boolean' then
                raise exception 'Each choice requires text and a correctness value';
            end if;
            if (entry->>'is_correct')::boolean then
                correct_count := correct_count + 1;
                correct_letter := substr('ABCD',idx+1,1);
            end if;
            idx := idx + 1;
        end loop;
        if correct_count <> 1 then raise exception 'Exactly one correct choice is required'; end if;
        if upper(answer_text) <> correct_letter then
            raise exception 'Answer letter does not match the correct choice';
        end if;
    elsif v.question_type_code = 'TRUE_FALSE' then
        if jsonb_typeof(target_candidate->'statements') <> 'array'
           or jsonb_array_length(target_candidate->'statements') <> 4 then
            raise exception 'Exactly four true/false statements are required';
        end if;
        for entry in select value from jsonb_array_elements(target_candidate->'statements') loop
            if length(trim(coalesce(entry->>'text',''))) = 0
               or jsonb_typeof(entry->'correct_value') <> 'boolean' then
                raise exception 'Each statement requires text and a truth value';
            end if;
        end loop;
    elsif v.question_type_code = 'ESSAY' then
        if jsonb_typeof(target_candidate->'scoring_steps') <> 'array'
           or jsonb_array_length(target_candidate->'scoring_steps') < 1
           or jsonb_array_length(target_candidate->'scoring_steps') > 12 then
            raise exception 'Essay scoring steps are required';
        end if;
        for entry in select value from jsonb_array_elements(target_candidate->'scoring_steps') loop
            if length(trim(coalesce(entry->>'description',''))) = 0
               or coalesce(entry->>'score','') !~ '^\d+(\.\d+)?$'
               or (entry->>'score')::numeric <= 0 then
                raise exception 'Invalid scoring step';
            end if;
            total_score := total_score + (entry->>'score')::numeric;
        end loop;
        if total_score <> v.default_score then
            raise exception 'Scoring steps must sum to question score';
        end if;
    elsif v.question_type_code <> 'SHORT_RESPONSE' then
        raise exception 'Question type is not supported by this editor';
    end if;

    select * into answer_row from public.assessment_question_answers
    where question_version_id = v.question_version_id for update;
    select * into solution_row from public.assessment_question_solutions
    where question_version_id = v.question_version_id and is_primary = true for update;
    if answer_row.answer_id is null or solution_row.solution_id is null then
        raise exception 'Question answer or primary solution is missing';
    end if;
    update public.assessment_question_versions
       set prompt_text = trim(target_candidate->>'prompt_text')
     where question_version_id = v.question_version_id;
    update public.assessment_question_answers
       set exact_answer_text = answer_text
     where answer_id = answer_row.answer_id;
    update public.assessment_question_solutions
       set solution_text = trim(target_candidate->>'solution')
     where solution_id = solution_row.solution_id;

    if v.question_type_code = 'MULTIPLE_CHOICE' then
        delete from public.assessment_question_options where question_version_id = v.question_version_id;
        for idx in 0..3 loop
            entry := target_candidate->'options'->idx;
            insert into public.assessment_question_options
                (question_version_id,option_code,option_text,sequence_number,is_correct)
            values (v.question_version_id, substr('ABCD',idx+1,1),trim(entry->>'text'),idx+1,
                    (entry->>'is_correct')::boolean);
        end loop;
    elsif v.question_type_code = 'TRUE_FALSE' then
        delete from public.assessment_question_statements where question_version_id = v.question_version_id;
        for idx in 0..3 loop
            entry := target_candidate->'statements'->idx;
            insert into public.assessment_question_statements
                (question_version_id,statement_code,statement_text,sequence_number,correct_value)
            values (v.question_version_id,substr('abcd',idx+1,1),trim(entry->>'text'),idx+1,
                    (entry->>'correct_value')::boolean);
        end loop;
    elsif v.question_type_code = 'ESSAY' then
        delete from public.assessment_question_scoring_steps
         where question_version_id = v.question_version_id;
        for idx in 0..jsonb_array_length(target_candidate->'scoring_steps')-1 loop
            entry := target_candidate->'scoring_steps'->idx;
            insert into public.assessment_question_scoring_steps
                (solution_id,question_version_id,step_code,step_description,sequence_number,step_score)
            values (solution_row.solution_id,v.question_version_id,'STEP-'||(idx+1),
                    trim(entry->>'description'),idx+1,(entry->>'score')::numeric);
        end loop;
    end if;
end;
$$;

revoke all on function public.edit_owned_assessment_question_draft(uuid,jsonb) from public;
grant execute on function public.edit_owned_assessment_question_draft(uuid,jsonb) to authenticated;
