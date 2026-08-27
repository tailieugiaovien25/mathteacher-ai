begin;

create table if not exists public.competency_frameworks (
    framework_id text primary key,
    framework_code text not null unique,
    framework_name text not null,
    authority_source_version_id text null references
        public.educational_source_versions(source_version_id) on delete restrict,
    version_number integer not null default 1 check (version_number > 0),
    lifecycle_status text not null default 'DRAFT' check (
        lifecycle_status in ('DRAFT','PENDING_REVIEW','ACTIVE','INACTIVE','SUPERSEDED')
    ),
    metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata)='object'),
    created_by uuid null,
    updated_by uuid null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.competency_domains (
    competency_domain_id text primary key,
    framework_id text not null references
        public.competency_frameworks(framework_id) on delete restrict,
    competency_code text not null,
    competency_name text not null,
    competency_group text not null check (
        competency_group in ('QUALITY','GENERAL','SUBJECT_SPECIFIC','DIGITAL','AI')
    ),
    subject_id text null references public.subjects(subject_id) on delete restrict,
    description text not null default '',
    display_order integer not null default 0 check (display_order >= 0),
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata)='object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(framework_id, competency_code),
    check (
        (competency_group='SUBJECT_SPECIFIC' and subject_id is not null)
        or competency_group <> 'SUBJECT_SPECIFIC'
    )
);

create table if not exists public.competency_components (
    competency_component_id text primary key,
    competency_domain_id text not null references
        public.competency_domains(competency_domain_id) on delete restrict,
    component_code text not null,
    component_name text not null,
    description text not null default '',
    display_order integer not null default 0 check (display_order >= 0),
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata)='object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(competency_domain_id, component_code)
);

create table if not exists public.competency_indicators (
    competency_indicator_id text primary key,
    competency_component_id text not null references
        public.competency_components(competency_component_id) on delete restrict,
    indicator_code text not null,
    indicator_text text not null,
    observable_behavior text not null default '',
    evidence_guidance text not null default '',
    grade_min integer null check (grade_min between 1 and 12),
    grade_max integer null check (grade_max between 1 and 12),
    proficiency_level text not null default 'UNSPECIFIED' check (
        proficiency_level in ('UNSPECIFIED','EMERGING','DEVELOPING','PROFICIENT','ADVANCED')
    ),
    evidence_strength text not null default 'INDIRECT' check (
        evidence_strength in ('DIRECT','INDIRECT','CONTEXTUAL')
    ),
    display_order integer not null default 0 check (display_order >= 0),
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata)='object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(competency_component_id, indicator_code),
    check (grade_min is null or grade_max is null or grade_max >= grade_min)
);

create table if not exists public.learning_requirement_competency_links (
    requirement_competency_link_id uuid primary key default gen_random_uuid(),
    program_code text not null,
    requirement_code text not null references
        public.assessment_learning_requirements(requirement_code)
        on update cascade on delete restrict,
    competency_indicator_id text not null references
        public.competency_indicators(competency_indicator_id) on delete restrict,
    relation_type text not null check (
        relation_type in ('PRIMARY','SUPPORTING','CONTEXTUAL')
    ),
    evidence_strength text not null check (
        evidence_strength in ('DIRECT','INDIRECT','CONTEXTUAL')
    ),
    rationale text not null default '',
    source_version_id text null references
        public.educational_source_versions(source_version_id) on delete restrict,
    status text not null default 'ACTIVE' check (status in ('ACTIVE','INACTIVE')),
    created_by uuid null,
    created_at timestamptz not null default now(),
    unique(program_code, requirement_code, competency_indicator_id)
);

create table if not exists public.competency_change_log (
    change_id uuid primary key default gen_random_uuid(),
    entity_type text not null,
    entity_id text not null,
    operation text not null check (operation in ('CREATE','UPDATE','ACTIVATE','DEACTIVATE')),
    before_value jsonb null,
    after_value jsonb null,
    changed_by uuid not null references auth.users(id) on delete restrict,
    changed_at timestamptz not null default now()
);

create or replace function public.save_canonical_competency_entity(
    target_entity_type text,
    target_payload jsonb
)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
    actor uuid := (select auth.uid());
    entity_id text;
    old_value jsonb;
    new_value jsonb;
