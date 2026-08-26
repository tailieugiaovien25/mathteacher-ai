-- English canonical YCCD Grades 6-9 projection into assessment schema.
-- Generated from committed canonical JSON.
-- Idempotent: insert-if-absent, assert semantic equality on existing keys.
-- No blind canonical update.


do $$
begin
    if not exists (
        select 1
        from public.subjects
        where subject_id = 'subject-foreign-language-1'
    ) then
        raise exception 'ENGLISH_SUBJECT_IDENTITY_MISSING';
    end if;

    if not exists (
        select 1
        from public.education_programs
        where program_id = 'program-vn-gdpt-2018'
    ) then
        raise exception 'GDPT2018_PROGRAM_IDENTITY_MISSING';
    end if;
end
$$;


do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_programs
        where program_code = 'GDPT2018-ENGLISH-THCS'
          and (
            subject_code is distinct from 'FOREIGN_LANGUAGE_1'
            or education_level is distinct from 'THCS'
            or grade_min is distinct from 6
            or grade_max is distinct from 9
            or version_label is distinct from '2018'
          )
    ) then
        raise exception 'ENGLISH_ASSESSMENT_PROGRAM_CONFLICT: GDPT2018-ENGLISH-THCS';
    end if;
end
$$;

insert into public.assessment_curriculum_programs (
    program_code,
    program_name,
    subject_code,
    education_level,
    grade_min,
    grade_max,
    version_label,
    effective_from,
    effective_to,
    status,
    metadata
)
values (
    'GDPT2018-ENGLISH-THCS',
    'Chương trình giáo dục phổ thông môn Tiếng Anh - THCS',
    'FOREIGN_LANGUAGE_1',
    'THCS',
    6,
    9,
    '2018',
    '2018-12-26'::date,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical":true,"canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","projection_type":"SUBJECT_SPECIFIC_ASSESSMENT","regulation_id":"32/2018/TT-BGDĐT"}'::jsonb
)
on conflict (program_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is not null
            or grade_level is distinct from 6
            or domain_code is distinct from 'GRADE'
            or topic_name is distinct from 'English Grade 6'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-001';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-001',
    'GDPT2018-ENGLISH-THCS',
    null,
    6,
    'GRADE',
    'English Grade 6',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"ENG-G6","canonical_node_type":"GRADE","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-001'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Language skills'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-002';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-001',
    6,
    'LANGUAGE_SKILL',
    'Language skills',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_SKILL","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-001'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Language knowledge'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-007';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-001',
    6,
    'LANGUAGE_KNOWLEDGE',
    'Language knowledge',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_KNOWLEDGE","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-002'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Listening'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-003';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-002',
    6,
    'LANGUAGE_SKILL',
    'Listening',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LISTENING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-007'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Pronunciation'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-008';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-007',
    6,
    'LANGUAGE_KNOWLEDGE',
    'Pronunciation',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"PRONUNCIATION","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-002'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Speaking'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-004';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-002',
    6,
    'LANGUAGE_SKILL',
    'Speaking',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"SPEAKING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-007'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Vocabulary'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-009';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-007',
    6,
    'LANGUAGE_KNOWLEDGE',
    'Vocabulary',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"VOCABULARY","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-002'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Reading'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-005';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-002',
    6,
    'LANGUAGE_SKILL',
    'Reading',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"READING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-007'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Grammar'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-010';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-007',
    6,
    'LANGUAGE_KNOWLEDGE',
    'Grammar',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"GRAMMAR","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G6-006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G6-002'
            or grade_level is distinct from 6
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Writing'
            or sequence_number is distinct from 4
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G6-006';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G6-006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-002',
    6,
    'LANGUAGE_SKILL',
    'Writing',
    4,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"WRITING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is not null
            or grade_level is distinct from 7
            or domain_code is distinct from 'GRADE'
            or topic_name is distinct from 'English Grade 7'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-001';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-001',
    'GDPT2018-ENGLISH-THCS',
    null,
    7,
    'GRADE',
    'English Grade 7',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"ENG-G7","canonical_node_type":"GRADE","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-001'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Language skills'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-002';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-001',
    7,
    'LANGUAGE_SKILL',
    'Language skills',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_SKILL","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-001'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Language knowledge'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-007';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-001',
    7,
    'LANGUAGE_KNOWLEDGE',
    'Language knowledge',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_KNOWLEDGE","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-002'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Listening'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-003';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-002',
    7,
    'LANGUAGE_SKILL',
    'Listening',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LISTENING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-007'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Pronunciation'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-008';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-007',
    7,
    'LANGUAGE_KNOWLEDGE',
    'Pronunciation',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"PRONUNCIATION","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-002'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Speaking'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-004';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-002',
    7,
    'LANGUAGE_SKILL',
    'Speaking',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"SPEAKING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-007'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Vocabulary'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-009';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-007',
    7,
    'LANGUAGE_KNOWLEDGE',
    'Vocabulary',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"VOCABULARY","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-002'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Reading'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-005';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-002',
    7,
    'LANGUAGE_SKILL',
    'Reading',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"READING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-007'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Grammar'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-010';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-007',
    7,
    'LANGUAGE_KNOWLEDGE',
    'Grammar',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"GRAMMAR","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G7-006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G7-002'
            or grade_level is distinct from 7
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Writing'
            or sequence_number is distinct from 4
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G7-006';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G7-006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-002',
    7,
    'LANGUAGE_SKILL',
    'Writing',
    4,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"WRITING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is not null
            or grade_level is distinct from 8
            or domain_code is distinct from 'GRADE'
            or topic_name is distinct from 'English Grade 8'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-001';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-001',
    'GDPT2018-ENGLISH-THCS',
    null,
    8,
    'GRADE',
    'English Grade 8',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"ENG-G8","canonical_node_type":"GRADE","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-001'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Language skills'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-002';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-001',
    8,
    'LANGUAGE_SKILL',
    'Language skills',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_SKILL","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-001'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Language knowledge'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-007';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-001',
    8,
    'LANGUAGE_KNOWLEDGE',
    'Language knowledge',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_KNOWLEDGE","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-002'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Listening'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-003';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-002',
    8,
    'LANGUAGE_SKILL',
    'Listening',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LISTENING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-007'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Pronunciation'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-008';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-007',
    8,
    'LANGUAGE_KNOWLEDGE',
    'Pronunciation',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"PRONUNCIATION","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-002'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Speaking'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-004';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-002',
    8,
    'LANGUAGE_SKILL',
    'Speaking',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"SPEAKING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-007'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Vocabulary'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-009';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-007',
    8,
    'LANGUAGE_KNOWLEDGE',
    'Vocabulary',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"VOCABULARY","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-002'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Reading'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-005';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-002',
    8,
    'LANGUAGE_SKILL',
    'Reading',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"READING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-007'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Grammar'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-010';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-007',
    8,
    'LANGUAGE_KNOWLEDGE',
    'Grammar',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"GRAMMAR","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G8-006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G8-002'
            or grade_level is distinct from 8
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Writing'
            or sequence_number is distinct from 4
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G8-006';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G8-006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-002',
    8,
    'LANGUAGE_SKILL',
    'Writing',
    4,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"WRITING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is not null
            or grade_level is distinct from 9
            or domain_code is distinct from 'GRADE'
            or topic_name is distinct from 'English Grade 9'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-001';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-001',
    'GDPT2018-ENGLISH-THCS',
    null,
    9,
    'GRADE',
    'English Grade 9',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"ENG-G9","canonical_node_type":"GRADE","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-001'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Language skills'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-002';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-001',
    9,
    'LANGUAGE_SKILL',
    'Language skills',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_SKILL","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-001'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Language knowledge'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-007';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-001',
    9,
    'LANGUAGE_KNOWLEDGE',
    'Language knowledge',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LANGUAGE_KNOWLEDGE","canonical_node_type":"DOMAIN","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-002'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Listening'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-003';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-002',
    9,
    'LANGUAGE_SKILL',
    'Listening',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"LISTENING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-007'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Pronunciation'
            or sequence_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-008';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-007',
    9,
    'LANGUAGE_KNOWLEDGE',
    'Pronunciation',
    1,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"PRONUNCIATION","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-002'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Speaking'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-004';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-002',
    9,
    'LANGUAGE_SKILL',
    'Speaking',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"SPEAKING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-007'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Vocabulary'
            or sequence_number is distinct from 2
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-009';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-007',
    9,
    'LANGUAGE_KNOWLEDGE',
    'Vocabulary',
    2,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"VOCABULARY","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-002'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Reading'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-005';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-002',
    9,
    'LANGUAGE_SKILL',
    'Reading',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"READING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-007'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_KNOWLEDGE'
            or topic_name is distinct from 'Grammar'
            or sequence_number is distinct from 3
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-010';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-007',
    9,
    'LANGUAGE_KNOWLEDGE',
    'Grammar',
    3,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"GRAMMAR","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_curriculum_topics
        where topic_code = 'CURR-NODE-ENG-G9-006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or parent_topic_code is distinct from 'CURR-NODE-ENG-G9-002'
            or grade_level is distinct from 9
            or domain_code is distinct from 'LANGUAGE_SKILL'
            or topic_name is distinct from 'Writing'
            or sequence_number is distinct from 4
          )
    ) then
        raise exception 'ENGLISH_TOPIC_CONFLICT: CURR-NODE-ENG-G9-006';
    end if;
