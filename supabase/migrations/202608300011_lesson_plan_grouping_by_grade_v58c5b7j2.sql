-- V58-C5B7J2: add grade-level lesson-plan grouping mode.
alter table public.lesson_plan_grouping_policy_config
drop constraint if exists lesson_plan_grouping_policy_config_grouping_mode_check;

alter table public.lesson_plan_grouping_policy_config
add constraint lesson_plan_grouping_policy_config_grouping_mode_check
check (grouping_mode in ('BY_PERIOD', 'BY_LESSON', 'BY_WEEK', 'BY_GRADE'));
