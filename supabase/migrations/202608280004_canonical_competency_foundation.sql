-- Canonical Competency Foundation V1 - Backbone-compatible revision
-- Integrates NLC + MATH + ENG + DIG + AI into the existing Educational Data Backbone.
-- IMPORTANT: reuses the existing Framework -> Domain -> Component -> Indicator hierarchy.
-- Additive: preserves existing competency_* rows and assessment_mathematical_competencies.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Compatibility layer: preserve existing physical keys while exposing the
-- canonical contract required by the competency catalog/admin application.
-- ---------------------------------------------------------------------------

alter table public.competency_frameworks
    add column if not exists canonical_code text,
    add column if not exists framework_type text,
    add column if not exists subject_id text null references public.subjects(subject_id) on delete restrict,
    add column if not exists version_label text,
    add column if not exists provenance_status text,
    add column if not exists status text;

update public.competency_frameworks
set canonical_code = coalesce(canonical_code, framework_code),
    framework_type = coalesce(framework_type, metadata->>'framework_type', 'LEGACY'),
    subject_id = subject_id,
    version_label = coalesce(version_label, version_number::text, '1.0'),
    provenance_status = coalesce(provenance_status, metadata->>'provenance_status', 'LEGACY_MIGRATED'),
    status = coalesce(status, lifecycle_status, 'ACTIVE')
where canonical_code is null
   or framework_type is null
   or version_label is null
   or provenance_status is null
   or status is null;

create unique index if not exists competency_frameworks_canonical_code_uq
    on public.competency_frameworks(canonical_code)
    where canonical_code is not null;

create or replace function public.sync_competency_framework_compat()
returns trigger
language plpgsql
set search_path=public
as $$
begin
    if tg_op = 'INSERT' then
        new.canonical_code := coalesce(nullif(new.canonical_code,''), nullif(new.framework_code,''));
        new.framework_code := coalesce(nullif(new.framework_code,''), nullif(new.canonical_code,''));
        new.framework_type := coalesce(nullif(new.framework_type,''), new.metadata->>'framework_type', 'LEGACY');
        new.version_label := coalesce(nullif(new.version_label,''), new.version_number::text, '1.0');
        new.provenance_status := coalesce(nullif(new.provenance_status,''), new.metadata->>'provenance_status', 'REVIEWED');
        new.status := coalesce(nullif(new.status,''), nullif(new.lifecycle_status,''), 'ACTIVE');
        new.lifecycle_status := coalesce(nullif(new.status,''), nullif(new.lifecycle_status,''), 'ACTIVE');
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'framework_type', new.framework_type,
                'subject_id', new.subject_id,
                'version_label', new.version_label,
                'provenance_status', new.provenance_status
            ));
    else
        if new.canonical_code is distinct from old.canonical_code then
            new.framework_code := new.canonical_code;
        elsif new.framework_code is distinct from old.framework_code then
            new.canonical_code := new.framework_code;
        end if;
        if new.status is distinct from old.status then
            new.lifecycle_status := new.status;
        elsif new.lifecycle_status is distinct from old.lifecycle_status then
            new.status := new.lifecycle_status;
        end if;
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'framework_type', new.framework_type,
                'subject_id', new.subject_id,
                'version_label', new.version_label,
                'provenance_status', new.provenance_status
            ));
    end if;
    return new;
end;
$$;

drop trigger if exists competency_frameworks_compat_trigger on public.competency_frameworks;
create trigger competency_frameworks_compat_trigger
before insert or update on public.competency_frameworks
for each row execute function public.sync_competency_framework_compat();

alter table public.competency_components
    add column if not exists component_id text,
    add column if not exists framework_id text null references public.competency_frameworks(framework_id) on delete restrict,
    add column if not exists canonical_code text,
    add column if not exists source_code text,
    add column if not exists parent_component_id text,
    add column if not exists sequence_number integer;

update public.competency_components c
set component_id = coalesce(c.component_id, c.competency_component_id),
    framework_id = coalesce(c.framework_id, d.framework_id),
    canonical_code = coalesce(c.canonical_code, c.component_code),
    source_code = coalesce(c.source_code, nullif(c.metadata->>'source_code','')),
    sequence_number = coalesce(c.sequence_number, c.display_order, 0)
from public.competency_domains d
where d.competency_domain_id = c.competency_domain_id
  and (c.component_id is null
       or c.framework_id is null
       or c.canonical_code is null
       or c.sequence_number is null);

create unique index if not exists competency_components_component_id_uq
    on public.competency_components(component_id);

create unique index if not exists competency_components_framework_canonical_uq
    on public.competency_components(framework_id,canonical_code)
    where framework_id is not null and canonical_code is not null;

create or replace function public.sync_competency_component_compat()
returns trigger
language plpgsql
set search_path=public
as $$
declare
    resolved_domain_id text;
begin
    if tg_op = 'INSERT' then
        new.component_id := coalesce(nullif(new.component_id,''), nullif(new.competency_component_id,''));
        new.competency_component_id := coalesce(nullif(new.competency_component_id,''), nullif(new.component_id,''));
        new.canonical_code := coalesce(nullif(new.canonical_code,''), nullif(new.component_code,''));
        new.component_code := coalesce(nullif(new.component_code,''), nullif(new.canonical_code,''));
        new.sequence_number := coalesce(new.sequence_number, new.display_order, 0);
        new.display_order := coalesce(new.display_order, new.sequence_number, 0);

        if new.framework_id is null and new.competency_domain_id is not null then
            select d.framework_id into new.framework_id
            from public.competency_domains d
            where d.competency_domain_id = new.competency_domain_id;
        end if;

        if new.competency_domain_id is null and new.framework_id is not null then
            select d.competency_domain_id into resolved_domain_id
            from public.competency_domains d
            where d.framework_id = new.framework_id
            order by
                case when coalesce(d.metadata->>'canonical_v74_root','false')='true' then 0 else 1 end,
                d.display_order,
                d.competency_domain_id
            limit 1;
            new.competency_domain_id := resolved_domain_id;
        end if;

        new.source_code := coalesce(new.source_code, nullif(new.metadata->>'source_code',''));
        new.description := coalesce(new.description, '');
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'canonical_code', new.canonical_code,
                'source_code', new.source_code,
                'framework_id', new.framework_id,
                'parent_component_id', new.parent_component_id,
                'sequence_number', new.sequence_number
            ));
    else
        if new.component_id is distinct from old.component_id then
            new.competency_component_id := new.component_id;
        elsif new.competency_component_id is distinct from old.competency_component_id then
            new.component_id := new.competency_component_id;
        end if;
        if new.canonical_code is distinct from old.canonical_code then
            new.component_code := new.canonical_code;
        elsif new.component_code is distinct from old.component_code then
            new.canonical_code := new.component_code;
        end if;
        if new.sequence_number is distinct from old.sequence_number then
            new.display_order := new.sequence_number;
        elsif new.display_order is distinct from old.display_order then
            new.sequence_number := new.display_order;
        end if;
        if new.framework_id is distinct from old.framework_id then
            select d.competency_domain_id into resolved_domain_id
            from public.competency_domains d
            where d.framework_id = new.framework_id
            order by
                case when coalesce(d.metadata->>'canonical_v74_root','false')='true' then 0 else 1 end,
                d.display_order,
                d.competency_domain_id
            limit 1;
            new.competency_domain_id := resolved_domain_id;
        elsif new.competency_domain_id is distinct from old.competency_domain_id then
            select d.framework_id into new.framework_id
            from public.competency_domains d
            where d.competency_domain_id = new.competency_domain_id;
        end if;
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'canonical_code', new.canonical_code,
                'source_code', new.source_code,
                'framework_id', new.framework_id,
                'parent_component_id', new.parent_component_id,
                'sequence_number', new.sequence_number
            ));
    end if;
    return new;
end;
$$;

drop trigger if exists competency_components_compat_trigger on public.competency_components;
create trigger competency_components_compat_trigger
before insert or update on public.competency_components
for each row execute function public.sync_competency_component_compat();

alter table public.competency_indicators
    add column if not exists indicator_id text,
    add column if not exists framework_id text null references public.competency_frameworks(framework_id) on delete restrict,
    add column if not exists component_id text,
    add column if not exists canonical_code text,
    add column if not exists source_code text,
    add column if not exists indicator_name text,
    add column if not exists observable_flag boolean,
    add column if not exists assessable_flag boolean,
    add column if not exists version_label text,
    add column if not exists provenance_status text,
    add column if not exists replaced_by_indicator_id text,
    add column if not exists created_by uuid null references auth.users(id) on delete set null,
    add column if not exists updated_by uuid null references auth.users(id) on delete set null;

update public.competency_indicators i
set indicator_id = coalesce(i.indicator_id, i.competency_indicator_id),
    framework_id = coalesce(i.framework_id, d.framework_id),
    component_id = coalesce(i.component_id, i.competency_component_id),
    canonical_code = coalesce(i.canonical_code, i.indicator_code),
    source_code = coalesce(i.source_code, nullif(i.metadata->>'source_code','')),
    indicator_name = coalesce(i.indicator_name, nullif(i.metadata->>'indicator_name',''), i.indicator_text),
    observable_flag = coalesce(i.observable_flag, true),
    assessable_flag = coalesce(i.assessable_flag, true),
    version_label = coalesce(i.version_label, nullif(i.metadata->>'version_label',''), '1.0'),
    provenance_status = coalesce(i.provenance_status, nullif(i.metadata->>'provenance_status',''), 'LEGACY_MIGRATED')
from public.competency_components c
join public.competency_domains d on d.competency_domain_id = c.competency_domain_id
where c.competency_component_id = i.competency_component_id
  and (i.indicator_id is null
       or i.framework_id is null
       or i.component_id is null
       or i.canonical_code is null
       or i.indicator_name is null
       or i.observable_flag is null
       or i.assessable_flag is null
       or i.version_label is null
       or i.provenance_status is null);

create unique index if not exists competency_indicators_indicator_id_uq
    on public.competency_indicators(indicator_id);

create index if not exists competency_indicators_framework_status_idx
    on public.competency_indicators(framework_id,status,canonical_code);