begin
    if actor is null then raise exception 'AUTHENTICATION_REQUIRED'; end if;
    if not public.current_user_is_portal_admin() then
        raise exception 'ADMIN_REQUIRED';
    end if;
    if jsonb_typeof(target_payload) <> 'object' then
        raise exception 'COMPETENCY_PAYLOAD_INVALID';
    end if;

    if target_entity_type = 'FRAMEWORK' then
        entity_id := nullif(trim(target_payload->>'framework_id'),'');
        select to_jsonb(row) into old_value from public.competency_frameworks row
         where row.framework_id=entity_id;
        insert into public.competency_frameworks(
            framework_id,framework_code,framework_name,authority_source_version_id,
            version_number,lifecycle_status,metadata,created_by,updated_by
        ) values (
            entity_id,trim(target_payload->>'framework_code'),
            trim(target_payload->>'framework_name'),
            nullif(trim(target_payload->>'authority_source_version_id'),''),
            coalesce((target_payload->>'version_number')::integer,1),
            coalesce(nullif(target_payload->>'lifecycle_status',''),'DRAFT'),
            coalesce(target_payload->'metadata','{}'::jsonb),actor,actor
        ) on conflict(framework_id) do update set
            framework_code=excluded.framework_code,
            framework_name=excluded.framework_name,
            authority_source_version_id=excluded.authority_source_version_id,
            version_number=excluded.version_number,
            lifecycle_status=excluded.lifecycle_status,
            metadata=excluded.metadata,updated_by=actor,updated_at=now();
        select to_jsonb(row) into new_value from public.competency_frameworks row
         where row.framework_id=entity_id;
    elsif target_entity_type = 'DOMAIN' then
        entity_id := nullif(trim(target_payload->>'competency_domain_id'),'');
        select to_jsonb(row) into old_value from public.competency_domains row
         where row.competency_domain_id=entity_id;
        insert into public.competency_domains(
            competency_domain_id,framework_id,competency_code,competency_name,
            competency_group,subject_id,description,display_order,status,metadata
        ) values (
            entity_id,trim(target_payload->>'framework_id'),trim(target_payload->>'competency_code'),
            trim(target_payload->>'competency_name'),trim(target_payload->>'competency_group'),
            nullif(trim(target_payload->>'subject_id'),''),coalesce(target_payload->>'description',''),
            coalesce((target_payload->>'display_order')::integer,0),
            coalesce(nullif(target_payload->>'status',''),'ACTIVE'),
            coalesce(target_payload->'metadata','{}'::jsonb)
        ) on conflict(competency_domain_id) do update set
            framework_id=excluded.framework_id,competency_code=excluded.competency_code,
            competency_name=excluded.competency_name,competency_group=excluded.competency_group,
            subject_id=excluded.subject_id,description=excluded.description,
            display_order=excluded.display_order,status=excluded.status,
            metadata=excluded.metadata,updated_at=now();
        select to_jsonb(row) into new_value from public.competency_domains row
         where row.competency_domain_id=entity_id;
    elsif target_entity_type = 'COMPONENT' then
        entity_id := nullif(trim(target_payload->>'competency_component_id'),'');
        select to_jsonb(row) into old_value from public.competency_components row
         where row.competency_component_id=entity_id;
        insert into public.competency_components(
            competency_component_id,competency_domain_id,component_code,component_name,
            description,display_order,status,metadata
        ) values (
            entity_id,trim(target_payload->>'competency_domain_id'),trim(target_payload->>'component_code'),
            trim(target_payload->>'component_name'),coalesce(target_payload->>'description',''),
            coalesce((target_payload->>'display_order')::integer,0),
            coalesce(nullif(target_payload->>'status',''),'ACTIVE'),
            coalesce(target_payload->'metadata','{}'::jsonb)
        ) on conflict(competency_component_id) do update set
            competency_domain_id=excluded.competency_domain_id,component_code=excluded.component_code,
            component_name=excluded.component_name,description=excluded.description,
            display_order=excluded.display_order,status=excluded.status,
            metadata=excluded.metadata,updated_at=now();
        select to_jsonb(row) into new_value from public.competency_components row
         where row.competency_component_id=entity_id;
    elsif target_entity_type = 'INDICATOR' then
        entity_id := nullif(trim(target_payload->>'competency_indicator_id'),'');
        select to_jsonb(row) into old_value from public.competency_indicators row
         where row.competency_indicator_id=entity_id;
        insert into public.competency_indicators(
            competency_indicator_id,competency_component_id,indicator_code,indicator_text,
            observable_behavior,evidence_guidance,grade_min,grade_max,proficiency_level,
            evidence_strength,display_order,status,metadata
        ) values (
            entity_id,trim(target_payload->>'competency_component_id'),trim(target_payload->>'indicator_code'),
            trim(target_payload->>'indicator_text'),coalesce(target_payload->>'observable_behavior',''),
            coalesce(target_payload->>'evidence_guidance',''),nullif(target_payload->>'grade_min','')::integer,
            nullif(target_payload->>'grade_max','')::integer,
            coalesce(nullif(target_payload->>'proficiency_level',''),'UNSPECIFIED'),
            coalesce(nullif(target_payload->>'evidence_strength',''),'INDIRECT'),
            coalesce((target_payload->>'display_order')::integer,0),
            coalesce(nullif(target_payload->>'status',''),'ACTIVE'),
            coalesce(target_payload->'metadata','{}'::jsonb)
        ) on conflict(competency_indicator_id) do update set
            competency_component_id=excluded.competency_component_id,indicator_code=excluded.indicator_code,
            indicator_text=excluded.indicator_text,observable_behavior=excluded.observable_behavior,
            evidence_guidance=excluded.evidence_guidance,grade_min=excluded.grade_min,
            grade_max=excluded.grade_max,proficiency_level=excluded.proficiency_level,
            evidence_strength=excluded.evidence_strength,display_order=excluded.display_order,
            status=excluded.status,metadata=excluded.metadata,updated_at=now();
        select to_jsonb(row) into new_value from public.competency_indicators row
         where row.competency_indicator_id=entity_id;
    else raise exception 'COMPETENCY_ENTITY_TYPE_INVALID';
    end if;

    if entity_id is null then raise exception 'COMPETENCY_ENTITY_ID_REQUIRED'; end if;
    insert into public.competency_change_log(
        entity_type,entity_id,operation,before_value,after_value,changed_by
    ) values (
        target_entity_type,entity_id,case when old_value is null then 'CREATE' else 'UPDATE' end,
        old_value,new_value,actor
    );
    return new_value;
