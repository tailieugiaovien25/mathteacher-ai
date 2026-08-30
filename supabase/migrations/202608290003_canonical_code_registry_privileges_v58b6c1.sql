-- V58-B6C1: table privileges required before PostgreSQL can evaluate RLS.
-- RLS remains enabled and remains the write authorization authority.
-- authenticated gets table-level SELECT/INSERT/UPDATE only.
-- Existing ADMIN-only RLS policies still decide whether writes are allowed.
-- DELETE remains forbidden.

revoke all on table public.canonical_code_registry from anon;
revoke delete on table public.canonical_code_registry from authenticated;

grant select, insert, update
on table public.canonical_code_registry
to authenticated;

do $$
begin
    if not has_table_privilege('authenticated','public.canonical_code_registry','SELECT') then
        raise exception 'authenticated SELECT privilege missing';
    end if;

    if not has_table_privilege('authenticated','public.canonical_code_registry','INSERT') then
        raise exception 'authenticated INSERT privilege missing';
    end if;

    if not has_table_privilege('authenticated','public.canonical_code_registry','UPDATE') then
        raise exception 'authenticated UPDATE privilege missing';
    end if;

    if has_table_privilege('authenticated','public.canonical_code_registry','DELETE') then
        raise exception 'authenticated DELETE privilege must remain disabled';
    end if;
end
$$;
