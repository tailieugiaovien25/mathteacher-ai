from datetime import date

import pytest

from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.auto_ppct_scope_mapping_service import (
    AutoPPCTScopeMappingService,
)
from educational_planning_v2.services.ppct_scope_catalog import (
    PPCTScopeOption,
)


def make_assignment(
    *,
    component_ref=None,
):
    return TeachingAssignment(
        assignment_id="A-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id="class-6a1",
        role=TeachingAssignmentRole.TEACHING,
        subject_ref="subject-toan",
        component_ref=component_ref,
        effective_from=date(
            2026,
            9,
            1,
        ),
        effective_to=date(
            2027,
            5,
            31,
        ),
        status=(
            TeachingAssignmentStatus.ACTIVE
        ),
    )


def make_class():
    return ClassCatalog(
        class_id="class-6a1",
        academic_year="2026-2027",
        grade_level="6",
        class_code="6A1",
        class_name="6A1",
    )


def make_subject():
    return Subject(
        subject_id="subject-toan",
        code="TOAN",
        name="Toán",
        component_policy=(
            SubjectComponentPolicy.OPTIONAL
        ),
        status=CatalogStatus.ACTIVE,
        display_order=1,
    )


def test_resolves_subject_without_component():
    result = (
        AutoPPCTScopeMappingService()
        .resolve(
            assignment=make_assignment(),
            class_item=make_class(),
            subject=make_subject(),
            component=None,
            options=(
                PPCTScopeOption(
                    subject_grade="Toán 6",
                    sub_subject=None,
                ),
            ),
        )
    )

    assert (
        result.rule.subject_grade
        == "Toán 6"
    )
    assert result.rule.sub_subject is None


def test_resolves_component_scope():
    component = SubjectComponent(
        component_id="component-so-hoc",
        subject_id="subject-toan",
        code="SO_HOC",
        name="Số học",
        status=CatalogStatus.ACTIVE,
        display_order=1,
    )

    result = (
        AutoPPCTScopeMappingService()
        .resolve(
            assignment=make_assignment(
                component_ref=(
                    "component-so-hoc"
                ),
            ),
            class_item=make_class(),
            subject=make_subject(),
            component=component,
            options=(
                PPCTScopeOption(
                    subject_grade="Toán 6",
                    sub_subject="Số học",
                ),
            ),
        )
    )

    assert (
        result.rule.component_ref
        == "component-so-hoc"
    )
    assert (
        result.rule.sub_subject
        == "Số học"
    )


def test_rejects_missing_scope():
    with pytest.raises(
        LookupError,
        match="no PPCT scope matches",
    ):
        (
            AutoPPCTScopeMappingService()
            .resolve(
                assignment=make_assignment(),
                class_item=make_class(),
                subject=make_subject(),
                component=None,
                options=(
                    PPCTScopeOption(
                        subject_grade="Toán 7",
                    ),
                ),
            )
        )
