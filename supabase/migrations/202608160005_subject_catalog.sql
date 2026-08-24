create table if not exists public.subjects (
    subject_id text primary key,

    code text not null unique
        check (
            char_length(trim(code))
            between 1 and 50
        ),

    name text not null
        check (
            char_length(trim(name))
            between 1 and 150
        ),

    component_policy text not null
        default 'NONE'
        check (
            component_policy in (
                'NONE',
                'OPTIONAL',
                'REQUIRED'
            )
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    display_order integer not null
        default 0
        check (
            display_order >= 0
        ),

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now()
);


create table if not exists
    public.subject_components (
        component_id text primary key,

        subject_id text not null
            references public.subjects(
                subject_id
            )
            on delete cascade,

        code text not null,

        name text not null
            check (
                char_length(trim(name))
                between 1 and 150
            ),

        status text not null
            default 'ACTIVE'
            check (
                status in (
                    'ACTIVE',
                    'INACTIVE'
                )
            ),

        display_order integer not null
            default 0
            check (
                display_order >= 0
            ),

        description text,

        created_at timestamptz
            not null default now(),

        updated_at timestamptz
            not null default now(),

        constraint
            subject_components_subject_code_unique
        unique (
            subject_id,
            code
        ),

        constraint
            subject_components_subject_component_unique
        unique (
            subject_id,
            component_id
        )
    );


create index if not exists
    subjects_status_order_idx
on public.subjects (
    status,
    display_order
);


create index if not exists
    subject_components_subject_status_order_idx
on public.subject_components (
    subject_id,
    status,
    display_order
);


alter table
    public.subjects
enable row level security;


alter table
    public.subject_components
enable row level security;


revoke all
on table public.subjects
from anon;


revoke all
on table public.subject_components
from anon;


grant select
on table public.subjects
to authenticated;


grant select
on table public.subject_components
to authenticated;


grant
    insert,
    update,
    delete
on table public.subjects
to authenticated;


grant
    insert,
    update,
    delete
on table public.subject_components
to authenticated;


/*
Authenticated users may read the canonical catalog.

Write access requires ADMIN in public.portal_roles.

The client cannot grant itself ADMIN because portal_roles
already has its own protected RLS model.
*/


drop policy if exists
    "authenticated_read_subjects"
on public.subjects;


create policy
    "authenticated_read_subjects"
on public.subjects
for select
to authenticated
using (
    (select auth.uid()) is not null
);


drop policy if exists
    "admin_insert_subjects"
on public.subjects;


create policy
    "admin_insert_subjects"
on public.subjects
for insert
to authenticated
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);


drop policy if exists
    "admin_update_subjects"
on public.subjects;


create policy
    "admin_update_subjects"
on public.subjects
for update
to authenticated
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
)
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);


drop policy if exists
    "admin_delete_subjects"
on public.subjects;


create policy
    "admin_delete_subjects"
on public.subjects
for delete
to authenticated
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);


drop policy if exists
    "authenticated_read_subject_components"
on public.subject_components;


create policy
    "authenticated_read_subject_components"
on public.subject_components
for select
to authenticated
using (
    (select auth.uid()) is not null
);


drop policy if exists
    "admin_insert_subject_components"
on public.subject_components;


create policy
    "admin_insert_subject_components"
on public.subject_components
for insert
to authenticated
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);


drop policy if exists
    "admin_update_subject_components"
on public.subject_components;


create policy
    "admin_update_subject_components"
on public.subject_components
for update
to authenticated
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
)
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);


drop policy if exists
    "admin_delete_subject_components"
on public.subject_components;


create policy
    "admin_delete_subject_components"
on public.subject_components
for delete
to authenticated
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (
                select auth.uid()
            )
            and pr.role = 'ADMIN'
    )
);
