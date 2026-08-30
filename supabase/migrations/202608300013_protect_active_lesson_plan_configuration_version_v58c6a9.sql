-- V58-C6A9
-- Follow-up integrity guard for ADMIN lesson-plan configuration.
-- Migration 202608300012 is already applied remotely and must remain immutable.
--
-- Invariant:
-- An ACTIVE lesson-plan configuration profile must never point to a version
-- whose status is no longer PUBLISHED.
--
-- Operational rule:
-- ADMIN must first publish/select another version and update current_version_id,
-- then the previously-current version may be retired.

create or replace function public.protect_active_lesson_plan_configuration_version_retirement()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    if old.version_status = 'PUBLISHED'
       and new.version_status <> 'PUBLISHED'
       and exists (
           select 1
           from public.lesson_plan_configuration_profiles p
           where p.lifecycle_status = 'ACTIVE'
             and p.current_version_id = old.configuration_version_id
       )
    then
        raise exception
            'Cannot retire or unpublish lesson-plan configuration version % while it is current for an ACTIVE profile',
            old.configuration_version_id;
    end if;

    return new;
end;
$$;

drop trigger if exists lesson_plan_configuration_versions_protect_active_current_retirement
on public.lesson_plan_configuration_versions;

create trigger lesson_plan_configuration_versions_protect_active_current_retirement
before update of version_status
on public.lesson_plan_configuration_versions
for each row
execute function public.protect_active_lesson_plan_configuration_version_retirement();

comment on function public.protect_active_lesson_plan_configuration_version_retirement()
is 'Prevents PUBLISHED -> non-PUBLISHED transition while the version is current for any ACTIVE lesson-plan configuration profile.';
