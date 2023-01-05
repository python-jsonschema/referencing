import pytest

from referencing import (
    CannotDetermineSpecification,
    Registry,
    Resource,
    Specification,
)


def test_registry_with_resource():
    """
    Adding a resource to the registry then allows re-retrieving it.
    """

    resource = Resource(
        contents={"foo": "bar"},
        specification=Specification.OPAQUE,
    )
    uri = "urn:example"
    registry = Registry().with_resources([(uri, resource)])
    assert registry[uri] is resource


def test_registry_crawl_still_has_top_level_resource():
    resource = Resource(
        contents={"foo": "bar"},
        specification=Specification.OPAQUE,
    )
    uri = "urn:example"
    registry = Registry().with_resources([(uri, resource)]).crawl()
    assert registry[uri] is resource


def test_registry_contents():
    resource = Resource(
        contents={"foo": "bar"},
        specification=Specification.OPAQUE,
    )
    uri = "urn:example"
    registry = Registry().with_resources([(uri, resource)])
    assert registry.contents(uri) == {"foo": "bar"}


def test_resource_from_contents_with_no_discernible_information():
    """
    Creating a resource with no discernible way to see what specification it
    belongs to (e.g. no $schema keyword for JSON Schema) raises an error.
    """

    with pytest.raises(CannotDetermineSpecification):
        Resource.from_contents({"foo": "bar"})


def test_resource_from_contents_with_no_discernible_information_and_default():
    resource = Resource.from_contents(
        {"foo": "bar"},
        default_specification=Specification.OPAQUE,
    )
    assert resource == Resource(
        contents={"foo": "bar"},
        specification=Specification.OPAQUE,
    )


def test_resource_from_contents_unneeded_default():
    from referencing.jsonschema import DRAFT202012

    resource = Resource.from_contents(
        {"$schema": "https://json-schema.org/draft/2020-12/schema"},
        default_specification=Specification.OPAQUE,
    )
    assert resource == Resource(
        contents={"$schema": "https://json-schema.org/draft/2020-12/schema"},
        specification=DRAFT202012,
    )


def test_non_mapping_resource_from_contents_with_no_discernible_information():
    resource = Resource.from_contents(
        True,
        default_specification=Specification.OPAQUE,
    )
    assert resource == Resource(
        contents=True,
        specification=Specification.OPAQUE,
    )


def test_resource_from_contents_with_fallback():
    resource = Resource.from_contents(
        {"foo": "bar"},
        default_specification=Specification.OPAQUE,
    )
    assert resource == Resource(
        contents={"foo": "bar"},
        specification=Specification.OPAQUE,
    )


def test_resource_id_delegates_to_specification():
    specification = Specification(id_of=lambda contents: "urn:fixedID")
    resource = Resource(
        contents={"foo": "baz"},
        specification=specification,
    )
    assert resource.id() == "urn:fixedID"
