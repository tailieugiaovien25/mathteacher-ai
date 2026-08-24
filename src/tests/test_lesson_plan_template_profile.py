import pytest

from lesson_planning_v2.lesson_plan_template_profile import (
    DraftingWeekday,
    LessonPlanAlignment,
    LessonPlanApprovalProfile,
    LessonPlanHeaderProfile,
    LessonPlanLayoutProfile,
    LessonPlanSchedulingPolicy,
    LessonPlanStructureProfile,
    LessonPlanStructureSection,
    LessonPlanTemplateProfile,
)


def test_default_template_profile_exists():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    assert (
        profile.profile_name
        == "Mẫu giáo án THCS mặc định"
    )

    assert profile.is_default is True


def test_default_structure_has_expected_sections():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    keys = tuple(
        section.key
        for section
        in profile.structure.sections
    )

    assert "OBJECTIVES" in keys
    assert "EQUIPMENT" in keys
    assert "TEACHING_PROCESS" in keys
    assert "OPENING" in keys
    assert "KNOWLEDGE_FORMATION" in keys
    assert "PRACTICE" in keys
    assert "APPLICATION" in keys


def test_default_header_matches_agreed_rules():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    header = profile.header

    assert (
        header.drafting_teaching_alignment
        is LessonPlanAlignment.LEFT
    )

    assert (
        header.period_alignment
        is LessonPlanAlignment.CENTER
    )

    assert header.period_bold is True

    assert (
        header.lesson_title_alignment
        is LessonPlanAlignment.CENTER
    )

    assert (
        header.lesson_title_uppercase
        is True
    )

    assert (
        header.lesson_title_bold
        is True
    )


def test_default_layout_uses_times_new_roman():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    assert (
        profile.layout.font_name
        == "Times New Roman"
    )

    assert (
        profile.layout.page_size
        == "A4"
    )


def test_default_scheduling_policy():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    scheduling = profile.scheduling

    assert (
        scheduling.drafting_weekday
        is DraftingWeekday.SATURDAY
    )

    assert (
        scheduling.approval_offset_days
        == 2
    )

    assert (
        scheduling.allow_projected_teaching_dates
        is True
    )


def test_default_approval_profile():
    profile = (
        LessonPlanTemplateProfile
        .default()
    )

    approval = profile.approval

    assert (
        approval.alignment
        is LessonPlanAlignment.RIGHT
    )

    assert (
        approval.approval_label
        == "Tổ CM duyệt"
    )

    assert (
        approval.signature_blank_lines
        == 5
    )


def test_structure_can_be_customized():
    structure = LessonPlanStructureProfile(
        sections=(
            LessonPlanStructureSection(
                key="OBJECTIVES",
                title="I. MỤC TIÊU",
                order=10,
            ),
            LessonPlanStructureSection(
                key="CUSTOM",
                title="II. NỘI DUNG RIÊNG",
                order=20,
            ),
        )
    )

    assert (
        len(structure.sections)
        == 2
    )

    assert (
        structure.sections[1].key
        == "CUSTOM"
    )


def test_duplicate_structure_keys_rejected():
    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        LessonPlanStructureProfile(
            sections=(
                LessonPlanStructureSection(
                    key="OBJECTIVES",
                    title="I. MỤC TIÊU",
                    order=10,
                ),
                LessonPlanStructureSection(
                    key="OBJECTIVES",
                    title="MỤC TIÊU KHÁC",
                    order=20,
                ),
            )
        )


def test_template_profile_can_be_customized():
    profile = LessonPlanTemplateProfile(
        profile_name="Mẫu Tổ Toán",
        structure=(
            LessonPlanStructureProfile
            .default()
        ),
        header=LessonPlanHeaderProfile(),
        layout=LessonPlanLayoutProfile(
            body_font_size_pt=13,
            margin_left_cm=2.5,
        ),
        scheduling=(
            LessonPlanSchedulingPolicy(
                drafting_weekday=(
                    DraftingWeekday.FRIDAY
                ),
                approval_offset_days=3,
            )
        ),
        approval=(
            LessonPlanApprovalProfile(
                signature_blank_lines=6
            )
        ),
    )

    assert (
        profile.profile_name
        == "Mẫu Tổ Toán"
    )

    assert (
        profile.layout.body_font_size_pt
        == 13
    )

    assert (
        profile.scheduling.drafting_weekday
        is DraftingWeekday.FRIDAY
    )

    assert (
        profile.scheduling.approval_offset_days
        == 3
    )

    assert (
        profile.approval.signature_blank_lines
        == 6
    )
