-- V58-C5B7J3
-- Grade remains a mandatory canonical partition, not a grouping strategy.
-- Valid strategies: BY_PERIOD | BY_LESSON | BY_WEEK.

do $$
declare
    target_constraint text;
begin
    -- Migrate legacy policy rows first.
    update public.lesson_plan_grouping_policy_config
       set grouping_mode = 'BY_WEEK',
           rule_version = greatest(coalesce(rule_version, 1), 1) + 1
     where grouping_mode = 'BY_GRADE';

    -- Remove any CHECK constraint on grouping_mode so it can be rebuilt canonically.
    for target_constraint in
        select c.conname
          from pg_constraint c
          join pg_class t on t.oid = c.conrelid
          join pg_namespace n on n.oid = t.relnamespace
         where n.nspname = 'public'
           and t.relname = 'lesson_plan_grouping_policy_config'
           and c.contype = 'c'
           and pg_get_constraintdef(c.oid) ilike '%grouping_mode%'
    loop
        execute format(
            'alter table public.lesson_plan_grouping_policy_config drop constraint %I',
            target_constraint
        );
    end loop;
end $$;

alter table public.lesson_plan_grouping_policy_config
    add constraint lesson_plan_grouping_policy_config_grouping_mode_check
    check (grouping_mode in ('BY_PERIOD', 'BY_LESSON', 'BY_WEEK'));
