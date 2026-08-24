do $$
declare
    current_year text;
    current_start_date date;
    first_round_id text;
begin
    select
        academic_year,
        start_date
    into
        current_year,
        current_start_date
    from public.academic_year_configurations
    where is_current = true
      and status = 'ACTIVE'
    limit 1;

    if current_year is null then
        raise notice
            'No current ACTIVE academic year; '
            'assignment round backfill skipped.';
        return;
    end if;

    select round_id
    into first_round_id
    from public.assignment_rounds
    where academic_year = current_year
      and round_number = 1
    limit 1;

    if first_round_id is null then
        first_round_id = (
            'round-'
            || replace(
                current_year,
                '-',
                ''
            )
            || '-1'
        );

        insert into public.assignment_rounds (
            round_id,
            academic_year,
            round_number,
            effective_from,
            label,
            status
        )
        values (
            first_round_id,
            current_year,
            1,
            current_start_date,
            'Lần 1',
            'ACTIVE'
        )
        on conflict (
            academic_year,
            round_number
        )
        do nothing;

        select round_id
        into first_round_id
        from public.assignment_rounds
        where academic_year = current_year
          and round_number = 1
        limit 1;
    end if;

    update public.teaching_assignments
    set
        assignment_round_id = first_round_id,
        updated_at = now()
    where academic_year = current_year
      and assignment_round_id is null;
end
$$;
