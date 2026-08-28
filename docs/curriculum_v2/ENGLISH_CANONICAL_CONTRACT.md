# English Canonical Curriculum Contract

## 1. Purpose

This contract defines the canonical educational-data identity for
English learning requirements for Grades 6, 7, 8, and 9.

The English canonical dataset MUST reuse the existing
CanonicalLearningRequirement and curriculum-node architecture.

It MUST NOT introduce a competing learning-requirement schema.

## 2. Authority

- Source ID: `SRC-CUR-ENGLISH-2018`
- Curriculum ID: `CURRICULUM-ENGLISH-2018`
- Legal authority: Bộ Giáo dục và Đào tạo
- Regulation: `32/2018/TT-BGDĐT`
- Source type: `OFFICIAL_CURRICULUM`
- Target grades: 6, 7, 8, 9

The canonical YCCD source is the official curriculum.

A textbook family such as Global Success MUST NOT be treated as
the legal authority for canonical learning requirements.

## 3. Subject identity

- Subject ID: `subject-foreign-language-1`
- Subject name: `Tiếng Anh`
- Component policy: `NONE`

English MUST NOT be modeled as a subject component.

Listening, Speaking, Reading, Writing, pronunciation, vocabulary,
grammar, and other language-knowledge dimensions MUST be represented
inside the curriculum structure and MUST NOT create new subjects or
subject components.

## 4. Canonical namespace

Learning requirement IDs MUST use:

`YCCD-ENG-{GRADE_2_DIGITS}-{SEQUENCE_4_DIGITS}`

Examples:

- `YCCD-ENG-06-0001`
- `YCCD-ENG-07-0001`
- `YCCD-ENG-08-0001`
- `YCCD-ENG-09-0001`

Curriculum node IDs MUST use:

`CURR-NODE-ENG-G{GRADE}-{SEQUENCE_3_DIGITS}`

Examples:

- `CURR-NODE-ENG-G6-001`
- `CURR-NODE-ENG-G7-001`
- `CURR-NODE-ENG-G8-001`
- `CURR-NODE-ENG-G9-001`

## 5. Requirement schema

Every English canonical requirement MUST use exactly the same
record schema used by canonical Mathematics:

- `canonical_id`
- `curriculum_node_ref`
- `provenance`
- `requirement_text_original`
- `status`
- `validation`

No English-specific competing columns are permitted.

## 6. Provenance schema

Every requirement provenance object MUST use:

- `legal_authority`
- `regulation_id`
- `source_document_id`
- `source_location`
- `source_version`
- `verified_copy_id`

Required values include:

- `legal_authority = Bộ Giáo dục và Đào tạo`
- `regulation_id = 32/2018/TT-BGDĐT`
- `source_document_id = SRC-CUR-ENGLISH-2018`
- `source_version = 2018`

`source_location` MUST identify the official curriculum location
of the learning requirement.

## 7. Validation

Verified canonical records MUST satisfy all four gates:

- `identity_integrity = PASS`
- `provenance_integrity = PASS`
- `structural_integrity = PASS`
- `text_integrity = PASS`

A record MUST NOT have status `VERIFIED` unless all validation gates
are `PASS`.

## 8. Curriculum-node schema

English curriculum nodes MUST reuse the existing node schema:

- `code`
- `curriculum_node_id`
- `name`
- `node_type`
- `parent_id`
- `sequence`
- `status`

The curriculum-node hierarchy MAY represent language skills,
language knowledge, themes/topics, and other official curriculum
structures without changing the requirement record schema.

## 9. Textbook independence

Canonical YCCD MUST remain independent of textbook families.

The following relationship is permitted:

Official curriculum
-> canonical learning requirement
-> textbook mapping
-> textbook unit / lesson

The following relationship is prohibited:

Textbook unit
-> invented canonical YCCD

Global Success is an initial textbook family for English Grades 6-9,
not the authority source for canonical YCCD.

## 10. Extension rule

Future approved English textbook families MUST be addable without
changing the canonical YCCD identity.

Future subjects MUST be addable without redesigning this schema.

Data may change; the system architecture MUST remain stable.