end
$$;

insert into public.assessment_curriculum_topics (
    topic_code,
    program_code,
    parent_topic_code,
    grade_level,
    domain_code,
    topic_name,
    sequence_number,
    status,
    metadata
)
values (
    'CURR-NODE-ENG-G9-006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-002',
    9,
    'LANGUAGE_SKILL',
    'Writing',
    4,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_code":"WRITING","canonical_node_type":"CATEGORY","canonical_status":"ACTIVE","canonical_subject_id":"subject-foreign-language-1"}'::jsonb
)
on conflict (topic_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-003'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ngắn và đơn giản khác nhau.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/LISTENING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0001';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0001',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-003',
    6,
    'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ngắn và đơn giản khác nhau.',
    'GRADE_6/LANGUAGE_SKILL/LISTENING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/LISTENING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-003'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Nghe hiểu các chỉ dẫn ngắn, đơn giản sử dụng trong các hoạt động học tập trong lớp học.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/LISTENING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0002';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-003',
    6,
    'Nghe hiểu các chỉ dẫn ngắn, đơn giản sử dụng trong các hoạt động học tập trong lớp học.',
    'GRADE_6/LANGUAGE_SKILL/LISTENING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/LISTENING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-003'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Nghe hiểu nội dung chính, nội dung tương đối chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 80 - 100 từ về các chủ đề trong Chương trình; nghe hiểu được nội dung chính các câu chuyện đơn giản về các chủ đề quen thuộc.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/LISTENING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0003';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-003',
    6,
    'Nghe hiểu nội dung chính, nội dung tương đối chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 80 - 100 từ về các chủ đề trong Chương trình; nghe hiểu được nội dung chính các câu chuyện đơn giản về các chủ đề quen thuộc.',
    'GRADE_6/LANGUAGE_SKILL/LISTENING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/LISTENING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-004'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ngắn và đơn giản khác nhau.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/SPEAKING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0004';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-004',
    6,
    'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ngắn và đơn giản khác nhau.',
    'GRADE_6/LANGUAGE_SKILL/SPEAKING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/SPEAKING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-004'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Nói các chỉ dẫn ngắn, đơn giản sử dụng trong lớp học; những câu đơn giản, liền ý về các chủ đề quen thuộc (có gợi ý).'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/SPEAKING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0005';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-004',
    6,
    'Nói các chỉ dẫn ngắn, đơn giản sử dụng trong lớp học; những câu đơn giản, liền ý về các chủ đề quen thuộc (có gợi ý).',
    'GRADE_6/LANGUAGE_SKILL/SPEAKING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/SPEAKING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-004'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Hỏi và trả lời ngắn gọn về các chủ đề trong Chương trình như nhà trường, bạn bè, lễ hội, danh lam thắng cảnh, …'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/SPEAKING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0006';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-004',
    6,
    'Hỏi và trả lời ngắn gọn về các chủ đề trong Chương trình như nhà trường, bạn bè, lễ hội, danh lam thắng cảnh, …',
    'GRADE_6/LANGUAGE_SKILL/SPEAKING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/SPEAKING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-004'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Trình bày có chuẩn bị trước và có gợi ý các dự án về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/SPEAKING/4'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0007';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-004',
    6,
    'Trình bày có chuẩn bị trước và có gợi ý các dự án về các chủ đề trong Chương trình.',
    'GRADE_6/LANGUAGE_SKILL/SPEAKING/4',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/SPEAKING/4","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-005'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Đọc hiểu nội dung chính, nội dung tương đối chi tiết các đoạn hội thoại, độc thoại đơn giản về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/READING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0008';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-005',
    6,
    'Đọc hiểu nội dung chính, nội dung tương đối chi tiết các đoạn hội thoại, độc thoại đơn giản về các chủ đề trong Chương trình.',
    'GRADE_6/LANGUAGE_SKILL/READING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/READING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-005'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Đọc hiểu nội dung chính các thư cá nhân, thông báo, đoạn văn ngắn, đơn giản khoảng 100 - 120 từ thuộc phạm vi các chủ đề quen thuộc (có thể có một số từ, cấu trúc mới).'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/READING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0009';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-005',
    6,
    'Đọc hiểu nội dung chính các thư cá nhân, thông báo, đoạn văn ngắn, đơn giản khoảng 100 - 120 từ thuộc phạm vi các chủ đề quen thuộc (có thể có một số từ, cấu trúc mới).',
    'GRADE_6/LANGUAGE_SKILL/READING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/READING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-006'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Viết (có hướng dẫn) một đoạn văn ngắn, đơn giản khoảng 40 - 60 từ về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/WRITING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0010';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-006',
    6,
    'Viết (có hướng dẫn) một đoạn văn ngắn, đơn giản khoảng 40 - 60 từ về các chủ đề trong Chương trình.',
    'GRADE_6/LANGUAGE_SKILL/WRITING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/WRITING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-06-0011'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G6-006'
            or grade_level is distinct from 6
            or requirement_text is distinct from 'Viết thư, bưu thiếp, tin nhắn hoặc ghi chép cá nhân ngắn, đơn giản liên quan đến nhu cầu giao tiếp hằng ngày trong phạm vi các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_6/LANGUAGE_SKILL/WRITING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-06-0011';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-06-0011',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G6-006',
    6,
    'Viết thư, bưu thiếp, tin nhắn hoặc ghi chép cá nhân ngắn, đơn giản liên quan đến nhu cầu giao tiếp hằng ngày trong phạm vi các chủ đề trong Chương trình.',
    'GRADE_6/LANGUAGE_SKILL/WRITING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_6/LANGUAGE_SKILL/WRITING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-003'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu đơn giản.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/LISTENING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0001';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0001',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-003',
    7,
    'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu đơn giản.',
    'GRADE_7/LANGUAGE_SKILL/LISTENING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/LISTENING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-003'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Nghe hiểu các chỉ dẫn ngắn, đơn giản sử dụng trong các hoạt động học tập trong và ngoài lớp học.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/LISTENING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0002';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-003',
    7,
    'Nghe hiểu các chỉ dẫn ngắn, đơn giản sử dụng trong các hoạt động học tập trong và ngoài lớp học.',
    'GRADE_7/LANGUAGE_SKILL/LISTENING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/LISTENING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-003'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 120 - 140 từ về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/LISTENING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0003';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-003',
    7,
    'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 120 - 140 từ về các chủ đề trong Chương trình.',
    'GRADE_7/LANGUAGE_SKILL/LISTENING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/LISTENING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-004'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu đơn giản khác nhau.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/SPEAKING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0004';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-004',
    7,
    'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu đơn giản khác nhau.',
    'GRADE_7/LANGUAGE_SKILL/SPEAKING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/SPEAKING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-004'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Nói các chỉ dẫn ngắn sử dụng trong các hoạt động trong và ngoài lớp học.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/SPEAKING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0005';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-004',
    7,
    'Nói các chỉ dẫn ngắn sử dụng trong các hoạt động trong và ngoài lớp học.',
    'GRADE_7/LANGUAGE_SKILL/SPEAKING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/SPEAKING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-004'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Trao đổi các thông tin cơ bản về các chủ đề quen thuộc.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/SPEAKING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0006';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-004',
    7,
    'Trao đổi các thông tin cơ bản về các chủ đề quen thuộc.',
    'GRADE_7/LANGUAGE_SKILL/SPEAKING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/SPEAKING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-004'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Trình bày có chuẩn bị trước và có gợi ý các dự án về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/SPEAKING/4'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0007';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-004',
    7,
    'Trình bày có chuẩn bị trước và có gợi ý các dự án về các chủ đề trong Chương trình.',
    'GRADE_7/LANGUAGE_SKILL/SPEAKING/4',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/SPEAKING/4","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-005'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Đọc hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 120 - 150 từ về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/READING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0008';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-005',
    7,
    'Đọc hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 120 - 150 từ về các chủ đề trong Chương trình.',
    'GRADE_7/LANGUAGE_SKILL/READING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/READING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-005'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Đọc hiểu nội dung chính các mẩu tin, thực đơn, quảng cáo… ngắn, đơn giản thuộc phạm vi chủ đề quen thuộc (có thể có một số từ, cấu trúc mới).'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/READING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0009';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-005',
    7,
    'Đọc hiểu nội dung chính các mẩu tin, thực đơn, quảng cáo… ngắn, đơn giản thuộc phạm vi chủ đề quen thuộc (có thể có một số từ, cấu trúc mới).',
    'GRADE_7/LANGUAGE_SKILL/READING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/READING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-006'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Viết một đoạn văn ngắn, đơn giản, có gợi ý khoảng 60 - 80 từ để mô tả các sự kiện, hoạt động cá nhân liên quan đến các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/WRITING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0010';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-006',
    7,
    'Viết một đoạn văn ngắn, đơn giản, có gợi ý khoảng 60 - 80 từ để mô tả các sự kiện, hoạt động cá nhân liên quan đến các chủ đề trong Chương trình.',
    'GRADE_7/LANGUAGE_SKILL/WRITING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/WRITING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-07-0011'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G7-006'
            or grade_level is distinct from 7
            or requirement_text is distinct from 'Viết thư, bưu thiếp, tin nhắn hoặc ghi chép cá nhân ngắn, đơn giản liên quan đến nhu cầu giao tiếp hằng ngày trong phạm vi các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_7/LANGUAGE_SKILL/WRITING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-07-0011';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-07-0011',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G7-006',
    7,
    'Viết thư, bưu thiếp, tin nhắn hoặc ghi chép cá nhân ngắn, đơn giản liên quan đến nhu cầu giao tiếp hằng ngày trong phạm vi các chủ đề trong Chương trình.',
    'GRADE_7/LANGUAGE_SKILL/WRITING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_7/LANGUAGE_SKILL/WRITING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-003'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ghép cơ bản.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/LISTENING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0001';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0001',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-003',
    8,
    'Nghe và nhận biết âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ghép cơ bản.',
    'GRADE_8/LANGUAGE_SKILL/LISTENING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/LISTENING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-003'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 140 - 160 từ về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/LISTENING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0002';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-003',
    8,
    'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 140 - 160 từ về các chủ đề trong Chương trình.',
    'GRADE_8/LANGUAGE_SKILL/LISTENING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/LISTENING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-003'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Nghe hiểu nội dung chính các thông báo đơn giản, được nói rõ ràng liên quan đến các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/LISTENING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0003';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-003',
    8,
    'Nghe hiểu nội dung chính các thông báo đơn giản, được nói rõ ràng liên quan đến các chủ đề trong Chương trình.',
    'GRADE_8/LANGUAGE_SKILL/LISTENING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/LISTENING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-004'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ghép cơ bản.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/SPEAKING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0004';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-004',
    8,
    'Phát âm các âm, trọng âm, ngữ điệu và nhịp điệu trong các câu ghép cơ bản.',
    'GRADE_8/LANGUAGE_SKILL/SPEAKING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/SPEAKING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-004'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Nói các chỉ dẫn đơn giản sử dụng trong giao tiếp hằng ngày liên quan đến các chủ điểm đã học.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/SPEAKING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0005';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-004',
    8,
    'Nói các chỉ dẫn đơn giản sử dụng trong giao tiếp hằng ngày liên quan đến các chủ điểm đã học.',
    'GRADE_8/LANGUAGE_SKILL/SPEAKING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/SPEAKING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-004'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Tham gia các hội thoại ngắn, đơn giản về các chủ điểm quen thuộc.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/SPEAKING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0006';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-004',
    8,
    'Tham gia các hội thoại ngắn, đơn giản về các chủ điểm quen thuộc.',
    'GRADE_8/LANGUAGE_SKILL/SPEAKING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/SPEAKING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-004'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Trình bày ngắn gọn, có chuẩn bị trước các dự án về các chủ điểm quen thuộc.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/SPEAKING/4'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0007';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-004',
    8,
    'Trình bày ngắn gọn, có chuẩn bị trước các dự án về các chủ điểm quen thuộc.',
    'GRADE_8/LANGUAGE_SKILL/SPEAKING/4',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/SPEAKING/4","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-005'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Đọc hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 150 - 180 từ về các chủ đề quen thuộc.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/READING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0008';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-005',
    8,
    'Đọc hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 150 - 180 từ về các chủ đề quen thuộc.',
    'GRADE_8/LANGUAGE_SKILL/READING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/READING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-005'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Đọc hiểu nội dung chính, nội dung chi tiết các chỉ dẫn, thông báo, biển báo... ngắn, đơn giản về các chủ đề quen thuộc trong cuộc sống hằng ngày.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/READING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0009';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-005',
    8,
    'Đọc hiểu nội dung chính, nội dung chi tiết các chỉ dẫn, thông báo, biển báo... ngắn, đơn giản về các chủ đề quen thuộc trong cuộc sống hằng ngày.',
    'GRADE_8/LANGUAGE_SKILL/READING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/READING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-005'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Đọc hiểu và đoán được nghĩa của từ mới dựa vào ngữ cảnh.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/READING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0010';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-005',
    8,
    'Đọc hiểu và đoán được nghĩa của từ mới dựa vào ngữ cảnh.',
    'GRADE_8/LANGUAGE_SKILL/READING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/READING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0011'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-006'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Viết (có hướng dẫn) một đoạn văn ngắn, đơn giản về các chủ đề quen thuộc trong cuộc sống hằng ngày.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/WRITING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0011';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0011',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-006',
    8,
    'Viết (có hướng dẫn) một đoạn văn ngắn, đơn giản về các chủ đề quen thuộc trong cuộc sống hằng ngày.',
    'GRADE_8/LANGUAGE_SKILL/WRITING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/WRITING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-08-0012'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G8-006'
            or grade_level is distinct from 8
            or requirement_text is distinct from 'Viết các hướng dẫn, chỉ dẫn, thông báo, … ngắn, đơn giản khoảng 80 - 100 từ liên quan đến các chủ đề quen thuộc.'
            or source_locator is distinct from 'GRADE_8/LANGUAGE_SKILL/WRITING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-08-0012';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-08-0012',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G8-006',
    8,
    'Viết các hướng dẫn, chỉ dẫn, thông báo, … ngắn, đơn giản khoảng 80 - 100 từ liên quan đến các chủ đề quen thuộc.',
    'GRADE_8/LANGUAGE_SKILL/WRITING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_8/LANGUAGE_SKILL/WRITING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0001'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-003'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Nghe hiểu các cụm từ, chỉ dẫn và cách diễn đạt đơn giản liên quan tới nhu cầu giao tiếp hằng ngày.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/LISTENING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0001';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0001',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-003',
    9,
    'Nghe hiểu các cụm từ, chỉ dẫn và cách diễn đạt đơn giản liên quan tới nhu cầu giao tiếp hằng ngày.',
    'GRADE_9/LANGUAGE_SKILL/LISTENING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/LISTENING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0002'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-003'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 160 - 180 từ về các chủ đề trong Chương trình.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/LISTENING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0002';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0002',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-003',
    9,
    'Nghe hiểu nội dung chính, nội dung chi tiết các đoạn hội thoại, độc thoại đơn giản khoảng 160 - 180 từ về các chủ đề trong Chương trình.',
    'GRADE_9/LANGUAGE_SKILL/LISTENING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/LISTENING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0003'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-003'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Nghe hiểu và xác định được những ý chính trong các giao dịch quen thuộc hằng ngày, các thông báo, bản tin, ... ngắn, rõ ràng và đơn giản.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/LISTENING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0003';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0003',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-003',
    9,
    'Nghe hiểu và xác định được những ý chính trong các giao dịch quen thuộc hằng ngày, các thông báo, bản tin, ... ngắn, rõ ràng và đơn giản.',
    'GRADE_9/LANGUAGE_SKILL/LISTENING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/LISTENING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0004'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-004'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Phát âm rõ ràng, tương đối chính xác âm, trọng âm, ngữ điệu, nhịp điệu các cụm từ và câu.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/SPEAKING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0004';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0004',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-004',
    9,
    'Phát âm rõ ràng, tương đối chính xác âm, trọng âm, ngữ điệu, nhịp điệu các cụm từ và câu.',
    'GRADE_9/LANGUAGE_SKILL/SPEAKING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/SPEAKING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0005'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-004'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Tham gia các hội thoại ngắn, đơn giản về những vấn đề quen thuộc liên quan đến công việc và cuộc sống hằng ngày.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/SPEAKING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0005';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0005',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-004',
    9,
    'Tham gia các hội thoại ngắn, đơn giản về những vấn đề quen thuộc liên quan đến công việc và cuộc sống hằng ngày.',
    'GRADE_9/LANGUAGE_SKILL/SPEAKING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/SPEAKING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0006'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-004'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Trình bày ngắn gọn, có chuẩn bị trước các dự án về các chủ đề quen thuộc; nêu lý do và giải thích ngắn gọn về quan điểm cá nhân.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/SPEAKING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0006';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0006',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-004',
    9,
    'Trình bày ngắn gọn, có chuẩn bị trước các dự án về các chủ đề quen thuộc; nêu lý do và giải thích ngắn gọn về quan điểm cá nhân.',
    'GRADE_9/LANGUAGE_SKILL/SPEAKING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/SPEAKING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0007'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-004'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Trao đổi ý kiến, thông tin về những chủ đề quen thuộc bằng các diễn ngôn đơn giản.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/SPEAKING/4'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0007';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0007',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-004',
    9,
    'Trao đổi ý kiến, thông tin về những chủ đề quen thuộc bằng các diễn ngôn đơn giản.',
    'GRADE_9/LANGUAGE_SKILL/SPEAKING/4',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/SPEAKING/4","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0008'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-005'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Đọc hiểu các văn bản khoảng 180 - 200 từ về các chủ đề quen thuộc và cụ thể, có thể sử dụng những từ thường gặp trong đời sống hằng ngày.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/READING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0008';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0008',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-005',
    9,
    'Đọc hiểu các văn bản khoảng 180 - 200 từ về các chủ đề quen thuộc và cụ thể, có thể sử dụng những từ thường gặp trong đời sống hằng ngày.',
    'GRADE_9/LANGUAGE_SKILL/READING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/READING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0009'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-005'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Đọc hiểu và xác định thông tin cụ thể trong các văn bản liên quan đến các chủ đề về đời sống hằng ngày như quảng cáo, biển báo, thông báo,... các bài báo ngắn mô tả sự kiện.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/READING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0009';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0009',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-005',
    9,
    'Đọc hiểu và xác định thông tin cụ thể trong các văn bản liên quan đến các chủ đề về đời sống hằng ngày như quảng cáo, biển báo, thông báo,... các bài báo ngắn mô tả sự kiện.',
    'GRADE_9/LANGUAGE_SKILL/READING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/READING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0010'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-005'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Đọc hiểu và đoán nghĩa của từ mới dựa vào văn cảnh và suy luận, nhận biết tổ chức của đoạn văn ngắn, đơn giản.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/READING/3'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0010';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0010',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-005',
    9,
    'Đọc hiểu và đoán nghĩa của từ mới dựa vào văn cảnh và suy luận, nhận biết tổ chức của đoạn văn ngắn, đơn giản.',
    'GRADE_9/LANGUAGE_SKILL/READING/3',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/READING/3","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0011'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-006'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Viết (có hướng dẫn) một đoạn văn ngắn khoảng 100 - 120 từ về gia đình; viết thư cá nhân, tin nhắn ngắn, đơn giản liên quan các vấn đề thuộc lĩnh vực quan tâm.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/WRITING/1'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0011';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0011',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-006',
    9,
    'Viết (có hướng dẫn) một đoạn văn ngắn khoảng 100 - 120 từ về gia đình; viết thư cá nhân, tin nhắn ngắn, đơn giản liên quan các vấn đề thuộc lĩnh vực quan tâm.',
    'GRADE_9/LANGUAGE_SKILL/WRITING/1',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/WRITING/1","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
begin
    if exists (
        select 1
        from public.assessment_learning_requirements
        where requirement_code = 'YCCD-ENG-09-0012'
          and (
            program_code is distinct from 'GDPT2018-ENGLISH-THCS'
            or topic_code is distinct from 'CURR-NODE-ENG-G9-006'
            or grade_level is distinct from 9
            or requirement_text is distinct from 'Viết tóm tắt thông tin, viết những đoạn văn theo lối đơn giản, sử dụng cách hành văn và trình tự như trong văn bản gốc.'
            or source_locator is distinct from 'GRADE_9/LANGUAGE_SKILL/WRITING/2'
            or version_number is distinct from 1
          )
    ) then
        raise exception 'ENGLISH_REQUIREMENT_CONFLICT: YCCD-ENG-09-0012';
    end if;
end
$$;

insert into public.assessment_learning_requirements (
    requirement_code,
    program_code,
    topic_code,
    grade_level,
    requirement_text,
    source_locator,
    version_number,
    replaces_requirement_code,
    status,
    metadata
)
values (
    'YCCD-ENG-09-0012',
    'GDPT2018-ENGLISH-THCS',
    'CURR-NODE-ENG-G9-006',
    9,
    'Viết tóm tắt thông tin, viết những đoạn văn theo lối đơn giản, sử dụng cách hành văn và trình tự như trong văn bản gốc.',
    'GRADE_9/LANGUAGE_SKILL/WRITING/2',
    1,
    null,
    'ACTIVE',
    '{"authority_source_id":"SRC-CUR-ENGLISH-2018","canonical_status":"VERIFIED","canonical_subject_id":"subject-foreign-language-1","generic_program_id":"program-vn-gdpt-2018","provenance":{"legal_authority":"Bộ Giáo dục và Đào tạo","regulation_id":"32/2018/TT-BGDĐT","source_document_id":"SRC-CUR-ENGLISH-2018","source_location":"GRADE_9/LANGUAGE_SKILL/WRITING/2","source_version":"2018","verified_copy_id":"sha256:3fda4047158558216149df61610f6a72adc817c46d45c051fa5d704a7baefae7"},"validation":{"identity_integrity":"PASS","provenance_integrity":"PASS","structural_integrity":"PASS","text_integrity":"PASS"}}'::jsonb
)
on conflict (requirement_code) do nothing;

do $$
declare
    program_count integer;
    topic_count integer;
    requirement_count integer;
    orphan_topic_count integer;
    orphan_requirement_count integer;
    verified_metadata_count integer;
    active_requirement_count integer;
begin
    select count(*)
    into program_count
    from public.assessment_curriculum_programs
    where program_code = 'GDPT2018-ENGLISH-THCS';

    select count(*)
    into topic_count
    from public.assessment_curriculum_topics
    where program_code = 'GDPT2018-ENGLISH-THCS';

    select count(*)
    into requirement_count
    from public.assessment_learning_requirements
    where program_code = 'GDPT2018-ENGLISH-THCS';

    select count(*)
    into orphan_topic_count
    from public.assessment_curriculum_topics child
    where child.program_code = 'GDPT2018-ENGLISH-THCS'
      and child.parent_topic_code is not null
      and not exists (
          select 1
          from public.assessment_curriculum_topics parent
          where parent.topic_code = child.parent_topic_code
      );

    select count(*)
    into orphan_requirement_count
    from public.assessment_learning_requirements requirement
    where requirement.program_code = 'GDPT2018-ENGLISH-THCS'
      and not exists (
          select 1
          from public.assessment_curriculum_topics topic
          where topic.topic_code = requirement.topic_code
      );

    select count(*)
    into verified_metadata_count
    from public.assessment_learning_requirements
    where program_code = 'GDPT2018-ENGLISH-THCS'
      and metadata ->> 'canonical_status' = 'VERIFIED';

    select count(*)
    into active_requirement_count
    from public.assessment_learning_requirements
    where program_code = 'GDPT2018-ENGLISH-THCS'
      and status = 'ACTIVE';

    if program_count <> 1 then
        raise exception
            'ENGLISH_PROGRAM_COUNT_INVALID: %',
            program_count;
    end if;

    if topic_count <> 40 then
        raise exception
            'ENGLISH_TOPIC_COUNT_INVALID: %',
            topic_count;
    end if;

    if requirement_count <> 46 then
        raise exception
            'ENGLISH_REQUIREMENT_COUNT_INVALID: %',
            requirement_count;
    end if;

    if orphan_topic_count <> 0 then
        raise exception
            'ENGLISH_ORPHAN_TOPIC_COUNT_INVALID: %',
            orphan_topic_count;
    end if;

    if orphan_requirement_count <> 0 then
        raise exception
            'ENGLISH_ORPHAN_REQUIREMENT_COUNT_INVALID: %',
            orphan_requirement_count;
    end if;

    if verified_metadata_count <> 46 then
        raise exception
            'ENGLISH_VERIFIED_METADATA_COUNT_INVALID: %',
            verified_metadata_count;
    end if;

    if active_requirement_count <> 46 then
        raise exception
            'ENGLISH_ACTIVE_REQUIREMENT_COUNT_INVALID: %',
            active_requirement_count;
    end if;
end
$$;
