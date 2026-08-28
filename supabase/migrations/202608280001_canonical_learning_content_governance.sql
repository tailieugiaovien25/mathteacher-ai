begin;

create table if not exists public.canonical_learning_content_units (
    content_unit_id text primary key,
    program_id text not null references public.education_programs(program_id) on delete restrict,
    subject_id text not null references public.subjects(subject_id) on delete restrict,
    grade_id text not null references public.grades(grade_id) on delete restrict,
    parent_content_unit_id text null,
    content_code text not null,
    content_type text not null check (
        content_type in ('DOMAIN','STRAND','TOPIC','LESSON','KNOWLEDGE','SKILL','LANGUAGE_FUNCTION','PRACTICE')
    ),
    title text not null check (char_length(trim(title)) between 1 and 300),
    normalized_description text not null default '',
    display_order integer not null default 0 check (display_order >= 0),
    source_version_id text null references public.educational_source_versions(source_version_id) on delete restrict,
    lifecycle_status text not null default 'DRAFT' check (
        lifecycle_status in ('DRAFT','PENDING_REVIEW','ACTIVE','INACTIVE','SUPERSEDED')
    ),
    metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata)='object'),
    created_by uuid null,
    updated_by uuid null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(program_id,subject_id,grade_id,content_code),
    unique(content_unit_id,program_id,subject_id,grade_id),
    check (parent_content_unit_id is null or parent_content_unit_id <> content_unit_id),
    foreign key (parent_content_unit_id,program_id,subject_id,grade_id)
        references public.canonical_learning_content_units(
            content_unit_id,program_id,subject_id,grade_id
        ) on delete restrict
);

create table if not exists public.textbook_content_unit_links (
    textbook_content_link_id uuid primary key default gen_random_uuid(),
    content_unit_id text not null references
        public.canonical_learning_content_units(content_unit_id) on delete restrict,
    textbook_unit_id text not null references public.textbook_units(textbook_unit_id) on delete restrict,
    relation_type text not null check (
        relation_type in ('PRIMARY_LOCATION','SUPPORTING_LOCATION','PRACTICE_LOCATION','REFERENCE')
    ),
    coverage_status text not null default 'PARTIAL' check (
        coverage_status in ('FULL','PARTIAL','INTRODUCTORY','EXTENDED')
    ),
    notes text not null default '',
    source_version_id text null references public.educational_source_versions(source_version_id) on delete restrict,
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    created_by uuid null,
    created_at timestamptz not null default now(),
    unique(content_unit_id,textbook_unit_id,relation_type)
);

create table if not exists public.learning_requirement_content_links (
    requirement_content_link_id uuid primary key default gen_random_uuid(),
    requirement_code text not null references
        public.assessment_learning_requirements(requirement_code) on update cascade on delete restrict,
    content_unit_id text not null references
        public.canonical_learning_content_units(content_unit_id) on delete restrict,
    relation_type text not null check (
        relation_type in ('PRIMARY','SUPPORTING','PREREQUISITE','EXTENSION')
    ),
    alignment_strength text not null check (
        alignment_strength in ('DIRECT','INDIRECT','CONTEXTUAL')
    ),
    rationale text not null default '',
    source_version_id text null references public.educational_source_versions(source_version_id) on delete restrict,
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    created_by uuid null,
    created_at timestamptz not null default now(),
    unique(requirement_code,content_unit_id,relation_type)
);

create table if not exists public.learning_content_change_log (
    change_id uuid primary key default gen_random_uuid(),
    entity_type text not null,
    entity_id text not null,
    operation text not null check (operation in ('CREATE','UPDATE','LINK','ACTIVATE','DEACTIVATE')),
    before_value jsonb null,
    after_value jsonb null,
    changed_by uuid not null references auth.users(id) on delete restrict,
    changed_at timestamptz not null default now()
);

create index if not exists canonical_learning_content_scope_idx
on public.canonical_learning_content_units(program_id,subject_id,grade_id,lifecycle_status);
create index if not exists canonical_learning_content_parent_idx
on public.canonical_learning_content_units(parent_content_unit_id);
create index if not exists textbook_content_links_textbook_idx
on public.textbook_content_unit_links(textbook_unit_id,status);
create index if not exists requirement_content_links_requirement_idx
on public.learning_requirement_content_links(requirement_code,status);

