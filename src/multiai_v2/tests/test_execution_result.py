from dataclasses import FrozenInstanceError

import pytest

from src.multiai_v2.contracts import ExecutionResult


def test_valid_execution_result_is_accepted():
    result = ExecutionResult(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
        output_data={"value": "generated"},
        success=True,
    )

    assert result.capability_id == "lesson.pedagogical_proposal"
    assert result.capability_version == "1.0"
    assert result.provider_id == "provider-a"
    assert result.output_data == {"value": "generated"}
    assert result.success is True
    assert result.error is None


def test_execution_identity_is_normalized():
    result = ExecutionResult(
        capability_id="  lesson.pedagogical_proposal  ",
        capability_version="  1.0  ",
        provider_id="  provider-a  ",
        output_data=None,
        success=True,
    )

    assert result.capability_id == "lesson.pedagogical_proposal"
    assert result.capability_version == "1.0"
    assert result.provider_id == "provider-a"


@pytest.mark.parametrize(
    "field,value",
    [
        ("capability_id", "   "),
        ("capability_version", ""),
        ("provider_id", " "),
    ],
)
def test_empty_execution_identity_is_blocked(field, value):
    kwargs = {
        "capability_id": "lesson.pedagogical_proposal",
        "capability_version": "1.0",
        "provider_id": "provider-a",
        "output_data": None,
        "success": True,
    }
    kwargs[field] = value

    with pytest.raises(ValueError):
        ExecutionResult(**kwargs)


def test_failed_execution_can_carry_error():
    result = ExecutionResult(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
        output_data=None,
        success=False,
        error="provider timeout",
    )

    assert result.success is False
    assert result.error == "provider timeout"


def test_execution_result_is_immutable():
    result = ExecutionResult(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
        output_data=None,
        success=True,
    )

    with pytest.raises(FrozenInstanceError):
        result.provider_id = "provider-b"


def test_execution_result_has_no_acceptance_responsibility():
    forbidden = {
        "accept",
        "reject",
        "validate",
        "select_provider",
        "route",
        "fallback",
    }

    assert forbidden.isdisjoint(ExecutionResult.__dict__)

def test_error_is_normalized():
    result = ExecutionResult(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
        output_data=None,
        success=False,
        error="  provider timeout  ",
    )

    assert result.error == "provider timeout"


def test_empty_error_is_blocked_when_provided():
    with pytest.raises(ValueError):
        ExecutionResult(
            capability_id="lesson.pedagogical_proposal",
            capability_version="1.0",
            provider_id="provider-a",
            output_data=None,
            success=False,
            error="   ",
        )


def test_success_must_be_bool():
    with pytest.raises(TypeError):
        ExecutionResult(
            capability_id="lesson.pedagogical_proposal",
            capability_version="1.0",
            provider_id="provider-a",
            output_data=None,
            success="yes",
        )