create table if not exists public.assignment_rounds (
    round_id text primary key,

    academic_year text not null
        check (
            char_length(academic_year)
            between 1 and 30
        ),

    round_number integer not null
        check (
            round_number >= 1
        ),

    effective_from date not null,

    label text not null
        check (
            char_length(label)
            between 1 and 100
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'CLOSED'
            )
        ),

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now(),

    constraint assignment_round_year_number_unique
        unique (
            academic_year,
            round_number
        )
);

create index if not exists
    assignment_rounds_year_idx
on public.assignment_rounds (
    academic_year
);

create index if not exists
    assignment_rounds_year_status_idx
on public.assignment_rounds (
    academic_year,
    status
);

alter table
    public.assignment_rounds
enable row level security;

revoke all
on table public.assignment_rounds
from anon;

grant
    select,
    insert,
    update,
    delete
on table public.assignment_rounds
to authenticated;

-- ---------------------------------------------------------
-- AUTHENTICATED: READ ASSIGNMENT ROUNDS
-- ---------------------------------------------------------

drop policy if exists
    "authenticated_select_assignment_rounds"
on public.assignment_rounds;

create policy
    "authenticated_select_assignment_rounds"
on public.assignment_rounds
for select
to authenticated
using (
    (select auth.uid()) is not null
);


-- ---------------------------------------------------------
-- ADMIN: CREATE ASSIGNMENT ROUNDS
-- ---------------------------------------------------------

drop policy if exists
    "admins_insert_assignment_rounds"
on public.assignment_rounds;

create policy
    "admins_insert_assignment_rounds"
on public.assignment_rounds
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE ASSIGNMENT ROUNDS
-- ---------------------------------------------------------

drop policy if exists
    "admins_update_assignment_rounds"
on public.assignment_rounds;

create policy
    "admins_update_assignment_rounds"
on public.assignment_rounds
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: DELETE ASSIGNMENT ROUNDS
-- ---------------------------------------------------------

drop policy if exists
    "admins_delete_assignment_rounds"
on public.assignment_rounds;

create policy
    "admins_delete_assignment_rounds"
on public.assignment_rounds
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.assignment_rounds is
'Canonical academic-year assignment rounds administered by portal ADMIN. Authenticated users may read rounds; only ADMIN may create, update, or delete them.';