create or replace function public.save_canonical_learning_content(
    target_payload jsonb
)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
    actor uuid := (select auth.uid());
    entity_id text := nullif(trim(target_payload->>'content_unit_id'),'');
    target_program text := nullif(trim(target_payload->>'program_id'),'');
    target_subject text := nullif(trim(target_payload->>'subject_id'),'');
    target_grade text := nullif(trim(target_payload->>'grade_id'),'');
    old_value jsonb;
    result_row jsonb;
begin
    if actor is null then raise exception 'AUTHENTICATION_REQUIRED'; end if;
    if not public.current_user_is_portal_admin() then raise exception 'ADMIN_REQUIRED'; end if;
    if jsonb_typeof(target_payload) <> 'object' then raise exception 'CONTENT_PAYLOAD_INVALID'; end if;
    if entity_id is null then raise exception 'CONTENT_UNIT_ID_REQUIRED'; end if;
    if not exists (
        select 1 from public.education_program_scopes scope
         where scope.program_id=target_program and scope.subject_id=target_subject
           and scope.grade_id=target_grade and scope.status='ACTIVE'
    ) then raise exception 'ACTIVE_PROGRAM_SCOPE_NOT_FOUND'; end if;

    select to_jsonb(row) into old_value
      from public.canonical_learning_content_units row
     where row.content_unit_id=entity_id;

    insert into public.canonical_learning_content_units(
        content_unit_id,program_id,subject_id,grade_id,parent_content_unit_id,
        content_code,content_type,title,normalized_description,display_order,
        source_version_id,lifecycle_status,metadata,created_by,updated_by
    ) values (
        entity_id,target_program,target_subject,target_grade,
        nullif(trim(target_payload->>'parent_content_unit_id'),''),
        trim(target_payload->>'content_code'),trim(target_payload->>'content_type'),
        trim(target_payload->>'title'),coalesce(target_payload->>'normalized_description',''),
        coalesce((target_payload->>'display_order')::integer,0),
        nullif(trim(target_payload->>'source_version_id'),''),
        coalesce(nullif(trim(target_payload->>'lifecycle_status'),''),'DRAFT'),
        coalesce(target_payload->'metadata','{}'::jsonb),actor,actor
    ) on conflict(content_unit_id) do update set
        program_id=excluded.program_id,subject_id=excluded.subject_id,grade_id=excluded.grade_id,
        parent_content_unit_id=excluded.parent_content_unit_id,content_code=excluded.content_code,
        content_type=excluded.content_type,title=excluded.title,
        normalized_description=excluded.normalized_description,display_order=excluded.display_order,
        source_version_id=excluded.source_version_id,lifecycle_status=excluded.lifecycle_status,
        metadata=excluded.metadata,updated_by=actor,updated_at=now();

    select to_jsonb(row) into result_row
      from public.canonical_learning_content_units row where row.content_unit_id=entity_id;
    insert into public.learning_content_change_log(
        entity_type,entity_id,operation,before_value,after_value,changed_by
    ) values ('CONTENT_UNIT',entity_id,case when old_value is null then 'CREATE' else 'UPDATE' end,
              old_value,result_row,actor);
    return result_row;
end;
$$;

create or replace function public.save_textbook_content_unit_link(
    target_content_unit_id text,
    target_textbook_unit_id text,
    target_relation_type text,
    target_coverage_status text,
    target_notes text default '',
    target_source_version_id text default null
)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
    actor uuid := (select auth.uid());
    content_subject text;
    content_grade text;
    book_subject text;
    book_grade text;
    result_row jsonb;
