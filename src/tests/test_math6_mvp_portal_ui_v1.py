from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from portal_v2.ui import math6_mvp_demo_streamlit as math6_ui
from portal_v2.ui.admin_navigation import (
    ADMIN_PAGE_ASSESSMENT_REVIEWS,
    ADMIN_PAGE_ASSESSMENT_TEMPLATES,
    ADMIN_PAGE_MATH6_ASSESSMENT,
    admin_portal_page_ids,
    admin_portal_pages,
)


ROOT = Path(__file__).resolve().parents[2]


class _NoRenderSt:
    def __getattr__(self, name):
        raise AssertionError(
            f"rendering started before role validation: {name}"
        )


class _RendererSt:
    def __init__(self, workflow):
        self.session_state = {
            math6_ui.SESSION_WORKFLOW_KEY: workflow,
        }

    def title(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None

    def divider(self, *args, **kwargs):
        return None


def test_invalid_role_raises_valueerror_before_rendering():
    with pytest.raises(ValueError, match="invalid role: superadmin"):
        math6_ui.render_math6_mvp_demo_role(
            _NoRenderSt(),
            role="superadmin",
        )


def test_shared_renderer_propagates_teacher_role(monkeypatch):
    workflow = math6_ui.InMemoryMath6MvpWorkflow()
    st = _RendererSt(workflow)
    calls = []

    monkeypatch.setattr(
        math6_ui,
        "_render_summary",
        lambda st, workflow: calls.append(("summary", None)),
    )
    monkeypatch.setattr(
        math6_ui,
        "_render_question_bank",
        lambda st, workflow, *, role: calls.append(
            ("question_bank", role)
        ),
    )
    monkeypatch.setattr(
        math6_ui,
        "_render_blueprint",
        lambda st, workflow, *, role: calls.append(
            ("blueprint", role)
        ),
    )
    monkeypatch.setattr(
        math6_ui,
        "_render_exam",
        lambda st, workflow, *, role: calls.append(
            ("exam", role)
        ),
    )

    math6_ui.render_math6_mvp_demo_role(st, role="teacher")

    assert calls == [
        ("summary", None),
        ("question_bank", "teacher"),
        ("blueprint", "teacher"),
        ("exam", "teacher"),
    ]


def test_legacy_renderer_delegates_to_admin(monkeypatch):
    calls = []

    def fake_role_renderer(st, *, role):
        calls.append((st, role))

    monkeypatch.setattr(
        math6_ui,
        "render_math6_mvp_demo_role",
        fake_role_renderer,
    )

    st = object()
    math6_ui.render_math6_mvp_demo(st)

    assert calls == [(st, "admin")]


def test_teacher_mode_has_explicit_admin_question_gates():
    source = inspect.getsource(math6_ui._render_question_bank)

    assert (
        'if role == "admin" and workflow.question_review_queue:'
        in source
    )
    assert 'if role == "admin" and lockable:' in source
    assert "workflow.review_question(" in source
    assert "workflow.lock_question(" in source


def test_teacher_mode_has_blueprint_exam_and_publish_gates():
    blueprint_source = inspect.getsource(
        math6_ui._render_blueprint
    )
    exam_source = inspect.getsource(math6_ui._render_exam)

    assert 'if role != "admin":\n            return' in blueprint_source
    assert "workflow.review_blueprint(" in blueprint_source

    assert exam_source.count(
        'if role != "admin":\n            return'
    ) >= 2
    assert "workflow.review_exam(" in exam_source
    assert "workflow.publish_exam(" in exam_source


def test_published_zip_download_is_not_admin_only():
    source = inspect.getsource(math6_ui._render_exam)

    published_marker = "elif exam.review_status == PUBLISHED:"
    assert published_marker in source

    published_tail = source.split(published_marker, 1)[1]

    assert "download_button(" in published_tail
    assert 'role == "admin"' not in published_tail
    assert 'role != "admin"' not in published_tail


def test_teacher_portal_wiring_and_existing_pages_preserved():
    source = (
        ROOT / "scripts/teacher_portal/app.py"
    ).read_text(encoding="utf-8")

    assert (
        r"'T\u1ea1o \u0111\u1ec1 ki\u1ec3m tra To\xe1n 6'"
        in source
    )
    assert 'selected == "T\u1ea1o \u0111\u1ec1 ki\u1ec3m tra To\xe1n 6"' in source
    assert 'render_math6_mvp_demo_role(st, role="teacher")' in source

    for existing_page in (
        r"'Thi\u1ebft \u0111\u1eb7t \u0111\u1ec1 ki\u1ec3m tra'",
        r"'Ma tr\u1eadn & b\u1ea3n \u0111\u1eb7c t\u1ea3'",
        r"'T\u1ea1o \u0111\u1ec1 ki\u1ec3m tra'",
        r"'Xu\u1ea5t \u0111\u1ec1 ki\u1ec3m tra'",
    ):
        assert existing_page in source


def test_admin_navigation_and_existing_pages_preserved():
    assert ADMIN_PAGE_MATH6_ASSESSMENT == "math6_assessment"
    assert ADMIN_PAGE_MATH6_ASSESSMENT in admin_portal_page_ids()

    pages = {
        page.page_id: page.label
        for page in admin_portal_pages()
    }

    assert (
        pages[ADMIN_PAGE_MATH6_ASSESSMENT]
        == "Qu\u1ea3n tr\u1ecb \u0111\u1ec1 ki\u1ec3m tra To\xe1n 6"
    )
    assert ADMIN_PAGE_ASSESSMENT_TEMPLATES in pages
    assert ADMIN_PAGE_ASSESSMENT_REVIEWS in pages
