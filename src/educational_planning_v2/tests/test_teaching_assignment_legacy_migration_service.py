from datetime import date

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.teaching_assignment_legacy_migration_service import (
    TeachingAssignmentLegacyMigrationService,
)


def _assignment(
    *,
    class_id="8A1",
    subject_ref="Toan",
    component_ref="Hinh hoc",
):
    return TeachingAssignment(
        assignment_id="legacy-001",
        owner_id="user-1",
        academic_year="2026-2027",
        class_id=class_id,
        subject_ref=subject_ref,
        component_ref=component_ref,
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 8, 16),
        effective_to=date(2027, 8, 16),
        status=TeachingAssignmentStatus.ACTIVE,
    )


def test_atomic_assignment_is_not_legacy():
    preview = (
        TeachingAssignmentLegacyMigrationService()
        .preview(
            _assignment()
        )
    )

    assert preview.is_legacy is False
    assert preview.can_auto_migrate is False


def test_multi_dimension_legacy_requires_manual_review():
    preview = (
        TeachingAssignmentLegacyMigrationService()
        .preview(
            _assignment(
                class_id="6A1, 6A2, 7A1, 8A1",
                subject_ref="Toan, Am nhac",
                component_ref=(
                    "So hoc, Dai so, Hinh hoc"
                ),
            )
        )
    )

    assert preview.is_legacy is True
    assert preview.can_auto_migrate is False

    assert preview.class_refs == (
        "6A1",
        "6A2",
        "7A1",
        "8A1",
    )

    assert preview.subject_refs == (
        "Toan",
        "Am nhac",
    )

    assert preview.component_refs == (
        "So hoc",
        "Dai so",
        "Hinh hoc",
    )


def test_single_dimension_values_are_safe():
    preview = (
        TeachingAssignmentLegacyMigrationService()
        .preview(
            _assignment(
                class_id=" 8A1 ",
                subject_ref=" Toan ",
                component_ref=" Hinh hoc ",
            )
        )
    )

    assert preview.is_legacy is False
    assert preview.class_refs == ("8A1",)
    assert preview.subject_refs == ("Toan",)
    assert preview.component_refs == ("Hinh hoc",)


def test_semicolon_legacy_is_detected():
    preview = (
        TeachingAssignmentLegacyMigrationService()
        .preview(
            _assignment(
                class_id="8A1; 8A2",
            )
        )
    )

    assert preview.is_legacy is True
    assert preview.can_auto_migrate is False
