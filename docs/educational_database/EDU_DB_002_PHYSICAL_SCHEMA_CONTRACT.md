# EDU-DB-002 — Physical Schema Contract

## 1. Purpose

This document locks the physical relational contract for
EDU-DB-002 before any Supabase migration is written.

EDU-DB-002 MUST reuse the canonical foundation created by EDU-DB-001.

Existing canonical tables MUST NOT be duplicated:

- public.education_programs
- public.grades
- public.education_program_scopes
- public.educational_sources
- public.educational_source_versions
- public.canonical_entity_links
- public.subjects

Core rule:

> Data may change; the system must not change.

---

## 2. New physical tables

EDU-DB-002 introduces four new physical tables:

1. public.textbook_catalog
2. public.textbook_units
3. public.media_assets
4. public.educational_asset_links

No fifth subject-specific table is permitted for English or Mathematics.

---

# 3. public.textbook_catalog

## 3.1 Purpose

Represents stable textbook identities.

One textbook record belongs to exactly one canonical:

program + subject + grade

and links to an existing educational source.

---

## 3.2 Columns

### textbook_id

Type:

text

Rules:

- PRIMARY KEY
- NOT NULL
- immutable application identity

Recommended format:

textbook-...

---

### source_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.educational_sources(source_id)

Delete policy:

RESTRICT

A source must not disappear while a textbook references it.

---

### program_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.education_programs(program_id)

Delete policy:

RESTRICT

---

### subject_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.subjects(subject_id)

Delete policy:

RESTRICT

Initial stable values include:

- subject-math
- subject-foreign-language-1

---

### grade_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.grades(grade_id)

Delete policy:

RESTRICT

Initial grades:

- grade-06
- grade-07
- grade-08
- grade-09

---

### textbook_family_code

Type:

text

Rules:

- NOT NULL
- non-empty
- stable family identity independent from display title

Examples:

- KNTT
- GLOBAL_SUCCESS

The exact seed values will be locked in a later activity.

---

### textbook_code

Type:

text

Rules:

- NOT NULL
- non-empty
- stable identifier within the catalog

---

### title

Type:

text

Rules:

- NOT NULL
- non-empty

Titles are display data and MUST NOT be used as foreign keys.

---

### edition_label

Type:

text

Rules:

- nullable

---

### publisher_name

Type:

text

Rules:

- nullable

Publisher identity may later be normalized into a separate catalog
without changing textbook identity.

---

### publication_year

Type:

integer

Rules:

- nullable
- CHECK between 1900 and 2200 when present

---

### volume_code

Type:

text

Rules:

- nullable

Supports books split into volumes.

---

### status

Type:

text

Rules:

- NOT NULL
- default ACTIVE
- CHECK in:
  - DRAFT
  - ACTIVE
  - INACTIVE
  - ARCHIVED

---

### display_order

Type:

integer

Rules:

- NOT NULL
- default 0
- CHECK display_order >= 0

---

### metadata

Type:

jsonb

Rules:

- NOT NULL
- default empty JSON object

---

### created_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

### updated_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

## 3.3 Uniqueness

Required unique identity:

(program_id, subject_id, grade_id, textbook_code)

This prevents duplicate canonical textbooks inside the same
educational scope.

A title is NOT a uniqueness key.

---

## 3.4 Indexes

Required indexes:

- program_id
- subject_id
- grade_id
- source_id
- status
- (program_id, subject_id, grade_id)
- textbook_family_code

---

# 4. public.textbook_units

## 4.1 Purpose

Represents arbitrary hierarchical structure inside a textbook.

This table MUST support both Mathematics and English without
schema changes.

Examples:

Mathematics:

Book
→ Chapter
→ Lesson
→ Section

English:

Book
→ Unit
→ Lesson
→ Skills / Looking Back / Project

---

## 4.2 Columns

### textbook_unit_id

Type:

text

Rules:

- PRIMARY KEY
- NOT NULL

Recommended format:

textbook-unit-...

---

