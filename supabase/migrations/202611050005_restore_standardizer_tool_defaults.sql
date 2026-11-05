-- Seed common tool controls when no global tool profile is active.
-- Existing tool profiles and drafts are preserved.
do $restore_tool$
declare
    p uuid;
    v uuid;
begin
    if not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where lifecycle_status='ACTIVE' and subject_ref='' and component_ref=''
          and profile_code like 'STANDARDIZER_TOOL::%'
    ) and not exists (
        select 1 from public.lesson_plan_configuration_profiles
        where profile_code='STANDARDIZER_TOOL::GLOBAL'
    ) then
        insert into public.lesson_plan_configuration_profiles
            (profile_code,profile_name,subject_ref,component_ref,lifecycle_status)
        values ('STANDARDIZER_TOOL::GLOBAL','Công cụ chuẩn giáo án chung','','','DRAFT')
        returning profile_id into p;

        insert into public.lesson_plan_configuration_versions
            (profile_id,version_number,version_status,configuration_payload,change_note,published_at)
        values (p,1,'PUBLISHED',
            '{"configuration_kind":"STANDARDIZER_TOOL","tool_common":{"enabled":true,"ai_enabled":true,"allowed_actions":["Tải giáo án","Xem trước","Chuẩn hóa định dạng","Đề xuất bằng AI","Kiểm tra toàn vẹn","Lưu hệ thống","Tải xuống","Gộp giáo án"],"confirmation_policy":"Bắt buộc","integrity_gate":true,"preserve_formula_value":true,"system_instruction":"Tuân thủ cấu hình ADMIN và không thay đổi nội dung ngoài phạm vi được giao."}}'::jsonb,
            'Safe tool defaults; provider AI remains off until enabled in lesson-plan AI settings.',now())
        returning configuration_version_id into v;

        update public.lesson_plan_configuration_profiles
        set current_version_id=v,lifecycle_status='ACTIVE',updated_at=now()
        where profile_id=p;
    end if;
end;
$restore_tool$;
