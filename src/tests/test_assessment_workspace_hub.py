from portal_v2.ui.assessment_workspace_hub import (
    ASSESSMENT_EXPERIMENTAL_DESTINATIONS,
    ASSESSMENT_LEGACY_DESTINATIONS,
    ASSESSMENT_PRIMARY_DESTINATIONS,
)
from portal_v2.ui.workspace_navigation import route_from_label, visible_teacher_labels
from scripts.teacher_portal.app import select_portal_page


def test_hub_destinations_keep_legacy_routes_without_duplicates():
    targets = [target for _, target, _ in (
        *ASSESSMENT_PRIMARY_DESTINATIONS, *ASSESSMENT_EXPERIMENTAL_DESTINATIONS
    )]
    assert len(targets) == len(set(targets)) == len(ASSESSMENT_LEGACY_DESTINATIONS)
    assert all(route_from_label(target).space == "teacher" for target in targets)
    assert "Đề kiểm tra" in visible_teacher_labels()
    assert {"Tạo đề kiểm tra Toán 6", "Tạo đề kiểm tra Toán 6–9", "Xưởng câu hỏi"} <= {
        target for _, target, _ in ASSESSMENT_EXPERIMENTAL_DESTINATIONS
    }


def test_hub_navigation_only_queues_a_request():
    state = {"portal_page": "Đề kiểm tra"}
    select_portal_page(state, "Tạo đề kiểm tra")
    assert state == {"portal_page": "Đề kiểm tra",
                     "portal_navigation_request": "Tạo đề kiểm tra"}
