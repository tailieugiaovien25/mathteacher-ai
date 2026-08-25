begin;

create table if not exists public.assessment_blueprints (
    blueprint_id uuid primary key default gen_random_uuid(),

    blueprint_code text not null
        check (char_length(blueprint_code) between 1 and 140),

    owner_user_id uuid not null
        references auth.users(id)
        on delete restrict,

    subject_code text not null default 'MATH'
        check (char_length(subject_code) between 1 and 100),

    education_level text not null default 'THCS'
        check (
            education_level in (
                'PRIMARY',
                'THCS',
                'THPT'
            )
        ),

    grade_level integer not null
        check (grade_level between 1 and 12),

    current_version_number integer not null default 0
        check (current_version_number >= 0),

    lifecycle_status text not null default 'DRAFT'
        check (
            lifecycle_status in (
                'DRAFT',
                'ACTIVE',
                'ARCHIVED'
            )
        ),

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        owner_user_id,
        blueprint_code
    )
);

create table if not exists public.assessment_blueprint_versions (
    blueprint_version_id uuid primary key default gen_random_uuid(),

    blueprint_id uuid not null
        references public.assessment_blueprints(blueprint_id)
        on delete restrict,

    version_number integer not null
        check (version_number >= 1),

    profile_code text not null
        references public.assessment_profiles(profile_code)
        on update cascade
        on delete restrict,

    blueprint_name text not null
        check (char_length(trim(blueprint_name)) > 0),

    academic_year text null
        check (
            academic_year is null
            or char_length(academic_year) between 4 and 20
        ),

    semester_number integer null
        check (
            semester_number is null
            or semester_number between 1 and 3
        ),

    total_score numeric(6,2) not null
        check (total_score > 0),

    duration_minutes integer not null
        check (duration_minutes > 0),

    origin_type text not null default 'HUMAN'
        check (
            origin_type in (
                'HUMAN',
                'AI',
                'IMPORTED'
            )
        ),

    ai_generation_reference text null,

    review_status text not null default 'DRAFT'
        check (
            review_status in (
                'DRAFT',
                'AI_PROPOSED',
                'PENDING_REVIEW',
                'REVISION_REQUIRED',
                'APPROVED',
                'REJECTED',
                'RETIRED'
            )
        ),

    teacher_note text not null default '',
    locked_at timestamptz null,

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        blueprint_id,
        version_number
    ),

    check (
        origin_type = 'AI'
        or ai_generation_reference is null
    ),

    check (
        review_status not in (
            'APPROVED',
            'REJECTED',
            'RETIRED'
        )
        or locked_at is not null
    )
);

create table if not exists public.assessment_blueprint_cells (
    blueprint_cell_id uuid primary key default gen_random_uuid(),

    blueprint_version_id uuid not null
        references public.assessment_blueprint_versions(
            blueprint_version_id
        )
        on delete cascade,

    profile_code text not null,
    section_code text not null,

    topic_code text not null
        references public.assessment_curriculum_topics(topic_code)
        on update cascade
        on delete restrict,

    cognitive_level_code text not null
        references public.assessment_cognitive_levels(
            cognitive_level_code
        )
        on update cascade
        on delete restrict,

    question_type_code text not null
        references public.assessment_question_types(
            question_type_code
        )
        on update cascade
        on delete restrict,

    question_count integer not null
        check (question_count > 0),

    response_count integer not null
        check (response_count > 0),

    target_score numeric(6,2) not null
        check (target_score > 0),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    specification_note text not null default '',

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    foreign key (
        profile_code,
        section_code
    )
    references public.assessment_profile_sections (
        profile_code,
        section_code
    )
    on update cascade
    on delete restrict,

    unique (
        blueprint_version_id,
        profile_code,
        section_code,
        topic_code,
        cognitive_level_code,
        question_type_code
    ),

    check (response_count >= question_count)
);

create table if not exists public.assessment_blueprint_requirement_links (
    blueprint_version_id uuid not null
        references public.assessment_blueprint_versions(
            blueprint_version_id
        )
        on delete cascade,

    requirement_code text not null
        references public.assessment_learning_requirements(
            requirement_code
        )
        on update cascade
        on delete restrict,

    coverage_role text not null default 'PRIMARY'
        check (
            coverage_role in (
                'PRIMARY',
                'SUPPORTING'
            )
        ),

    target_question_count integer not null default 1
        check (target_question_count > 0),

    target_score numeric(6,2) null
        check (
            target_score is null
            or target_score > 0
        ),

    sequence_number integer not null default 0
        check (sequence_number >= 0),

    specification_note text not null default '',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    primary key (
        blueprint_version_id,
        requirement_code
    )
);

create or replace function
public.assessment_blueprint_version_is_visible(
    target_blueprint_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_blueprint_versions blueprint_version
        join public.assessment_blueprints blueprint
            on blueprint.blueprint_id =
                blueprint_version.blueprint_id
        where
            blueprint_version.blueprint_version_id =
                target_blueprint_version_id
            and (
                blueprint.owner_user_id =
                    (select auth.uid())
                or public.current_user_is_portal_admin()
            )
    );