end;
$$;

create or replace function public.save_learning_requirement_competency_link(
    target_requirement_code text,
    target_competency_indicator_id text,
    target_relation_type text,
    target_evidence_strength text,
    target_rationale text,
    target_source_version_id text default null
)
returns jsonb language plpgsql security definer set search_path=''
as $$
declare
    actor uuid := (select auth.uid());
    requirement_program_code text;
    requirement_grade integer;
    indicator_min integer;
    indicator_max integer;
    result_row jsonb;
begin
    if actor is null then raise exception 'AUTHENTICATION_REQUIRED'; end if;
    if not public.current_user_is_portal_admin() then raise exception 'ADMIN_REQUIRED'; end if;
    if target_relation_type not in ('PRIMARY','SUPPORTING','CONTEXTUAL') then
        raise exception 'REQUIREMENT_COMPETENCY_RELATION_INVALID';
    end if;
    if target_evidence_strength not in ('DIRECT','INDIRECT','CONTEXTUAL') then
        raise exception 'REQUIREMENT_COMPETENCY_EVIDENCE_INVALID';
    end if;

    select program_code,grade_level into requirement_program_code,requirement_grade
      from public.assessment_learning_requirements
     where requirement_code=target_requirement_code and status='ACTIVE';
    if requirement_program_code is null then raise exception 'ACTIVE_REQUIREMENT_NOT_FOUND'; end if;

    select grade_min,grade_max into indicator_min,indicator_max
      from public.competency_indicators
     where competency_indicator_id=target_competency_indicator_id and status='ACTIVE';
    if not found then raise exception 'ACTIVE_COMPETENCY_INDICATOR_NOT_FOUND'; end if;
    if (indicator_min is not null and requirement_grade < indicator_min)
       or (indicator_max is not null and requirement_grade > indicator_max) then
        raise exception 'REQUIREMENT_COMPETENCY_GRADE_MISMATCH';
    end if;

    insert into public.learning_requirement_competency_links(
        program_code,requirement_code,competency_indicator_id,relation_type,
        evidence_strength,rationale,source_version_id,status,created_by
    ) values (
        requirement_program_code,target_requirement_code,target_competency_indicator_id,
        target_relation_type,target_evidence_strength,coalesce(target_rationale,''),
        nullif(trim(target_source_version_id),''),'ACTIVE',actor
    ) on conflict(program_code,requirement_code,competency_indicator_id) do update set
        relation_type=excluded.relation_type,evidence_strength=excluded.evidence_strength,
        rationale=excluded.rationale,source_version_id=excluded.source_version_id,
        status='ACTIVE';

    select to_jsonb(row) into result_row
      from public.learning_requirement_competency_links row
     where row.program_code=requirement_program_code
       and row.requirement_code=target_requirement_code
       and row.competency_indicator_id=target_competency_indicator_id;
    insert into public.competency_change_log(
        entity_type,entity_id,operation,after_value,changed_by
    ) values (
        'REQUIREMENT_LINK',target_requirement_code||':'||target_competency_indicator_id,
        'UPDATE',result_row,actor
    );
    return result_row;
