create table if not exists public.portal_user_registrations (
    registration_id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,
    email text null,
    full_name text not null,
    school_name text null,
    requested_teacher_code text null,
    status text not null default 'PENDING'
        check (status in ('PENDING','APPROVED','REJECTED')),
    submitted_at timestamptz not null default now(),
    reviewed_at timestamptz null,
    reviewed_by uuid null references auth.users(id) on delete set null,
    review_note text null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists portal_user_registrations_status_idx
    on public.portal_user_registrations(status, submitted_at desc);

alter table public.portal_user_registrations enable row level security;

revoke all on table public.portal_user_registrations from anon;
grant select, insert, update on table public.portal_user_registrations to authenticated;

drop policy if exists "registrations_select_own_or_admin"
    on public.portal_user_registrations;
create policy "registrations_select_own_or_admin"
on public.portal_user_registrations
for select
to authenticated
using (
    user_id = auth.uid()
    or public.current_user_is_portal_admin()
);

drop policy if exists "registrations_insert_own"
    on public.portal_user_registrations;
create policy "registrations_insert_own"
on public.portal_user_registrations
for insert
to authenticated
with check (
    user_id = auth.uid()
    and status = 'PENDING'
    and reviewed_at is null
    and reviewed_by is null
);

drop policy if exists "registrations_update_admin_only"
    on public.portal_user_registrations;
create policy "registrations_update_admin_only"
on public.portal_user_registrations
for update
to authenticated
using (public.current_user_is_portal_admin())
with check (public.current_user_is_portal_admin());

create or replace function public.create_or_refresh_own_portal_registration(
    p_full_name text,
    p_school_name text default null,
    p_requested_teacher_code text default null
)
returns public.portal_user_registrations
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_user auth.users;
    v_row public.portal_user_registrations;
begin
    select *
      into v_user
      from auth.users
     where id = auth.uid();

    if v_user.id is null then
        raise exception 'AUTH_USER_REQUIRED';
    end if;

    if nullif(trim(coalesce(p_full_name,'')), '') is null then
        raise exception 'FULL_NAME_REQUIRED';
    end if;

    insert into public.portal_user_registrations (
        user_id,
        email,
        full_name,
        school_name,
        requested_teacher_code,
        status,
        submitted_at,
        reviewed_at,
        reviewed_by,
        review_note,
        updated_at
    )
    values (
        v_user.id,
        v_user.email,
        trim(p_full_name),
        nullif(trim(coalesce(p_school_name,'')), ''),
        nullif(trim(coalesce(p_requested_teacher_code,'')), ''),
        'PENDING',
        now(),
        null,
        null,
        null,
        now()
    )
    on conflict (user_id) do update
    set
        email = excluded.email,
        full_name = excluded.full_name,
        school_name = excluded.school_name,
        requested_teacher_code = excluded.requested_teacher_code,
        status = case
            when public.portal_user_registrations.status = 'APPROVED'
                then public.portal_user_registrations.status
            else 'PENDING'
        end,
        submitted_at = case
            when public.portal_user_registrations.status = 'APPROVED'
                then public.portal_user_registrations.submitted_at
            else now()
        end,
        reviewed_at = case
            when public.portal_user_registrations.status = 'APPROVED'
                then public.portal_user_registrations.reviewed_at
            else null
        end,
        reviewed_by = case
            when public.portal_user_registrations.status = 'APPROVED'
                then public.portal_user_registrations.reviewed_by
            else null
        end,
        review_note = case
            when public.portal_user_registrations.status = 'APPROVED'
                then public.portal_user_registrations.review_note
            else null
        end,
        updated_at = now()
    returning * into v_row;

    return v_row;
end;
$$;

revoke all on function public.create_or_refresh_own_portal_registration(text,text,text) from public;
grant execute on function public.create_or_refresh_own_portal_registration(text,text,text) to authenticated;

create or replace function public.review_portal_user_registration(
    p_registration_id uuid,
    p_decision text,
    p_teacher_code text default null,
    p_full_name text default null,
    p_school_name text default null,
    p_review_note text default null
)
returns public.portal_user_registrations
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_registration public.portal_user_registrations;
    v_decision text := upper(trim(coalesce(p_decision,'')));
begin
    if not public.current_user_is_portal_admin() then
        raise exception 'PORTAL_ADMIN_REQUIRED';
    end if;

    if v_decision not in ('APPROVED','REJECTED') then
        raise exception 'INVALID_REVIEW_DECISION';
    end if;

    select *
      into v_registration
      from public.portal_user_registrations
     where registration_id = p_registration_id
     for update;

    if v_registration.registration_id is null then
        raise exception 'REGISTRATION_NOT_FOUND';
    end if;

    if v_registration.status <> 'PENDING' then
        raise exception 'REGISTRATION_NOT_PENDING';
    end if;

    if v_decision = 'APPROVED' then
        insert into public.portal_roles(user_id, role, is_active)
        values (v_registration.user_id, 'teacher', true)
        on conflict (user_id) do update
        set role = 'teacher',
            is_active = true;

        insert into public.teacher_profiles(
            user_id,
            teacher_code,
            full_name,
            school_name
        )
        values (
            v_registration.user_id,
            coalesce(
                nullif(trim(coalesce(p_teacher_code,'')), ''),
                v_registration.requested_teacher_code
            ),
            coalesce(
                nullif(trim(coalesce(p_full_name,'')), ''),
                v_registration.full_name
            ),
            coalesce(
                nullif(trim(coalesce(p_school_name,'')), ''),
                v_registration.school_name
            )
        )
        on conflict (user_id) do update
        set
            teacher_code = coalesce(
                nullif(trim(coalesce(p_teacher_code,'')), ''),
                excluded.teacher_code,
                public.teacher_profiles.teacher_code
            ),
            full_name = coalesce(
                nullif(trim(coalesce(p_full_name,'')), ''),
                excluded.full_name,
                public.teacher_profiles.full_name
            ),
            school_name = coalesce(
                nullif(trim(coalesce(p_school_name,'')), ''),
                excluded.school_name,
                public.teacher_profiles.school_name
            );
    end if;

    update public.portal_user_registrations
       set status = v_decision,
           reviewed_at = now(),
           reviewed_by = auth.uid(),
           review_note = nullif(trim(coalesce(p_review_note,'')), ''),
           updated_at = now()
     where registration_id = p_registration_id
     returning * into v_registration;

    return v_registration;
end;
$$;

revoke all on function public.review_portal_user_registration(uuid,text,text,text,text,text) from public;
grant execute on function public.review_portal_user_registration(uuid,text,text,text,text,text) to authenticated;

comment on table public.portal_user_registrations is
'Canonical portal account registration lifecycle. Registration never self-grants portal role; ADMIN approval activates teacher access.';
