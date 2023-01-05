from referencing import Registry, Resource, Specification


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


def test_resource_from_contents_with_no_discernable_information():
    """
    Creating a resource with no discernable way to see what specification it
    belongs to (e.g. no $schema keyword for JSON Schema) creates one with an
    opaque specification.
    """

    resource = Resource.from_contents({"foo": "bar"})
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