### textbook_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.textbook_catalog(textbook_id)

Delete policy:

CASCADE

If a catalog entry is intentionally removed before production use,
its structural nodes may be removed together.

Operational deletion of active textbooks remains governed separately.

---

### parent_unit_id

Type:

text

Rules:

- nullable
- self FOREIGN KEY to public.textbook_units(textbook_unit_id)

Delete policy:

CASCADE

Null means root-level node.

---

### unit_type

Type:

text

Rules:

- NOT NULL
- non-empty

Examples may include:

- BOOK
- PART
- CHAPTER
- UNIT
- LESSON
- SECTION
- SKILL
- REVIEW
- PROJECT
- APPENDIX

The schema MUST NOT enforce one fixed hierarchy.

---

### canonical_code

Type:

text

Rules:

- NOT NULL
- non-empty

Identity is stable inside the parent textbook.

---

### title

Type:

text

Rules:

- NOT NULL
- non-empty

---

### sequence_number

Type:

integer

Rules:

- nullable
- CHECK sequence_number > 0 when present

---

### display_order

Type:

integer

Rules:

- NOT NULL
- default 0
- CHECK display_order >= 0

---

### curriculum_period_from

Type:

integer

Rules:

- nullable
- CHECK > 0 when present

---

### curriculum_period_to

Type:

integer

Rules:

- nullable
- CHECK > 0 when present

Additional rule:

when both period values are present:

curriculum_period_to >= curriculum_period_from

---

### status

Type:

text

Rules:

- NOT NULL
- default ACTIVE
- CHECK in:
  - DRAFT
  - ACTIVE
  - INACTIVE
  - ARCHIVED

---

### metadata

Type:

jsonb

Rules:

- NOT NULL
- default empty JSON object

---

### created_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

### updated_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

## 4.3 Uniqueness

Required:

(textbook_id, canonical_code)

This allows codes to repeat across different textbooks but never
inside the same textbook.

---

## 4.4 Self-reference integrity

The migration implementation MUST prevent:

parent_unit_id = textbook_unit_id

Cross-textbook parenting MUST also be prevented.

A child cannot reference a parent belonging to another textbook.

This may be enforced using a composite foreign-key design or an
equivalent guarded implementation.

---

## 4.5 Indexes

Required indexes:

- textbook_id
- parent_unit_id
- unit_type
- status
- (textbook_id, display_order)
- (textbook_id, parent_unit_id, display_order)

---

# 5. public.media_assets

## 5.1 Purpose

Represents reusable media identities independently from physical
storage providers.

English and Mathematics MUST share this table.

---

## 5.2 Columns

### media_asset_id

Type:

text

Rules:

- PRIMARY KEY
- NOT NULL

Recommended format:

media-...

---

### source_version_id

Type:

text

Rules:

- nullable
- FOREIGN KEY to
  public.educational_source_versions(source_version_id)

Delete policy:

SET NULL

The asset may remain cataloged even if a source version is later
retired.

---

### media_type

Type:

text

Rules:

- NOT NULL
- CHECK in:
  - PDF
  - IMAGE
  - AUDIO
  - VIDEO
  - TRANSCRIPT
  - DOCUMENT
  - WORKSHEET
  - ARCHIVE
  - EXTERNAL_LINK

---

### title

Type:

text

Rules:

- NOT NULL
- non-empty

---

### mime_type

Type:

text

Rules:

- nullable

Examples:

- application/pdf
- image/png
- audio/mpeg
- video/mp4
- text/plain

---

### language_code

Type:

text

Rules:

- nullable

Examples:

- vi
- en

---

### duration_seconds

Type:

numeric

Rules:

- nullable
- CHECK duration_seconds >= 0 when present

---

### page_number

Type:

integer

Rules:

- nullable
- CHECK page_number > 0 when present

---

### storage_provider

Type:

text

Rules:

- NOT NULL

Initial supported values:

- SUPABASE
- GOOGLE_DRIVE
- LOCAL_IMPORT
- EXTERNAL

