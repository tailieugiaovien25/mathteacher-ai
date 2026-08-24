create table if not exists
    public.notifications (
        notification_id text primary key,

        owner_id uuid not null
            references auth.users(id)
            on delete cascade,

        type text not null
            check (
                type in (
                    'DATA_CHANGED',
                    'ASSIGNMENT_CHANGED',
                    'SCHEDULE_CHANGED',
                    'PROCESS_COMPLETED',
                    'SYSTEM'
                )
            ),

        priority text not null
            default 'NORMAL'
            check (
                priority in (
                    'LOW',
                    'NORMAL',
                    'HIGH',
                    'URGENT'
                )
            ),

        title text not null
            check (
                char_length(trim(title))
                between 1 and 300
            ),

        message text not null
            check (
                char_length(trim(message))
                between 1 and 5000
            ),

        source_module text not null
            check (
                char_length(trim(source_module))
                between 1 and 200
            ),

        source_id text null
            check (
                source_id is null
                or char_length(trim(source_id))
                between 1 and 300
            ),

        action_ref text null
            check (
                action_ref is null
                or char_length(trim(action_ref))
                between 1 and 300
            ),

        status text not null
            default 'UNREAD'
            check (
                status in (
                    'UNREAD',
                    'READ',
                    'ARCHIVED'
                )
            ),

        created_at timestamptz
            not null default now(),

        read_at timestamptz null,

        updated_at timestamptz
            not null default now(),

        constraint
            notification_read_state_consistency
        check (
            (
                status = 'UNREAD'
                and read_at is null
            )
            or
            (
                status = 'READ'
                and read_at is not null
            )
            or
            (
                status = 'ARCHIVED'
            )
        )
    );


create index if not exists
    notifications_owner_status_created_idx
on public.notifications (
    owner_id,
    status,
    created_at desc
);


create index if not exists
    notifications_owner_created_idx
on public.notifications (
    owner_id,
    created_at desc
);


create index if not exists
    notifications_source_idx
on public.notifications (
    owner_id,
    source_module,
    source_id
);


alter table
    public.notifications
enable row level security;


revoke all
on table public.notifications
from anon;


grant
    select,
    insert,
    update,
    delete
on table public.notifications
to authenticated;


drop policy if exists
    "users_select_own_notifications"
on public.notifications;


create policy
    "users_select_own_notifications"
on public.notifications
for select
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);


drop policy if exists
    "users_insert_own_notifications"
on public.notifications;


create policy
    "users_insert_own_notifications"
on public.notifications
for insert
to authenticated
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);


drop policy if exists
    "users_update_own_notifications"
on public.notifications;


create policy
    "users_update_own_notifications"
on public.notifications
for update
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
)
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);


drop policy if exists
    "users_delete_own_notifications"
on public.notifications;


create policy
    "users_delete_own_notifications"
on public.notifications
for delete
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);
