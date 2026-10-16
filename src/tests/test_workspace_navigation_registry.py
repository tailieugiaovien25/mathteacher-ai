"""Keep the new route IDs compatible with the production menu during rollout."""

import ast
from pathlib import Path

from portal_v2.ui.workspace_navigation import (
    TEACHER_ROUTES,
    admin_routes,
    labels_for_group,
    navigation_groups,
    route_from_label,
    visible_teacher_labels,
)
from portal_v2.ui.admin_navigation import admin_portal_pages
from scripts.teacher_portal.app import _select_teacher_navigation_group


def test_teacher_registry_preserves_legacy_menu_order():
    source = Path(__file__).resolve().parents[2] / "scripts/teacher_portal/app.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PORTAL_PAGES"
                for target in node.targets)
    )
    assert visible_teacher_labels() == ast.literal_eval(assignment.value)


def test_route_ids_and_hidden_legacy_destinations():
    assert len({route.route_id for route in TEACHER_ROUTES}) == len(TEACHER_ROUTES)
    assert len({route.label for route in TEACHER_ROUTES}) == len(TEACHER_ROUTES)
    assert route_from_label("Lớp học ôn tập").route_id == "classroom"
    assert route_from_label("Công cụ soạn bài").visible is False
    assert route_from_label("Soạn bài cùng chuẩn giáo án V2").visible is False


def test_admin_registry_keeps_canonical_ids_and_review_page():
    routes = admin_routes()
    assert tuple((route.route_id, route.label) for route in routes[:-1]) == tuple(
        (page.page_id, page.label) for page in admin_portal_pages()
    )
    assert routes[-1].route_id == "math_question_reviews"
    assert len({route.route_id for route in routes}) == len(routes)


def test_grouping_keeps_all_visible_destinations_once():
    for routes, expected in ((TEACHER_ROUTES, visible_teacher_labels()),
                             (admin_routes(), tuple(route.label for route in admin_routes()))):
        grouped = tuple(
            label for group in navigation_groups(routes)
            for label in labels_for_group(routes, group)
        )
        assert len(grouped) == len(expected)
        assert set(grouped) == set(expected)


def test_group_change_preserves_teacher_autosave_request():
    state = {"portal_page": "Tổng quan", "portal_navigation_group": "Đề kiểm tra",
             "lesson_authoring_working_context": {"draft": "kept"}}
    _select_teacher_navigation_group(state)
    assert state["portal_navigation_request"] == "Thiết đặt đề kiểm tra"
    assert state["portal_navigation_autosave"]["previous_page"] == "Tổng quan"
    assert state["portal_navigation_autosave"]["lesson_context"] == {"draft": "kept"}