begin
    if actor is null then raise exception 'AUTHENTICATION_REQUIRED'; end if;
    if not public.current_user_is_portal_admin() then raise exception 'ADMIN_REQUIRED'; end if;
    if target_relation_type not in ('PRIMARY_LOCATION','SUPPORTING_LOCATION','PRACTICE_LOCATION','REFERENCE')
        then raise exception 'TEXTBOOK_CONTENT_RELATION_INVALID'; end if;
    if target_coverage_status not in ('FULL','PARTIAL','INTRODUCTORY','EXTENDED')
        then raise exception 'TEXTBOOK_CONTENT_COVERAGE_INVALID'; end if;

    select subject_id,grade_id into content_subject,content_grade
      from public.canonical_learning_content_units
     where content_unit_id=target_content_unit_id and lifecycle_status='ACTIVE';
    if not found then raise exception 'ACTIVE_CONTENT_UNIT_NOT_FOUND'; end if;
    select catalog.subject_id,catalog.grade_id into book_subject,book_grade
      from public.textbook_units unit_row join public.textbook_catalog catalog
        on catalog.textbook_id=unit_row.textbook_id
     where unit_row.textbook_unit_id=target_textbook_unit_id
       and unit_row.status='ACTIVE' and catalog.status='ACTIVE';
    if not found then raise exception 'ACTIVE_TEXTBOOK_UNIT_NOT_FOUND'; end if;
    if content_subject is distinct from book_subject or content_grade is distinct from book_grade
        then raise exception 'TEXTBOOK_CONTENT_SCOPE_MISMATCH'; end if;

    insert into public.textbook_content_unit_links(
        content_unit_id,textbook_unit_id,relation_type,coverage_status,notes,
        source_version_id,status,created_by
    ) values (
        target_content_unit_id,target_textbook_unit_id,target_relation_type,
        target_coverage_status,coalesce(target_notes,''),nullif(trim(target_source_version_id),''),
        'ACTIVE',actor
    ) on conflict(content_unit_id,textbook_unit_id,relation_type) do update set
        coverage_status=excluded.coverage_status,notes=excluded.notes,
        source_version_id=excluded.source_version_id,status='ACTIVE';
    select to_jsonb(row) into result_row from public.textbook_content_unit_links row
     where row.content_unit_id=target_content_unit_id
       and row.textbook_unit_id=target_textbook_unit_id and row.relation_type=target_relation_type;
    insert into public.learning_content_change_log(entity_type,entity_id,operation,after_value,changed_by)
    values ('TEXTBOOK_CONTENT_LINK',target_content_unit_id||':'||target_textbook_unit_id,'LINK',result_row,actor);
    return result_row;
end;
$$;

create or replace function public.save_learning_requirement_content_link(
    target_requirement_code text,
    target_content_unit_id text,
    target_relation_type text,
    target_alignment_strength text,
    target_rationale text default '',
    target_source_version_id text default null
)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
    actor uuid := (select auth.uid());
    requirement_grade integer;
    requirement_subject text;
    content_grade integer;
    content_subject text;
    result_row jsonb;
begin
    if actor is null then raise exception 'AUTHENTICATION_REQUIRED'; end if;
    if not public.current_user_is_portal_admin() then raise exception 'ADMIN_REQUIRED'; end if;
    if target_relation_type not in ('PRIMARY','SUPPORTING','PREREQUISITE','EXTENSION')
        then raise exception 'REQUIREMENT_CONTENT_RELATION_INVALID'; end if;
    if target_alignment_strength not in ('DIRECT','INDIRECT','CONTEXTUAL')
        then raise exception 'REQUIREMENT_CONTENT_ALIGNMENT_INVALID'; end if;

    select req.grade_level,program.metadata->>'canonical_subject_id'
      into requirement_grade,requirement_subject
      from public.assessment_learning_requirements req
      join public.assessment_curriculum_programs program on program.program_code=req.program_code
     where req.requirement_code=target_requirement_code and req.status='ACTIVE';
    if not found then raise exception 'ACTIVE_REQUIREMENT_NOT_FOUND'; end if;
    select grade.grade_number,content.subject_id into content_grade,content_subject
      from public.canonical_learning_content_units content
      join public.grades grade on grade.grade_id=content.grade_id
     where content.content_unit_id=target_content_unit_id and content.lifecycle_status='ACTIVE';
    if not found then raise exception 'ACTIVE_CONTENT_UNIT_NOT_FOUND'; end if;
    if requirement_grade is distinct from content_grade
       or requirement_subject is distinct from content_subject
        then raise exception 'REQUIREMENT_CONTENT_SCOPE_MISMATCH'; end if;

    insert into public.learning_requirement_content_links(
        requirement_code,content_unit_id,relation_type,alignment_strength,rationale,
        source_version_id,status,created_by
    ) values (
        target_requirement_code,target_content_unit_id,target_relation_type,
        target_alignment_strength,coalesce(target_rationale,''),
        nullif(trim(target_source_version_id),''),'ACTIVE',actor
    ) on conflict(requirement_code,content_unit_id,relation_type) do update set
        alignment_strength=excluded.alignment_strength,rationale=excluded.rationale,
        source_version_id=excluded.source_version_id,status='ACTIVE';
    select to_jsonb(row) into result_row from public.learning_requirement_content_links row
     where row.requirement_code=target_requirement_code
       and row.content_unit_id=target_content_unit_id and row.relation_type=target_relation_type;
    insert into public.learning_content_change_log(entity_type,entity_id,operation,after_value,changed_by)
    values ('REQUIREMENT_CONTENT_LINK',target_requirement_code||':'||target_content_unit_id,'LINK',result_row,actor);
    return result_row;
