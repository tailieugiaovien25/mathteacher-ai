-- Seed a safe global template only when no global lesson-plan profile is active.
-- Existing ADMIN profiles and drafts are preserved.
do $restore_lesson_plan$
declare
    p uuid;
    v uuid;
begin
    if not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where lifecycle_status='ACTIVE' and subject_ref='' and component_ref=''
          and profile_code not like 'STANDARDIZER_TOOL::%'
    ) and not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where profile_code='LESSON_PLAN::GLOBAL::RESTORED_DEFAULT'
    ) then
        insert into public.lesson_plan_configuration_profiles
            (profile_code,profile_name,subject_ref,component_ref,lifecycle_status)
        values ('LESSON_PLAN::GLOBAL::RESTORED_DEFAULT',
            'Cấu hình giáo án toàn hệ thống (mặc định khôi phục)','','','DRAFT')
        returning profile_id into p;

        insert into public.lesson_plan_configuration_versions
            (profile_id,version_number,version_status,configuration_payload,change_note,published_at)
        values (p,1,'PUBLISHED',
            '{"template_profile":{"profile_name":"Kế hoạch bài dạy mặc định","layout":{"paper_size":"A4","font_name":"Times New Roman","font_color":"black","body_font_size_pt":14,"line_spacing":1.15,"character_spacing_pt":0,"margin_left_cm":3,"margin_right_cm":2,"margin_top_cm":2,"margin_bottom_cm":2,"page_border_enabled":false,"table_repeat_header":true,"table_allow_row_split":true,"image_max_width_percent":100},"equations":{"mode":"force_times","text_font":"Times New Roman","math_font":"Times New Roman","preserve_omml_structure":true,"preserve_value":true,"rollback_on_integrity_failure":true}},"date_policy":{"drafting_before_monday_enabled":true,"drafting_before_monday_days":3,"approval_before_monday_enabled":true,"approval_before_monday_days":1},"approval_policy":{"approval_label":"TỔ CM DUYỆT","alignment":"right","approval_offset_days":1}}'::jsonb,
            'Safe template defaults; no AI credentials or personal storage IDs.',now())
        returning configuration_version_id into v;

        update public.lesson_plan_configuration_profiles
        set current_version_id=v,lifecycle_status='ACTIVE',updated_at=now()
        where profile_id=p;
    end if;
end;
$restore_lesson_plan$;
