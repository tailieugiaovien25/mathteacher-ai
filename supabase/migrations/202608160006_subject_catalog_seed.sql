/*
Canonical subject/component seed.

Stable IDs/codes are machine identifiers.
Vietnamese names are canonical display values.
UI must read this catalog instead of hard-coding subjects/components.
*/


-- ============================================================
-- SUBJECTS
-- ============================================================

insert into public.subjects (
    subject_id,
    code,
    name,
    component_policy,
    status,
    display_order
)
values
    (
        'subject-math',
        'MATH',
        'Toán',
        'OPTIONAL',
        'ACTIVE',
        10
    ),
    (
        'subject-literature',
        'LITERATURE',
        'Ngữ văn',
        'NONE',
        'ACTIVE',
        20
    ),
    (
        'subject-foreign-language-1',
        'FOREIGN_LANGUAGE_1',
        'Ngoại ngữ 1',
        'NONE',
        'ACTIVE',
        30
    ),
    (
        'subject-civic-education',
        'CIVIC_EDUCATION',
        'Giáo dục công dân',
        'NONE',
        'ACTIVE',
        40
    ),
    (
        'subject-natural-science',
        'NATURAL_SCIENCE',
        'Khoa học tự nhiên',
        'OPTIONAL',
        'ACTIVE',
        50
    ),
    (
        'subject-history-geography',
        'HISTORY_GEOGRAPHY',
        'Lịch sử và Địa lí',
        'OPTIONAL',
        'ACTIVE',
        60
    ),
    (
        'subject-technology',
        'TECHNOLOGY',
        'Công nghệ',
        'NONE',
        'ACTIVE',
        70
    ),
    (
        'subject-informatics',
        'INFORMATICS',
        'Tin học',
        'NONE',
        'ACTIVE',
        80
    ),
    (
        'subject-physical-education',
        'PHYSICAL_EDUCATION',
        'Giáo dục thể chất',
        'NONE',
        'ACTIVE',
        90
    ),
    (
        'subject-art',
        'ART',
        'Nghệ thuật',
        'OPTIONAL',
        'ACTIVE',
        100
    ),
    (
        'subject-experiential-activities',
        'EXPERIENTIAL_ACTIVITIES',
        'Hoạt động trải nghiệm, hướng nghiệp',
        'NONE',
        'ACTIVE',
        110
    ),
    (
        'subject-local-education',
        'LOCAL_EDUCATION',
        'Nội dung giáo dục của địa phương',
        'NONE',
        'ACTIVE',
        120
    )
on conflict (
    subject_id
)
do update set
    code = excluded.code,
    name = excluded.name,
    component_policy = excluded.component_policy,
    status = excluded.status,
    display_order = excluded.display_order,
    updated_at = now();


-- ============================================================
-- MATHEMATICS COMPONENTS
-- ============================================================

insert into public.subject_components (
    component_id,
    subject_id,
    code,
    name,
    status,
    display_order,
    description
)
values
    (
        'component-math-arithmetic',
        'subject-math',
        'ARITHMETIC',
        'Số học',
        'ACTIVE',
        10,
        'Phân môn Số học của môn Toán.'
    ),
    (
        'component-math-algebra',
        'subject-math',
        'ALGEBRA',
        'Đại số',
        'ACTIVE',
        20,
        'Phân môn Đại số của môn Toán.'
    ),
    (
        'component-math-statistics-probability',
        'subject-math',
        'SXTK',
        'SXTK',
        'ACTIVE',
        30,
        'Phân môn xác suất và thống kê của môn Toán.'
    ),
    (
        'component-math-geometry',
        'subject-math',
        'GEOMETRY',
        'Hình học',
        'ACTIVE',
        40,
        'Phân môn Hình học của môn Toán.'
    )
on conflict (
    component_id
)
do update set
    subject_id = excluded.subject_id,
    code = excluded.code,
    name = excluded.name,
    status = excluded.status,
    display_order = excluded.display_order,
    description = excluded.description,
    updated_at = now();


-- ============================================================
-- NATURAL SCIENCE COMPONENTS
-- ============================================================

insert into public.subject_components (
    component_id,
    subject_id,
    code,
    name,
    status,
    display_order,
    description
)
values
    (
        'component-natural-science-physics',
        'subject-natural-science',
        'PHYSICS',
        'Vật lí',
        'ACTIVE',
        10,
        'Phân môn Vật lí của môn Khoa học tự nhiên.'
    ),
    (
        'component-natural-science-chemistry',
        'subject-natural-science',
        'CHEMISTRY',
        'Hóa học',
        'ACTIVE',
        20,
        'Phân môn Hóa học của môn Khoa học tự nhiên.'
    ),
    (
        'component-natural-science-biology',
        'subject-natural-science',
        'BIOLOGY',
        'Sinh học',
        'ACTIVE',
        30,
        'Phân môn Sinh học của môn Khoa học tự nhiên.'
    )
on conflict (
    component_id
)
do update set
    subject_id = excluded.subject_id,
    code = excluded.code,
    name = excluded.name,
    status = excluded.status,
    display_order = excluded.display_order,
    description = excluded.description,
    updated_at = now();


-- ============================================================
-- HISTORY AND GEOGRAPHY COMPONENTS
-- ============================================================

insert into public.subject_components (
    component_id,
    subject_id,
    code,
    name,
    status,
    display_order,
    description
)
values
    (
        'component-history-geography-history',
        'subject-history-geography',
        'HISTORY',
        'Lịch sử',
        'ACTIVE',
        10,
        'Phân môn Lịch sử.'
    ),
    (
        'component-history-geography-geography',
        'subject-history-geography',
        'GEOGRAPHY',
        'Địa lí',
        'ACTIVE',
        20,
        'Phân môn Địa lí.'
    )
on conflict (
    component_id
)
do update set
    subject_id = excluded.subject_id,
    code = excluded.code,
    name = excluded.name,
    status = excluded.status,
    display_order = excluded.display_order,
    description = excluded.description,
    updated_at = now();


-- ============================================================
-- ART COMPONENTS
-- ============================================================

insert into public.subject_components (
    component_id,
    subject_id,
    code,
    name,
    status,
    display_order,
    description
)
values
    (
        'component-art-music',
        'subject-art',
        'MUSIC',
        'Âm nhạc',
        'ACTIVE',
        10,
        'Phân môn Âm nhạc của môn Nghệ thuật.'
    ),
    (
        'component-art-fine-arts',
        'subject-art',
        'FINE_ARTS',
        'Mĩ thuật',
        'ACTIVE',
        20,
        'Phân môn Mĩ thuật của môn Nghệ thuật.'
    )
on conflict (
    component_id
)
do update set
    subject_id = excluded.subject_id,
    code = excluded.code,
    name = excluded.name,
    status = excluded.status,
    display_order = excluded.display_order,
    description = excluded.description,
    updated_at = now();
