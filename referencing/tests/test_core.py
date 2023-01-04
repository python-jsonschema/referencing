import referencing


def test_with_resource():
    """
    Adding a resource to the registry then allows re-retrieving it.
    """

    resource = referencing.Resource(
        contents={"foo": "bar"},
        specification=referencing.Specification.OPAQUE,
    )
    uri = "urn:example"
    registry = referencing.Registry().with_resources([(uri, resource)])
    assert registry[uri] is resource
