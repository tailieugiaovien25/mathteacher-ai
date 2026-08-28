# EDU-DB-002 — Schema Contract

## Canonical entities

The implementation phase is expected to provide or extend these
logical entities.

### Existing from EDU-DB-001

- education_programs
- grades
- education_program_scopes
- educational_sources
- educational_source_versions
- canonical_entity_links

EDU-DB-002 MUST reuse these foundations rather than duplicate them.

---

## New logical entities

### textbook_catalog

Purpose:
Stable textbook identity and publication catalog.

Required logical fields:

- textbook_id
- source_id
- program_id
- subject_id
- grade_id
- textbook_family_code
- textbook_code
- title
- edition_label
- publisher_name
- publication_year
- volume_code
- status
- display_order
- metadata
- created_at
- updated_at

---

### textbook_units

Purpose:
Data-driven hierarchical structure for textbooks.

Required logical fields:

- textbook_unit_id
- textbook_id
- parent_unit_id
- unit_type
- canonical_code
- title
- sequence_number
- display_order
- curriculum_period_from
- curriculum_period_to
- status
- metadata
- created_at
- updated_at

`parent_unit_id` MUST support arbitrary hierarchy.

---

### media_assets

Purpose:
Canonical media identity independent from storage provider.

Required logical fields:

- media_asset_id
- source_version_id
- media_type
- title
- mime_type
- language_code
- duration_seconds
- page_number
- storage_provider
- storage_locator
- external_url
- checksum_sha256
- status
- metadata
- created_at
- updated_at

Storage credentials MUST NEVER be stored in this table.

---

### educational_asset_links

Purpose:
Reusable link between media and canonical educational entities.

Required logical fields:

- asset_link_id
- media_asset_id
- entity_type
- entity_id
- relation_type
- display_order
- status
- metadata
- created_at
- updated_at

The link model MUST allow the same asset to be reused by multiple
tools and educational entities.

---

## Identity constraints

Canonical IDs are immutable.

Human-readable titles and storage paths are mutable attributes.

Foreign keys MUST reference canonical identities, not names.

---

## Scope rules

A textbook belongs to one canonical:

program + subject + grade

A textbook's content hierarchy inherits that scope.

A source may be broader than a single textbook.

---

## Initial subject contracts

Mathematics:

subject_id = subject-math

English:

subject_id = subject-foreign-language-1

English MUST NOT be modeled as a subject component.

---

## Initial grade contract

Supported first:

grade-06
grade-07
grade-08
grade-09

The schema MUST support other grades without migration redesign.

---

## Media contract

Initial media types:

PDF
IMAGE
AUDIO
VIDEO
TRANSCRIPT
DOCUMENT
WORKSHEET
ARCHIVE
EXTERNAL_LINK

Media type expansion SHOULD be data-driven where practical.

---

## Governance contract

ADMIN operations must modify catalog/source records without requiring
changes in application code.

Application tools must query canonical source/catalog records.

---

## Migration implementation rule

The future EDU-DB-002 migration MUST be additive.

It MUST NOT:

- drop current tables
- delete existing operational data
- rename current application tables
- replace stable subject identities
- duplicate EDU-DB-001 canonical program/grade/scope data

Any required normalization of existing records must be separately
identified and guarded.
