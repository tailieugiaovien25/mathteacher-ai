-- Canonicalize Subject Catalog ADMIN role checks.
--
-- Canonical portal roles are lowercase:
--   teacher
--   admin
--
-- The original Subject Catalog migration used 'ADMIN'
-- in RLS policies. PostgreSQL text comparison is
-- case-sensitive, while portal_roles stores 'admin'.

alter policy "admin_insert_subjects"
on public.subjects
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

alter policy "admin_update_subjects"
on public.subjects
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
)
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

alter policy "admin_delete_subjects"
on public.subjects
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

alter policy "admin_insert_subject_components"
on public.subject_components
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

alter policy "admin_update_subject_components"
on public.subject_components
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
)
with check (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

alter policy "admin_delete_subject_components"
on public.subject_components
using (
    exists (
        select 1
        from public.portal_roles pr
        where
            pr.user_id = (select auth.uid())
            and pr.role = 'admin'
    )
);

comment on table public.portal_roles is
'Server-governed portal authorization roles. Canonical roles are lowercase: teacher, admin.';
