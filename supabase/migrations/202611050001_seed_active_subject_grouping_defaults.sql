-- Give every active subject an explicit initial grouping policy.
-- A component-specific policy continues to take precedence over this default.
-- Existing administrator choices, including inactive rows, are preserved.

insert into public.lesson_plan_grouping_policy_config (
    subject_ref,
    component_ref,
    grouping_mode,
    status,
    rule_version,
    metadata
)
select
    subject_id,
    '',
    'BY_PERIOD',
    'ACTIVE',
    1,
    jsonb_build_object(
        'source', 'active_subject_grouping_defaults_migration',
        'default_mode', 'BY_PERIOD'
    )
from public.subjects
where status = 'ACTIVE'
on conflict (subject_ref, component_ref) do nothing;
