from dataclasses import FrozenInstanceError

import pytest

from src.multiai_v2.contracts import CapabilityRequest


def test_valid_capability_request_is_accepted():
    request = CapabilityRequest(
        capability_id="generate_pedagogical_proposal",
        capability_version="1.0",
        input_data={"lesson": "LESSON-001"},
    )

    assert request.capability_id == "generate_pedagogical_proposal"
    assert request.capability_version == "1.0"
    assert request.input_data == {"lesson": "LESSON-001"}
    assert request.context is None


def test_capability_identity_is_normalized():
    request = CapabilityRequest(
        capability_id="  generate_pedagogical_proposal  ",
        capability_version="  1.0  ",
        input_data=None,
    )

    assert request.capability_id == "generate_pedagogical_proposal"
    assert request.capability_version == "1.0"


def test_empty_capability_id_is_blocked():
    with pytest.raises(
        ValueError,
        match="capability_id must not be empty",
    ):
        CapabilityRequest(
            capability_id="   ",
            capability_version="1.0",
            input_data=None,
        )


def test_empty_capability_version_is_blocked():
    with pytest.raises(
        ValueError,
        match="capability_version must not be empty",
    ):
        CapabilityRequest(
            capability_id="generate_text",
            capability_version="   ",
            input_data=None,
        )


def test_request_is_immutable():
    request = CapabilityRequest(
        capability_id="generate_text",
        capability_version="1.0",
        input_data="input",
    )

    with pytest.raises(FrozenInstanceError):
        request.capability_id = "other"


def test_public_contract_import_works():
    assert CapabilityRequest.__name__ == "CapabilityRequest"


def test_request_has_no_routing_responsibility():
    forbidden = {
        "route",
        "select_provider",
        "execute",
        "accept",
    }

    assert forbidden.isdisjoint(
        CapabilityRequest.__dict__
    )