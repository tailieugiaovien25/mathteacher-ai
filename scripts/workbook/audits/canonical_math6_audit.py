import json
from collections import Counter
from pathlib import Path

from curriculum_v2.processors import (
    load_canonical_requirements,
)
from curriculum_v2.validators import (
    validate_canonical_dataset,
)


BASE = (
    Path("src")
    / "curriculum_v2"
    / "data"
)

SOURCE_FILE = (
    BASE
    / "sources"
    / "SRC-CUR-MATH-2018.json"
)

GRADE_DIR = (
    BASE
    / "canonical"
    / "mathematics"
    / "grade_06"
)

NODES_FILE = (
    GRADE_DIR
    / "curriculum_nodes.json"
)

REQUIREMENTS_FILE = (
    GRADE_DIR
    / "learning_requirements.json"
)


print("=" * 78)
print("WR-001D.4 - CANONICAL MATH 6 DATASET REALITY AUDIT")
print("=" * 78)


# ------------------------------------------------------------
# 1. Physical source verification
# ------------------------------------------------------------

print()
print("SOURCE FILES")

files = (
    SOURCE_FILE,
    NODES_FILE,
    REQUIREMENTS_FILE,
)

for path in files:
    print(
        f"{path}: "
        f"{'FOUND' if path.exists() else 'MISSING'}"
    )

missing = [
    path
    for path in files
    if not path.exists()
]

if missing:
    print()
    print("RESULT: FAIL - REQUIRED CANONICAL FILE MISSING")
    raise SystemExit(1)


# ------------------------------------------------------------
# 2. Load raw canonical data
# ------------------------------------------------------------

with SOURCE_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    source_data = json.load(file)

with NODES_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    nodes_data = json.load(file)

with REQUIREMENTS_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    requirements_data = json.load(file)


# ------------------------------------------------------------
# 3. Canonical validation
# ------------------------------------------------------------

errors = validate_canonical_dataset(
    REQUIREMENTS_FILE,
    NODES_FILE,
    SOURCE_FILE,
)

requirements = load_canonical_requirements(
    REQUIREMENTS_FILE
)

nodes = nodes_data["nodes"]


print()
print("DATASET IDENTITY")
print(
    "SOURCE ID               : "
    f"{source_data.get('source_id')}"
)
print(
    "CURRICULUM REF          : "
    f"{requirements_data.get('curriculum_ref')}"
)
print(
    "SCHEMA VERSION          : "
    f"{requirements_data.get('schema_version')}"
)


# ------------------------------------------------------------
# 4. Dataset statistics
# ------------------------------------------------------------

print()
print("DATASET STATISTICS")
print(
    f"CURRICULUM NODES        : "
    f"{len(nodes)}"
)
print(
    f"CANONICAL REQUIREMENTS  : "
    f"{len(requirements)}"
)

status_counts = Counter(
    requirement.status
    for requirement in requirements
)

print()
print("STATUS DISTRIBUTION")

for status, count in sorted(
    status_counts.items()
):
    print(
        f"{status:<24}: {count}"
    )


# ------------------------------------------------------------
# 5. Integrity
# ------------------------------------------------------------

print()
print("CANONICAL VALIDATION")
print(
    f"VALIDATION ERRORS       : "
    f"{len(errors)}"
)

for error in errors[:30]:
    print(f"- {error}")

canonical_ids = [
    requirement.canonical_id
    for requirement in requirements
]

unique_ids = set(canonical_ids)

print(
    f"UNIQUE IDS              : "
    f"{len(unique_ids)}"
)

print(
    "ALL IDS UNIQUE          : "
    f"{len(unique_ids) == len(canonical_ids)}"
)

verified_count = sum(
    requirement.status == "VERIFIED"
    for requirement in requirements
)

print(
    f"VERIFIED REQUIREMENTS   : "
    f"{verified_count}/{len(requirements)}"
)


# ------------------------------------------------------------
# 6. Node coverage
# ------------------------------------------------------------

node_counts = Counter(
    requirement.curriculum_node_ref
    for requirement in requirements
)

node_ids = {
    node["curriculum_node_id"]
    for node in nodes
}

referenced_nodes = set(
    node_counts
)

unreferenced_nodes = (
    node_ids
    - referenced_nodes
)

unknown_nodes = (
    referenced_nodes
    - node_ids
)

print()
print("CURRICULUM NODE COVERAGE")
print(
    f"DEFINED NODES           : "
    f"{len(node_ids)}"
)
print(
    f"REFERENCED NODES        : "
    f"{len(referenced_nodes)}"
)
print(
    f"UNREFERENCED NODES      : "
    f"{len(unreferenced_nodes)}"
)
print(
    f"UNKNOWN NODE REFS       : "
    f"{len(unknown_nodes)}"
)


# ------------------------------------------------------------
# 7. Requirements by node
# ------------------------------------------------------------

print()
print("REQUIREMENTS BY NODE")

for node_id in sorted(node_ids):
    print(
        f"{node_id:<32} "
        f"{node_counts.get(node_id, 0)}"
    )


# ------------------------------------------------------------
# 8. First canonical records
# ------------------------------------------------------------

print()
print("FIRST 20 CANONICAL REQUIREMENTS")

for requirement in requirements[:20]:
    text = " ".join(
        requirement
        .requirement_text_original
        .split()
    )

    if len(text) > 100:
        text = text[:97] + "..."

    print(
        f"{requirement.canonical_id} | "
        f"{requirement.curriculum_node_ref} | "
        f"{requirement.status} | "
        f"{text}"
    )


# ------------------------------------------------------------
# 9. Provenance consistency
# ------------------------------------------------------------

source_ids = {
    requirement.provenance.source_document_id
    for requirement in requirements
}

regulation_ids = {
    requirement.provenance.regulation_id
    for requirement in requirements
}

print()
print("PROVENANCE")
print(
    "SOURCE DOCUMENT IDS     : "
    f"{sorted(source_ids)}"
)
print(
    "REGULATION IDS          : "
    f"{sorted(regulation_ids)}"
)


# ------------------------------------------------------------
# 10. Final decision
# ------------------------------------------------------------

passed = (
    len(errors) == 0
    and len(requirements) > 0
    and len(unique_ids)
        == len(requirements)
    and verified_count
        == len(requirements)
    and len(unknown_nodes) == 0
)

print()
print("=" * 78)

if passed:
    print(
        "RESULT: PASS - "
        "CANONICAL MATH 6 DATASET VERIFIED"
    )
else:
    print(
        "RESULT: REVIEW REQUIRED - "
        "CANONICAL MATH 6 DATASET "
        "IS NOT GENERATION-READY"
    )

print("=" * 78)
