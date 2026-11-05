-- Seed active subjects without replacing administrator-defined policies.
insert into public.lesson_plan_grouping_policy_config (
    subject_ref, component_ref, grouping_mode, status, rule_version, metadata
)
select subject_id,'','BY_PERIOD','ACTIVE',1,
       jsonb_build_object('source','coordination_center_restore','default_mode','BY_PERIOD')
from public.subjects
where status='ACTIVE'
on conflict (subject_ref, component_ref) do nothing;
