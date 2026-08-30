from datetime import datetime, timezone

from portal_v2.context.identity import ContextIdentity
from portal_v2.context.models import ContextChange, SystemContext
from portal_v2.context.user_scoped_store import UserScopedContextStore


def make_context(user: str, week: int, subject: str) -> SystemContext:
    return SystemContext(
        user_id=user,
        academic_year="2026-2027",
        week_number=week,
        subject_ref=subject,
    )


def make_change(field: str, value, page: str, control: str) -> ContextChange:
    return ContextChange(
        field=field,
        value=value,
        source_page=page,
        source_control=control,
        occurred_at=datetime.now(timezone.utc),
    )


def test_two_users_are_isolated():
    store = UserScopedContextStore()
    user_a = ContextIdentity.create(user_id="teacher-a")
    user_b = ContextIdentity.create(user_id="teacher-b")

    store.put(user_a, make_context("teacher-a", 5, "MATH"))
    store.put(user_b, make_context("teacher-b", 8, "ENGLISH"))

    store.apply(
        user_a,
        make_change(
            "week_number",
            6,
            "weekly_schedule",
            "week_selector",
        ),
    )

    assert store.get(user_a).week_number == 6
    assert store.get(user_b).week_number == 8
    assert store.get(user_b).subject_ref == "ENGLISH"


def test_same_user_can_have_two_independent_context_ids():
    store = UserScopedContextStore()
    context_a = ContextIdentity.create(user_id="teacher-a")
    context_b = ContextIdentity.create(user_id="teacher-a")

    store.put(context_a, make_context("teacher-a", 5, "MATH"))
    store.put(context_b, make_context("teacher-a", 9, "MATH"))

    store.apply(
        context_a,
        make_change("week_number", 7, "page-a", "week-a"),
    )

    assert store.get(context_a).week_number == 7
    assert store.get(context_b).week_number == 9


def test_cross_user_put_is_rejected():
    store = UserScopedContextStore()
    identity = ContextIdentity.create(user_id="teacher-a")

    try:
        store.put(
            identity,
            make_context("teacher-b", 5, "MATH"),
        )
    except ValueError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("cross-user context must be rejected")


def test_existing_contextchange_contract_is_reused():
    item = make_change(
        "week_number",
        5,
        "standardization",
        "week_selector",
    )
    assert item.field == "week_number"
    assert item.source_page == "standardization"
    assert item.source_control == "week_selector"
    assert item.occurred_at.tzinfo is not None


def test_subject_change_does_not_touch_other_user():
    store = UserScopedContextStore()
    user_a = ContextIdentity.create(user_id="teacher-a")
    user_b = ContextIdentity.create(user_id="teacher-b")

    store.put(user_a, make_context("teacher-a", 5, "MATH"))
    store.put(user_b, make_context("teacher-b", 8, "ENGLISH"))

    store.apply(
        user_a,
        make_change(
            "subject_ref",
            "ENGLISH",
            "standardization",
            "subject_selector",
        ),
    )

    assert store.get(user_a).subject_ref == "ENGLISH"
    assert store.get(user_b).subject_ref == "ENGLISH"
    assert store.get(user_b).week_number == 8