end;
$$;

insert into public.competency_frameworks(
    framework_id,framework_code,framework_name,version_number,lifecycle_status,metadata
) values (
    'framework-vn-gdpt2018-competency-v1','VN-GDPT2018-COMPETENCY-V1',
    'Khung phẩm chất và năng lực Chương trình GDPT 2018',1,'ACTIVE',
    '{"canonical":true,"scope":"multi-subject"}'::jsonb
) on conflict(framework_id) do nothing;

insert into public.competency_domains(
    competency_domain_id,framework_id,competency_code,competency_name,
    competency_group,subject_id,display_order,status
) values
('competency-general-autonomy','framework-vn-gdpt2018-competency-v1','NL-GEN-AUTONOMY','Tự chủ và tự học','GENERAL',null,10,'ACTIVE'),
('competency-general-communication','framework-vn-gdpt2018-competency-v1','NL-GEN-COMMUNICATION','Giao tiếp và hợp tác','GENERAL',null,20,'ACTIVE'),
('competency-general-problem-solving','framework-vn-gdpt2018-competency-v1','NL-GEN-PROBLEM','Giải quyết vấn đề và sáng tạo','GENERAL',null,30,'ACTIVE'),
('competency-math','framework-vn-gdpt2018-competency-v1','NL-MATH','Năng lực toán học','SUBJECT_SPECIFIC','subject-math',40,'ACTIVE'),
('competency-english','framework-vn-gdpt2018-competency-v1','NL-ENG','Năng lực giao tiếp tiếng Anh','SUBJECT_SPECIFIC','subject-foreign-language-1',50,'ACTIVE'),
('competency-digital','framework-vn-gdpt2018-competency-v1','NL-DIGITAL','Năng lực số','DIGITAL',null,60,'ACTIVE'),
('competency-ai','framework-vn-gdpt2018-competency-v1','NL-AI','Năng lực AI','AI',null,70,'ACTIVE')
on conflict(competency_domain_id) do nothing;

alter table public.competency_frameworks enable row level security;
alter table public.competency_domains enable row level security;
alter table public.competency_components enable row level security;
alter table public.competency_indicators enable row level security;
alter table public.learning_requirement_competency_links enable row level security;
alter table public.competency_change_log enable row level security;

revoke insert,update,delete on public.competency_frameworks,
public.competency_domains,public.competency_components,
public.competency_indicators,public.learning_requirement_competency_links,
public.competency_change_log from authenticated;

grant select on public.competency_frameworks,public.competency_domains,
public.competency_components,public.competency_indicators,
public.learning_requirement_competency_links to authenticated;

create policy competency_frameworks_read on public.competency_frameworks
for select to authenticated using (true);
create policy competency_domains_read on public.competency_domains
for select to authenticated using (true);
create policy competency_components_read on public.competency_components
for select to authenticated using (true);
create policy competency_indicators_read on public.competency_indicators
for select to authenticated using (true);
create policy requirement_competency_links_read on public.learning_requirement_competency_links
for select to authenticated using (true);
create policy competency_change_log_admin_read on public.competency_change_log
for select to authenticated using (public.current_user_is_portal_admin());

revoke all on function public.save_canonical_competency_entity(text,jsonb) from public;
grant execute on function public.save_canonical_competency_entity(text,jsonb) to authenticated;
revoke all on function public.save_learning_requirement_competency_link(
    text,text,text,text,text,text
) from public;
grant execute on function public.save_learning_requirement_competency_link(
    text,text,text,text,text,text
) to authenticated;

commit;
