begin;

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'assessment-document-templates',
    'assessment-document-templates',
    false,
    26214400,
    array[
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]::text[]
)
on conflict (id) do update
set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create or replace function
public.assessment_template_asset_version_id(
    object_name text
)
returns uuid
language plpgsql
immutable
set search_path = ''
as $$
declare
    first_segment text;
begin
    first_segment := split_part(object_name, '/', 1);

    if first_segment !~
        '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    then
        return null;
    end if;

    return first_segment::uuid;
end;
$$;

revoke all on function
public.assessment_template_asset_version_id(text)
from public;

grant execute on function
public.assessment_template_asset_version_id(text)
to authenticated;

create or replace function
public.assessment_template_asset_is_editable(
    object_name text
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        join public.assessment_document_template_sets
            template_set
            on template_set.template_set_id =
                template_version.template_set_id
        where
            template_version.template_version_id =
                public.assessment_template_asset_version_id(
                    object_name
                )
            and template_version.review_status in (
                'DRAFT',
                'REVISION_REQUIRED'
            )
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id = auth.uid()
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and public.current_user_is_portal_admin()
                )
            )
    );
$$;

revoke all on function
public.assessment_template_asset_is_editable(text)
from public;

grant execute on function
public.assessment_template_asset_is_editable(text)
to authenticated;

drop policy if exists
assessment_template_assets_select_visible
on storage.objects;

create policy
assessment_template_assets_select_visible
on storage.objects
for select
to authenticated
using (
    bucket_id = 'assessment-document-templates'
    and exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        where
            template_version.template_version_id =
                public.assessment_template_asset_version_id(
                    storage.objects.name
                )
            and public.assessment_document_template_set_is_visible(
                template_version.template_set_id
            )
    )
);

drop policy if exists
assessment_template_assets_insert_editable
on storage.objects;

create policy
assessment_template_assets_insert_editable
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'assessment-document-templates'
    and public.assessment_template_asset_is_editable(
        storage.objects.name
    )
);

drop policy if exists
assessment_template_assets_update_editable
on storage.objects;

create policy
assessment_template_assets_update_editable
on storage.objects
for update
to authenticated
using (
    bucket_id = 'assessment-document-templates'
    and public.assessment_template_asset_is_editable(
        storage.objects.name
    )
)
with check (
    bucket_id = 'assessment-document-templates'
    and public.assessment_template_asset_is_editable(
        storage.objects.name
    )
);

drop policy if exists
assessment_template_assets_delete_editable
on storage.objects;

create policy
assessment_template_assets_delete_editable
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'assessment-document-templates'
    and public.assessment_template_asset_is_editable(
        storage.objects.name
    )
);

comment on function
public.assessment_template_asset_version_id(text) is
'Safely resolves the template-version UUID prefix from a private storage object path.';

comment on function
public.assessment_template_asset_is_editable(text) is
'Allows owners of user templates and portal administrators to edit assets only while the template version remains editable.';

commit;
