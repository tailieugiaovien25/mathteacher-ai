begin;

create or replace function
public.create_default_assessment_document_template_draft()
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid;
    target_template_set_id uuid;
    target_template_version_id uuid;
    document_definition record;
begin
    current_user_id := (select auth.uid());

    if current_user_id is null then
        raise exception 'Authentication is required.';
    end if;

    if not (
        select public.current_user_is_portal_admin()
    ) then
        raise exception
            'Only a portal administrator may create the default template.';
    end if;

    select template_set.template_set_id
    into target_template_set_id
    from public.assessment_document_template_sets template_set
    where template_set.template_code =
        'MATHTEACHER_DEFAULT_FLEXIBLE'
    for update;

    if target_template_set_id is null then
        insert into public.assessment_document_template_sets (
            template_code,
            template_name,
            authority_scope,
            authority_reference,
            owner_user_id,
            lifecycle_status,
            current_version_number,
            description,
            metadata,
            created_by
        )
        values (
            'MATHTEACHER_DEFAULT_FLEXIBLE',
            'Bộ mẫu đánh giá linh hoạt mặc định',
            'SCHOOL',
            'MATHTEACHER_DEFAULT',
            null,
            'DRAFT',
            null,
            'Bộ mẫu trung tính để kiểm thử và làm nền cho mẫu của cơ quan quản lý.',
            jsonb_build_object(
                'bootstrap_code', 'V61',
                'replaceable_without_system_change', true,
                'governance', 'HUMAN_REVIEW_REQUIRED'
            ),
            current_user_id
        )
        returning template_set_id
        into target_template_set_id;
    end if;

    select template_version.template_version_id
    into target_template_version_id
    from public.assessment_document_template_versions template_version
    where
        template_version.template_set_id = target_template_set_id
        and template_version.version_number = 1;

    if target_template_version_id is not null then
        return target_template_version_id;
    end if;

    insert into public.assessment_document_template_versions (
        template_set_id,
        version_number,
        version_label,
        review_status,
        compatibility_schema_version,
        global_layout_schema,
        global_style_schema,
        required_context_schema,
        change_summary,
        created_by
    )
    values (
        target_template_set_id,
        1,
        'Mặc định linh hoạt V1',
        'DRAFT',
        1,
        jsonb_build_object(
            'page_size', 'A4',
            'orientation', 'PORTRAIT',
            'margins_mm', jsonb_build_object(
                'top', 20,
                'right', 15,
                'bottom', 20,
                'left', 20
            )
        ),
        jsonb_build_object(
            'font_family', 'Times New Roman',
            'font_size', 12,
            'heading_size', 14,
            'line_spacing', 1.15,
            'paragraph_space_after_pt', 3
        ),
        jsonb_build_object(
            'canonical_schema_version', 2,
            'required_roots', jsonb_build_array(
                'metadata',
                'matrix',
                'specification',
                'questions',
                'answer_key',
                'scoring_guide'
            )
        ),
        'Khởi tạo bộ mẫu trung tính; cần ADMIN duyệt trước khi kích hoạt.',
        current_user_id
    )
    returning template_version_id
    into target_template_version_id;

    for document_definition in
        select *
        from (
            values
                ('MATRIX', 'matrix', 'Ma trận đề kiểm tra', 1),
                ('SPECIFICATION', 'specification', 'Bản đặc tả đề kiểm tra', 2),
                ('STUDENT_EXAM', 'questions', 'Đề kiểm tra', 3),
                ('ANSWER_KEY', 'answer_key', 'Đáp án', 4),
                ('SCORING_GUIDE', 'scoring_guide', 'Hướng dẫn chấm', 5)
        ) as definition(
            document_type_code,
            binding_path,
            section_title,
            sort_order
        )
    loop
        insert into public.assessment_document_template_definitions (
            template_version_id,
            document_type_code,
            renderer_code,
            supported_formats,
            layout_schema,
            style_schema,
            binding_schema,
            section_schema,
            template_asset_path,
            template_asset_hash,
            sort_order,
            metadata,
            created_by
        )
        values (
            target_template_version_id,
            document_definition.document_type_code,
            'DOCX_JSON_V1',
            array['DOCX', 'JSON']::text[],
            '{}'::jsonb,
            '{}'::jsonb,
            jsonb_build_object(
                'content', document_definition.binding_path
            ),
            jsonb_build_array(
                jsonb_build_object(
                    'section_code', 'main_content',
                    'section_type', 'REPEAT',
                    'title', document_definition.section_title,
                    'title_alignment', 'CENTER',
                    'bindings', jsonb_build_array('content')
                )
            ),
            null,
            null,
            document_definition.sort_order,
            jsonb_build_object(
                'bootstrap_code', 'V61',
                'customizable', true
            ),
            current_user_id
        );
    end loop;

    return target_template_version_id;
end;
$$;

revoke all on function
public.create_default_assessment_document_template_draft()
from public;

grant execute on function
public.create_default_assessment_document_template_draft()
to authenticated;

comment on function
public.create_default_assessment_document_template_draft() is
    'Creates one idempotent DRAFT default template set. Human review and activation remain mandatory.';

commit;
