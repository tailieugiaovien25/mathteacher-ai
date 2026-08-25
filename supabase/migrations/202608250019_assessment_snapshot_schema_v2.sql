begin;

alter function
public.build_assessment_exam_snapshot_document(uuid, uuid)
rename to build_assessment_exam_snapshot_document_v1;

create or replace function
public.build_assessment_blueprint_snapshot_document(
    target_blueprint_version_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'sections',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'profile_code',
                                profile_section.profile_code,
                            'section_code',
                                profile_section.section_code,
                            'section_name',
                                profile_section.section_name,
                            'question_type_code',
                                profile_section.question_type_code,
                            'question_type_name',
                                question_type.question_type_name,
                            'answer_mode',
                                question_type.answer_mode,
                            'sequence_number',
                                profile_section.sequence_number,
                            'question_count',
                                profile_section.question_count,
                            'response_count',
                                profile_section.response_count,
                            'section_score',
                                profile_section.section_score,
                            'score_per_response',
                                profile_section.score_per_response,
                            'instructions',
                                profile_section.instructions
                        )
                        order by
                            profile_section.sequence_number
                    )
                    from public.assessment_profile_sections
                        profile_section
                    join public.assessment_question_types
                        question_type
                        on question_type.question_type_code =
                            profile_section.question_type_code
                    where
                        profile_section.profile_code =
                            blueprint_version.profile_code
                ),
                '[]'::jsonb
            ),
        'matrix_cells',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'blueprint_cell_id',
                                blueprint_cell.blueprint_cell_id,
                            'profile_code',
                                blueprint_cell.profile_code,
                            'section_code',
                                blueprint_cell.section_code,
                            'section_name',
                                profile_section.section_name,
                            'topic_code',
                                blueprint_cell.topic_code,
                            'topic_name',
                                topic.topic_name,
                            'domain_code',
                                topic.domain_code,
                            'topic_sequence_number',
                                topic.sequence_number,
                            'cognitive_level_code',
                                blueprint_cell.cognitive_level_code,
                            'cognitive_level_name',
                                cognitive_level.cognitive_level_name,
                            'cognitive_sequence_number',
                                cognitive_level.sequence_number,
                            'question_type_code',
                                blueprint_cell.question_type_code,
                            'question_type_name',
                                question_type.question_type_name,
                            'answer_mode',
                                question_type.answer_mode,
                            'question_count',
                                blueprint_cell.question_count,
                            'response_count',
                                blueprint_cell.response_count,
                            'target_score',
                                blueprint_cell.target_score,
                            'sequence_number',
                                blueprint_cell.sequence_number,
                            'specification_note',
                                blueprint_cell.specification_note,
                            'metadata',
                                blueprint_cell.metadata
                        )
                        order by
                            blueprint_cell.sequence_number,
                            topic.sequence_number,
                            cognitive_level.sequence_number
                    )
                    from public.assessment_blueprint_cells
                        blueprint_cell
                    join public.assessment_profile_sections
                        profile_section
                        on profile_section.profile_code =
                            blueprint_cell.profile_code
                        and profile_section.section_code =
                            blueprint_cell.section_code
                    join public.assessment_curriculum_topics
                        topic
                        on topic.topic_code =
                            blueprint_cell.topic_code
                    join public.assessment_cognitive_levels
                        cognitive_level
                        on cognitive_level.cognitive_level_code =
                            blueprint_cell.cognitive_level_code
                    join public.assessment_question_types
                        question_type
                        on question_type.question_type_code =
                            blueprint_cell.question_type_code
                    where
                        blueprint_cell.blueprint_version_id =
                            blueprint_version.blueprint_version_id
                ),
                '[]'::jsonb
            ),
        'requirement_links',
            coalesce(
                (
                    select jsonb_agg(
                        jsonb_build_object(
                            'requirement_code',
                                requirement_link.requirement_code,
                            'requirement_text',
                                requirement.requirement_text,
                            'requirement_version_number',
                                requirement.version_number,
                            'source_locator',
                                requirement.source_locator,
                            'topic_code',
                                requirement.topic_code,
                            'topic_name',
                                topic.topic_name,
                            'domain_code',
                                topic.domain_code,
                            'coverage_role',
                                requirement_link.coverage_role,
                            'target_question_count',
                                requirement_link.target_question_count,
                            'target_score',
                                requirement_link.target_score,
                            'sequence_number',
                                requirement_link.sequence_number,
                            'specification_note',
                                requirement_link.specification_note,
                            'competencies',
                                coalesce(
                                    (
                                        select jsonb_agg(
                                            jsonb_build_object(
                                                'competency_code',
                                                    competency.competency_code,
                                                'competency_name',
                                                    competency.competency_name,
                                                'description',
                                                    competency.description,
                                                'sequence_number',
                                                    competency.sequence_number
                                            )
                                            order by
                                                competency.sequence_number
                                        )
                                        from
                                            public.assessment_requirement_competency_links
                                                competency_link
                                        join
                                            public.assessment_mathematical_competencies
                                                competency
                                            on competency.competency_code =
                                                competency_link.competency_code
                                        where
                                            competency_link.requirement_code =
                                                requirement.requirement_code
                                    ),
                                    '[]'::jsonb
                                )
                        )
                        order by
                            requirement_link.sequence_number,
                            requirement.requirement_code
                    )
                    from
                        public.assessment_blueprint_requirement_links
                            requirement_link
                    join public.assessment_learning_requirements
                        requirement
                        on requirement.requirement_code =
                            requirement_link.requirement_code
                    join public.assessment_curriculum_topics
                        topic
                        on topic.topic_code =
                            requirement.topic_code
                    where
                        requirement_link.blueprint_version_id =
                            blueprint_version.blueprint_version_id
                ),
                '[]'::jsonb
            )
    )
    from public.assessment_blueprint_versions
        blueprint_version
    where
        blueprint_version.blueprint_version_id =
            target_blueprint_version_id;