$$;

revoke all on function
public.assessment_blueprint_version_is_visible(uuid)
from public;

grant execute on function
public.assessment_blueprint_version_is_visible(uuid)
to authenticated;

create or replace function
public.assessment_blueprint_version_is_editable(
    target_blueprint_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_blueprint_versions blueprint_version
        join public.assessment_blueprints blueprint
            on blueprint.blueprint_id =
                blueprint_version.blueprint_id
        where
            blueprint_version.blueprint_version_id =
                target_blueprint_version_id
            and blueprint.owner_user_id =
                (select auth.uid())
            and blueprint_version.review_status in (
                'DRAFT',
                'AI_PROPOSED',
                'REVISION_REQUIRED'
            )
            and blueprint_version.locked_at is null
    );
$$;

revoke all on function
public.assessment_blueprint_version_is_editable(uuid)
from public;

grant execute on function
public.assessment_blueprint_version_is_editable(uuid)
to authenticated;

create or replace function
public.enforce_assessment_blueprint_cell_consistency()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    expected_profile_code text;
    expected_grade_level integer;
    expected_question_type_code text;
    actual_topic_grade integer;
begin
    select
        blueprint_version.profile_code,
        blueprint.grade_level
    into
        expected_profile_code,
        expected_grade_level
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            new.blueprint_version_id;

    if expected_profile_code is null then
        raise exception
            'Blueprint version does not exist.';
    end if;

    if new.profile_code is distinct from expected_profile_code then
        raise exception
            'Blueprint cell profile does not match blueprint version.';
    end if;

    select profile_section.question_type_code
    into expected_question_type_code
    from public.assessment_profile_sections profile_section
    where
        profile_section.profile_code = new.profile_code
        and profile_section.section_code = new.section_code;

    if expected_question_type_code is null then
        raise exception
            'Assessment profile section does not exist.';
    end if;

    if (
        new.question_type_code
        is distinct from expected_question_type_code
    ) then
        raise exception
            'Blueprint cell question type does not match profile section.';
    end if;

    select topic.grade_level
    into actual_topic_grade
    from public.assessment_curriculum_topics topic
    where topic.topic_code = new.topic_code;

    if (
        actual_topic_grade is not null
        and actual_topic_grade is distinct from expected_grade_level
    ) then
        raise exception
            'Blueprint topic grade does not match blueprint grade.';
    end if;

    return new;
end;
$$;

revoke all on function
public.enforce_assessment_blueprint_cell_consistency()
from public;

drop trigger if exists
assessment_blueprint_cells_consistency
on public.assessment_blueprint_cells;

create trigger assessment_blueprint_cells_consistency
before insert or update
on public.assessment_blueprint_cells
for each row
execute function
public.enforce_assessment_blueprint_cell_consistency();

create or replace function
public.assessment_blueprint_totals_match(
    target_blueprint_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_blueprint_versions blueprint_version
        where
            blueprint_version.blueprint_version_id =
                target_blueprint_version_id
            and exists (
                select 1
                from public.assessment_blueprint_cells blueprint_cell
                where
                    blueprint_cell.blueprint_version_id =
                        blueprint_version.blueprint_version_id
            )
            and abs(
                (
                    select coalesce(
                        sum(blueprint_cell.target_score),
                        0
                    )
                    from public.assessment_blueprint_cells
                        blueprint_cell
                    where
                        blueprint_cell.blueprint_version_id =
                            blueprint_version.blueprint_version_id
                )
                -
                blueprint_version.total_score
            ) <= 0.0001
    );
$$;

revoke all on function
public.assessment_blueprint_totals_match(uuid)
from public;

grant execute on function
public.assessment_blueprint_totals_match(uuid)
to authenticated;

create or replace function
public.assessment_blueprint_ready_for_review(
    target_blueprint_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_blueprint_versions blueprint_version
        where
            blueprint_version.blueprint_version_id =
                target_blueprint_version_id
            and blueprint_version.review_status in (
                'DRAFT',
                'AI_PROPOSED',
                'PENDING_REVIEW',
                'REVISION_REQUIRED'
            )
            and blueprint_version.locked_at is null
            and exists (
                select 1
                from public.assessment_blueprint_requirement_links
                    requirement_link
                where
                    requirement_link.blueprint_version_id =
                        blueprint_version.blueprint_version_id
                    and requirement_link.coverage_role = 'PRIMARY'
            )
            and public.assessment_blueprint_totals_match(
                blueprint_version.blueprint_version_id
            )
    );
$$;

revoke all on function
public.assessment_blueprint_ready_for_review(uuid)
from public;

grant execute on function
public.assessment_blueprint_ready_for_review(uuid)
to authenticated;

alter table public.assessment_blueprints
    enable row level security;

alter table public.assessment_blueprint_versions
    enable row level security;

