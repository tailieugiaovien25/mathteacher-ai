from types import SimpleNamespace

import pytest

from portal_v2.authorization.portal_role_source import (
    PortalRoleResolution,
)
from portal_v2.authorization.supabase_session_guard import (
    PortalSessionValidationError,
    validate_supabase_portal_session,
)


class FakeAuth:
    def __init__(self, *, user=None, error=None):
        self.user = user
        self.error = error
        self.calls = 0

    def get_user(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return SimpleNamespace(user=self.user)


class FakeClient:
    def __init__(self, auth):
        self.auth = auth


class SequenceRoleSource:
    def __init__(self, *resolutions):
        self.resolutions = list(resolutions)
        self.calls = []

    def resolve_role(self, *, user_id):
        self.calls.append(user_id)
        return self.resolutions.pop(0)


def role(*, role="teacher", trusted=True, active=True):
    return PortalRoleResolution(
        user_id="user-1",
        role=role,
        source_ref="TEST",
        trusted=trusted,
        active=active,
    )


def client_with_user(
    user_id="user-1",
    email="teacher@example.com",
):
    auth = FakeAuth(
        user=SimpleNamespace(
            id=user_id,
            email=email,
        )
    )
    return FakeClient(auth), auth


def test_valid_session_returns_fresh_trusted_role():
    client, auth = client_with_user()
    source = SequenceRoleSource(
        role(role="admin")
    )

    validated = validate_supabase_portal_session(
        client=client,
        expected_user_id="user-1",
        role_source=source,
    )

    assert validated.user_id == "user-1"
    assert validated.email == "teacher@example.com"
    assert validated.role == "admin"
    assert auth.calls == 1
    assert source.calls == ["user-1"]


def test_role_is_revalidated_on_each_protected_rerun():
    client, auth = client_with_user()
    source = SequenceRoleSource(
        role(role="admin"),
        role(role="teacher"),
    )

    first = validate_supabase_portal_session(
        client=client,
        expected_user_id="user-1",
        role_source=source,
    )
    second = validate_supabase_portal_session(
        client=client,
        expected_user_id="user-1",
        role_source=source,
    )

    assert first.role == "admin"
    assert second.role == "teacher"
    assert auth.calls == 2


def test_missing_authenticated_user_fails_closed():
    client = FakeClient(
        FakeAuth(user=None)
    )

    with pytest.raises(PortalSessionValidationError):
        validate_supabase_portal_session(
            client=client,
            expected_user_id="user-1",
            role_source=SequenceRoleSource(role()),
        )


def test_cached_identity_mismatch_fails_closed():
    client, _ = client_with_user(
        user_id="other-user"
    )

    with pytest.raises(PortalSessionValidationError):
        validate_supabase_portal_session(
            client=client,
            expected_user_id="user-1",
            role_source=SequenceRoleSource(role()),
        )


def test_untrusted_or_inactive_role_cannot_access_portal():
    client, _ = client_with_user()

    for denied_role in (
        role(trusted=False, active=False),
        role(trusted=True, active=False),
    ):
        with pytest.raises(PortalSessionValidationError):
            validate_supabase_portal_session(
                client=client,
                expected_user_id="user-1",
                role_source=SequenceRoleSource(denied_role),
            )


def test_auth_server_failure_fails_closed():
    client = FakeClient(
        FakeAuth(error=RuntimeError("network"))
    )

    with pytest.raises(PortalSessionValidationError):
        validate_supabase_portal_session(
            client=client,
            expected_user_id="user-1",
            role_source=SequenceRoleSource(role()),
        )
