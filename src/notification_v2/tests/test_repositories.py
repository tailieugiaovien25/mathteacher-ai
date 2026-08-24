import inspect

import pytest

from notification_v2.repositories import (
    NotificationRepository,
)


def test_notification_repository_is_abstract():
    assert inspect.isabstract(
        NotificationRepository
    )


def test_incomplete_repository_cannot_be_instantiated():
    class IncompleteRepository(
        NotificationRepository
    ):
        pass

    with pytest.raises(TypeError):
        IncompleteRepository()


def test_repository_contract_has_required_operations():
    required = {
        "save",
        "get",
        "list_for_owner",
        "count_unread",
        "mark_read",
        "mark_all_read",
    }

    assert required.issubset(
        NotificationRepository.__abstractmethods__
    )


def test_list_for_owner_contract_is_owner_scoped():
    signature = inspect.signature(
        NotificationRepository.list_for_owner
    )

    assert "owner_id" in signature.parameters
    assert "status" in signature.parameters
    assert "limit" in signature.parameters


def test_get_contract_requires_owner_scope():
    signature = inspect.signature(
        NotificationRepository.get
    )

    assert "notification_id" in signature.parameters
    assert "owner_id" in signature.parameters


def test_mark_read_contract_requires_owner_scope():
    signature = inspect.signature(
        NotificationRepository.mark_read
    )

    assert "notification_id" in signature.parameters
    assert "owner_id" in signature.parameters
    assert "read_at" in signature.parameters


def test_mark_all_read_contract_requires_owner_scope():
    signature = inspect.signature(
        NotificationRepository.mark_all_read
    )

    assert "owner_id" in signature.parameters
    assert "read_at" in signature.parameters
