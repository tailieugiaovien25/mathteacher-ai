import pytest

from src.multiai_v2.capability_catalog import CapabilityCatalog
from src.multiai_v2.contracts import ProviderCapability


def _capability(
    capability_id: str = "lesson.pedagogical_proposal",
    version: str = "1.0",
) -> ProviderCapability:
    return ProviderCapability(
        capability_id=capability_id,
        version=version,
    )


def test_empty_catalog_is_allowed():
    catalog = CapabilityCatalog()

    assert catalog.capabilities() == ()


def test_capability_can_be_registered():
    catalog = CapabilityCatalog()

    capability = _capability()

    catalog.register(capability)

    assert catalog.capabilities() == (capability,)


def test_registered_capability_can_be_resolved():
    catalog = CapabilityCatalog()

    capability = _capability()
    catalog.register(capability)

    result = catalog.get(
        capability_id="lesson.pedagogical_proposal",
        version="1.0",
    )

    assert result == capability


def test_unknown_capability_returns_none():
    catalog = CapabilityCatalog()

    result = catalog.get(
        capability_id="lesson.unknown",
        version="1.0",
    )

    assert result is None


def test_same_capability_id_can_have_multiple_versions():
    catalog = CapabilityCatalog()

    version_1 = _capability(version="1.0")
    version_2 = _capability(version="2.0")

    catalog.register(version_1)
    catalog.register(version_2)

    assert catalog.get(
        "lesson.pedagogical_proposal",
        "1.0",
    ) == version_1

    assert catalog.get(
        "lesson.pedagogical_proposal",
        "2.0",
    ) == version_2


def test_duplicate_capability_registration_is_blocked():
    catalog = CapabilityCatalog()

    catalog.register(_capability())

    with pytest.raises(ValueError):
        catalog.register(_capability())


def test_registration_requires_provider_capability():
    catalog = CapabilityCatalog()

    with pytest.raises(TypeError):
        catalog.register("lesson.pedagogical_proposal")


def test_lookup_identity_is_normalized():
    catalog = CapabilityCatalog()

    capability = _capability()
    catalog.register(capability)

    result = catalog.get(
        "  lesson.pedagogical_proposal  ",
        "  1.0  ",
    )

    assert result == capability


def test_empty_lookup_identity_is_blocked():
    catalog = CapabilityCatalog()

    with pytest.raises(ValueError):
        catalog.get("", "1.0")

    with pytest.raises(ValueError):
        catalog.get(
            "lesson.pedagogical_proposal",
            "   ",
        )


def test_catalog_has_no_provider_selection_responsibility():
    forbidden = {
        "select_provider",
        "rank_provider",
        "route",
        "fallback",
        "execute",
        "accept",
        "reject",
    }

    assert forbidden.isdisjoint(CapabilityCatalog.__dict__)