end;
$$;

create or replace view public.assessment_content_context_catalog as
select
    content.content_unit_id,content.content_code,content.title as content_title,
    content.program_id,content.subject_id,content.grade_id,
    req_link.requirement_code,requirement.requirement_text,
    competency_link.competency_indicator_id,indicator.indicator_code,indicator.indicator_text,
    book.textbook_id,book.title as textbook_title,unit_row.textbook_unit_id,
    unit_row.title as textbook_unit_title
from public.canonical_learning_content_units content
left join public.learning_requirement_content_links req_link
  on req_link.content_unit_id=content.content_unit_id and req_link.status='ACTIVE'
left join public.assessment_learning_requirements requirement
  on requirement.requirement_code=req_link.requirement_code
left join public.learning_requirement_competency_links competency_link
  on competency_link.requirement_code=requirement.requirement_code and competency_link.status='ACTIVE'
left join public.competency_indicators indicator
  on indicator.competency_indicator_id=competency_link.competency_indicator_id
left join public.textbook_content_unit_links book_link
  on book_link.content_unit_id=content.content_unit_id and book_link.status='ACTIVE'
left join public.textbook_units unit_row on unit_row.textbook_unit_id=book_link.textbook_unit_id
left join public.textbook_catalog book on book.textbook_id=unit_row.textbook_id
where content.lifecycle_status='ACTIVE';

alter table public.canonical_learning_content_units enable row level security;
alter table public.textbook_content_unit_links enable row level security;
alter table public.learning_requirement_content_links enable row level security;
alter table public.learning_content_change_log enable row level security;

revoke insert,update,delete on public.canonical_learning_content_units,
public.textbook_content_unit_links,public.learning_requirement_content_links,
public.learning_content_change_log from authenticated;
grant select on public.canonical_learning_content_units,public.textbook_content_unit_links,
public.learning_requirement_content_links,public.assessment_content_context_catalog to authenticated;

create policy canonical_learning_content_read on public.canonical_learning_content_units
for select to authenticated using (true);
create policy textbook_content_unit_links_read on public.textbook_content_unit_links
for select to authenticated using (true);
create policy learning_requirement_content_links_read on public.learning_requirement_content_links
for select to authenticated using (true);
create policy learning_content_change_log_admin_read on public.learning_content_change_log
for select to authenticated using (public.current_user_is_portal_admin());

revoke all on function public.save_canonical_learning_content(jsonb) from public;
grant execute on function public.save_canonical_learning_content(jsonb) to authenticated;
revoke all on function public.save_textbook_content_unit_link(text,text,text,text,text,text) from public;
grant execute on function public.save_textbook_content_unit_link(text,text,text,text,text,text) to authenticated;
revoke all on function public.save_learning_requirement_content_link(text,text,text,text,text,text) from public;
grant execute on function public.save_learning_requirement_content_link(text,text,text,text,text,text) to authenticated;

commit;