create or replace function public.sync_competency_indicator_compat()
returns trigger
language plpgsql
set search_path=public
as $$
begin
    if tg_op = 'INSERT' then
        new.indicator_id := coalesce(nullif(new.indicator_id,''), nullif(new.competency_indicator_id,''));
        new.competency_indicator_id := coalesce(nullif(new.competency_indicator_id,''), nullif(new.indicator_id,''));
        new.component_id := coalesce(nullif(new.component_id,''), nullif(new.competency_component_id,''));
        new.competency_component_id := coalesce(nullif(new.competency_component_id,''), nullif(new.component_id,''));
        new.canonical_code := coalesce(nullif(new.canonical_code,''), nullif(new.indicator_code,''));
        new.indicator_code := coalesce(nullif(new.indicator_code,''), nullif(new.canonical_code,''));

        if new.framework_id is null and new.competency_component_id is not null then
            select d.framework_id into new.framework_id
            from public.competency_components c
            join public.competency_domains d on d.competency_domain_id = c.competency_domain_id
            where c.competency_component_id = new.competency_component_id;
        end if;

        new.indicator_name := coalesce(nullif(new.indicator_name,''), nullif(new.metadata->>'indicator_name',''), new.indicator_text);
        new.observable_flag := coalesce(new.observable_flag, true);
        new.assessable_flag := coalesce(new.assessable_flag, true);
        new.version_label := coalesce(nullif(new.version_label,''), nullif(new.metadata->>'version_label',''), '1.0');
        new.provenance_status := coalesce(nullif(new.provenance_status,''), nullif(new.metadata->>'provenance_status',''), 'REVIEWED');
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'indicator_name', new.indicator_name,
                'source_code', new.source_code,
                'observable_flag', new.observable_flag,
                'assessable_flag', new.assessable_flag,
                'version_label', new.version_label,
                'provenance_status', new.provenance_status,
                'framework_id', new.framework_id,
                'component_id', new.component_id
            ));
    else
        if new.indicator_id is distinct from old.indicator_id then
            new.competency_indicator_id := new.indicator_id;
        elsif new.competency_indicator_id is distinct from old.competency_indicator_id then
            new.indicator_id := new.competency_indicator_id;
        end if;
        if new.component_id is distinct from old.component_id then
            new.competency_component_id := new.component_id;
        elsif new.competency_component_id is distinct from old.competency_component_id then
            new.component_id := new.competency_component_id;
        end if;
        if new.canonical_code is distinct from old.canonical_code then
            new.indicator_code := new.canonical_code;
        elsif new.indicator_code is distinct from old.indicator_code then
            new.canonical_code := new.indicator_code;
        end if;
        if new.competency_component_id is distinct from old.competency_component_id then
            select d.framework_id into new.framework_id
            from public.competency_components c
            join public.competency_domains d on d.competency_domain_id = c.competency_domain_id
            where c.competency_component_id = new.competency_component_id;
        end if;
        new.metadata := coalesce(new.metadata,'{}'::jsonb) ||
            jsonb_strip_nulls(jsonb_build_object(
                'indicator_name', new.indicator_name,
                'source_code', new.source_code,
                'observable_flag', new.observable_flag,
                'assessable_flag', new.assessable_flag,
                'version_label', new.version_label,
                'provenance_status', new.provenance_status,
                'framework_id', new.framework_id,
                'component_id', new.component_id
            ));
    end if;
    return new;
end;
$$;

drop trigger if exists competency_indicators_compat_trigger on public.competency_indicators;
create trigger competency_indicators_compat_trigger
before insert or update on public.competency_indicators
for each row execute function public.sync_competency_indicator_compat();

