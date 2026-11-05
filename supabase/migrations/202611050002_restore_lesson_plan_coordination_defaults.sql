-- Restore safe, versioned defaults for the lesson-plan coordination center.
-- Existing administrator configurations and drafts are never overwritten.

do $$
begin
    if to_regclass('public.lesson_plan_configuration_profiles') is null
       or to_regclass('public.lesson_plan_configuration_versions') is null then
        raise exception 'Apply migrations 202608300012 and 202608300013 before restoring lesson-plan defaults.';
    end if;
end;
$$;

-- Lesson-plan settings and STANDARDIZER_TOOL settings are independent
-- configuration families, even when both apply to the global scope.
drop index if exists public.lesson_plan_configuration_profiles_one_active_scope;
create unique index lesson_plan_configuration_profiles_one_active_scope
on public.lesson_plan_configuration_profiles (
    (case when profile_code like 'STANDARDIZER_TOOL::%' then 'STANDARDIZER_TOOL' else 'LESSON_PLAN' end),
    subject_ref,
    component_ref
)
where lifecycle_status = 'ACTIVE';

do $$
declare
    profile_id_value uuid;
    version_id_value uuid;
begin
    -- Keep all existing active settings. Only create the global recovery
    -- profile when the ordinary lesson-plan family has no global authority.
    if not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where lifecycle_status = 'ACTIVE'
          and subject_ref = '' and component_ref = ''
          and profile_code not like 'STANDARDIZER_TOOL::%'
    ) and not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where profile_code = 'LESSON_PLAN::GLOBAL::RESTORED_DEFAULT'
    ) then
        insert into public.lesson_plan_configuration_profiles (
            profile_code, profile_name, subject_ref, component_ref,
            lifecycle_status
        ) values (
            'LESSON_PLAN::GLOBAL::RESTORED_DEFAULT',
            'Cấu hình giáo án toàn hệ thống (mặc định khôi phục)',
            '', '', 'DRAFT'
        ) returning profile_id into profile_id_value;

        insert into public.lesson_plan_configuration_versions (
            profile_id, version_number, version_status,
            configuration_payload, change_note, published_at
        ) values (
            profile_id_value, 1, 'PUBLISHED',
            '{
              "template_profile": {
                "profile_name": "Kế hoạch bài dạy mặc định",
                "page": {"paper_size":"A4","margin_left_cm":3.0,"margin_right_cm":2.0,"margin_top_cm":2.0,"margin_bottom_cm":2.0},
                "body": {"font":"Times New Roman","size_pt":14,"line_spacing":1.15},
                "title": {"size_pt":14},
                "table": {"size_pt":14,"repeat_header":true,"allow_row_split":true},
                "header_footer": {"remove_existing":true,"page_number":true,"page_number_alignment":"center"},
                "equations": {"mode":"force_times","text_font":"Times New Roman","math_font":"Times New Roman","preserve_omml_structure":true,"preserve_value":true,"rollback_on_integrity_failure":true},
                "layout": {"paper_size":"A4","font_name":"Times New Roman","font_color":"black","body_font_size_pt":14,"line_spacing":1.15,"character_spacing_pt":0,"margin_left_cm":3,"margin_right_cm":2,"margin_top_cm":2,"margin_bottom_cm":2,"page_border_enabled":false,"page_border_style":"single","page_border_width_pt":0.5,"table_border_style":"single","table_border_width_pt":0.5,"table_repeat_header":true,"table_allow_row_split":true,"image_max_width_percent":100}
              },
              "date_policy": {"drafting_before_monday_enabled":true,"drafting_before_monday_days":3,"approval_before_monday_enabled":true,"approval_before_monday_days":1},
              "approval_policy": {"approval_label":"TỔ CM DUYỆT","alignment":"right","approval_offset_days":1},
              "standardization_policy": {"enabled":true,"preserve_formula_value":true,"rollback_on_integrity_failure":true}
            }'::jsonb,
            'Safe default restored by migration; no AI credentials or personal storage identifiers.',
            now()
        ) returning configuration_version_id into version_id_value;

        update public.lesson_plan_configuration_profiles
        set current_version_id = version_id_value,
            lifecycle_status = 'ACTIVE', updated_at = now()
        where profile_id = profile_id_value;
    end if;

    -- The tool manager requires this exact profile code. Do not replace a
    -- pre-existing draft or inactive administrator profile.
    if not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where lifecycle_status = 'ACTIVE' and subject_ref = '' and component_ref = ''
          and profile_code like 'STANDARDIZER_TOOL::%'
    ) and not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where profile_code = 'STANDARDIZER_TOOL::GLOBAL'
    ) then
        insert into public.lesson_plan_configuration_profiles (
            profile_code, profile_name, subject_ref, component_ref,
            lifecycle_status
        ) values (
            'STANDARDIZER_TOOL::GLOBAL',
            'Công cụ chuẩn giáo án chung', '', '', 'DRAFT'
        ) returning profile_id into profile_id_value;

        insert into public.lesson_plan_configuration_versions (
            profile_id, version_number, version_status,
            configuration_payload, change_note, published_at
        ) values (
            profile_id_value, 1, 'PUBLISHED',
            '{
              "configuration_kind":"STANDARDIZER_TOOL",
              "tool_common": {
                "enabled":true,
                "ai_enabled":true,
                "allowed_actions":["Tải giáo án","Xem trước","Chuẩn hóa định dạng","Đề xuất bằng AI","Kiểm tra toàn vẹn","Lưu hệ thống","Tải xuống","Gộp giáo án"],
                "confirmation_policy":"Bắt buộc",
                "integrity_gate":true,
                "preserve_formula_value":true,
                "system_instruction":"Tuân thủ cấu hình ADMIN và không thay đổi nội dung ngoài phạm vi được giao."
              }
            }'::jsonb,
            'Safe default restored by migration; AI provider runtime remains disabled until separately configured by ADMIN.',
            now()
        ) returning configuration_version_id into version_id_value;

        update public.lesson_plan_configuration_profiles
        set current_version_id = version_id_value,
            lifecycle_status = 'ACTIVE', updated_at = now()
        where profile_id = profile_id_value;
    end if;
end;
$$;

-- Ensure every currently active subject has a deterministic first policy;
-- administrator-defined rows (including inactive rows) are preserved.
insert into public.lesson_plan_grouping_policy_config (
    subject_ref, component_ref, grouping_mode, status, rule_version, metadata
)
select subject_id, '', 'BY_PERIOD', 'ACTIVE', 1,
       jsonb_build_object('source', 'coordination_center_restore', 'default_mode', 'BY_PERIOD')
from public.subjects
where status = 'ACTIVE'
on conflict (subject_ref, component_ref) do nothing;