$$;

revoke all on function
public.build_assessment_blueprint_snapshot_document(uuid)
from public;

create or replace function
public.build_assessment_exam_snapshot_document(
    target_exam_version_id uuid,
    target_publication_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    with base_snapshot as (
        select
            public.build_assessment_exam_snapshot_document_v1(
                target_exam_version_id,
                target_publication_id
            ) as snapshot_document
    )
    select
        case
            when base_snapshot.snapshot_document is null
                then null
            else
                jsonb_set(
                    jsonb_set(
                        base_snapshot.snapshot_document,
                        '{snapshot_schema_version}',
                        '2'::jsonb,
                        true
                    ),
                    '{blueprint}',
                    coalesce(
                        base_snapshot.snapshot_document
                            -> 'blueprint',
                        '{}'::jsonb
                    )
                    ||
                    coalesce(
                        public.build_assessment_blueprint_snapshot_document(
                            (
                                base_snapshot.snapshot_document
                                    -> 'blueprint'
                                    ->> 'blueprint_version_id'
                            )::uuid
                        ),
                        jsonb_build_object(
                            'sections',
                                '[]'::jsonb,
                            'matrix_cells',
                                '[]'::jsonb,
                            'requirement_links',
                                '[]'::jsonb
                        )
                    ),
                    true
                )
        end
    from base_snapshot;
$$;

revoke all on function
public.build_assessment_exam_snapshot_document(uuid, uuid)
from public;

comment on function
public.build_assessment_exam_snapshot_document_v1(uuid, uuid) is
'Legacy schema-1 snapshot builder retained for reproducibility.';

comment on function
public.build_assessment_blueprint_snapshot_document(uuid) is
'Builds immutable matrix, specification, curriculum, and competency data for assessment snapshot schema 2.';

comment on function
public.build_assessment_exam_snapshot_document(uuid, uuid) is
'Builds assessment snapshot schema 2 with complete blueprint and question data.';

commit;
