from hypothesis import given, settings

from referencing.tests.strategies import registries, resources


@settings(max_examples=25)
@given(resources())
def test_resources_are_opaque(resource):
    assert resource.id() is None
    assert list(resource.subresources()) == []
    assert list(resource.anchors()) == []


@settings(max_examples=25)
@given(registries())
def test_registries_contain_unique_resource_uris(registry):
    assert len(registry) == len(set(registry))
    assert all(registry[uri].id() is None for uri in registry)
