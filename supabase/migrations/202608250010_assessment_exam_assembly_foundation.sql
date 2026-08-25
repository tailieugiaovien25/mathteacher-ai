begin;

create table if not exists public.assessment_exams (
    exam_id uuid primary key default gen_random_uuid(),

    exam_code text not null
        check (char_length(exam_code) between 1 and 140),

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
        exam_code
    )
);

create table if not exists public.assessment_exam_versions (
    exam_version_id uuid primary key default gen_random_uuid(),

    exam_id uuid not null
        references public.assessment_exams(exam_id)
        on delete restrict,

    version_number integer not null
        check (version_number >= 1),

    blueprint_version_id uuid not null
        references public.assessment_blueprint_versions(
            blueprint_version_id
        )
        on delete restrict,

    exam_title text not null
        check (char_length(trim(exam_title)) > 0),

    exam_code_label text not null default '',

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

    scheduled_date date null,

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

    assembly_status text not null default 'DRAFT'
        check (
            assembly_status in (
                'DRAFT',
                'AI_PROPOSED',
                'ASSEMBLED',
                'PENDING_REVIEW',
                'REVISION_REQUIRED',
                'APPROVED',
                'REJECTED',
                'PUBLISHED',
                'RETIRED'
            )
        ),

    instruction_text text not null default '',
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
        exam_id,
        version_number
    ),

    check (
        origin_type = 'AI'
        or ai_generation_reference is null
    ),

    check (
        assembly_status not in (
            'APPROVED',
            'REJECTED',
            'PUBLISHED',
            'RETIRED'
        )
        or locked_at is not null
    )
);

create table if not exists public.assessment_exam_questions (
    exam_question_id uuid primary key default gen_random_uuid(),

    exam_version_id uuid not null
        references public.assessment_exam_versions(exam_version_id)
        on delete cascade,

    blueprint_cell_id uuid not null
        references public.assessment_blueprint_cells(
            blueprint_cell_id
        )
        on delete restrict,

    question_version_id uuid not null
        references public.assessment_question_versions(
            question_version_id
        )
        on delete restrict,

    display_number integer not null
        check (display_number >= 1),

    assigned_score numeric(6,2) not null
        check (assigned_score > 0),

    selection_origin text not null default 'TEACHER'
        check (
            selection_origin in (
                'TEACHER',
                'AI_SUGGESTED',
                'IMPORTED'
            )
        ),

    ai_selection_reference text null,

    selection_note text not null default '',

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        exam_version_id,
        question_version_id
    ),

    unique (
        exam_version_id,
        display_number
    ),

    check (
        selection_origin = 'AI_SUGGESTED'
        or ai_selection_reference is null
    )
);

create or replace function
public.assessment_exam_version_is_visible(
    target_exam_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_exam_versions exam_version
        join public.assessment_exams exam
            on exam.exam_id = exam_version.exam_id
        where
            exam_version.exam_version_id =
                target_exam_version_id
            and (
                exam.owner_user_id = (select auth.uid())
                or public.current_user_is_portal_admin()
            )
    );
$$;

revoke all on function
public.assessment_exam_version_is_visible(uuid)
from public;

grant execute on function
public.assessment_exam_version_is_visible(uuid)
to authenticated;

create or replace function
public.assessment_exam_version_is_editable(
    target_exam_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_exam_versions exam_version
        join public.assessment_exams exam
            on exam.exam_id = exam_version.exam_id
        where
            exam_version.exam_version_id =
                target_exam_version_id
            and exam.owner_user_id = (select auth.uid())
            and exam_version.assembly_status in (
                'DRAFT',
                'AI_PROPOSED',
                'ASSEMBLED',
                'REVISION_REQUIRED'
            )
            and exam_version.locked_at is null
    );
$$;

revoke all on function
public.assessment_exam_version_is_editable(uuid)
from public;

grant execute on function
public.assessment_exam_version_is_editable(uuid)
to authenticated;

create or replace function
public.enforce_assessment_exam_version_context()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    exam_owner_user_id uuid;
    exam_subject_code text;
    exam_education_level text;
    exam_grade_level integer;

    blueprint_status text;
    blueprint_locked_at timestamptz;
    blueprint_total_score numeric(6,2);
    blueprint_duration_minutes integer;
    blueprint_subject_code text;
    blueprint_education_level text;
    blueprint_grade_level integer;