The model remains provider-independent.

---

### storage_locator

Type:

text

Rules:

- nullable

This stores an object identifier, file path, bucket/object key or
equivalent locator.

It MUST NOT contain passwords, access tokens or service credentials.

---

### external_url

Type:

text

Rules:

- nullable

---

### checksum_sha256

Type:

text

Rules:

- nullable

When present:

- exactly 64 hexadecimal characters

---

### status

Type:

text

Rules:

- NOT NULL
- default ACTIVE
- CHECK in:
  - DRAFT
  - ACTIVE
  - INACTIVE
  - ARCHIVED
  - BROKEN

---

### metadata

Type:

jsonb

Rules:

- NOT NULL
- default empty JSON object

---

### created_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

### updated_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

## 5.3 Locator rule

At least one must be present:

- storage_locator
- external_url

The database must not accept an asset with neither a storage locator
nor an external URL.

---

## 5.4 Indexes

Required indexes:

- source_version_id
- media_type
- storage_provider
- status
- checksum_sha256

Checksum is indexed for duplicate detection but is NOT necessarily
globally unique because intentional reuse is allowed.

---

# 6. public.educational_asset_links

## 6.1 Purpose

Provides reusable links between a media asset and educational entities.

The same media may be reused in several contexts.

---

## 6.2 Columns

### asset_link_id

Type:

text

Rules:

- PRIMARY KEY
- NOT NULL

---

### media_asset_id

Type:

text

Rules:

- NOT NULL
- FOREIGN KEY to public.media_assets(media_asset_id)

Delete policy:

CASCADE

---

### entity_type

Type:

text

Rules:

- NOT NULL
- CHECK initial values in:
  - TEXTBOOK
  - TEXTBOOK_UNIT
  - SOURCE
  - SOURCE_VERSION
  - PROGRAM_SCOPE
  - CANONICAL_ENTITY

This list may be extended through controlled migration when needed.

---

### entity_id

Type:

text

Rules:

- NOT NULL
- non-empty

Because the target entity is polymorphic, normal SQL foreign keys
cannot cover all target tables through a single column.

Referential integrity MUST therefore be enforced by the application
service and/or a guarded database trigger.

---

### relation_type

Type:

text

Rules:

- NOT NULL
- non-empty

Initial semantic examples:

- PRIMARY_DOCUMENT
- SUPPLEMENTARY_DOCUMENT
- COVER_IMAGE
- ILLUSTRATION
- LISTENING_AUDIO
- PRONUNCIATION_AUDIO
- DIALOGUE_AUDIO
- VIDEO
- TRANSCRIPT
- WORKSHEET
- TEACHING_RESOURCE

---

### display_order

Type:

integer

Rules:

- NOT NULL
- default 0
- CHECK display_order >= 0

---

### status

Type:

text

Rules:

- NOT NULL
- default ACTIVE
- CHECK in:
  - ACTIVE
  - INACTIVE
  - ARCHIVED

---

### metadata

Type:

jsonb

Rules:

- NOT NULL
- default empty JSON object

---

### created_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

### updated_at

Type:

timestamptz

Rules:

- NOT NULL
- default now()

---

## 6.3 Uniqueness

Required uniqueness:

(media_asset_id, entity_type, entity_id, relation_type)

The same media may link to the same entity under different relation
types, but an identical semantic link may not be duplicated.

---

## 6.4 Indexes

Required indexes:

- media_asset_id
- entity_type
- entity_id
- relation_type
- status
- (entity_type, entity_id)
- (entity_type, entity_id, display_order)

---

# 7. Lifecycle rules

Physical deletion must not be the normal ADMIN operation.

Normal lifecycle changes use status fields.

Typical progression:

DRAFT
→ ACTIVE
→ INACTIVE
→ ARCHIVED

BROKEN is additionally available for media assets when the underlying
storage object cannot be resolved.

---

# 8. Timestamp rule

Every new EDU-DB-002 table must contain:

