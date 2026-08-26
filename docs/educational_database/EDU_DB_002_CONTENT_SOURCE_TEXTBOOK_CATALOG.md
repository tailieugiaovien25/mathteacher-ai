# EDU-DB-002 — Content Source & Textbook Catalog

## 1. Purpose

EDU-DB-002 establishes the common educational-content source model
for MathTeacher-AI.

The model MUST support all tools through one shared data foundation:

- Lesson authoring
- Lesson-plan standardization
- Assessment generation
- Presentation / lecture generation
- Learning-resource retrieval
- Future educational AI tools

Core rule:

> Data may change; the system must not change.

No application tool may hard-code textbook names, grades, subjects,
publishers, media types, units, lessons, or source locations into its
business logic.

---

## 2. First supported subject scopes

### Mathematics

- Subject identity: `subject-math`
- Grades: 6, 7, 8, 9
- Initial textbook family:
  `Kết nối tri thức với cuộc sống`

### English

- Subject identity: `subject-foreign-language-1`
- Grades: 6, 7, 8, 9
- Initial textbook family:
  `Global Success`

English is a first-class subject.

Listening, Speaking, Reading, Writing, Grammar, Vocabulary and
Pronunciation are NOT subjects and are NOT subject components.

They may be represented later as pedagogical skills, content tags,
learning activities or media metadata.

---

## 3. Shared source architecture

The architecture must support these logical entities.

### 3.1 educational_sources

Represents the stable identity of an educational source.

Examples:

- Student textbook
- Teacher book
- Workbook
- Curriculum document
- Official guidance
- Audio collection
- Video collection
- Image collection
- Transcript collection
- Worksheet collection

The source identity MUST be independent from a physical file.

---

### 3.2 educational_source_versions

Represents a specific version or edition of an educational source.

A version may change while the source identity remains stable.

Examples:

- 2026 edition
- revised edition
- corrected digital copy
- publisher update

---

### 3.3 textbook_catalog

Represents textbook identity and publication metadata.

A textbook MUST link to:

- education program
- subject
- grade
- source identity

Textbook names MUST be data, never application constants.

---

### 3.4 textbook_units

Represents hierarchical textbook structure.

The structure MUST support arbitrary depth.

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

The system MUST NOT require the same hierarchy for every subject.

---

### 3.5 media_assets

Represents reusable educational media.

Supported initial asset categories:

- PDF
- IMAGE
- AUDIO
- VIDEO
- TRANSCRIPT
- DOCUMENT
- WORKSHEET
- ARCHIVE
- EXTERNAL_LINK

A media asset MAY belong to:

- a source version
- a textbook
- a unit
- a lesson
- another canonical educational entity

---

### 3.6 source_scope_links

Links educational content to canonical educational scope.

The canonical scope is based on:

- program_id
- subject_id
- grade_id

Tools query scope data instead of embedding subject/grade rules.

---

## 4. Stable identity rules

Every canonical entity MUST have a stable application identifier.

Examples:

- source-...
- source-version-...
- textbook-...
- textbook-unit-...
- media-...

Display names, filenames, storage locations and URLs MUST NOT be used
as canonical identity.

---

## 5. Storage independence

Database identity MUST be independent from physical storage.

A media asset may point to:

- Supabase Storage
- Google Drive
- local import staging
- publisher URL
- authorized external repository
- future storage providers

Changing storage provider MUST NOT require changing educational
business logic.

---

## 6. Versioning rules

Educational content is versioned.

Historical versions MUST remain identifiable even when a newer version
becomes active.

Tools SHOULD resolve the active version through data state rather than
hard-coded version numbers.

---

## 7. Textbook hierarchy rules

Textbook structure MUST be data-driven.

Required fields must support:

- parent node
- node type
- title
- display order
- canonical code
- optional lesson number
- optional curriculum-period mapping

The schema MUST support different structures across subjects without
schema changes.

---

## 8. Media rules for English

English content may include richer media than Mathematics.

The shared model MUST support:

- audio tracks
- listening scripts
- pronunciation audio
- dialogue audio
- video
- images
- transcripts
- workbook files
- supplementary worksheets

These are assets linked to educational content.

They do NOT create a separate English database architecture.

---

## 9. Cross-tool reuse

All application tools MUST resolve educational content from this common
foundation.

Examples:

Lesson authoring:
→ textbook lesson
→ requirements
→ media

Assessment:
→ curriculum scope
→ lesson/unit
→ learning requirements

Lecture generation:
→ lesson
→ images
→ audio/video
→ teaching resources

No tool owns a private copy of textbook identity.

---

## 10. ADMIN governance

ADMIN MUST be able to:

- add sources
- deactivate sources
- create new source versions
- add textbook editions
- edit metadata
- add grades
- add future subjects
- add media assets
- correct source mappings

These operations MUST NOT require application-code changes when they
remain within the canonical schema contract.

---

## 11. Initial canonical textbook targets

Initial data targets:

### Mathematics

- Grades 6–9
- `subject-math`
- Textbook family:
  `Kết nối tri thức với cuộc sống`

### English

- Grades 6–9
- `subject-foreign-language-1`
- Textbook family:
  `Global Success`

The architecture MUST remain open to additional approved textbook
families and additional subjects.

---

## 12. Non-goals of EDU-DB-002

EDU-DB-002 does NOT yet:

- ingest full textbook content
- download textbook PDFs
- extract OCR
- create embeddings
- generate lesson plans
- generate assessments
- store copyrighted textbook page reproductions

Those are later ingestion and application activities.

EDU-DB-002 defines the canonical catalog and source architecture first.

---

## 13. Architectural acceptance criteria

EDU-DB-002 design is acceptable only if:

1. Mathematics and English use the same source architecture.
2. English remains a first-class subject.
3. Textbook names are data.
4. Grade and subject scope are canonical references.
5. Media storage is provider-independent.
6. Textbook hierarchy is data-driven.
7. Versioning is explicit.
8. ADMIN can extend catalog data without code changes.
9. All educational tools can reuse the same canonical records.
10. Adding another subject does not require redesigning the schema.