begin
    select
        exam.owner_user_id,
        exam.subject_code,
        exam.education_level,
        exam.grade_level
    into
        exam_owner_user_id,
        exam_subject_code,
        exam_education_level,
        exam_grade_level
    from public.assessment_exams exam
    where exam.exam_id = new.exam_id;

    if exam_owner_user_id is null then
        raise exception
            'Assessment exam does not exist.';
    end if;

    if exam_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may create or modify its version.';
    end if;

    select
        blueprint_version.review_status,
        blueprint_version.locked_at,
        blueprint_version.total_score,
        blueprint_version.duration_minutes,
        blueprint.subject_code,
        blueprint.education_level,
        blueprint.grade_level
    into
        blueprint_status,
        blueprint_locked_at,
        blueprint_total_score,
        blueprint_duration_minutes,
        blueprint_subject_code,
        blueprint_education_level,
        blueprint_grade_level
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            new.blueprint_version_id;

    if blueprint_status is null then
        raise exception
            'Assessment blueprint version does not exist.';
    end if;

    if (
        blueprint_status is distinct from 'APPROVED'
        or blueprint_locked_at is null
    ) then
        raise exception
            'Only an approved locked blueprint may assemble an exam.';
    end if;

    if (
        exam_subject_code is distinct from blueprint_subject_code
        or exam_education_level
            is distinct from blueprint_education_level
        or exam_grade_level is distinct from blueprint_grade_level
    ) then
        raise exception
            'Exam context does not match blueprint context.';
    end if;

    if (
        new.total_score is distinct from blueprint_total_score
        or new.duration_minutes
            is distinct from blueprint_duration_minutes
    ) then
        raise exception
            'Exam totals must match the approved blueprint.';
    end if;

    return new;
end;
$$;

revoke all on function
public.enforce_assessment_exam_version_context()
from public;

drop trigger if exists
assessment_exam_versions_context
on public.assessment_exam_versions;

create trigger assessment_exam_versions_context
before insert or update of
    exam_id,
    blueprint_version_id,
    total_score,
    duration_minutes
on public.assessment_exam_versions
for each row
execute function
public.enforce_assessment_exam_version_context();

create or replace function
public.enforce_assessment_exam_question_alignment()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    expected_blueprint_version_id uuid;
    expected_topic_code text;
    expected_question_type_code text;
    expected_cognitive_level_code text;

    actual_question_type_code text;
    actual_cognitive_level_code text;
    actual_default_score numeric(6,2);
    actual_review_status text;
    actual_locked_at timestamptz;
    actual_lifecycle_status text;
    actual_subject_code text;
    actual_education_level text;
    actual_grade_level integer;

    exam_subject_code text;
    exam_education_level text;
    exam_grade_level integer;
begin
    if not public.assessment_exam_version_is_editable(
        new.exam_version_id
    ) then
        raise exception
            'Assessment exam version is not editable.';
    end if;

    select
        exam_version.blueprint_version_id,
        exam.subject_code,
        exam.education_level,
        exam.grade_level
    into
        expected_blueprint_version_id,
        exam_subject_code,
        exam_education_level,
        exam_grade_level
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where
        exam_version.exam_version_id =
            new.exam_version_id;

    select
        blueprint_cell.topic_code,
        blueprint_cell.question_type_code,
        blueprint_cell.cognitive_level_code
    into
        expected_topic_code,
        expected_question_type_code,
        expected_cognitive_level_code
    from public.assessment_blueprint_cells blueprint_cell
    where
        blueprint_cell.blueprint_cell_id =
            new.blueprint_cell_id
        and blueprint_cell.blueprint_version_id =
            expected_blueprint_version_id;

    if expected_topic_code is null then
        raise exception
            'Blueprint cell does not belong to the exam blueprint.';
    end if;

    select
        question_version.question_type_code,
        question_version.cognitive_level_code,
        question_version.default_score,
        question_version.review_status,
        question_version.locked_at,
        question.lifecycle_status,
        question.subject_code,
        question.education_level,
        question.grade_level
    into
        actual_question_type_code,
        actual_cognitive_level_code,
        actual_default_score,
        actual_review_status,
        actual_locked_at,
        actual_lifecycle_status,
        actual_subject_code,
        actual_education_level,
        actual_grade_level
    from public.assessment_question_versions question_version
    join public.assessment_question_items question
        on question.question_id =
            question_version.question_id
    where
        question_version.question_version_id =
            new.question_version_id;

    if actual_review_status is null then
        raise exception
            'Assessment question version does not exist.';
    end if;

    if (
        actual_review_status is distinct from 'APPROVED'
        or actual_locked_at is null
        or actual_lifecycle_status is distinct from 'ACTIVE'
    ) then
        raise exception
            'Only an active approved locked question may be used.';
    end if;

    if (
        actual_subject_code is distinct from exam_subject_code
        or actual_education_level
            is distinct from exam_education_level
        or actual_grade_level is distinct from exam_grade_level
    ) then
        raise exception
            'Question context does not match exam context.';
    end if;

    if (
        actual_question_type_code
            is distinct from expected_question_type_code
        or actual_cognitive_level_code
            is distinct from expected_cognitive_level_code
    ) then
        raise exception
            'Question type or cognitive level does not match matrix cell.';
    end if;

    if new.assigned_score is distinct from actual_default_score then
        raise exception
            'Assigned score must match the approved question score.';
    end if;

    if not exists (
        select 1
        from public.assessment_question_requirement_links
            question_requirement
        join public.assessment_learning_requirements requirement
            on requirement.requirement_code =
                question_requirement.requirement_code
        where
            question_requirement.question_version_id =
                new.question_version_id
            and question_requirement.link_role = 'PRIMARY'
            and requirement.topic_code = expected_topic_code
    ) then
        raise exception
            'Question primary requirement does not match matrix topic.';
    end if;

    return new;