- created_at
- updated_at

The migration implementation should reuse the repository's established
updated_at trigger pattern where compatible.

It MUST NOT introduce a competing timestamp mechanism without review.

---

# 9. RLS and privileges

EDU-DB-002 migration MUST NOT casually grant broad public write access.

Before deployment, implementation must inspect the repository's
existing Supabase RLS and privilege conventions.

The migration must follow those conventions.

ADMIN write capability will be exposed through governed application
services, not direct anonymous table writes.

---

# 10. English media model

English remains:

subject_id = subject-foreign-language-1

English media such as:

- Listening audio
- Speaking dialogue audio
- Pronunciation audio
- Videos
- Images
- Transcripts
- Worksheets

must be represented through media_assets + educational_asset_links.

These media categories MUST NOT create subject components.

---

# 11. Mathematics media model

Mathematics remains:

subject_id = subject-math

Typical assets may include:

- textbook PDFs
- diagrams
- illustrations
- worksheets
- teacher resources
- videos

They use the same media_assets and educational_asset_links tables.

---

# 12. Initial textbook scope

Initial catalog scope:

program-vn-gdpt-2018

Mathematics:

- subject-math
- grade-06
- grade-07
- grade-08
- grade-09
- textbook family: Kết nối tri thức với cuộc sống

English:

- subject-foreign-language-1
- grade-06
- grade-07
- grade-08
- grade-09
- textbook family: Global Success

Textbook display names remain data.

---

# 13. Migration constraints

The future EDU-DB-002 migration MUST:

- be additive
- create only the new EDU-DB-002 structures
- reference EDU-DB-001 canonical identities
- preserve existing subject IDs
- preserve existing operational tables
- use guarded constraints
- use explicit indexes
- support UTF-8 content
- remain subject-neutral in its physical schema

The migration MUST NOT:

- DROP existing application tables
- DELETE existing operational records
- TRUNCATE existing tables
- rename stable subjects
- convert English into a subject component
- create a separate English-specific catalog architecture
- duplicate education_programs
- duplicate grades
- duplicate subjects
- duplicate educational_sources
- duplicate educational_source_versions

---


# 14. Repository alignment rules

The physical implementation MUST follow the established repository
conventions confirmed by EDU-DB-001 and existing migrations.

Canonical foreign-key identities use text:

- program_id
- subject_id
- grade_id
- source_id
- source_version_id

EDU-DB-002 metadata columns MUST be named:

metadata

and use:

jsonb not null default '{}'::jsonb

The implementation MUST NOT introduce metadata_json as a competing
column convention.

Foreign keys from textbook_catalog to canonical foundation tables
use ON DELETE RESTRICT.

media_assets.source_version_id uses ON DELETE SET NULL as explicitly
defined by the EDU-DB-002 contract.

The repository commonly uses:

- create index if not exists
- row level security
- revoke all before explicit grants
- authenticated read access for canonical catalog data

EDU-DB-002 therefore follows a catalog-governance model:

- anon receives no direct table privileges
- authenticated users may receive SELECT access
- direct authenticated INSERT/UPDATE/DELETE is not granted by default
- governed ADMIN/service operations perform mutations

New EDU-DB-002 tables contain created_at and updated_at because they
are mutable catalog entities.

This does not imply that every pre-existing EDU-DB-001 table has an
updated_at column.

---

# 15. Acceptance criteria


Physical schema contract passes only when:

1. Four new physical tables are defined.
2. EDU-DB-001 foundation is reused.
3. PK/FK behavior is explicit.
4. Uniqueness rules are explicit.
5. CHECK constraints are explicit.
6. Required indexes are explicit.
7. Textbook hierarchy supports arbitrary depth.
8. Cross-textbook parenting is prohibited.
9. Media storage is provider-independent.
10. Media credentials are prohibited.
11. English and Mathematics share one architecture.
12. English remains a first-class subject.
13. Media links are reusable across tools.
14. Lifecycle/status rules are explicit.
15. Migration remains additive.
