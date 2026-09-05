-- V14B6K
-- Preserve subject-level vs component-level timetable selection.
--
-- component_id IS NULL:
--     subject-level selection, e.g. To?n - Tr?ng.
--
-- component_id IS NOT NULL:
--     specific canonical component, e.g. To?n - H?nh h?c.

alter table public.teacher_timetable_slots
    add column if not exists component_id text null;

comment on column
    public.teacher_timetable_slots.component_id
is
    'Optional canonical component for timetable slot; NULL means subject-level selection.';