end;
$$;

revoke all on function
public.enforce_assessment_exam_question_alignment()
from public;

drop trigger if exists
assessment_exam_questions_alignment
on public.assessment_exam_questions;

create trigger assessment_exam_questions_alignment
before insert or update
on public.assessment_exam_questions
for each row
execute function
public.enforce_assessment_exam_question_alignment();

alter table public.assessment_exams
    enable row level security;

alter table public.assessment_exam_versions
    enable row level security;

alter table public.assessment_exam_questions
    enable row level security;

revoke all on table
    public.assessment_exams,
    public.assessment_exam_versions,
    public.assessment_exam_questions
from anon;

grant select, insert, update
on table public.assessment_exams
to authenticated;

grant select, insert, update
on table public.assessment_exam_versions
to authenticated;

grant select, insert, update, delete
on table public.assessment_exam_questions
to authenticated;

drop policy if exists
assessment_exams_select_visible
on public.assessment_exams;

create policy assessment_exams_select_visible
on public.assessment_exams
for select
to authenticated
using (
    owner_user_id = (select auth.uid())
    or public.current_user_is_portal_admin()
);

drop policy if exists
assessment_exams_insert_owned
on public.assessment_exams;

create policy assessment_exams_insert_owned
on public.assessment_exams
for insert
to authenticated
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
assessment_exams_update_owned
on public.assessment_exams;

create policy assessment_exams_update_owned
on public.assessment_exams
for update
to authenticated
using (
    owner_user_id = (select auth.uid())
)
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
assessment_exam_versions_select_visible
on public.assessment_exam_versions;

create policy assessment_exam_versions_select_visible
on public.assessment_exam_versions
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(
        exam_version_id
    )
);

drop policy if exists
assessment_exam_versions_insert_owned
on public.assessment_exam_versions;

create policy assessment_exam_versions_insert_owned
on public.assessment_exam_versions
for insert
to authenticated
with check (
    exists (
        select 1
        from public.assessment_exams exam
        where
            exam.exam_id =
                assessment_exam_versions.exam_id
            and exam.owner_user_id =
                (select auth.uid())
    )
    and created_by = (select auth.uid())
    and assembly_status in (
        'DRAFT',
        'AI_PROPOSED'
    )
    and locked_at is null
);

drop policy if exists
assessment_exam_versions_update_owned
on public.assessment_exam_versions;

create policy assessment_exam_versions_update_owned
on public.assessment_exam_versions
for update
to authenticated
using (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
)
with check (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
    and created_by = (select auth.uid())
    and exists (
        select 1
        from public.assessment_exams exam
        where
            exam.exam_id =
                assessment_exam_versions.exam_id
            and exam.owner_user_id =
                (select auth.uid())
    )
);

drop policy if exists
assessment_exam_questions_select_visible
on public.assessment_exam_questions;

create policy assessment_exam_questions_select_visible
on public.assessment_exam_questions
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(
        exam_version_id
    )
);

drop policy if exists
assessment_exam_questions_insert_editable
on public.assessment_exam_questions;

create policy assessment_exam_questions_insert_editable
on public.assessment_exam_questions
for insert
to authenticated
with check (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
);

drop policy if exists
assessment_exam_questions_update_editable
on public.assessment_exam_questions;

create policy assessment_exam_questions_update_editable
on public.assessment_exam_questions
for update
to authenticated
using (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
)
with check (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
);

drop policy if exists
assessment_exam_questions_delete_editable
on public.assessment_exam_questions;

create policy assessment_exam_questions_delete_editable
on public.assessment_exam_questions
for delete
to authenticated
using (
    public.assessment_exam_version_is_editable(
        exam_version_id
    )
);

comment on table public.assessment_exams is
'Teacher-owned identities for assembled assessment exams.';

comment on table public.assessment_exam_versions is
'Versioned exam papers assembled from approved blueprints.';

comment on table public.assessment_exam_questions is
'Ordered approved question versions assigned to blueprint cells.';

commit;