create table if not exists public.competency_grade_descriptors (
    descriptor_id text primary key,
    indicator_id text not null references public.competency_indicators(indicator_id) on delete restrict,
    grade_id text not null references public.grades(grade_id) on delete restrict,
    canonical_code text not null unique,
    descriptor_text text not null,
    version_label text not null default '1.0',
    provenance_status text not null default 'UNVERIFIED',
    status text not null default 'DRAFT' check (status in ('DRAFT','REVIEWED','ACTIVE','DEPRECATED','INACTIVE')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(indicator_id, grade_id, version_label)
);

create table if not exists public.competency_descriptor_constraints (
    constraint_id text primary key,
    descriptor_id text null references public.competency_grade_descriptors(descriptor_id) on delete restrict,
    grade_id text not null references public.grades(grade_id) on delete restrict,
    skill_code text null,
    constraint_type text not null,
    min_value numeric null,
    max_value numeric null,
    unit text null,
    applies_to text null,
    source_requirement_code text null references public.assessment_learning_requirements(requirement_code) on delete set null,
    verification_status text not null default 'UNVERIFIED',
    version_label text not null default '1.0',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.competency_requirement_links (
    requirement_code text not null references public.assessment_learning_requirements(requirement_code) on delete cascade,
    indicator_id text not null references public.competency_indicators(indicator_id) on delete restrict,
    descriptor_id text null references public.competency_grade_descriptors(descriptor_id) on delete restrict,
    mapping_type text not null check(mapping_type in ('DIRECT','PARTIAL','SUPPORTING','DERIVED')),
    mapping_confidence numeric(4,3) null check(mapping_confidence is null or (mapping_confidence >= 0 and mapping_confidence <= 1)),
    mapping_note text not null default '',
    review_status text not null default 'PENDING' check(review_status in ('PENDING','REVIEWED','VERIFIED')),
    reviewed_by uuid null references auth.users(id) on delete set null,
    reviewed_at timestamptz null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key(requirement_code, indicator_id)
);

create table if not exists public.competency_aliases (
    alias_id text primary key,
    indicator_id text not null references public.competency_indicators(indicator_id) on delete restrict,
    alias_code text not null unique,
    alias_kind text not null default 'LEGACY',
    source_reference text null,
    status text not null default 'ACTIVE' check(status in ('ACTIVE','INACTIVE','DEPRECATED')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.competency_projection_mappings (
    projection_mapping_id text primary key,
    projection_scope text not null,
    external_code text not null,
    framework_id text not null references public.competency_frameworks(framework_id) on delete restrict,
    component_id text null references public.competency_components(component_id) on delete restrict,
    indicator_id text null references public.competency_indicators(indicator_id) on delete restrict,
    relation_type text not null default 'EQUIVALENT_OR_BROADER',
    status text not null default 'ACTIVE' check(status in ('ACTIVE','INACTIVE','DEPRECATED')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique(projection_scope, external_code),
    check(component_id is not null or indicator_id is not null)
);

create table if not exists public.competency_crosswalks (
    crosswalk_id text primary key,
    source_reference text not null,
    target_reference text not null,
    relation_type text not null default 'RELATED',
    notes text not null default '',
    status text not null default 'ACTIVE' check(status in ('ACTIVE','INACTIVE','DEPRECATED')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.competency_audit_log (
    audit_id uuid primary key default gen_random_uuid(),
    entity_type text not null,
    entity_id text not null,
    action text not null,
    changed_by uuid null references auth.users(id) on delete set null,
    reason text null,
    before_data jsonb null,
    after_data jsonb null,
    changed_at timestamptz not null default now()
);

create index if not exists competency_grade_descriptors_indicator_grade_idx on public.competency_grade_descriptors(indicator_id,grade_id,status);
create index if not exists competency_requirement_links_requirement_idx on public.competency_requirement_links(requirement_code,review_status);

insert into public.competency_frameworks(framework_id,canonical_code,framework_name,framework_type,subject_id,version_label,provenance_status,status,metadata)
values ('framework-nlc','NLC','Năng lực chung','GENERAL',NULL,'1.0','REVIEWED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(framework_id) do update set canonical_code=excluded.canonical_code, framework_name=excluded.framework_name, framework_type=excluded.framework_type, subject_id=excluded.subject_id, version_label=excluded.version_label, provenance_status=excluded.provenance_status, status=excluded.status, metadata=coalesce(public.competency_frameworks.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_frameworks(framework_id,canonical_code,framework_name,framework_type,subject_id,version_label,provenance_status,status,metadata)
values ('framework-math','MATH','Năng lực đặc thù môn Toán','SUBJECT_SPECIFIC','subject-math','1.0','REVIEWED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(framework_id) do update set canonical_code=excluded.canonical_code, framework_name=excluded.framework_name, framework_type=excluded.framework_type, subject_id=excluded.subject_id, version_label=excluded.version_label, provenance_status=excluded.provenance_status, status=excluded.status, metadata=coalesce(public.competency_frameworks.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_frameworks(framework_id,canonical_code,framework_name,framework_type,subject_id,version_label,provenance_status,status,metadata)
values ('framework-eng','ENG','Năng lực đặc thù môn Tiếng Anh','SUBJECT_SPECIFIC','subject-foreign-language-1','1.0','REVIEWED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(framework_id) do update set canonical_code=excluded.canonical_code, framework_name=excluded.framework_name, framework_type=excluded.framework_type, subject_id=excluded.subject_id, version_label=excluded.version_label, provenance_status=excluded.provenance_status, status=excluded.status, metadata=coalesce(public.competency_frameworks.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_frameworks(framework_id,canonical_code,framework_name,framework_type,subject_id,version_label,provenance_status,status,metadata)
values ('framework-dig','DIG','Năng lực số','DIGITAL',NULL,'1.0','REVIEWED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(framework_id) do update set canonical_code=excluded.canonical_code, framework_name=excluded.framework_name, framework_type=excluded.framework_type, subject_id=excluded.subject_id, version_label=excluded.version_label, provenance_status=excluded.provenance_status, status=excluded.status, metadata=coalesce(public.competency_frameworks.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_frameworks(framework_id,canonical_code,framework_name,framework_type,subject_id,version_label,provenance_status,status,metadata)
values ('framework-ai','AI','Năng lực AI','AI',NULL,'1.0','REVIEWED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(framework_id) do update set canonical_code=excluded.canonical_code, framework_name=excluded.framework_name, framework_type=excluded.framework_type, subject_id=excluded.subject_id, version_label=excluded.version_label, provenance_status=excluded.provenance_status, status=excluded.status, metadata=coalesce(public.competency_frameworks.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();

-- Canonical root domains bridge the canonical framework catalog into the
-- existing Framework -> Domain -> Component hierarchy.
insert into public.competency_domains(
    competency_domain_id,framework_id,subject_id,competency_group,
    competency_code,competency_name,description,status,display_order,metadata
)
values
('domain-canonical-nlc','framework-nlc',NULL,'GENERAL','NLC','Năng lực chung','Miền canonical NLC','ACTIVE',10,'{"canonical_v74_root":true}'::jsonb),
('domain-canonical-math','framework-math','subject-math','SUBJECT_SPECIFIC','MATH','Năng lực đặc thù môn Toán','Miền canonical MATH','ACTIVE',20,'{"canonical_v74_root":true}'::jsonb),
('domain-canonical-eng','framework-eng','subject-foreign-language-1','SUBJECT_SPECIFIC','ENG','Năng lực đặc thù môn Tiếng Anh','Miền canonical ENG','ACTIVE',30,'{"canonical_v74_root":true}'::jsonb),
('domain-canonical-dig','framework-dig',NULL,'DIGITAL','DIG','Năng lực số','Miền canonical DIG','ACTIVE',40,'{"canonical_v74_root":true}'::jsonb),
('domain-canonical-ai','framework-ai',NULL,'AI','AI','Năng lực AI','Miền canonical AI','ACTIVE',50,'{"canonical_v74_root":true}'::jsonb)
on conflict(competency_domain_id) do update set
    framework_id=excluded.framework_id,
    subject_id=excluded.subject_id,
    competency_group=excluded.competency_group,
    competency_code=excluded.competency_code,
    competency_name=excluded.competency_name,
    description=excluded.description,
    status=excluded.status,
    display_order=excluded.display_order,
    metadata=coalesce(public.competency_domains.metadata,'{}'::jsonb) || excluded.metadata,
    updated_at=now();

insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-nlc-001','framework-nlc','NLC.TCTH','TC-TH','Tự chủ và tự học',1,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-nlc-002','framework-nlc','NLC.GTHT','GT-HT','Giao tiếp và hợp tác',2,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-nlc-003','framework-nlc','NLC.GQVDST','GQVĐ-ST','Giải quyết vấn đề và sáng tạo',3,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-math-004','framework-math','MATH.TD','TD','Tư duy và lập luận toán học',4,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-math-005','framework-math','MATH.MHH','MHH','Mô hình hóa toán học',5,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-math-006','framework-math','MATH.GQVD','GQVĐ','Giải quyết vấn đề toán học',6,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-math-007','framework-math','MATH.GT','GT','Giao tiếp toán học',7,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-math-008','framework-math','MATH.CC','CC','Sử dụng công cụ, phương tiện học toán',8,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-009','framework-dig','DIG.1.1','1.1','Duyệt, tìm kiếm và lọc dữ liệu, thông tin và nội dung số',9,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-010','framework-dig','DIG.1.2','1.2','Đánh giá dữ liệu, thông tin và nội dung số',10,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-011','framework-dig','DIG.1.3','1.3','Quản lý dữ liệu, thông tin và nội dung số',11,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-012','framework-dig','DIG.2.1','2.1','Tương tác thông qua công nghệ số',12,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-013','framework-dig','DIG.2.2','2.2','Chia sẻ thông tin và nội dung thông qua công nghệ số',13,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-014','framework-dig','DIG.2.3','2.3','Tham gia với tư cách công dân thông qua công nghệ số',14,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-015','framework-dig','DIG.2.4','2.4','Hợp tác thông qua công nghệ số',15,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-016','framework-dig','DIG.2.5','2.5','Chuẩn mực giao tiếp',16,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-017','framework-dig','DIG.2.6','2.6','Quản lý danh tính số',17,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-018','framework-dig','DIG.3.1','3.1','Phát triển nội dung số',18,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-019','framework-dig','DIG.3.2','3.2','Tích hợp và tái tạo nội dung số',19,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-020','framework-dig','DIG.3.3','3.3','Bản quyền và giấy phép',20,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-021','framework-dig','DIG.3.4','3.4','Lập trình',21,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-022','framework-dig','DIG.4.1','4.1','Bảo vệ thiết bị',22,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-023','framework-dig','DIG.4.2','4.2','Bảo vệ dữ liệu cá nhân và quyền riêng tư',23,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-024','framework-dig','DIG.4.3','4.3','Bảo vệ sức khỏe và an sinh',24,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-025','framework-dig','DIG.4.4','4.4','Bảo vệ môi trường',25,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-026','framework-dig','DIG.5.1','5.1','Giải quyết vấn đề kĩ thuật',26,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-027','framework-dig','DIG.5.2','5.2','Xác định nhu cầu và giải pháp công nghệ',27,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-028','framework-dig','DIG.5.3','5.3','Sử dụng sáng tạo công nghệ số',28,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-029','framework-dig','DIG.5.4','5.4','Xác định khoảng trống năng lực số',29,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-030','framework-dig','DIG.6.1','6.1','Hiểu biết về trí tuệ nhân tạo',30,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-031','framework-dig','DIG.6.2','6.2','Sử dụng trí tuệ nhân tạo',31,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-dig-032','framework-dig','DIG.6.3','6.3','Đánh giá trí tuệ nhân tạo',32,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-ai-033','framework-ai','AI.NLa','NLa / A','Tư duy lấy con người làm trung tâm',33,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-ai-034','framework-ai','AI.NLb','NLb / B','Đạo đức AI',34,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-ai-035','framework-ai','AI.NLc','NLc / C','Các kĩ thuật và ứng dụng AI',35,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-ai-036','framework-ai','AI.NLd','NLd / D','Thiết kế hệ thống AI',36,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-eng-037','framework-eng','ENG.COM.L','L','Listening / Nghe',37,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-eng-038','framework-eng','ENG.COM.S','S','Speaking / Nói',38,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-eng-039','framework-eng','ENG.COM.R','R','Reading / Đọc',39,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_components(component_id,framework_id,canonical_code,source_code,component_name,sequence_number,status,metadata)
values ('comp-eng-040','framework-eng','ENG.COM.W','W','Writing / Viết',40,'ACTIVE','{"system_default":true}'::jsonb)
on conflict(component_id) do update set framework_id=excluded.framework_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, component_name=excluded.component_name, sequence_number=excluded.sequence_number, status=excluded.status, metadata=coalesce(public.competency_components.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0001','framework-nlc','comp-nlc-001','NLC.TCTH.I01','TC-TH','Tự chủ và tự học','Tự thực hiện nhiệm vụ học tập phù hợp với khả năng và điều kiện của bản thân.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0002','framework-nlc','comp-nlc-001','NLC.TCTH.I02','TC-TH','Tự chủ và tự học','Xác định được mục tiêu học tập và lập kế hoạch thực hiện nhiệm vụ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0003','framework-nlc','comp-nlc-001','NLC.TCTH.I03','TC-TH','Tự chủ và tự học','Chủ động tìm kiếm, lựa chọn và sử dụng nguồn học liệu phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0004','framework-nlc','comp-nlc-001','NLC.TCTH.I04','TC-TH','Tự chủ và tự học','Tự kiểm tra, nhận ra sai sót và điều chỉnh cách học hoặc cách thực hiện nhiệm vụ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0005','framework-nlc','comp-nlc-001','NLC.TCTH.I05','TC-TH','Tự chủ và tự học','Đánh giá được điểm mạnh, điểm hạn chế của bản thân trong học tập và hoạt động.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0006','framework-nlc','comp-nlc-001','NLC.TCTH.I06','TC-TH','Tự chủ và tự học','Vận dụng điều đã học để giải quyết nhiệm vụ mới và hình thành thói quen tự học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0007','framework-nlc','comp-nlc-002','NLC.GTHT.I01','GT-HT','Giao tiếp và hợp tác','Xác định được mục đích, nội dung, phương tiện và thái độ giao tiếp phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0008','framework-nlc','comp-nlc-002','NLC.GTHT.I02','GT-HT','Giao tiếp và hợp tác','Trình bày ý kiến rõ ràng; biết lắng nghe, phản hồi và tôn trọng ý kiến khác biệt.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0009','framework-nlc','comp-nlc-002','NLC.GTHT.I03','GT-HT','Giao tiếp và hợp tác','Hiểu nhiệm vụ của nhóm và nhận trách nhiệm phù hợp với bản thân.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0010','framework-nlc','comp-nlc-002','NLC.GTHT.I04','GT-HT','Giao tiếp và hợp tác','Phối hợp, chia sẻ thông tin và hỗ trợ thành viên để hoàn thành nhiệm vụ chung.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0011','framework-nlc','comp-nlc-002','NLC.GTHT.I05','GT-HT','Giao tiếp và hợp tác','Nhận biết, xử lí bất đồng theo hướng xây dựng và có căn cứ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0012','framework-nlc','comp-nlc-002','NLC.GTHT.I06','GT-HT','Giao tiếp và hợp tác','Tự đánh giá và tham gia đánh giá hiệu quả giao tiếp, hợp tác của nhóm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0013','framework-nlc','comp-nlc-003','NLC.GQVDST.I01','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Nhận biết, phát hiện và diễn đạt được vấn đề cần giải quyết.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0014','framework-nlc','comp-nlc-003','NLC.GQVDST.I02','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Thu thập, phân tích và lựa chọn thông tin có liên quan đến vấn đề.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0015','framework-nlc','comp-nlc-003','NLC.GQVDST.I03','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Đề xuất được một hoặc nhiều phương án/ý tưởng giải quyết.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0016','framework-nlc','comp-nlc-003','NLC.GQVDST.I04','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Lựa chọn và thực hiện giải pháp có căn cứ, phù hợp điều kiện.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0017','framework-nlc','comp-nlc-003','NLC.GQVDST.I05','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Đánh giá kết quả, phát hiện hạn chế và điều chỉnh giải pháp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-nlc-0018','framework-nlc','comp-nlc-003','NLC.GQVDST.I06','GQVĐ-ST','Giải quyết vấn đề và sáng tạo','Đề xuất cách tiếp cận, sản phẩm hoặc phương án mới trên cơ sở kiến thức và kinh nghiệm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0019','framework-math','comp-math-004','MATH.TD.I01','TD','Tư duy và lập luận toán học','Thực hiện các thao tác tư duy: so sánh, phân tích, tổng hợp, đặc biệt hóa, khái quát hóa, tương tự, quy nạp hoặc diễn dịch.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0020','framework-math','comp-math-004','MATH.TD.I02','TD','Tư duy và lập luận toán học','Quan sát, nhận ra và giải thích sự tương đồng/khác biệt trong tình huống toán học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0021','framework-math','comp-math-004','MATH.TD.I03','TD','Tư duy và lập luận toán học','Chỉ ra chứng cứ, lí lẽ và thực hiện lập luận hợp lí trước khi kết luận.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0022','framework-math','comp-math-004','MATH.TD.I04','TD','Tư duy và lập luận toán học','Nêu và trả lời câu hỏi trong quá trình lập luận, giải quyết vấn đề.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0023','framework-math','comp-math-004','MATH.TD.I05','TD','Tư duy và lập luận toán học','Giải thích, kiểm tra hoặc điều chỉnh cách giải quyết về phương diện toán học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0024','framework-math','comp-math-005','MATH.MHH.I01','MHH','Mô hình hóa toán học','Xác định được các đại lượng, quan hệ và giả thiết quan trọng của tình huống thực tiễn.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0025','framework-math','comp-math-005','MATH.MHH.I02','MHH','Mô hình hóa toán học','Thiết lập được mô hình toán học bằng công thức, phương trình, bảng, biểu đồ, hình vẽ, sơ đồ hoặc cấu trúc toán học phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0026','framework-math','comp-math-005','MATH.MHH.I03','MHH','Mô hình hóa toán học','Thực hiện được các thao tác/giải pháp toán học trên mô hình đã thiết lập.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0027','framework-math','comp-math-005','MATH.MHH.I04','MHH','Mô hình hóa toán học','Diễn giải kết quả toán học trở lại bối cảnh thực tiễn.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0028','framework-math','comp-math-005','MATH.MHH.I05','MHH','Mô hình hóa toán học','Kiểm tra tính hợp lí của kết quả, nhận biết giới hạn của mô hình và điều chỉnh khi cần.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0029','framework-math','comp-math-006','MATH.GQVD.I01','GQVĐ','Giải quyết vấn đề toán học','Nhận biết và phát hiện được vấn đề cần giải quyết bằng toán học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0030','framework-math','comp-math-006','MATH.GQVD.I02','GQVĐ','Giải quyết vấn đề toán học','Xác định, thu thập và sắp xếp kiến thức/thông tin toán học liên quan.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0031','framework-math','comp-math-006','MATH.GQVD.I03','GQVĐ','Giải quyết vấn đề toán học','Đề xuất và lựa chọn được cách thức hoặc giải pháp giải quyết vấn đề.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0032','framework-math','comp-math-006','MATH.GQVD.I04','GQVĐ','Giải quyết vấn đề toán học','Thực hiện được giải pháp và trình bày quá trình giải quyết.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0033','framework-math','comp-math-006','MATH.GQVD.I05','GQVĐ','Giải quyết vấn đề toán học','Kiểm tra, đánh giá, khái quát hóa hoặc mở rộng giải pháp/kết quả.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0034','framework-math','comp-math-007','MATH.GT.I01','GT','Giao tiếp toán học','Nghe, đọc và ghi chép được thông tin toán học cần thiết từ văn bản hoặc trao đổi.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0035','framework-math','comp-math-007','MATH.GT.I02','GT','Giao tiếp toán học','Trình bày, diễn đạt được ý tưởng, giải pháp và kết quả toán học rõ ràng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0036','framework-math','comp-math-007','MATH.GT.I03','GT','Giao tiếp toán học','Sử dụng đúng và linh hoạt ngôn ngữ toán học kết hợp ngôn ngữ thông thường.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0037','framework-math','comp-math-007','MATH.GT.I04','GT','Giao tiếp toán học','Sử dụng biểu diễn toán học như kí hiệu, bảng, biểu đồ, sơ đồ, hình vẽ để giao tiếp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0038','framework-math','comp-math-007','MATH.GT.I05','GT','Giao tiếp toán học','Trao đổi, đặt câu hỏi, phản biện và bảo vệ lập luận toán học có căn cứ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0039','framework-math','comp-math-008','MATH.CC.I01','CC','Sử dụng công cụ, phương tiện học toán','Nhận biết tên gọi, tác dụng, quy cách sử dụng và bảo quản công cụ/phương tiện học toán.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0040','framework-math','comp-math-008','MATH.CC.I02','CC','Sử dụng công cụ, phương tiện học toán','Sử dụng công cụ, phương tiện hoặc phần mềm phù hợp để khám phá, biểu diễn và giải quyết nhiệm vụ toán học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0041','framework-math','comp-math-008','MATH.CC.I03','CC','Sử dụng công cụ, phương tiện học toán','Sử dụng công cụ để kiểm tra, đo đạc, tính toán hoặc xác minh kết quả.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0042','framework-math','comp-math-008','MATH.CC.I04','CC','Sử dụng công cụ, phương tiện học toán','Nhận biết ưu điểm, hạn chế và lựa chọn công cụ/phương tiện phù hợp với nhiệm vụ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-math-0043','framework-math','comp-math-008','MATH.CC.I05','CC','Sử dụng công cụ, phương tiện học toán','Sử dụng công cụ an toàn, chính xác và có trách nhiệm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0044','framework-dig','comp-dig-009','DIG.1.1.I01','1.1','Duyệt, tìm kiếm và lọc dữ liệu, thông tin và nội dung số','Xác định nhu cầu thông tin và từ khóa/chiến lược tìm kiếm phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0045','framework-dig','comp-dig-009','DIG.1.1.I02','1.1','Duyệt, tìm kiếm và lọc dữ liệu, thông tin và nội dung số','Thực hiện tìm kiếm, duyệt và lọc dữ liệu, thông tin, nội dung số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0046','framework-dig','comp-dig-009','DIG.1.1.I03','1.1','Duyệt, tìm kiếm và lọc dữ liệu, thông tin và nội dung số','Điều chỉnh chiến lược tìm kiếm để thu được kết quả phù hợp hơn.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0047','framework-dig','comp-dig-010','DIG.1.2.I01','1.2','Đánh giá dữ liệu, thông tin và nội dung số','Xem xét nguồn, tác giả, thời điểm và bằng chứng của thông tin số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0048','framework-dig','comp-dig-010','DIG.1.2.I02','1.2','Đánh giá dữ liệu, thông tin và nội dung số','So sánh nhiều nguồn để đánh giá độ tin cậy, tính chính xác và thiên lệch.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0049','framework-dig','comp-dig-010','DIG.1.2.I03','1.2','Đánh giá dữ liệu, thông tin và nội dung số','Đưa ra kết luận có căn cứ về chất lượng và mức phù hợp của thông tin số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0050','framework-dig','comp-dig-011','DIG.1.3.I01','1.3','Quản lý dữ liệu, thông tin và nội dung số','Tổ chức dữ liệu/nội dung số theo cấu trúc dễ truy cập.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0051','framework-dig','comp-dig-011','DIG.1.3.I02','1.3','Quản lý dữ liệu, thông tin và nội dung số','Lưu trữ, đặt tên, phân loại và truy xuất dữ liệu phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0052','framework-dig','comp-dig-011','DIG.1.3.I03','1.3','Quản lý dữ liệu, thông tin và nội dung số','Sao lưu, cập nhật và quản lí vòng đời dữ liệu/nội dung số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0053','framework-dig','comp-dig-012','DIG.2.1.I01','2.1','Tương tác thông qua công nghệ số','Lựa chọn kênh/công cụ số phù hợp với mục đích tương tác.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0054','framework-dig','comp-dig-012','DIG.2.1.I02','2.1','Tương tác thông qua công nghệ số','Trao đổi thông tin qua công nghệ số đúng quy tắc và bối cảnh.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0055','framework-dig','comp-dig-012','DIG.2.1.I03','2.1','Tương tác thông qua công nghệ số','Điều chỉnh cách tương tác theo đối tượng, môi trường và yêu cầu nhiệm vụ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0056','framework-dig','comp-dig-013','DIG.2.2.I01','2.2','Chia sẻ thông tin và nội dung thông qua công nghệ số','Chia sẻ dữ liệu/nội dung bằng công cụ số phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0057','framework-dig','comp-dig-013','DIG.2.2.I02','2.2','Chia sẻ thông tin và nội dung thông qua công nghệ số','Thiết lập quyền truy cập/chia sẻ phù hợp với đối tượng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0058','framework-dig','comp-dig-013','DIG.2.2.I03','2.2','Chia sẻ thông tin và nội dung thông qua công nghệ số','Ghi nguồn và tôn trọng quyền sở hữu khi chia sẻ nội dung.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0059','framework-dig','comp-dig-014','DIG.2.3.I01','2.3','Tham gia với tư cách công dân thông qua công nghệ số','Nhận biết các dịch vụ và kênh số phục vụ học tập, cộng đồng và xã hội.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0060','framework-dig','comp-dig-014','DIG.2.3.I02','2.3','Tham gia với tư cách công dân thông qua công nghệ số','Tham gia hoạt động số có trách nhiệm và tôn trọng quy định.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0061','framework-dig','comp-dig-014','DIG.2.3.I03','2.3','Tham gia với tư cách công dân thông qua công nghệ số','Sử dụng công nghệ số để đóng góp tích cực cho cộng đồng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0062','framework-dig','comp-dig-015','DIG.2.4.I01','2.4','Hợp tác thông qua công nghệ số','Sử dụng công cụ cộng tác để cùng tạo và chỉnh sửa sản phẩm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0063','framework-dig','comp-dig-015','DIG.2.4.I02','2.4','Hợp tác thông qua công nghệ số','Phân công, theo dõi và phối hợp nhiệm vụ trên môi trường số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0064','framework-dig','comp-dig-015','DIG.2.4.I03','2.4','Hợp tác thông qua công nghệ số','Quản lí phiên bản, phản hồi và thống nhất sản phẩm chung.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0065','framework-dig','comp-dig-016','DIG.2.5.I01','2.5','Chuẩn mực giao tiếp','Thực hiện quy tắc ứng xử phù hợp trong giao tiếp số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0066','framework-dig','comp-dig-016','DIG.2.5.I02','2.5','Chuẩn mực giao tiếp','Tôn trọng khác biệt văn hóa, quyền riêng tư và phẩm giá người khác.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0067','framework-dig','comp-dig-016','DIG.2.5.I03','2.5','Chuẩn mực giao tiếp','Nhận biết và tránh hành vi gây hại, quấy rối hoặc phát tán nội dung không phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0068','framework-dig','comp-dig-017','DIG.2.6.I01','2.6','Quản lý danh tính số','Nhận biết dấu vết và danh tính số của bản thân.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0069','framework-dig','comp-dig-017','DIG.2.6.I02','2.6','Quản lý danh tính số','Quản lí thông tin hồ sơ, tài khoản và cách thể hiện bản thân trên mạng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0070','framework-dig','comp-dig-017','DIG.2.6.I03','2.6','Quản lý danh tính số','Bảo vệ uy tín, dữ liệu và quyền riêng tư gắn với danh tính số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0071','framework-dig','comp-dig-018','DIG.3.1.I01','3.1','Phát triển nội dung số','Tạo nội dung số phù hợp mục tiêu và đối tượng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0072','framework-dig','comp-dig-018','DIG.3.1.I02','3.1','Phát triển nội dung số','Biên tập, định dạng và trình bày nội dung bằng công cụ số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0073','framework-dig','comp-dig-018','DIG.3.1.I03','3.1','Phát triển nội dung số','Đánh giá và cải thiện chất lượng sản phẩm số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0074','framework-dig','comp-dig-019','DIG.3.2.I01','3.2','Tích hợp và tái tạo nội dung số','Kết hợp thông tin/nội dung từ nhiều nguồn thành sản phẩm mới.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0075','framework-dig','comp-dig-019','DIG.3.2.I02','3.2','Tích hợp và tái tạo nội dung số','Chỉnh sửa, chuyển đổi và tái cấu trúc nội dung số phù hợp mục tiêu.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0076','framework-dig','comp-dig-019','DIG.3.2.I03','3.2','Tích hợp và tái tạo nội dung số','Phân biệt phần tự tạo và phần kế thừa từ nguồn khác.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0077','framework-dig','comp-dig-020','DIG.3.3.I01','3.3','Bản quyền và giấy phép','Nhận biết quyền tác giả, giấy phép và điều kiện sử dụng nội dung số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0078','framework-dig','comp-dig-020','DIG.3.3.I02','3.3','Bản quyền và giấy phép','Trích dẫn/ghi nguồn phù hợp khi sử dụng tài nguyên của người khác.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0079','framework-dig','comp-dig-020','DIG.3.3.I03','3.3','Bản quyền và giấy phép','Lựa chọn và áp dụng giấy phép phù hợp cho nội dung do mình tạo ra.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0080','framework-dig','comp-dig-021','DIG.3.4.I01','3.4','Lập trình','Mô tả được chuỗi lệnh/thuật toán để thực hiện nhiệm vụ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0081','framework-dig','comp-dig-021','DIG.3.4.I02','3.4','Lập trình','Tạo hoặc chỉnh sửa chương trình/kịch bản đơn giản phù hợp yêu cầu.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0082','framework-dig','comp-dig-021','DIG.3.4.I03','3.4','Lập trình','Kiểm thử, phát hiện lỗi và cải tiến giải pháp lập trình.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0083','framework-dig','comp-dig-022','DIG.4.1.I01','4.1','Bảo vệ thiết bị','Nhận biết nguy cơ đối với thiết bị và dữ liệu.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0084','framework-dig','comp-dig-022','DIG.4.1.I02','4.1','Bảo vệ thiết bị','Áp dụng biện pháp bảo vệ thiết bị, tài khoản và phần mềm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0085','framework-dig','comp-dig-022','DIG.4.1.I03','4.1','Bảo vệ thiết bị','Cập nhật, sao lưu và xử lí sự cố bảo mật cơ bản.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0086','framework-dig','comp-dig-023','DIG.4.2.I01','4.2','Bảo vệ dữ liệu cá nhân và quyền riêng tư','Nhận biết dữ liệu cá nhân và dữ liệu nhạy cảm cần bảo vệ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0087','framework-dig','comp-dig-023','DIG.4.2.I02','4.2','Bảo vệ dữ liệu cá nhân và quyền riêng tư','Thiết lập quyền riêng tư và hạn chế chia sẻ dữ liệu không cần thiết.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0088','framework-dig','comp-dig-023','DIG.4.2.I03','4.2','Bảo vệ dữ liệu cá nhân và quyền riêng tư','Đánh giá rủi ro trước khi cung cấp dữ liệu cho nền tảng/dịch vụ số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0089','framework-dig','comp-dig-024','DIG.4.3.I01','4.3','Bảo vệ sức khỏe và an sinh','Nhận biết tác động của công nghệ số tới thể chất và tinh thần.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0090','framework-dig','comp-dig-024','DIG.4.3.I02','4.3','Bảo vệ sức khỏe và an sinh','Thực hành tư thế, thời lượng và thói quen sử dụng thiết bị lành mạnh.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0091','framework-dig','comp-dig-024','DIG.4.3.I03','4.3','Bảo vệ sức khỏe và an sinh','Nhận biết, phòng tránh nội dung/hành vi số có thể gây tổn hại.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0092','framework-dig','comp-dig-025','DIG.4.4.I01','4.4','Bảo vệ môi trường','Nhận biết tác động môi trường của thiết bị và hoạt động số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0093','framework-dig','comp-dig-025','DIG.4.4.I02','4.4','Bảo vệ môi trường','Sử dụng thiết bị, năng lượng và tài nguyên số tiết kiệm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0094','framework-dig','comp-dig-025','DIG.4.4.I03','4.4','Bảo vệ môi trường','Thực hiện tái sử dụng, bảo quản hoặc xử lí thiết bị điện tử có trách nhiệm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0095','framework-dig','comp-dig-026','DIG.5.1.I01','5.1','Giải quyết vấn đề kĩ thuật','Nhận biết và mô tả sự cố kĩ thuật.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0096','framework-dig','comp-dig-026','DIG.5.1.I02','5.1','Giải quyết vấn đề kĩ thuật','Thử các bước chẩn đoán và khắc phục phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0097','framework-dig','comp-dig-026','DIG.5.1.I03','5.1','Giải quyết vấn đề kĩ thuật','Tìm kiếm hỗ trợ hoặc chuyển cấp xử lí khi vượt khả năng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0098','framework-dig','comp-dig-027','DIG.5.2.I01','5.2','Xác định nhu cầu và giải pháp công nghệ','Phân tích nhiệm vụ để xác định nhu cầu công nghệ.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0099','framework-dig','comp-dig-027','DIG.5.2.I02','5.2','Xác định nhu cầu và giải pháp công nghệ','So sánh công cụ/giải pháp số theo tiêu chí phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0100','framework-dig','comp-dig-027','DIG.5.2.I03','5.2','Xác định nhu cầu và giải pháp công nghệ','Lựa chọn, cấu hình hoặc tùy biến giải pháp đáp ứng nhu cầu.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0101','framework-dig','comp-dig-028','DIG.5.3.I01','5.3','Sử dụng sáng tạo công nghệ số','Kết hợp công cụ số để tạo cách giải quyết mới.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0102','framework-dig','comp-dig-028','DIG.5.3.I02','5.3','Sử dụng sáng tạo công nghệ số','Thử nghiệm, tạo mẫu và cải tiến sản phẩm/quy trình số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0103','framework-dig','comp-dig-028','DIG.5.3.I03','5.3','Sử dụng sáng tạo công nghệ số','Đánh giá giá trị và tính khả thi của giải pháp sáng tạo.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0104','framework-dig','comp-dig-029','DIG.5.4.I01','5.4','Xác định khoảng trống năng lực số','Tự đánh giá điểm mạnh và hạn chế về năng lực số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0105','framework-dig','comp-dig-029','DIG.5.4.I02','5.4','Xác định khoảng trống năng lực số','Xác định kiến thức/kĩ năng số cần bổ sung.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0106','framework-dig','comp-dig-029','DIG.5.4.I03','5.4','Xác định khoảng trống năng lực số','Lập và thực hiện kế hoạch tự học, cập nhật năng lực số.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0107','framework-dig','comp-dig-030','DIG.6.1.I01','6.1','Hiểu biết về trí tuệ nhân tạo','Nhận biết khái niệm, đặc trưng và ví dụ ứng dụng AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0108','framework-dig','comp-dig-030','DIG.6.1.I02','6.1','Hiểu biết về trí tuệ nhân tạo','Mô tả ở mức phù hợp vai trò của dữ liệu, thuật toán/mô hình và quá trình tạo kết quả.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0109','framework-dig','comp-dig-030','DIG.6.1.I03','6.1','Hiểu biết về trí tuệ nhân tạo','Nhận biết giới hạn, sai số, thiên lệch và tác động của AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0110','framework-dig','comp-dig-031','DIG.6.2.I01','6.2','Sử dụng trí tuệ nhân tạo','Lựa chọn công cụ AI phù hợp với mục tiêu và bối cảnh.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0111','framework-dig','comp-dig-031','DIG.6.2.I02','6.2','Sử dụng trí tuệ nhân tạo','Cung cấp yêu cầu/đầu vào rõ ràng và tương tác lặp để cải thiện kết quả.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0112','framework-dig','comp-dig-031','DIG.6.2.I03','6.2','Sử dụng trí tuệ nhân tạo','Kiểm tra, chỉnh sửa và sử dụng đầu ra AI có trách nhiệm.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0113','framework-dig','comp-dig-032','DIG.6.3.I01','6.3','Đánh giá trí tuệ nhân tạo','Đánh giá độ chính xác, phù hợp và độ tin cậy của kết quả AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0114','framework-dig','comp-dig-032','DIG.6.3.I02','6.3','Đánh giá trí tuệ nhân tạo','Xem xét rủi ro về thiên lệch, quyền riêng tư, bản quyền và đạo đức.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-dig-0115','framework-dig','comp-dig-032','DIG.6.3.I03','6.3','Đánh giá trí tuệ nhân tạo','So sánh kết quả AI với nguồn/bằng chứng khác trước khi quyết định sử dụng.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0116','framework-ai','comp-ai-033','AI.NLa.I01','NLa / A','Tư duy lấy con người làm trung tâm','Phân biệt vai trò, khả năng và giới hạn giữa con người và hệ thống AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0117','framework-ai','comp-ai-033','AI.NLa.I02','NLa / A','Tư duy lấy con người làm trung tâm','Xác định khi nào nên, không nên hoặc cần thận trọng khi sử dụng AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0118','framework-ai','comp-ai-033','AI.NLa.I03','NLa / A','Tư duy lấy con người làm trung tâm','Kiểm tra và phản biện kết quả AI thay vì phụ thuộc hoàn toàn vào AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0119','framework-ai','comp-ai-033','AI.NLa.I04','NLa / A','Tư duy lấy con người làm trung tâm','Giữ vai trò quyết định của con người và chịu trách nhiệm đối với quyết định có sử dụng AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0120','framework-ai','comp-ai-033','AI.NLa.I05','NLa / A','Tư duy lấy con người làm trung tâm','Định hướng việc sử dụng AI phục vụ học tập, con người và lợi ích chung.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0121','framework-ai','comp-ai-034','AI.NLb.I01','NLb / B','Đạo đức AI','Nhận biết vấn đề công bằng, thiên lệch và phân biệt đối xử trong hệ thống AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0122','framework-ai','comp-ai-034','AI.NLb.I02','NLb / B','Đạo đức AI','Bảo vệ dữ liệu cá nhân, quyền riêng tư và an toàn khi sử dụng AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0123','framework-ai','comp-ai-034','AI.NLb.I03','NLb / B','Đạo đức AI','Nhận biết vấn đề sở hữu trí tuệ, nguồn gốc và tính xác thực của nội dung do AI hỗ trợ tạo.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0124','framework-ai','comp-ai-034','AI.NLb.I04','NLb / B','Đạo đức AI','Đánh giá hậu quả có thể xảy ra đối với cá nhân, cộng đồng và xã hội khi dùng AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0125','framework-ai','comp-ai-034','AI.NLb.I05','NLb / B','Đạo đức AI','Sử dụng AI minh bạch, trung thực, có trách nhiệm và phù hợp quy định.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0126','framework-ai','comp-ai-035','AI.NLc.I01','NLc / C','Các kĩ thuật và ứng dụng AI','Nhận biết AI và các ứng dụng AI trong học tập, đời sống và nghề nghiệp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0127','framework-ai','comp-ai-035','AI.NLc.I02','NLc / C','Các kĩ thuật và ứng dụng AI','Mô tả được vai trò của dữ liệu, luật/thuật toán, mô hình và quá trình học của AI ở mức phù hợp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0128','framework-ai','comp-ai-035','AI.NLc.I03','NLc / C','Các kĩ thuật và ứng dụng AI','Sử dụng được một số công cụ/ứng dụng AI để thực hiện nhiệm vụ học tập.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0129','framework-ai','comp-ai-035','AI.NLc.I04','NLc / C','Các kĩ thuật và ứng dụng AI','Thiết kế đầu vào/yêu cầu và điều chỉnh tương tác để nâng cao chất lượng kết quả.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0130','framework-ai','comp-ai-035','AI.NLc.I05','NLc / C','Các kĩ thuật và ứng dụng AI','Kiểm chứng kết quả AI bằng kiến thức, dữ liệu hoặc nguồn độc lập.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0131','framework-ai','comp-ai-036','AI.NLd.I01','NLd / D','Thiết kế hệ thống AI','Xác định vấn đề hoặc nhu cầu có thể được hỗ trợ bằng một hệ thống/sản phẩm AI.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0132','framework-ai','comp-ai-036','AI.NLd.I02','NLd / D','Thiết kế hệ thống AI','Xác định dữ liệu đầu vào, kết quả mong đợi và tiêu chí đánh giá giải pháp.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0133','framework-ai','comp-ai-036','AI.NLd.I03','NLd / D','Thiết kế hệ thống AI','Thiết kế hoặc tạo mẫu quy trình/sản phẩm AI ở mức phù hợp với cấp học.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0134','framework-ai','comp-ai-036','AI.NLd.I04','NLd / D','Thiết kế hệ thống AI','Thử nghiệm, đánh giá và cải tiến giải pháp dựa trên kết quả thực tế.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-ai-0135','framework-ai','comp-ai-036','AI.NLd.I05','NLd / D','Thiết kế hệ thống AI','Xem xét an toàn, đạo đức, công bằng và trách nhiệm con người trong thiết kế.',true,true,'1.0','REFERENCE_MAPPED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0136','framework-eng','comp-eng-037','ENG.COM.L.I01','L','Listening / Nghe','Nhận biết đặc trưng âm thanh/ngữ điệu',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0137','framework-eng','comp-eng-037','ENG.COM.L.I02','L','Listening / Nghe','Hiểu chỉ dẫn/thông báo ngắn',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0138','framework-eng','comp-eng-037','ENG.COM.L.I03','L','Listening / Nghe','Hiểu ý chính văn bản nghe',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0139','framework-eng','comp-eng-037','ENG.COM.L.I04','L','Listening / Nghe','Hiểu thông tin chi tiết văn bản nghe',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0140','framework-eng','comp-eng-037','ENG.COM.L.I05','L','Listening / Nghe','Diễn giải/xử lí thông tin nghe theo ngữ cảnh',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0141','framework-eng','comp-eng-038','ENG.COM.S.I01','S','Speaking / Nói','Phát âm, trọng âm, nhịp điệu, ngữ điệu',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0142','framework-eng','comp-eng-038','ENG.COM.S.I02','S','Speaking / Nói','Thực hiện chức năng giao tiếp ngắn',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0143','framework-eng','comp-eng-038','ENG.COM.S.I03','S','Speaking / Nói','Trình bày chủ đề quen thuộc',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0144','framework-eng','comp-eng-038','ENG.COM.S.I04','S','Speaking / Nói','Hỏi–đáp và tương tác',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0145','framework-eng','comp-eng-038','ENG.COM.S.I05','S','Speaking / Nói','Trình bày sản phẩm/dự án và phản hồi',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0146','framework-eng','comp-eng-039','ENG.COM.R.I01','R','Reading / Đọc','Đọc hiểu ý chính',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0147','framework-eng','comp-eng-039','ENG.COM.R.I02','R','Reading / Đọc','Đọc hiểu thông tin chi tiết',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0148','framework-eng','comp-eng-039','ENG.COM.R.I03','R','Reading / Đọc','Đọc văn bản chức năng/đời sống',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0149','framework-eng','comp-eng-039','ENG.COM.R.I04','R','Reading / Đọc','Suy đoán nghĩa từ ngữ cảnh',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0150','framework-eng','comp-eng-039','ENG.COM.R.I05','R','Reading / Đọc','Suy luận/diễn giải thông tin',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0151','framework-eng','comp-eng-040','ENG.COM.W.I01','W','Writing / Viết','Viết đoạn/văn bản có hướng dẫn',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0152','framework-eng','comp-eng-040','ENG.COM.W.I02','W','Writing / Viết','Viết văn bản giao tiếp chức năng',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0153','framework-eng','comp-eng-040','ENG.COM.W.I03','W','Writing / Viết','Viết thông tin/tin nhắn/ghi chép',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0154','framework-eng','comp-eng-040','ENG.COM.W.I04','W','Writing / Viết','Tổ chức và liên kết ý',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_indicators(indicator_id,framework_id,component_id,canonical_code,source_code,indicator_name,indicator_text,observable_flag,assessable_flag,version_label,provenance_status,status,metadata)
values ('indicator-eng-0155','framework-eng','comp-eng-040','ENG.COM.W.I05','W','Writing / Viết','Độ chính xác ngôn ngữ trong viết',true,true,'1.2','PROVENANCE_PACKAGE_LOCKED','ACTIVE','{"system_default":true}'::jsonb)
on conflict(indicator_id) do update set framework_id=excluded.framework_id, component_id=excluded.component_id, canonical_code=excluded.canonical_code, source_code=excluded.source_code, indicator_name=excluded.indicator_name, indicator_text=excluded.indicator_text, observable_flag=excluded.observable_flag, assessable_flag=excluded.assessable_flag, provenance_status=excluded.provenance_status, version_label=excluded.version_label, status=excluded.status, metadata=coalesce(public.competency_indicators.metadata,'{}'::jsonb)||excluded.metadata, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i01-g06','indicator-eng-0136','grade-06','ENG.COM.L.I01.G06','Nhận biết đặc trưng âm thanh/ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i01-g07','indicator-eng-0136','grade-07','ENG.COM.L.I01.G07','Nhận biết đặc trưng âm thanh/ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i01-g08','indicator-eng-0136','grade-08','ENG.COM.L.I01.G08','Nhận biết đặc trưng âm thanh/ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i01-g09','indicator-eng-0136','grade-09','ENG.COM.L.I01.G09','Nhận biết đặc trưng âm thanh/ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i02-g06','indicator-eng-0137','grade-06','ENG.COM.L.I02.G06','Hiểu chỉ dẫn/thông báo ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i02-g07','indicator-eng-0137','grade-07','ENG.COM.L.I02.G07','Hiểu chỉ dẫn/thông báo ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i02-g08','indicator-eng-0137','grade-08','ENG.COM.L.I02.G08','Hiểu chỉ dẫn/thông báo ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i02-g09','indicator-eng-0137','grade-09','ENG.COM.L.I02.G09','Hiểu chỉ dẫn/thông báo ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i03-g06','indicator-eng-0138','grade-06','ENG.COM.L.I03.G06','Hiểu ý chính văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i03-g07','indicator-eng-0138','grade-07','ENG.COM.L.I03.G07','Hiểu ý chính văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i03-g08','indicator-eng-0138','grade-08','ENG.COM.L.I03.G08','Hiểu ý chính văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i03-g09','indicator-eng-0138','grade-09','ENG.COM.L.I03.G09','Hiểu ý chính văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i04-g06','indicator-eng-0139','grade-06','ENG.COM.L.I04.G06','Hiểu thông tin chi tiết văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i04-g07','indicator-eng-0139','grade-07','ENG.COM.L.I04.G07','Hiểu thông tin chi tiết văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i04-g08','indicator-eng-0139','grade-08','ENG.COM.L.I04.G08','Hiểu thông tin chi tiết văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i04-g09','indicator-eng-0139','grade-09','ENG.COM.L.I04.G09','Hiểu thông tin chi tiết văn bản nghe','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i05-g06','indicator-eng-0140','grade-06','ENG.COM.L.I05.G06','Diễn giải/xử lí thông tin nghe theo ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i05-g07','indicator-eng-0140','grade-07','ENG.COM.L.I05.G07','Diễn giải/xử lí thông tin nghe theo ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i05-g08','indicator-eng-0140','grade-08','ENG.COM.L.I05.G08','Diễn giải/xử lí thông tin nghe theo ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-l-i05-g09','indicator-eng-0140','grade-09','ENG.COM.L.I05.G09','Diễn giải/xử lí thông tin nghe theo ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i01-g06','indicator-eng-0141','grade-06','ENG.COM.S.I01.G06','Phát âm, trọng âm, nhịp điệu, ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i01-g07','indicator-eng-0141','grade-07','ENG.COM.S.I01.G07','Phát âm, trọng âm, nhịp điệu, ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i01-g08','indicator-eng-0141','grade-08','ENG.COM.S.I01.G08','Phát âm, trọng âm, nhịp điệu, ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i01-g09','indicator-eng-0141','grade-09','ENG.COM.S.I01.G09','Phát âm, trọng âm, nhịp điệu, ngữ điệu','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i02-g06','indicator-eng-0142','grade-06','ENG.COM.S.I02.G06','Thực hiện chức năng giao tiếp ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i02-g07','indicator-eng-0142','grade-07','ENG.COM.S.I02.G07','Thực hiện chức năng giao tiếp ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i02-g08','indicator-eng-0142','grade-08','ENG.COM.S.I02.G08','Thực hiện chức năng giao tiếp ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i02-g09','indicator-eng-0142','grade-09','ENG.COM.S.I02.G09','Thực hiện chức năng giao tiếp ngắn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i03-g06','indicator-eng-0143','grade-06','ENG.COM.S.I03.G06','Trình bày chủ đề quen thuộc','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i03-g07','indicator-eng-0143','grade-07','ENG.COM.S.I03.G07','Trình bày chủ đề quen thuộc','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i03-g08','indicator-eng-0143','grade-08','ENG.COM.S.I03.G08','Trình bày chủ đề quen thuộc','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i03-g09','indicator-eng-0143','grade-09','ENG.COM.S.I03.G09','Trình bày chủ đề quen thuộc','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i04-g06','indicator-eng-0144','grade-06','ENG.COM.S.I04.G06','Hỏi–đáp và tương tác','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i04-g07','indicator-eng-0144','grade-07','ENG.COM.S.I04.G07','Hỏi–đáp và tương tác','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i04-g08','indicator-eng-0144','grade-08','ENG.COM.S.I04.G08','Hỏi–đáp và tương tác','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i04-g09','indicator-eng-0144','grade-09','ENG.COM.S.I04.G09','Hỏi–đáp và tương tác','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i05-g06','indicator-eng-0145','grade-06','ENG.COM.S.I05.G06','Trình bày sản phẩm/dự án và phản hồi','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i05-g07','indicator-eng-0145','grade-07','ENG.COM.S.I05.G07','Trình bày sản phẩm/dự án và phản hồi','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i05-g08','indicator-eng-0145','grade-08','ENG.COM.S.I05.G08','Trình bày sản phẩm/dự án và phản hồi','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-s-i05-g09','indicator-eng-0145','grade-09','ENG.COM.S.I05.G09','Trình bày sản phẩm/dự án và phản hồi','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i01-g06','indicator-eng-0146','grade-06','ENG.COM.R.I01.G06','Đọc hiểu ý chính','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i01-g07','indicator-eng-0146','grade-07','ENG.COM.R.I01.G07','Đọc hiểu ý chính','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i01-g08','indicator-eng-0146','grade-08','ENG.COM.R.I01.G08','Đọc hiểu ý chính','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i01-g09','indicator-eng-0146','grade-09','ENG.COM.R.I01.G09','Đọc hiểu ý chính','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i02-g06','indicator-eng-0147','grade-06','ENG.COM.R.I02.G06','Đọc hiểu thông tin chi tiết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i02-g07','indicator-eng-0147','grade-07','ENG.COM.R.I02.G07','Đọc hiểu thông tin chi tiết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i02-g08','indicator-eng-0147','grade-08','ENG.COM.R.I02.G08','Đọc hiểu thông tin chi tiết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i02-g09','indicator-eng-0147','grade-09','ENG.COM.R.I02.G09','Đọc hiểu thông tin chi tiết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i03-g06','indicator-eng-0148','grade-06','ENG.COM.R.I03.G06','Đọc văn bản chức năng/đời sống','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i03-g07','indicator-eng-0148','grade-07','ENG.COM.R.I03.G07','Đọc văn bản chức năng/đời sống','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i03-g08','indicator-eng-0148','grade-08','ENG.COM.R.I03.G08','Đọc văn bản chức năng/đời sống','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i03-g09','indicator-eng-0148','grade-09','ENG.COM.R.I03.G09','Đọc văn bản chức năng/đời sống','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i04-g06','indicator-eng-0149','grade-06','ENG.COM.R.I04.G06','Suy đoán nghĩa từ ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i04-g07','indicator-eng-0149','grade-07','ENG.COM.R.I04.G07','Suy đoán nghĩa từ ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i04-g08','indicator-eng-0149','grade-08','ENG.COM.R.I04.G08','Suy đoán nghĩa từ ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i04-g09','indicator-eng-0149','grade-09','ENG.COM.R.I04.G09','Suy đoán nghĩa từ ngữ cảnh','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i05-g06','indicator-eng-0150','grade-06','ENG.COM.R.I05.G06','Suy luận/diễn giải thông tin','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i05-g07','indicator-eng-0150','grade-07','ENG.COM.R.I05.G07','Suy luận/diễn giải thông tin','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i05-g08','indicator-eng-0150','grade-08','ENG.COM.R.I05.G08','Suy luận/diễn giải thông tin','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-r-i05-g09','indicator-eng-0150','grade-09','ENG.COM.R.I05.G09','Suy luận/diễn giải thông tin','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i01-g06','indicator-eng-0151','grade-06','ENG.COM.W.I01.G06','Viết đoạn/văn bản có hướng dẫn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i01-g07','indicator-eng-0151','grade-07','ENG.COM.W.I01.G07','Viết đoạn/văn bản có hướng dẫn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i01-g08','indicator-eng-0151','grade-08','ENG.COM.W.I01.G08','Viết đoạn/văn bản có hướng dẫn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i01-g09','indicator-eng-0151','grade-09','ENG.COM.W.I01.G09','Viết đoạn/văn bản có hướng dẫn','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i02-g06','indicator-eng-0152','grade-06','ENG.COM.W.I02.G06','Viết văn bản giao tiếp chức năng','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i02-g07','indicator-eng-0152','grade-07','ENG.COM.W.I02.G07','Viết văn bản giao tiếp chức năng','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i02-g08','indicator-eng-0152','grade-08','ENG.COM.W.I02.G08','Viết văn bản giao tiếp chức năng','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i02-g09','indicator-eng-0152','grade-09','ENG.COM.W.I02.G09','Viết văn bản giao tiếp chức năng','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i03-g06','indicator-eng-0153','grade-06','ENG.COM.W.I03.G06','Viết thông tin/tin nhắn/ghi chép','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i03-g07','indicator-eng-0153','grade-07','ENG.COM.W.I03.G07','Viết thông tin/tin nhắn/ghi chép','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i03-g08','indicator-eng-0153','grade-08','ENG.COM.W.I03.G08','Viết thông tin/tin nhắn/ghi chép','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i03-g09','indicator-eng-0153','grade-09','ENG.COM.W.I03.G09','Viết thông tin/tin nhắn/ghi chép','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i04-g06','indicator-eng-0154','grade-06','ENG.COM.W.I04.G06','Tổ chức và liên kết ý','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i04-g07','indicator-eng-0154','grade-07','ENG.COM.W.I04.G07','Tổ chức và liên kết ý','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i04-g08','indicator-eng-0154','grade-08','ENG.COM.W.I04.G08','Tổ chức và liên kết ý','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i04-g09','indicator-eng-0154','grade-09','ENG.COM.W.I04.G09','Tổ chức và liên kết ý','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i05-g06','indicator-eng-0155','grade-06','ENG.COM.W.I05.G06','Độ chính xác ngôn ngữ trong viết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i05-g07','indicator-eng-0155','grade-07','ENG.COM.W.I05.G07','Độ chính xác ngôn ngữ trong viết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i05-g08','indicator-eng-0155','grade-08','ENG.COM.W.I05.G08','Độ chính xác ngôn ngữ trong viết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_grade_descriptors(descriptor_id,indicator_id,grade_id,canonical_code,descriptor_text,version_label,provenance_status,status,metadata)
values ('descriptor-eng-com-w-i05-g09','indicator-eng-0155','grade-09','ENG.COM.W.I05.G09','Độ chính xác ngôn ngữ trong viết','1.2','READY_FOR_SOURCE_REQUIREMENT_ETL','REVIEWED','{"system_default":true}'::jsonb)
on conflict(descriptor_id) do update set descriptor_text=excluded.descriptor_text, provenance_status=excluded.provenance_status, status=excluded.status, updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-6f6210b743d8',NULL,'grade-06','L','TEXT_LENGTH',80,100,'WORD','General dialogue/monologue','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-1870cda9c561',NULL,'grade-06','R','TEXT_LENGTH',100,120,'WORD','Short familiar texts','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-2d0ca08b679c',NULL,'grade-06','W','TEXT_LENGTH',40,60,'WORD','Guided paragraph','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-320141037451',NULL,'grade-07','L','TEXT_LENGTH',120,140,'WORD','Dialogue/monologue','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-214be22e58c9',NULL,'grade-07','R','TEXT_LENGTH',120,150,'WORD','Familiar text','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-008a852b9f30',NULL,'grade-07','W','TEXT_LENGTH',60,80,'WORD','Paragraph/task','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-e94766171b34',NULL,'grade-08','L','TEXT_LENGTH',140,160,'WORD','Dialogue/monologue','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-95b44c8fd6d0',NULL,'grade-08','R','TEXT_LENGTH',150,180,'WORD','Familiar text','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-24d76121d309',NULL,'grade-08','W','TEXT_LENGTH',80,100,'WORD','Especially instruction/notice-type requirements','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-d426be93f561',NULL,'grade-09','L','TEXT_LENGTH',160,180,'WORD','Dialogue/monologue/news/announcement','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-bb16d876feb5',NULL,'grade-09','R','TEXT_LENGTH',180,200,'WORD','Familiar concrete texts','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_descriptor_constraints(constraint_id,descriptor_id,grade_id,skill_code,constraint_type,min_value,max_value,unit,applies_to,verification_status,version_label,metadata)
values ('constraint-33b34b2fb6aa',NULL,'grade-09','W','TEXT_LENGTH',100,120,'WORD','Requirement/task scoped','SOURCE_LOCATED_PENDING_TEXT_VERIFY','1.2','{"scope":"GRADE_SKILL_PENDING_EXACT_DESCRIPTOR_MAPPING"}'::jsonb)
on conflict(constraint_id) do update set min_value=excluded.min_value,max_value=excluded.max_value,applies_to=excluded.applies_to,verification_status=excluded.verification_status,updated_at=now();
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-001','ASSESSMENT_MATH','MATH-REASONING','framework-math','comp-math-004','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.TD"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-002','ASSESSMENT_MATH','MATH-MODELING','framework-math','comp-math-005','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.MHH"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-003','ASSESSMENT_MATH','MATH-PROBLEM-SOLVING','framework-math','comp-math-006','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.GQVD"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-004','ASSESSMENT_MATH','MATH-COMMUNICATION','framework-math','comp-math-007','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.GT"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-005','ASSESSMENT_MATH','MATH-TOOLS','framework-math','comp-math-008','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.CC"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-006','LEGACY_CONFIG','NLT_TDLL','framework-math','comp-math-004','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.TD"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-007','LEGACY_CONFIG','NLT_MHH','framework-math','comp-math-005','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.MHH"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-008','LEGACY_CONFIG','NLT_GQVD','framework-math','comp-math-006','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.GQVD"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-009','LEGACY_CONFIG','NLT_GT','framework-math','comp-math-007','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.GT"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-010','LEGACY_CONFIG','NLT_CCPT','framework-math','comp-math-008','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"MATH.CC"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-011','LEGACY_CONFIG','NLC_TCTH','framework-nlc','comp-nlc-001','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"NLC.TCTH"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-012','LEGACY_CONFIG','NLC_GTHH','framework-nlc','comp-nlc-002','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"NLC.GTHT"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_projection_mappings(projection_mapping_id,projection_scope,external_code,framework_id,component_id,relation_type,status,metadata) values ('projection-013','LEGACY_CONFIG','NLC_GQVDS','framework-nlc','comp-nlc-003','EQUIVALENT_OR_BROADER','ACTIVE','{"canonical_component_code":"NLC.GQVDST"}'::jsonb) on conflict(projection_scope,external_code) do update set component_id=excluded.component_id,status=excluded.status;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-001','DIG.6.1','AI.NLa; AI.NLc','RELATED','Hiểu AI, vai trò con người, dữ liệu/kĩ thuật','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-002','DIG.6.2','AI.NLa; AI.NLb; AI.NLc','RELATED','Sử dụng AI có mục đích, an toàn và trách nhiệm','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-003','DIG.6.3','AI.NLa; AI.NLb; AI.NLc','RELATED','Kiểm chứng, đánh giá, thiên lệch, đạo đức','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-004','DIG.3.1–3.3','AI.NLb; AI.NLc','RELATED','Tạo nội dung, bản quyền, minh bạch nguồn','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-005','DIG.4.1–4.4','AI.NLb','RELATED','An toàn, riêng tư, sức khỏe, môi trường','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;
insert into public.competency_crosswalks(crosswalk_id,source_reference,target_reference,relation_type,notes,status) values ('crosswalk-006','DIG.5.3','AI.NLd','RELATED','Sáng tạo, tạo mẫu và cải tiến giải pháp','ACTIVE') on conflict(crosswalk_id) do update set notes=excluded.notes;

create or replace function public.competency_admin_authorized()
returns boolean language sql stable security definer set search_path=public as $$
    select exists (
        select 1 from public.portal_roles pr
        where pr.user_id=(select auth.uid()) and upper(pr.role)='ADMIN' and coalesce(pr.is_active,true)=true
    );
$$;

create or replace function public.audit_competency_change()
returns trigger language plpgsql security definer set search_path=public as $$
declare
    before_json jsonb;
    after_json jsonb;
    entity_key text;
begin
    before_json := case when TG_OP in ('UPDATE','DELETE') then to_jsonb(old) else null end;
    after_json := case when TG_OP in ('INSERT','UPDATE') then to_jsonb(new) else null end;
    entity_key := coalesce(
        after_json->>'indicator_id', after_json->>'framework_id', after_json->>'component_id', after_json->>'descriptor_id',
        before_json->>'indicator_id', before_json->>'framework_id', before_json->>'component_id', before_json->>'descriptor_id', 'UNKNOWN'
    );
    insert into public.competency_audit_log(entity_type,entity_id,action,changed_by,before_data,after_data)
    values (TG_TABLE_NAME,entity_key,TG_OP,(select auth.uid()),before_json,after_json);
    return case when TG_OP='DELETE' then old else new end;
end; $$;

-- RLS: teachers/authenticated users see published catalog; ADMIN sees all and is the only writer.
alter table public.competency_frameworks enable row level security;
revoke all on table public.competency_frameworks from anon;
grant select,insert,update on table public.competency_frameworks to authenticated;
drop policy if exists competency_competency_frameworks_read on public.competency_frameworks;
create policy competency_competency_frameworks_read on public.competency_frameworks for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_frameworks_admin_insert on public.competency_frameworks;
create policy competency_competency_frameworks_admin_insert on public.competency_frameworks for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_frameworks_admin_update on public.competency_frameworks;
create policy competency_competency_frameworks_admin_update on public.competency_frameworks for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_components enable row level security;
revoke all on table public.competency_components from anon;
grant select,insert,update on table public.competency_components to authenticated;
drop policy if exists competency_competency_components_read on public.competency_components;
create policy competency_competency_components_read on public.competency_components for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_components_admin_insert on public.competency_components;
create policy competency_competency_components_admin_insert on public.competency_components for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_components_admin_update on public.competency_components;
create policy competency_competency_components_admin_update on public.competency_components for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_indicators enable row level security;
revoke all on table public.competency_indicators from anon;
grant select,insert,update on table public.competency_indicators to authenticated;
drop policy if exists competency_competency_indicators_read on public.competency_indicators;
create policy competency_competency_indicators_read on public.competency_indicators for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_indicators_admin_insert on public.competency_indicators;
create policy competency_competency_indicators_admin_insert on public.competency_indicators for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_indicators_admin_update on public.competency_indicators;
create policy competency_competency_indicators_admin_update on public.competency_indicators for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_grade_descriptors enable row level security;
revoke all on table public.competency_grade_descriptors from anon;
grant select,insert,update on table public.competency_grade_descriptors to authenticated;
drop policy if exists competency_competency_grade_descriptors_read on public.competency_grade_descriptors;
create policy competency_competency_grade_descriptors_read on public.competency_grade_descriptors for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_grade_descriptors_admin_insert on public.competency_grade_descriptors;
create policy competency_competency_grade_descriptors_admin_insert on public.competency_grade_descriptors for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_grade_descriptors_admin_update on public.competency_grade_descriptors;
create policy competency_competency_grade_descriptors_admin_update on public.competency_grade_descriptors for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_descriptor_constraints enable row level security;
revoke all on table public.competency_descriptor_constraints from anon;
grant select,insert,update on table public.competency_descriptor_constraints to authenticated;
drop policy if exists competency_competency_descriptor_constraints_read on public.competency_descriptor_constraints;
create policy competency_competency_descriptor_constraints_read on public.competency_descriptor_constraints for select to authenticated using (((select auth.uid()) is not null));
drop policy if exists competency_competency_descriptor_constraints_admin_insert on public.competency_descriptor_constraints;
create policy competency_competency_descriptor_constraints_admin_insert on public.competency_descriptor_constraints for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_descriptor_constraints_admin_update on public.competency_descriptor_constraints;
create policy competency_competency_descriptor_constraints_admin_update on public.competency_descriptor_constraints for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_requirement_links enable row level security;
revoke all on table public.competency_requirement_links from anon;
grant select,insert,update on table public.competency_requirement_links to authenticated;
drop policy if exists competency_competency_requirement_links_read on public.competency_requirement_links;
create policy competency_competency_requirement_links_read on public.competency_requirement_links for select to authenticated using ((review_status = 'VERIFIED' or public.competency_admin_authorized()));
drop policy if exists competency_competency_requirement_links_admin_insert on public.competency_requirement_links;
create policy competency_competency_requirement_links_admin_insert on public.competency_requirement_links for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_requirement_links_admin_update on public.competency_requirement_links;
create policy competency_competency_requirement_links_admin_update on public.competency_requirement_links for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_aliases enable row level security;
revoke all on table public.competency_aliases from anon;
grant select,insert,update on table public.competency_aliases to authenticated;
drop policy if exists competency_competency_aliases_read on public.competency_aliases;
create policy competency_competency_aliases_read on public.competency_aliases for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_aliases_admin_insert on public.competency_aliases;
create policy competency_competency_aliases_admin_insert on public.competency_aliases for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_aliases_admin_update on public.competency_aliases;
create policy competency_competency_aliases_admin_update on public.competency_aliases for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_projection_mappings enable row level security;
revoke all on table public.competency_projection_mappings from anon;
grant select,insert,update on table public.competency_projection_mappings to authenticated;
drop policy if exists competency_competency_projection_mappings_read on public.competency_projection_mappings;
create policy competency_competency_projection_mappings_read on public.competency_projection_mappings for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_projection_mappings_admin_insert on public.competency_projection_mappings;
create policy competency_competency_projection_mappings_admin_insert on public.competency_projection_mappings for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_projection_mappings_admin_update on public.competency_projection_mappings;
create policy competency_competency_projection_mappings_admin_update on public.competency_projection_mappings for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_crosswalks enable row level security;
revoke all on table public.competency_crosswalks from anon;
grant select,insert,update on table public.competency_crosswalks to authenticated;
drop policy if exists competency_competency_crosswalks_read on public.competency_crosswalks;
create policy competency_competency_crosswalks_read on public.competency_crosswalks for select to authenticated using ((status = 'ACTIVE' or public.competency_admin_authorized()));
drop policy if exists competency_competency_crosswalks_admin_insert on public.competency_crosswalks;
create policy competency_competency_crosswalks_admin_insert on public.competency_crosswalks for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_crosswalks_admin_update on public.competency_crosswalks;
create policy competency_competency_crosswalks_admin_update on public.competency_crosswalks for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
alter table public.competency_audit_log enable row level security;
revoke all on table public.competency_audit_log from anon;
grant select,insert,update on table public.competency_audit_log to authenticated;
drop policy if exists competency_competency_audit_log_read on public.competency_audit_log;
create policy competency_competency_audit_log_read on public.competency_audit_log for select to authenticated using (public.competency_admin_authorized());
drop policy if exists competency_competency_audit_log_admin_insert on public.competency_audit_log;
create policy competency_competency_audit_log_admin_insert on public.competency_audit_log for insert to authenticated with check (public.competency_admin_authorized());
drop policy if exists competency_competency_audit_log_admin_update on public.competency_audit_log;
create policy competency_competency_audit_log_admin_update on public.competency_audit_log for update to authenticated using (public.competency_admin_authorized()) with check (public.competency_admin_authorized());
drop trigger if exists competency_frameworks_audit_trigger on public.competency_frameworks;
create trigger competency_frameworks_audit_trigger after insert or update on public.competency_frameworks for each row execute function public.audit_competency_change();
drop trigger if exists competency_components_audit_trigger on public.competency_components;
create trigger competency_components_audit_trigger after insert or update on public.competency_components for each row execute function public.audit_competency_change();
drop trigger if exists competency_indicators_audit_trigger on public.competency_indicators;
create trigger competency_indicators_audit_trigger after insert or update on public.competency_indicators for each row execute function public.audit_competency_change();
drop trigger if exists competency_grade_descriptors_audit_trigger on public.competency_grade_descriptors;
create trigger competency_grade_descriptors_audit_trigger after insert or update on public.competency_grade_descriptors for each row execute function public.audit_competency_change();

