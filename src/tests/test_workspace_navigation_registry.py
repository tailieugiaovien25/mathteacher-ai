"""Keep the new route IDs compatible with the production menu during rollout."""

import ast
from pathlib import Path

from portal_v2.ui.workspace_navigation import (
    TEACHER_ROUTES,
    admin_routes,
    route_from_label,
    visible_teacher_labels,
)
from portal_v2.ui.admin_navigation import admin_portal_pages


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
