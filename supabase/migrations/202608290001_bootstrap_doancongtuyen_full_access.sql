-- Give one explicitly authorized account full Teacher + ADMIN capabilities.
-- The application treats an active ADMIN with a teacher profile as an
-- assignable teacher while preserving ADMIN governance access.

do $$
declare
    v_target_email constant text := 'doancongtuyen@gmail.com';
    v_user auth.users%rowtype;
    v_registration public.portal_user_registrations%rowtype;
begin
    select * into v_user
      from auth.users
     where lower(email) = v_target_email
     order by created_at asc
     limit 1;

    if v_user.id is null then
        raise exception 'TARGET_AUTH_USER_NOT_FOUND: %', v_target_email;
    end if;

    select * into v_registration
      from public.portal_user_registrations
     where user_id = v_user.id;

    insert into public.portal_roles (user_id, role, is_active)
    values (v_user.id, 'admin', true)
    on conflict (user_id) do update
    set role = 'admin', is_active = true, updated_at = now();

    insert into public.teacher_profiles (
        user_id, teacher_code, full_name, school_name,
        subjects, grade_levels, default_academic_year,
        show_teacher_name, show_school_name
    )
    values (
        v_user.id,
        coalesce(
            nullif(trim(v_registration.requested_teacher_code), ''),
            nullif(trim(v_user.raw_user_meta_data ->> 'requested_teacher_code'), ''),
            'GV-DOANCONGTUYEN'
        ),
        coalesce(
            nullif(trim(v_registration.full_name), ''),
            nullif(trim(v_user.raw_user_meta_data ->> 'full_name'), ''),
            'Đoàn Công Tuyền'
        ),
        coalesce(
            nullif(trim(v_registration.school_name), ''),
            nullif(trim(v_user.raw_user_meta_data ->> 'school_name'), ''),
            'Chưa cập nhật'
        ),
        array['Toán']::text[],
        array['6','7','8','9']::text[],
        '2026-2027', true, true
    )
    on conflict (user_id) do update
    set teacher_code = coalesce(
            nullif(trim(public.teacher_profiles.teacher_code), ''),
            excluded.teacher_code
        ),
        full_name = coalesce(
            nullif(trim(public.teacher_profiles.full_name), ''),
            excluded.full_name
        ),
        school_name = coalesce(
            nullif(trim(public.teacher_profiles.school_name), ''),
            excluded.school_name
        ),
        updated_at = now();

    update public.portal_user_registrations
       set status = 'APPROVED',
           reviewed_at = coalesce(reviewed_at, now()),
           review_note = coalesce(
               review_note,
               'Trusted bootstrap: assignable Teacher and ADMIN access.'
           ),
           updated_at = now()
     where user_id = v_user.id
       and status <> 'APPROVED';
end;
$$;