alter table public.assessment_blueprint_cells
    enable row level security;

alter table public.assessment_blueprint_requirement_links
    enable row level security;

revoke all on table
    public.assessment_blueprints,
    public.assessment_blueprint_versions,
    public.assessment_blueprint_cells,
    public.assessment_blueprint_requirement_links
from anon;

grant select, insert, update
on table public.assessment_blueprints
to authenticated;

grant select, insert, update
on table public.assessment_blueprint_versions
to authenticated;

grant select, insert, update, delete
on table
    public.assessment_blueprint_cells,
    public.assessment_blueprint_requirement_links
to authenticated;

drop policy if exists
assessment_blueprints_select_visible
on public.assessment_blueprints;

create policy assessment_blueprints_select_visible
on public.assessment_blueprints
for select
to authenticated
using (
    owner_user_id = (select auth.uid())
    or public.current_user_is_portal_admin()
);

drop policy if exists
assessment_blueprints_insert_owned
on public.assessment_blueprints;

create policy assessment_blueprints_insert_owned
on public.assessment_blueprints
for insert
to authenticated
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
assessment_blueprints_update_owned
on public.assessment_blueprints;

create policy assessment_blueprints_update_owned
on public.assessment_blueprints
for update
to authenticated
using (
    owner_user_id = (select auth.uid())
)
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
assessment_blueprint_versions_select_visible
on public.assessment_blueprint_versions;

create policy assessment_blueprint_versions_select_visible
on public.assessment_blueprint_versions
for select
to authenticated
using (
    public.assessment_blueprint_version_is_visible(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_versions_insert_owned
on public.assessment_blueprint_versions;

create policy assessment_blueprint_versions_insert_owned
on public.assessment_blueprint_versions
for insert
to authenticated
with check (
    exists (
        select 1
        from public.assessment_blueprints blueprint
        where
            blueprint.blueprint_id =
                assessment_blueprint_versions.blueprint_id
            and blueprint.owner_user_id =
                (select auth.uid())
    )
    and created_by = (select auth.uid())
    and review_status in (
        'DRAFT',
        'AI_PROPOSED'
    )
    and locked_at is null
);

drop policy if exists
assessment_blueprint_versions_update_owned
on public.assessment_blueprint_versions;

create policy assessment_blueprint_versions_update_owned
on public.assessment_blueprint_versions
for update
to authenticated
using (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
)
with check (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
    and created_by = (select auth.uid())
    and exists (
        select 1
        from public.assessment_blueprints blueprint
        where
            blueprint.blueprint_id =
                assessment_blueprint_versions.blueprint_id
            and blueprint.owner_user_id =
                (select auth.uid())
    )
);

drop policy if exists
assessment_blueprint_cells_select_visible
on public.assessment_blueprint_cells;

create policy assessment_blueprint_cells_select_visible
on public.assessment_blueprint_cells
for select
to authenticated
using (
    public.assessment_blueprint_version_is_visible(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_cells_insert_editable
on public.assessment_blueprint_cells;

create policy assessment_blueprint_cells_insert_editable
on public.assessment_blueprint_cells
for insert
to authenticated
with check (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_cells_update_editable
on public.assessment_blueprint_cells;

create policy assessment_blueprint_cells_update_editable
on public.assessment_blueprint_cells
for update
to authenticated
using (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
)
with check (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_cells_delete_editable
on public.assessment_blueprint_cells;

create policy assessment_blueprint_cells_delete_editable
on public.assessment_blueprint_cells
for delete
to authenticated
using (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_requirements_select_visible
on public.assessment_blueprint_requirement_links;

create policy assessment_blueprint_requirements_select_visible
on public.assessment_blueprint_requirement_links
for select
to authenticated
using (
    public.assessment_blueprint_version_is_visible(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_requirements_insert_editable
on public.assessment_blueprint_requirement_links;

create policy assessment_blueprint_requirements_insert_editable
on public.assessment_blueprint_requirement_links
for insert
to authenticated
with check (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_requirements_update_editable
on public.assessment_blueprint_requirement_links;

create policy assessment_blueprint_requirements_update_editable
on public.assessment_blueprint_requirement_links
for update
to authenticated
using (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
)
with check (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_requirements_delete_editable
on public.assessment_blueprint_requirement_links;

create policy assessment_blueprint_requirements_delete_editable
on public.assessment_blueprint_requirement_links
for delete
to authenticated
using (
    public.assessment_blueprint_version_is_editable(
        blueprint_version_id
    )
);

comment on table public.assessment_blueprints is
'Teacher-owned identities for assessment matrices and specifications.';

comment on table public.assessment_blueprint_versions is
'Immutable-after-review versions of assessment matrices.';

comment on table public.assessment_blueprint_cells is
'Matrix cells allocating question counts and scores by section, topic, level, and question type.';

comment on table
public.assessment_blueprint_requirement_links is
'Learning-requirement scope and targets for an assessment blueprint version.';

commit;


