-- Run after migrations 202608300012 and 202608300013.
-- Separate profile families may both be ACTIVE at the same scope.
drop index if exists public.lesson_plan_configuration_profiles_one_active_scope;

create unique index lesson_plan_configuration_profiles_one_active_scope
on public.lesson_plan_configuration_profiles (
    (case when profile_code like 'STANDARDIZER_TOOL::%' then 'STANDARDIZER_TOOL' else 'LESSON_PLAN' end),
    subject_ref,
    component_ref
)
where lifecycle_status = 'ACTIVE';
