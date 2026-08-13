from curriculum_v2.authority import (
    CanonicalCurriculumAuthoritySource,
)
from curriculum_v2.canonical_curriculum import (
    get_canonical_curriculum,
)
from curriculum_v2.providers import (
    CapabilityEducationalDataProvider,
)
from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
)


CURRICULUM_REF = "CURRICULUM-MATH-2018"
SUBJECT_REF = "MATHEMATICS"
GRADE = 6


def main():
    print("=" * 76)
    print(
        "WR-001D.12B.4 - REAL CANONICAL AUTHORITY "
        "PROVIDER INTEGRATION TEST"
    )
    print("=" * 76)

    results = []

    facade = get_canonical_curriculum()

    authority = (
        CanonicalCurriculumAuthoritySource(
            facade=facade,
            curriculum_refs=(
                CURRICULUM_REF,
            ),
            subject_refs=(
                SUBJECT_REF,
            ),
        )
    )

    def requirements_handler(
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        requirements = (
            authority.requirements_for_grade(
                curriculum_ref=query.curriculum_ref,
                subject_ref=query.subject_ref,
                grade=int(query.grade_ref),
            )
        )

        return EducationalDataResult(
            capability=query.capability,
            data=requirements,
            provenance=EducationalDataProvenance(
                source_id="CANONICAL-CURRICULUM",
                authority_type="OFFICIAL_CANONICAL",
                source_version="CURRENT",
                status="VERIFIED",
            ),
            version=EducationalDataVersion(
                version_id="CURRENT",
            ),
        )

    def nodes_handler(
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        nodes = (
            authority.nodes_for_grade(
                curriculum_ref=query.curriculum_ref,
                subject_ref=query.subject_ref,
                grade=int(query.grade_ref),
            )
        )

        return EducationalDataResult(
            capability=query.capability,
            data=nodes,
            provenance=EducationalDataProvenance(
                source_id="CANONICAL-CURRICULUM",
                authority_type="OFFICIAL_CANONICAL",
                source_version="CURRENT",
                status="VERIFIED",
            ),
            version=EducationalDataVersion(
                version_id="CURRENT",
            ),
        )

    provider = (
        CapabilityEducationalDataProvider(
            handlers={
                "learning_requirements":
                    requirements_handler,
                "curriculum_nodes":
                    nodes_handler,
            }
        )
    )

    requirements_result = provider.query(
        EducationalDataQuery(
            capability="learning_requirements",
            curriculum_ref=CURRICULUM_REF,
            subject_ref=SUBJECT_REF,
            grade_ref=str(GRADE),
        )
    )

    nodes_result = provider.query(
        EducationalDataQuery(
            capability="curriculum_nodes",
            curriculum_ref=CURRICULUM_REF,
            subject_ref=SUBJECT_REF,
            grade_ref=str(GRADE),
        )
    )

    requirements = (
        requirements_result.data
    )

    nodes = (
        nodes_result.data
    )

    checks = [
        (
            "RCAPI1 Real requirements returned",
            len(requirements) == 80,
        ),
        (
            "RCAPI2 Real nodes returned",
            len(nodes) == 43,
        ),
        (
            "RCAPI3 All requirements verified",
            all(
                item.status == "VERIFIED"
                for item in requirements
            ),
        ),
        (
            "RCAPI4 Requirement curriculum preserved",
            all(
                item.curriculum_ref
                == CURRICULUM_REF
                for item in requirements
            ),
        ),
        (
            "RCAPI5 Node curriculum preserved",
            all(
                item.curriculum_ref
                == CURRICULUM_REF
                for item in nodes
            ),
        ),
        (
            "RCAPI6 Requirement provenance preserved",
            all(
                item.provenance.source_document_id
                == "SRC-CUR-MATH-2018"
                for item in requirements
            ),
        ),
        (
            "RCAPI7 Provider result verified",
            requirements_result.provenance.status
            == "VERIFIED",
        ),
        (
            "RCAPI8 Provider boundary used",
            requirements_result.capability
            == "learning_requirements",
        ),
        (
            "RCAPI9 Generic new capability works",
            nodes_result.capability
            == "curriculum_nodes",
        ),
    ]

    requirement_ids = {
        item.canonical_id
        for item in requirements
    }

    checks.append(
        (
            "RCAPI10 Requirement IDs unique",
            len(requirement_ids)
            == len(requirements),
        )
    )

    node_ids = {
        item.curriculum_node_id
        for item in nodes
    }

    checks.append(
        (
            "RCAPI11 Node IDs unique",
            len(node_ids)
            == len(nodes),
        )
    )

    referenced_nodes = {
        item.curriculum_node_ref
        for item in requirements
    }

    checks.append(
        (
            "RCAPI12 Requirement node refs valid",
            referenced_nodes.issubset(
                node_ids
            ),
        )
    )

    for label, passed in checks:
        results.append(
            passed
        )

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()
    print("REAL DATA SUMMARY")
    print(
        "CURRICULUM REF       :",
        CURRICULUM_REF,
    )
    print(
        "SUBJECT REF          :",
        SUBJECT_REF,
    )
    print(
        "GRADE                :",
        GRADE,
    )
    print(
        "REQUIREMENTS         :",
        len(requirements),
    )
    print(
        "CURRICULUM NODES     :",
        len(nodes),
    )
    print(
        "REFERENCED NODES     :",
        len(referenced_nodes),
    )
    print(
        "SOURCE DOCUMENT IDS  :",
        sorted(
            {
                item.provenance.source_document_id
                for item in requirements
            }
        ),
    )
    print()

    if all(results):
        print(
            "RESULT: PASS - REAL CANONICAL "
            "AUTHORITY PROVIDER INTEGRATION VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - REAL CANONICAL "
            "AUTHORITY PROVIDER INTEGRATION VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
